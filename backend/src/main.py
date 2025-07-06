# Assuming this is main.py
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Union

from api.adapters.adapters import BillAdapter, MemberAdapter
from api.db.db_manager import get_db_manager, shutdown_database, startup_database
from api.response.response import (
    APIResponse,
    BillStatisticResponse,
    MemberResponse,
    MemberStatisticResponse,
)
from api.service.analyzer import BillService, MemberService
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import String, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, joinedload

from etl.statatistic.update_statistics import (
    rebuild_all_statistics_atomic,
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============ FastAPI 앱 설정 ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        """앱 시작/종료 시 실행되는 코드"""
        logger.info("Assembly API Server Starting...")
        await startup_database()
        rebuild_all_statistics_atomic()
        logger.info("Database tables ensured.")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise e
    yield
    await shutdown_database()
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
    age: Optional[str] = Query(None, description="당선대수 필터"),
    party: Optional[str] = Query(None, description="정당명 필터"),
    db_session: AsyncSession = Depends(get_db_manager),
):
    """
    의원 목록 조회: 기본 정보 반환
    """
    try:
        service = MemberService(MemberAdapter, db_session)
        members = await service.get_members(age=age, party=party, limit=limit)
        if not members:
            raise HTTPException(status_code=404, detail="의원을 찾을 수 없습니다")

        # 의원 정보를 응답 형식에 맞게 변환
        members_response: list[MemberResponse] = [
            MemberResponse.model_validate(member)
            for member in members
        ]

        return APIResponse(
            success=True,
            message=f"{len(members_response)}명의 의원 정보를 조회했습니다",
            data=members_response,
            total=len(members_response),
        )
    except Exception as e:
        logger.error(
            f"Error fetching members: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/members/{member_id}", response_model=APIResponse)
async def get_member(member_id: str, db_session: AsyncSession = Depends(get_db_manager)):
    """
    의원 정보 조회: 의안 관련 통계 포함
    """
    try:
        service = MemberService(MemberAdapter, db_session)
        member_detail = await service.get_member(member_id)
        if not member_detail:
            raise HTTPException(status_code=404, detail="의원을 찾을 수 없습니다")

        # 의원 정보와 통계 정보를 결합
        stats_response = MemberStatisticResponse(
            member_info=member_detail.get("member"),
            bill_stats=member_detail.get("bill_stats"),
            committee_stats=member_detail.get("committee_stats"),
        )
        return APIResponse(success=True, message="의원 정보를 조회했습니다", data=stats_response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching member: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ranking/members", response_model=APIResponse)
async def get_top_members(
    limit: int = Query(20, ge=1, le=1000, description="조회할 개수"),
    criteria: Optional[str] = Query(None, description="정렬 기준(total, lead, co bill count)"),
    committee: Optional[str] = Query(None, description="위원회명 필터"),
    party: Optional[str] = Query(None, description="정당명 필터"),
    db_session: AsyncSession = Depends(get_db_manager),
):
    try:
        service = MemberService(MemberAdapter, db_session)
        top_members = service.get_top_members_by_criteria(criteria, committee, party, limit) 
        if not top_members:
            raise HTTPException(status_code=404)

        # 의원 정보와 통계 정보를 결합
        top_members_response = [MemberStatisticResponse(
            member_info=member_detail.get("member_info"),
            bill_stats=member_detail.get("bill_stats"),
            committee_stats=member_detail.get("committee_stats"),
        ) for member_detail in top_members]

        return APIResponse(
            success=True,
            message="의원 정보를 조회했습니다",
            data=top_members_response,
            total=len(top_members_response)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching top member list: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ranking/bills", response_model=APIResponse)
async def get_top_bills(
    limit: int = Query(20, ge=1, le=1000, description="조회할 개수"),
    criteria: Optional[str] = Query(None, description="정렬 기준(proposed, passed)"),
    committee: Optional[str] = Query(None, description="위원회명 필터"),
    party: Optional[str] = Query(None, description="정당명 필터"),
    db_session: AsyncSession = Depends(get_db_manager),
):
    # criiteria: proposed, passd
    service = BillService(BillAdapter, db_session)
    top_bills = service.get_top_bills_by_criteria(criteria, committee, party, limit)
    return APIResponse(
        success=True,
        message="의안 통계 정보를 조회했습니다",
        data=top_bills,
        total=len(top_bills)
    )


# ============ 의원 관련 API ============

if __name__ == "__main__":
    import uvicorn

    # uvicorn main:app --reload --host 0.0.0.0 --port 8001
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True, log_level="info")
