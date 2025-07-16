import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError


def rebuild(table_name: str, values, select_query):
    temp_table_name = f"{table_name}_temp_{int(datetime.now().timestamp())}"

    # 1. 임시 테이블 생성
    create_temp_query = text(
        f"""
        CREATE TABLE {temp_table_name} LIKE {table_name}
    """
    )

    # 2. 임시 테이블에 데이터 삽입
    insert_temp_query = text(
        f"""
        INSERT INTO {temp_table_name} ({values})
        {select_query}
    """
    )

    # 3. 테이블 교체
    replace_queries = [
        text(f"RENAME TABLE {table_name} TO {table_name}_old"),
        text(f"RENAME TABLE {temp_table_name} TO {table_name}"),
        text(f"DROP TABLE {table_name}_old"),
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
