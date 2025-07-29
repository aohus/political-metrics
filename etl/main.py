import asyncio
import logging
import multiprocessing as mp
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Optional

from configs import Config


class PipelineStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class PipelineResult:
    """파이프라인 실행 결과를 담는 데이터 클래스"""
    task_id: int
    process_id: Optional[int] = None
    status: PipelineStatus = PipelineStatus.SUCCESS
    data: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        """직렬화를 위한 딕셔너리 변환"""
        return asdict(self)


@dataclass
class PipelineConfig:
    name: str
    module_path: str
    class_name: str
    init_args: dict[str, Any]
    timeout: float = 300.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def pipeline_worker(task_id: int, pl_config: dict[str, Any], kwargs: dict[str, Any]) -> dict[str, Any]:
    """
    독립적인 워커 함수 - 각 프로세스에서 실행됩니다.
    
    Args:
        task_id: 작업 ID
        pl_config: 파이프라인 설정
        kwargs: 파이프라인 실행 인자
        
    Returns:
        PipelineResult의 딕셔너리 형태
    """
    import importlib
    import os
    import time
    
    start_time = time.time()
    process_id = os.getpid()
    
    try:
        pipeline_config = PipelineConfig(**pl_config)
        
        # 동적 모듈 로드
        module = importlib.import_module(pipeline_config.module_path)
        pipeline_class = getattr(module, pipeline_config.class_name)
        
        pipeline = pipeline_class(**pipeline_config.init_args)
        
        if hasattr(pipeline, 'run'):
            try:
                result_data = asyncio.run(pipeline.run(task_id=task_id, **kwargs))
            except RuntimeError:
                # 이미 실행 중인 이벤트 루프가 있는 경우
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result_data = loop.run_until_complete(pipeline.run(task_id=task_id, **kwargs))
                finally:
                    loop.close()
        else:
            raise AttributeError(f"Pipeline {pipeline_config.name} has no run method")
        
        execution_time = time.time() - start_time
        
        return PipelineResult(
            task_id=task_id,
            process_id=process_id,
            status=PipelineStatus.SUCCESS,
            data=result_data,
            execution_time=execution_time
        ).to_dict()
        
    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        
        return PipelineResult(
            task_id=task_id,
            process_id=process_id,
            status=PipelineStatus.FAILED,
            error=error_msg,
            execution_time=execution_time
        ).to_dict()


class PipelineExecutor:
    """Orchestrates multiple pipelines using Protocol-based design"""
    
    def __init__(self, config: Config):
        self.config = config
        self._pipeline_configs = {}
        self.logger = logging.getLogger("PipelineExecutor")

    def register_pipeline(
        self,
        name: str,
        module_path: str,
        class_name: str,
        init_args: Optional[dict[str, Any]] = None,
        kwargs: Optional[dict[str, Any]] = None,
        timeout: float = 300.0
    ) -> None:
        """
        파이프라인을 등록합니다.
        
        Args:
            name: 파이프라인 이름
            module_path: 파이프라인 모듈 경로 (예: 'myapp.pipelines')
            class_name: 파이프라인 클래스 이름
            init_args: 파이프라인 초기화 인자
            timeout: 실행 타임아웃
        """
        pl_config = PipelineConfig(
            name=name,
            module_path=module_path,
            class_name=class_name,
            init_args=init_args or {},
            kwargs=kwargs or {},
            timeout=timeout
        )
        self._pipeline_configs[name] = pl_config
        self.logger.info(f"Pipeline registered: {name}")
    
    async def run_multi_pipeline(
        self,
        pipeline_name: str,
        max_workers: int = None,
        timeout: float = None,
        **kwargs
    ) -> list[dict]:
        
        if pipeline_name not in self._pipeline_configs:
            raise ValueError(f"Unknown pipeline: {pipeline_name}")
        
        config = self._pipeline_configs[pipeline_name]
        max_workers = max_workers or min(mp.cpu_count())
        timeout = timeout or None
        
        self.logger.info(
            f"Starting multiprocess batch execution: {pipeline_name}, "
            f"max_workers: {max_workers}, timeout: {timeout}s"
        )
        
        # 현재 실행 중인 이벤트 루프 가져오기
        loop = asyncio.get_running_loop()
        
        start_time = time.time()
        results = []
        
        try:
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                # 모든 태스크 제출
                future_to_task = {
                    loop.run_in_executor(
                        executor,
                        pipeline_worker,
                        i,
                        config.to_dict(),
                        kwargs
                    ): i
                    for i in range(max_workers)
                }

                for future in asyncio.as_completed(future_to_task.keys(), timeout=timeout):
                    try:
                        result_dict = await future
                        result = PipelineResult(**result_dict)
                        results.append(result)
                    except asyncio.TimeoutError:
                        task_id = future_to_task[future]
                        result = PipelineResult(
                            task_id=task_id,
                            status=PipelineStatus.TIMEOUT,
                            error="Task execution timed out"
                        )
                        results.append(result)
                    except Exception as e:
                        task_id = future_to_task[future]
                        result = PipelineResult(
                            task_id=task_id,
                            status=PipelineStatus.FAILED,
                            error=f"Unexpected error: {str(e)}"
                        )
                        results.append(result)

        except Exception as e:
            self.logger.error(f"Batch execution failed: {str(e)}")
            raise

        total_time = time.time() - start_time
        results.sort(key=lambda x: x.task_id)

        # 실행 통계 로깅
        success_count = sum(1 for r in results if r.status == PipelineStatus.SUCCESS)
        failed_count = sum(1 for r in results if r.status == PipelineStatus.FAILED)
        timeout_count = sum(1 for r in results if r.status == PipelineStatus.TIMEOUT)

        self.logger.info(
            f"Batch execution completed: {pipeline_name}, "
            f"total_time: {total_time:.2f}s, "
            f"success: {success_count}, failed: {failed_count}, timeout: {timeout_count}"
        )
        return results

    async def run_single_pipeline(
        self,
        pipeline_name: str,
        timeout: float = None,
        **kwargs
    ) -> PipelineResult:
        """
        단일 파이프라인을 현재 프로세스에서 실행합니다.

        Args:
            pipeline_name: 실행할 파이프라인 이름
            timeout: 실행 타임아웃 (기본값: 파이프라인 설정의 타임아웃)
            **kwargs: 파이프라인에 전달할 추가 매개변수

        Returns:
            PipelineResult: 실행 결과
        """
        if pipeline_name not in self._pipeline_configs:
            raise ValueError(f"Unknown pipeline: {pipeline_name}")

        pl_config = self._pipeline_configs[pipeline_name]
        timeout = timeout or pl_config.timeout

        self.logger.info(f"Starting single pipeline execution: {pipeline_name}")

        start_time = time.time()

        try:
            import importlib
            module = importlib.import_module(pl_config.module_path)
            pipeline_class = getattr(module, pl_config.class_name)

            pipeline = pipeline_class(**pl_config.init_args)

            if hasattr(pipeline, 'run'):
                result_data = await asyncio.wait_for(
                    pipeline.run(**kwargs),
                    timeout=timeout
                )
            else:
                raise AttributeError(f"Pipeline {pipeline_name} has no run method")

            execution_time = time.time() - start_time

            self.logger.info(
                f"Single pipeline execution completed: {pipeline_name} "
                f"in {execution_time:.2f}s"
            )
            return PipelineResult(
                task_id=0,
                status=PipelineStatus.SUCCESS,
                data=result_data,
                execution_time=execution_time
            )
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            self.logger.warning(
                f"Single pipeline execution timed out: {pipeline_name} "
                f"after {execution_time:.2f}s"
            )
            return PipelineResult(
                task_id=0,
                status=PipelineStatus.TIMEOUT,
                execution_time=execution_time,
                error=f"Pipeline execution timed out after {timeout}s"
            )
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            self.logger.error(
                f"Single pipeline execution failed: {pipeline_name} "
                f"after {execution_time:.2f}s - {str(e)}"
                f"msg: {error_msg}"
            )
            return PipelineResult(
                task_id=0,
                status=PipelineStatus.FAILED,
                error=error_msg,
                execution_time=execution_time
            )

    async def run_all_pipelines(self) -> dict[str, Any]:
        results = {}
        logging.info(f"Run Pipelines: {", ".join(self.get_pipeline_names())}")

        pipelines = self.get_pipeline_configs()
        for name, config in pipelines.items():
            self.logger.info(f"Pipeline: {name} start to run")
            func = config.get("run_func")
            results[name] = await func(name, config.get("kwargs"))

        results["status"] = "all_completed"
        self.logger.info("All pipelines completed successfully")
        return results

    def get_pipeline_configs(self) -> list[dict]:
        return self._pipeline_configs

    def get_pipeline_names(self) -> list[str]:
        return list(self._pipeline_configs.keys())

    def get_pipeline_config(self, name: str) -> Optional[PipelineConfig]:
        return self._pipeline_configs.get(name)


async def main():
    config = Config("./configs/config.yaml")
    config.create_directories()

    executor = PipelineExecutor(config)
    executor.register_pipeline(
        name="assembly",
        module_path="pipelines.assembly.pipeline",
        class_name="AssemblyPipeline",
        run_func=executor.run_single_pipeline,
        init_args={"config": config},
        kwargs={"request_apis": {
            "law_bill_member": {"AGE": "21"}, 
            "law_bill_gov": {"AGE": "21"}, 
            "law_bill_cap": {"AGE": "21"},
        }},
        timeout=None
    )

    executor.register_pipeline(
        name="document",
        module_path="pipelines.document.pipeline", 
        class_name="DocumentPipeline",
        run_func=executor.run_multi_pipeline,
        init_args={"config": config},
        kwargs={"max_workers": 4},
        timeout=None
    )
    
    try:
        results = await executor.run_all_pipelines()
        print(f"Pipeline execution completed: {results['status']}")
        print(f"Pipeline execution completed: results: {results}")
        
        for pipeline_name, result in results.items():
            if isinstance(result, dict) and 'duration_seconds' in result:
                print(f"{pipeline_name}: {result['duration_seconds']:.2f}s")
                
    except Exception as e:
        print(f"Pipeline execution failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())