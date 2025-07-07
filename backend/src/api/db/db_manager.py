import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql import text

from ..model.orm import Base

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ========== 비동기 데이터베이스 설정 ===========

# SQLite 비동기 URL (aiosqlite 드라이버 사용)
DATABASE_URL = "sqlite+aiosqlite:///./politician_score.db"

# 비동기 엔진 생성
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # SQL 쿼리 로깅 (개발 시에만 True)
    future=True,  # SQLAlchemy 2.0 스타일 사용
    poolclass=StaticPool,  # SQLite용 풀 설정
    connect_args={
        "check_same_thread": False,  # SQLite 스레드 체크 비활성화
    },
)

# 비동기 세션 팩토리
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ==== 비동기 데이터베이스 테이블 생성 함수 =====
async def create_db_tables():
    """비동기로 데이터베이스 테이블 생성"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully!")


async def drop_db_tables():
    """비동기로 데이터베이스 테이블 삭제"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("Database tables dropped successfully!")


async def recreate_db_tables():
    """데이터베이스 테이블을 재생성"""
    await drop_db_tables()
    await create_db_tables()
    logger.info("Database tables recreated successfully!")


# ============ 비동기 의존성 주입 ============
async def get_db_manager() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 비동기 데이터베이스 의존성"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


# ============ 데이터베이스 연결 관리 ============
@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """직접 사용할 수 있는 비동기 세션 컨텍스트 매니저"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database operation failed: {e}", exc_info=True)
            raise
        finally:
            await session.close()


# ============ 엔진 생명주기 관리 ============
async def startup_database():
    """애플리케이션 시작 시 데이터베이스 초기화"""
    try:
        # 테이블 생성
        await create_db_tables()
        
        # 연결 테스트
        async with get_db_session() as session:
            result = await session.execute(text("SELECT 1"))
            logger.info(f"Database connection test: {result.scalar()}")
        logger.info("Database startup completed successfully!")
    except Exception as e:
        logger.error(f"Database startup failed: {e}")
        raise


async def shutdown_database():
    """애플리케이션 종료 시 데이터베이스 정리"""
    try:
        await engine.dispose()
        logger.info("Database shutdown completed successfully!")
    except Exception as e:
        logger.error(f"Database shutdown failed: {e}")
