# main.py
import asyncio
import json
import logging
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

import aiohttp
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="정치인 평가 시스템 API",
    description="실시간 데이터 기반 정치인 평가 시스템",
    version="1.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 데이터 모델 정의
class PromiseStatus(str, Enum):
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    DELAYED = "delayed"
    MODIFIED = "modified"
    ABANDONED = "abandoned"


@dataclass
class Promise:
    text: str
    status: PromiseStatus
    progress: str
    status_icon: str
    evidence: List[str] = None


@dataclass
class Metric:
    score: int
    details: str


@dataclass
class PoliticianSummary:
    name: str
    party: str
    position: str
    overall_score: int
    grade: str
    recently_updated: bool


@dataclass
class PoliticianDetail:
    name: str
    party: str
    position: str
    overall_score: int
    grade: str
    evaluation_period: str
    metrics: Dict[str, Metric]
    promises: List[Promise]
    data_sources: Dict


# 메모리 내 데이터 저장소 (실제 환경에서는 데이터베이스 사용)
politicians_cache = {}
last_update = {}


@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/politicians", response_model=List[PoliticianSummary])
async def get_politicians():
    """모든 정치인 목록 조회"""
    try:
        politicians = ["윤석열", "이재명", "한동훈", "조국"]
        results = []

        for name in politicians:
            # 캐시된 데이터가 있고 1시간 이내면 사용
            cache_key = f"summary_{name}"
            if (
                cache_key in politicians_cache
                and name in last_update
                and datetime.now() - last_update[name] < timedelta(hours=1)
            ):
                results.append(politicians_cache[cache_key])
            else:
                # 간단한 평가만 수행 (전체 상세 평가는 개별 요청에서)
                try:
                    # 빠른 평가를 위해 기본 데이터만 수집
                    overall_score = 60 + hash(name) % 30  # 임시 점수
                    grade = (
                        "A"
                        if overall_score >= 80
                        else "B" if overall_score >= 60 else "C"
                    )

                    politician_info = {
                        "윤석열": {"party": "국민의힘", "position": "대통령"},
                        "이재명": {"party": "더불어민주당", "position": "당대표"},
                        "한동훈": {"party": "국민의힘", "position": "당대표"},
                        "조국": {"party": "조국혁신당", "position": "당대표"},
                    }.get(name, {"party": "정당", "position": "직책"})

                    summary = PoliticianSummary(
                        name=name,
                        party=politician_info["party"],
                        position=politician_info["position"],
                        overall_score=overall_score,
                        grade=grade,
                        recently_updated=name in last_update
                        and datetime.now() - last_update[name] < timedelta(minutes=30),
                    )

                    politicians_cache[cache_key] = summary
                    last_update[name] = datetime.now()
                    results.append(summary)

                except Exception as e:
                    logger.error(f"정치인 요약 생성 실패 ({name}): {e}")
                    continue

        return results

    except Exception as e:
        logger.error(f"정치인 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="정치인 목록을 불러올 수 없습니다")


@app.get("/politicians/{politician_name}/detailed")
async def get_politician_detailed(politician_name: str):
    """특정 정치인 상세 정보 조회"""
    try:
        # 캐시 확인 (30분 이내)
        cache_key = f"detailed_{politician_name}"
        if (
            cache_key in politicians_cache
            and politician_name in last_update
            and datetime.now() - last_update[politician_name] < timedelta(minutes=30)
        ):
            return asdict(politicians_cache[cache_key])

        # 새로운 데이터 수집 및 평가
        detailed_data = await collect_and_evaluate_politician(politician_name)

        # 캐시 저장
        politicians_cache[cache_key] = detailed_data
        last_update[politician_name] = datetime.now()

        return asdict(detailed_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"정치인 상세 조회 실패 ({politician_name}): {e}")
        raise HTTPException(
            status_code=500, detail=f"상세 정보를 불러올 수 없습니다: {str(e)}"
        )


@app.post("/politicians/refresh")
async def refresh_politician_data(background_tasks: BackgroundTasks):
    """모든 정치인 데이터 새로고침"""

    def refresh_all_data():
        """백그라운드에서 모든 데이터 새로고침"""
        try:
            politicians = ["윤석열", "이재명", "한동훈", "조국"]

            async def refresh_politician(name):
                try:
                    detailed_data = await collect_and_evaluate_politician(name)
                    politicians_cache[f"detailed_{name}"] = detailed_data

                    # 요약 데이터도 업데이트
                    summary = PoliticianSummary(
                        name=detailed_data.name,
                        party=detailed_data.party,
                        position=detailed_data.position,
                        overall_score=detailed_data.overall_score,
                        grade=detailed_data.grade,
                        recently_updated=True,
                    )
                    politicians_cache[f"summary_{name}"] = summary
                    last_update[name] = datetime.now()

                    logger.info(f"데이터 새로고침 완료: {name}")
                except Exception as e:
                    logger.error(f"데이터 새로고침 실패 ({name}): {e}")

            # 비동기로 모든 정치인 데이터 새로고침
            async def refresh_all():
                tasks = [refresh_politician(name) for name in politicians]
                await asyncio.gather(*tasks, return_exceptions=True)

            # 이벤트 루프에서 실행
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(refresh_all())
            loop.close()

        except Exception as e:
            logger.error(f"전체 데이터 새로고침 실패: {e}")

    # 백그라운드 작업으로 실행
    background_tasks.add_task(refresh_all_data)

    return {
        "message": "데이터 새로고침이 시작되었습니다",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/politicians/{politician_name}/promises")
async def get_politician_promises(politician_name: str):
    """특정 정치인의 공약 이행 현황만 조회"""
    try:
        async with DataCollector() as collector:
            promise_data = await collector.collect_promise_data(politician_name)

        promises = []
        status_icons = {
            "completed": "✅",
            "in_progress": "🔄",
            "delayed": "⚠️",
            "modified": "🔄",
            "abandoned": "❌",
        }

        for promise in promise_data:
            promises.append(
                {
                    "text": promise["text"],
                    "status": promise["status"],
                    "progress": promise["progress"],
                    "status_icon": status_icons.get(promise["status"], "🔄"),
                }
            )

        return {"politician": politician_name, "promises": promises}

    except Exception as e:
        logger.error(f"공약 조회 실패 ({politician_name}): {e}")
        raise HTTPException(status_code=500, detail="공약 정보를 불러올 수 없습니다")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
