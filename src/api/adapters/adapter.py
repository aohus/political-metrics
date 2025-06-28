import logging

from db.db_manager import get_db_manager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


db_manager = get_db_manager()


async def get_members(member_id: str):
    try:
        conn = db_manager.get_connection()
        cursor = conn.execute("SELECT * FROM Member WHERE NAAS_CD = ?", (member_id,))
        return cursor.fetchone() if cursor.fetchone() else None
    except Exception as e:
        logger.error(f"Error fetching bills: {e}")
    finally:
        conn.close()


async def get_statics():
    return


def calculate_bill_pass_rate(total_bills: int, passed_bills: int) -> float:
    """통과율을 계산합니다."""
    if total_bills == 0:
        return 0.0
    return round((passed_bills / total_bills) * 100, 2)


def calculate_bill_pending_rate(total_bills: int, pending_bills: int) -> float:
    """계류율을 계산합니다."""
    if total_bills == 0:
        return 0.0
    return round((pending_bills / total_bills) * 100, 2)
