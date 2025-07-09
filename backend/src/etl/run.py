import asyncio
from datetime import datetime

from .configs import PathConfig
from .utils.file import read_file, write_file
from .pipelines.assembly.data_pipeline import run as run_assembly_pipeline
from .pipelines.document.data_pipeline import run as run_ducument_pipeline

# from .law.data_pipeline import run as run_law_pipeline


async def get_new_bills(new_bills_path: str, old_bills_path: str, output_dir: str) -> list:
    tasks = [read_file(new_bills_path), read_file(old_bills_path)]
    new_bills, old_bills = await asyncio.gather(*tasks)

    old_bill_no = {bill["BILL_NO"] for bill in old_bills}
    new_bills = [
        (bill["BILL_ID"], f"{bill["BILL_NO"]}_{bill["BILL_NAME"]}")
        for bill in new_bills
        if bill["BILL_NO"] not in old_bill_no
    ]
    await write_file(output_dir / f"new_bill_{str(datetime.date(datetime.now()))}.json", new_bills)


async def main():
    config = PathConfig("etl/configs/config.yaml")
    await run_assembly_pipeline(config)

    await get_new_bills(
        new_bills_path=config.assembly_temp_formatted / "bills.json",
        old_bills_path=config.assembly_formatted / "bills.json",
        output_dir=config.assembly_ref,
    )
    await run_ducument_pipeline(config)


if __name__ == "__main__":
    # 설정 로드
    asyncio.run(main())
