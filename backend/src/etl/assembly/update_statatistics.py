import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError


def rebuild_all_statistics_atomic(self):
    temp_table_name = f"member_bill_statistics_temp_{int(datetime.now().timestamp())}"

    # 1. 임시 테이블 생성
    create_temp_query = text(
        f"""
        CREATE TABLE {temp_table_name} LIKE member_bill_statistics
    """
    )

    # 2. 임시 테이블에 데이터 삽입
    insert_temp_query = text(
        f"""
        INSERT INTO {temp_table_name} (
            member_id, total_count, total_pass_rate, lead_count, lead_pass_rate,
            co_count, co_pass_rate, updated_at
        )
        SELECT 
            bp.MEMBER_ID,
            COUNT(b.BILL_ID) as total_count,
            ROUND(COALESCE(SUM(CASE WHEN b.STATUS IN :passed_statuses THEN 1 ELSE 0 END)
                  / NULLIF(COUNT(b.BILL_ID), 0), 0), 2) as total_pass_rate,
            SUM(CASE WHEN bp.PROPOSER_TYPE = 'LEAD' THEN 1 ELSE 0 END) as lead_count,
            ROUND(COALESCE(SUM(CASE WHEN bp.PROPOSER_TYPE = 'LEAD' AND b.STATUS IN :passed_statuses THEN 1 ELSE 0 END)
                  / NULLIF(SUM(CASE WHEN bp.PROPOSER_TYPE = 'LEAD' THEN 1 ELSE 0 END), 0), 0), 2) as lead_pass_rate,
            SUM(CASE WHEN bp.PROPOSER_TYPE = 'CO' THEN 1 ELSE 0 END) as co_count,
            ROUND(COALESCE(SUM(CASE WHEN bp.PROPOSER_TYPE = 'CO' AND b.STATUS IN :passed_statuses THEN 1 ELSE 0 END)
                  / NULLIF(SUM(CASE WHEN bp.PROPOSER_TYPE = 'CO' THEN 1 ELSE 0 END), 0), 0), 2) as co_pass_rate,
            NOW() as updated_at
        FROM bills b
        JOIN bill_proposers bp ON b.BILL_ID = bp.BILL_ID
        GROUP BY bp.MEMBER_ID
    """
    )

    # 3. 테이블 교체
    replace_queries = [
        text("RENAME TABLE member_bill_statistics TO member_bill_statistics_old"),
        text(f"RENAME TABLE {temp_table_name} TO member_bill_statistics"),
        text("DROP TABLE member_bill_statistics_old"),
    ]

    try:
        with self.db.begin() as trans:
            # 임시 테이블 생성 및 데이터 삽입
            self.db.execute(create_temp_query)
            result = self.db.execute(
                insert_temp_query, {"passed_statuses": tuple(self.passed_statuses)}
            )

            # 원자적 교체
            for query in replace_queries:
                self.db.execute(query)

            logging.info(f"Atomically rebuilt statistics for {result.rowcount} members")
            return result.rowcount

    except SQLAlchemyError as e:
        # 실패 시 임시 테이블 정리
        try:
            self.db.execute(text(f"DROP TABLE IF EXISTS {temp_table_name}"))
        except:
            pass
        logging.error(f"Failed to rebuild statistics: {e}")
        raise
