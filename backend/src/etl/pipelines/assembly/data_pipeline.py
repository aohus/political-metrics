import logging
import asyncio

from .assembly_extractor import extract
from .bill_processor import process_bills
from .proposer_processor import process_proposers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run(config):
    assembly_temp_raw = config.assembly_temp_raw
    assembly_temp_formatted = config.assembly_temp_formatted
    assembly_raw = config.assembly_raw
    assembly_formatted = config.assembly_formatted

    data_paths = await extract(
        request_apis=["law_bill_member", "law_bill_gov", "law_bill_cap"],
        output_dir=assembly_temp_raw,
    )

    tasks = [
        process_bills(
            config=config,
            data_paths=data_paths,
            output_dir=assembly_temp_formatted,
        ),
        process_proposers(
            config=config,
            data_paths=data_paths,
            output_dir=assembly_temp_formatted,
        ),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # UpsertDBProcessor.process(assembly_temp_formatted)
    # CleanDirProcessor.process()
