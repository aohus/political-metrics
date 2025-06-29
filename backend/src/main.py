# Assuming this is main.py
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from db.db_manager import create_db_tables, get_db_manager
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from model.orm import (
    Bill,
    BillDetail,
    BillProposer,
    BillStatus,
    Committee,
    CommitteeMember,
    Gender,
    Member,
    MemberHistory,
)
from response.response import APIResponse, BillResponse, MemberResponse
from sqlalchemy import String, case, cast, func, select
from sqlalchemy.orm import Session, aliased, joinedload
from src.service.bill_analizer import MemberBillStatisticsCalculator

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============ FastAPI 앱 설정 ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행되는 코드"""
    logger.info("Assembly API Server Starting...")
    try:
        # create_db_tables()
        logger.info("Database tables ensured.")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        # 실제 운영 환경에서는 앱 시작 실패로 처리할 수 있습니다.
    yield
    logger.info("Assembly API Server Shutting down...")


app = FastAPI(
    title="국회의원 의안 관리 시스템",
    description="국회의원 정보와 의안 데이터를 관리하는 REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 구체적인 도메인 지정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ API 엔드포인트들 ============
@app.get("/", response_model=APIResponse)
async def root():
    """API 루트 엔드포인트"""
    return APIResponse(
        success=True,
        message="국회의원 의안 관리 시스템 API",
        data={"version": "1.0.0", "docs": "/docs"},
    )


# ============ 의원 관련 API ============
@app.get("/members", response_model=APIResponse)
async def get_members(
    limit: int = Query(20, ge=1, le=1000, description="조회할 개수"),
    party: Optional[str] = Query(None, description="정당명 필터"),
    db_session: Session = Depends(get_db_manager),
):
    """
    의원 목록 조회: 기본 정보 반환
    """
    try:
        return APIResponse(
            success=True,
            message=f"{len(members_response)}명의 의원 정보를 조회했습니다",
            data=members_response,
            total=total,
        )
    except Exception as e:
        logger.error(
            f"Error fetching members: {e}", exc_info=True
        )  # exc_info=True로 traceback 출력
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/members/{member_id}", response_model=APIResponse)
async def get_member(member_id: str, db_session: Session = Depends(get_db_manager)):
    """
    의원 정보 조회: 의안 관련 통계 포함
    """
    try:
        calculator = MemberBillStatisticsCalculator(db_session)
        stats = calculator.calculate_member_statistics(member_id)
        return APIResponse(success=True, message="의원 정보를 조회했습니다", data=stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching member: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rankings/members/{criteria}")
async def get_top_members(
    criteria: str, limit: int = 10, db: Session = Depends(get_db_manager)
):
    # criiteria: total/lead/co, proposed/passed
    calculator = MemberBillStatisticsCalculator(db)
    top_members = calculator.get_top_members_by_criteria(criteria, limit)
    return top_members


@app.get("/rankings/bills/{criteria}")
async def get_top_members(
    criteria: str, limit: int = 10, db: Session = Depends(get_db_manager)
):
    # criiteria: proposed, passd
    calculator = MemberBillStatisticsCalculator(db)
    top_bills = calculator.get_top_members_by_criteria(criteria, limit)
    return top_bills


# ============ 의원 관련 API ============

if __name__ == "__main__":
    import uvicorn

    # uvicorn main:app --reload --host 0.0.0.0 --port 8001
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True, log_level="info")
