import logging
from typing import Optional

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..model.orm import Bill, BillProposer, BillStatus, Member, MemberBillStatistic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemberAdapter:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_members(self, limit: int = 20, age: Optional[str] = None, party: Optional[str] = None) -> list:
        """
        의원 목록 조회 (필터링 및 페이지네이션 지원)
        """
        # select 구문으로 쿼리 구성
        stmt = select(Member)
        
        # 필터 조건 적용
        if party:
            stmt = stmt.where(Member.PLPT_NM == party)
        if age:
            stmt = stmt.where(Member.GTELT_ERACO.like(f"%{age}%"))
        
        # 정렬 및 제한
        stmt = stmt.order_by(Member.NAAS_NM.asc()).limit(limit)
        
        # 비동기 실행
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_member_by_id(self, member_id: str) -> Member:
        """
        의원 ID로 의원 정보 조회
        """
        stmt = select(Member).where(Member.MEMBER_ID == member_id)
        result = await self.db.execute(stmt)
        member = result.scalar_one_or_none()
        
        if not member:
            raise ValueError(f"Member with ID {member_id} not found")
        return member
    
    async def get_member_bill_statistics(self, member_id: str) -> MemberBillStatistic:
        """
        의원 통계 정보 조회
        """
        stmt = select(MemberBillStatistic).where(MemberBillStatistic.MEMBER_ID == member_id)
        result = await self.db.execute(stmt)
        member_stats = result.scalar_one_or_none()
        
        if not member_stats:
            raise ValueError(f"Member statistics with ID {member_id} not found")
        return member_stats

    async def get_member_committee_statistics(self, member_id: str) -> list[dict]:
        """
        의원의 위원회 통계 정보 조회
        """
        stmt = (
            select(
                Bill.COMMITTEE_NAME.label("active_committee"),
                func.count(BillProposer.BILL_ID).label("total_count"),
                func.sum(case((BillProposer.RST == 1, 1), else_=0)).label("lead_count"),
                func.sum(case((BillProposer.RST == 0, 1), else_=0)).label("co_count"),
            )
            .select_from(BillProposer)
            .join(Bill, Bill.BILL_ID == BillProposer.BILL_ID)
            .where(BillProposer.MEMBER_ID == member_id)
            .group_by(Bill.COMMITTEE_NAME)
            .order_by(func.count(BillProposer.BILL_ID).desc())
            .limit(3)
        )
        
        result = await self.db.execute(stmt)
        data = result.all()
        
        return [
            {
                "active_committee": cs.active_committee,
                "total_count": cs.total_count,
                "lead_count": cs.lead_count,
                "co_count": cs.co_count,
            }
            for cs in data
        ]

    async def get_top_members_by_criteria(self, criteria: str, limit: int = 10) -> list[str]:
        """
        특정 기준으로 상위 의원 조회
        """
        if criteria == "total_bill_count":
            stmt = (
                select(MemberBillStatistic.MEMBER_ID)
                .order_by(MemberBillStatistic.total_count.desc())
                .limit(limit)
            )
        elif criteria == "total_pass_rate":
            stmt = (
                select(MemberBillStatistic.MEMBER_ID)
                .order_by(MemberBillStatistic.total_pass_rate.desc())
                .limit(limit)
            )
        elif criteria == "lead_bill_count":
            stmt = (
                select(MemberBillStatistic.MEMBER_ID)
                .order_by(MemberBillStatistic.lead_count.desc())
                .limit(limit)
            )
        elif criteria == "co_bill_count":
            stmt = (
                select(MemberBillStatistic.MEMBER_ID)
                .order_by(MemberBillStatistic.co_count.desc())
                .limit(limit)
            )
        else:
            raise ValueError("Invalid criteria for top members")
        
        result = await self.db.execute(stmt)
        return [row[0] for row in result.all()]  # MEMBER_ID만 추출

    async def get_member_with_statistics(self, member_id: str) -> dict:
        """
        의원 정보와 통계를 한 번에 조회 (효율적인 방법)
        """
        # 병렬로 여러 쿼리 실행
        member_task = self.get_member_by_id(member_id)
        stats_task = self.get_member_bill_statistics(member_id)
        committee_task = self.get_member_committee_statistics(member_id)
        
        # 동시 실행 (asyncio.gather 사용 권장)
        try:
            member = await member_task
            bill_stats = await stats_task
            committee_stats = await committee_task
            
            return {
                "member": member,
                "bill_stats": bill_stats,
                "committee_stats": committee_stats,
            }
        except ValueError as e:
            logger.error(f"Error fetching member data for {member_id}: {e}")
            raise

    async def search_members(self, 
                           name: Optional[str] = None,
                           party: Optional[str] = None,
                           committee: Optional[str] = None,
                           limit: int = 20) -> list[Member]:
        """
        복합 검색 조건으로 의원 검색
        """
        stmt = select(Member)
        
        conditions = []
        if name:
            conditions.append(Member.NAAS_NM.contains(name))
        if party:
            conditions.append(Member.PLPT_NM == party)
        if committee:
            conditions.append(Member.CMIT_NM == committee)
        
        if conditions:
            stmt = stmt.where(*conditions)
        
        stmt = stmt.order_by(Member.NAAS_NM.asc()).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()


class BillAdapter:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_top_bills_by_criteria(self,
                                      criteria: str = "proposed",
                                      limit: int = 10,
                                      party: Optional[str] = None,
                                      committee: Optional[str] = None
                                      ) -> list[dict]:
        """
        특정 기준으로 상위 의안 조회
        """
        if criteria == "proposed":
            stmt = (
                select(
                    Bill.BILL_NAME, 
                    func.count(Bill.BILL_ID).label("bill_count")
                )
                .group_by(Bill.BILL_NAME)
                .order_by(func.count(Bill.BILL_ID).desc())
                .limit(limit)
            )
        elif criteria == "passed":
            stmt = (
                select(
                    Bill.BILL_NAME, 
                    func.count(Bill.BILL_ID).label("bill_count")
                )
                .where(Bill.STATUS.in_([BillStatus.ORIGINAL_PASSED, BillStatus.AMENDED_PASSED]))
                .group_by(Bill.BILL_NAME)  # BILL_ID 대신 BILL_NAME으로 수정
                .order_by(func.count(Bill.BILL_ID).desc())
                .limit(limit)
            )
        elif criteria == "proposed_by_committee":
            if not committee:
                raise ValueError("Committee name is required for this criteria")
            stmt = (
                select(
                    Bill.BILL_NAME, 
                    func.count(Bill.BILL_ID).label("bill_count")
                )
                .where(Bill.COMMITTEE_NAME == committee)
                .group_by(Bill.BILL_NAME)
                .order_by(func.count(Bill.BILL_ID).desc())
                .limit(limit)
            )
        else:
            raise ValueError("Invalid criteria for top bills")
        
        result = await self.db.execute(stmt)
        top_bills = result.all()
        
        logger.info(f"Top bills by {criteria}: {len(top_bills)} results")
        
        return [
            {"bill_name": bill.BILL_NAME, "bill_count": bill.bill_count} 
            for bill in top_bills
        ]

    async def get_bill_by_id(self, bill_id: str) -> Bill:
        """
        의안 ID로 의안 정보 조회
        """
        stmt = select(Bill).where(Bill.BILL_ID == bill_id)
        result = await self.db.execute(stmt)
        bill = result.scalar_one_or_none()
        
        if not bill:
            raise ValueError(f"Bill with ID {bill_id} not found")
        return bill

    async def get_bills_by_member(self, member_id: str, limit: int = 10) -> list[Bill]:
        """
        특정 의원이 제안한 의안 목록 조회
        """
        stmt = (
            select(Bill)
            .join(BillProposer, Bill.BILL_ID == BillProposer.BILL_ID)
            .where(BillProposer.MEMBER_ID == member_id)
            .order_by(Bill.PRPS_DT.desc())  # 제안일자 내림차순
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_bills_by_status(self, status: BillStatus, limit: int = 10) -> list[Bill]:
        """
        특정 상태의 의안 목록 조회
        """
        stmt = (
            select(Bill)
            .where(Bill.STATUS == status)
            .order_by(Bill.PRPS_DT.desc())
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_bill_statistics(self) -> dict:
        """
        전체 의안 통계 조회
        """
        # 총 의안 수
        total_stmt = select(func.count(Bill.BILL_ID))
        total_result = await self.db.execute(total_stmt)
        total_count = total_result.scalar()
        
        # 상태별 의안 수
        status_stmt = (
            select(
                Bill.STATUS,
                func.count(Bill.BILL_ID).label("count")
            )
            .group_by(Bill.STATUS)
        )
        status_result = await self.db.execute(status_stmt)
        status_stats = {row.STATUS: row.count for row in status_result.all()}
        
        # 위원회별 의안 수
        committee_stmt = (
            select(
                Bill.COMMITTEE_NAME,
                func.count(Bill.BILL_ID).label("count")
            )
            .group_by(Bill.COMMITTEE_NAME)
            .order_by(func.count(Bill.BILL_ID).desc())
            .limit(10)
        )
        committee_result = await self.db.execute(committee_stmt)
        committee_stats = [
            {"committee": row.COMMITTEE_NAME, "count": row.count}
            for row in committee_result.all()
        ]
        
        return {
            "total_count": total_count,
            "status_distribution": status_stats,
            "top_committees": committee_stats,
        }


# ==========================================
# 사용 예시 및 의존성 주입
# ==========================================

class AdapterFactory:
    """
    Adapter 팩토리 클래스
    """
    @staticmethod
    def create_member_adapter(db_session: AsyncSession) -> MemberAdapter:
        return MemberAdapter(db_session)
    
    @staticmethod
    def create_bill_adapter(db_session: AsyncSession) -> BillAdapter:
        return BillAdapter(db_session)


# ==========================================
# FastAPI에서 사용하는 경우
# ==========================================

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


async def get_async_db() -> AsyncSession:
    """비동기 데이터베이스 세션 의존성"""
    # 실제 구현은 데이터베이스 설정에 따라 다름
    pass

# FastAPI 엔드포인트에서 사용
async def get_member_endpoint(
    member_id: str, 
    db: AsyncSession = Depends(get_async_db)
):
    adapter = MemberAdapter(db)
    try:
        member_data = await adapter.get_member_with_statistics(member_id)
        return member_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==========================================
# 에러 처리 및 로깅 개선
# ==========================================

import asyncio
from contextlib import asynccontextmanager


class SafeMemberAdapter(MemberAdapter):
    """
    에러 처리가 강화된 MemberAdapter
    """
    
    @asynccontextmanager
    async def handle_db_errors(self):
        """데이터베이스 에러 처리 컨텍스트 매니저"""
        try:
            yield
        except Exception as e:
            logger.error(f"Database operation failed: {e}", exc_info=True)
            await self.db.rollback()
            raise
    
    async def get_member_by_id_safe(self, member_id: str) -> Optional[Member]:
        """안전한 의원 조회 (예외 발생 시 None 반환)"""
        try:
            async with self.handle_db_errors():
                return await self.get_member_by_id(member_id)
        except ValueError:
            logger.warning(f"Member not found: {member_id}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching member {member_id}: {e}")
            return None
    
    async def batch_get_members(self, member_ids: list[str]) -> dict[str, Member]:
        """여러 의원을 배치로 조회"""
        stmt = select(Member).where(Member.MEMBER_ID.in_(member_ids))
        result = await self.db.execute(stmt)
        members = result.scalars().all()
        
        return {member.MEMBER_ID: member for member in members}


# ==========================================
# 성능 최적화된 버전
# ==========================================

class OptimizedMemberAdapter(MemberAdapter):
    """
    성능 최적화된 MemberAdapter
    """
    
    async def get_member_with_preloaded_relations(self, member_id: str) -> Member:
        """관계를 미리 로드하여 N+1 문제 방지"""
        stmt = (
            select(Member)
            .options(
                selectinload(Member.bills),  # 관계가 정의되어 있다면
                # selectinload(Member.committees)  # 필요한 관계들 추가
            )
            .where(Member.MEMBER_ID == member_id)
        )
        
        result = await self.db.execute(stmt)
        member = result.scalar_one_or_none()
        
        if not member:
            raise ValueError(f"Member with ID {member_id} not found")
        return member
    
    async def get_members_with_pagination(self, 
                                        page: int = 1, 
                                        page_size: int = 20,
                                        **filters) -> dict:
        offset = (page - 1) * page_size
        
        # 기본 쿼리
        base_stmt = select(Member)
        count_stmt = select(func.count(Member.MEMBER_ID))
        
        # 필터 적용
        if filters.get('party'):
            base_stmt = base_stmt.where(Member.PLPT_NM == filters['party'])
            count_stmt = count_stmt.where(Member.PLPT_NM == filters['party'])
        
        # 데이터와 총 개수를 병렬로 조회
        data_stmt = base_stmt.offset(offset).limit(page_size)
        
        data_result, count_result = await asyncio.gather(
            self.db.execute(data_stmt),
            self.db.execute(count_stmt)
        )
        
        members = data_result.scalars().all()
        total_count = count_result.scalar()
        
        return {
            "items": members,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size
        }