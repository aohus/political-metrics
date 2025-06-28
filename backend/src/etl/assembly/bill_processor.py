# get_data -> path -> bill processor
#                  -> document processor

# data_collector = AssemblyDataCollector(api_metadata=API_DEFINITIONS)
# async def collect_all_bill_data(self) -> Dict[str, List]:
#     """모든 의안 데이터 수집"""
#     try:
#         collection_config = {
#             "law_bill_member": {},
#             "law_bill_gov": {},
#             "law_bill_cap": {},
#         }

#         raw_data = await self.data_collector.collect_data_many(collection_config)
#         self.logger.info(f"Collected data from {len(raw_data)} sources")

#         return raw_data

#     except Exception as e:
#         raise DataProcessingError(f"Failed to collect bill data: {e}") from e

# config = BillServiceConfig(
#     member_id_file_path="./data/member_id.json", default_age="22"
# )


class BillProcessor:
    def process(self, path: str):
        bills, bill_details, bill_proposers = self.process_bill_data(raw_data)
        pass

    # def _save_to_database(
    #     self,
    #     bills: List[Bill],
    #     bill_details: List[BillDetail],
    #     bill_proposers: List[BillProposer],
    # ):
    #     """데이터베이스에 데이터 저장"""
    #     TODO: dict -> orm 객체 변환
    #     try:
    #         with self.db_session_factory() as db_session:
    #             # 트랜잭션 단위로 처리
    #             bulk_insert(db_session, bill_proposers)
    #             bulk_insert(db_session, bill_details)
    #             bulk_insert(db_session, bills)

    #             self.logger.info(
    #                 f"Successfully saved {len(bills)} bills, "
    #                 f"{len(bill_details)} details, "
    #                 f"{len(bill_proposers)} proposer relationships"
    #             )

    #     except SQLAlchemyError as e:
    #         raise DataProcessingError(f"Database save failed: {e}") from e
