import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ..utils.saver.db_raw_manager import PydanticDBGenerator


def rebuild_all_statistics_atomic():
    temp_table_name = f"member_bill_statistics_temp_{int(datetime.now().timestamp())}"

    # 1. 임시 테이블 생성
    create_temp_query = f"""
        CREATE TABLE {temp_table_name} AS 
        SELECT * FROM member_bill_statistics WHERE 0=1
    """

    # 2. 임시 테이블에 데이터 삽입
    insert_temp_query = f"""
        INSERT INTO {temp_table_name} (
            member_id, total_count, total_pass_rate, lead_count, lead_pass_rate,
            co_count, co_pass_rate, updated_at
        )
        SELECT 
            bp.MEMBER_ID,
            COUNT(b.BILL_ID) as total_count,
            ROUND(
                CASE 
                    WHEN COUNT(b.BILL_ID) > 0 
                    THEN (SUM(CASE WHEN b.STATUS IN ("ORIGINAL_PASSED", "AMENDED_PASSED") THEN 1 ELSE 0 END) * 100.0) / COUNT(b.BILL_ID)
                    ELSE 0 
                END, 2
            ) as total_pass_rate,
            SUM(CASE WHEN bp.RST = 1 THEN 1 ELSE 0 END) as lead_count,
            ROUND(
                CASE 
                    WHEN SUM(CASE WHEN bp.RST = 1 THEN 1 ELSE 0 END) > 0 
                    THEN (SUM(CASE WHEN bp.RST = 1 AND b.STATUS IN ("ORIGINAL_PASSED", "AMENDED_PASSED") THEN 1 ELSE 0 END) * 100.0) 
                            / SUM(CASE WHEN bp.RST = 1 THEN 1 ELSE 0 END)
                    ELSE 0 
                END, 2
            ) as lead_pass_rate,
            SUM(CASE WHEN bp.RST = 0 THEN 1 ELSE 0 END) as co_count,
            ROUND(
                CASE 
                    WHEN SUM(CASE WHEN bp.RST = 0 THEN 1 ELSE 0 END) > 0 
                    THEN (SUM(CASE WHEN bp.RST = 0 AND b.STATUS IN ("ORIGINAL_PASSED", "AMENDED_PASSED") THEN 1 ELSE 0 END) * 100.0) 
                            / SUM(CASE WHEN bp.RST = 0 THEN 1 ELSE 0 END)
                    ELSE 0 
                END, 2
            ) as co_pass_rate,
            datetime('now') as updated_at
        FROM bills b
        JOIN bill_proposers bp 
        ON b.BILL_ID = bp.BILL_ID
        GROUP BY bp.MEMBER_ID
    """

    # 3. 테이블 교체
    replace_queries = [
        "ALTER TABLE member_bill_statistics RENAME TO member_bill_statistics_old",
        f"ALTER TABLE {temp_table_name} RENAME TO member_bill_statistics",
        "DROP TABLE member_bill_statistics_old",
    ]

    db_gen = PydanticDBGenerator("politician_score.db")
    try:
        conn = db_gen.connect()
        conn.execute(create_temp_query)
        result = conn.execute(insert_temp_query)

        # 원자적 교체
        for query in replace_queries:
            conn.execute(query)
        conn.commit()
        conn.close()

        logging.info(f"Atomically rebuilt statistics for {result.rowcount} members")
        return result.rowcount

    except SQLAlchemyError as e:
        # 실패 시 임시 테이블 정리
        try:
            conn.execute(text(f"DROP TABLE IF EXISTS {temp_table_name}"))
        except:
            pass
        logging.error(f"Failed to rebuild statistics: {e}")
        raise
