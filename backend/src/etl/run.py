from .assembly.data_pipeline import run as run_assembly_pipeline
from .law.data_pipeline import run as run_law_pipeline
# from .document.data_pipeline import run as run_ducument_pipeline
from .configs import PathConfig
import asyncio


if __name__ == "__main__":
    # 설정 로드
    config = PathConfig('etl/configs/config.yaml')
    asyncio.run(run_assembly_pipeline(config))
