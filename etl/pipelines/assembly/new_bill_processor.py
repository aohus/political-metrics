import asyncio
import logging
from datetime import datetime
from typing import Optional

from configs import Config
from utils.file.fileio import read_file, write_file


async def write_new_bills(config: Config) -> Optional[list[tuple]]:
    """Identify and save new bills"""
    try:
        new_bills_path = config.assembly_temp_formatted / f"bills_{datetime.now().strftime('%Y-%m-%d')}.json"
        old_bills_path = config.assembly_formatted / "bills.json"
        
        # Read both files
        new_bills, old_bills = await asyncio.gather(
            read_file(new_bills_path),
            read_file(old_bills_path)
        )
        
        # Find new bills
        old_bill_no = {bill["BILL_NO"] for bill in old_bills}
        new_bills_list = [
            (bill["BILL_ID"], f"{bill['BILL_NO']}_{bill['BILL_NAME']}")
            for bill in new_bills
            if bill["BILL_NO"] not in old_bill_no
        ]
        
        # Save new bills in chunks
        if new_bills_list:
            new_bill_cnt = len(new_bills_list)
            chunk_size = new_bill_cnt // 4 + 1 if new_bill_cnt > 12000 else 3000

            chunks = [new_bills_list[i:i + chunk_size] for i in range(0, new_bill_cnt, chunk_size)]
            for i, chunk in enumerate(chunks):
                date_str = datetime.now().strftime("%Y-%m-%d")
                output_path = config.assembly_ref / f"new_bill_{date_str}_{i}.json"
                await write_file(output_path, chunk)
            # self.logger.info(f"Found {len(new_bills_list)} new bills")
        return len(chunks)
        
    except Exception as e:
        # self.logger.error(f"Failed to process new bills: {e}")
        return None
        