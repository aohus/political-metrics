import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from model.orm import Base

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ========== 데이터베이스 설정 ===========
DATABASE_URL = "sqlite:///./politician_score.db"  # SQLite 데이터베이스 파일 경로
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ==== 데이터베이스 테이블 생성 함수 =====
def create_db_tables():
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully!")


# ============ 의존성 주입 ============
def get_db_manager():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
