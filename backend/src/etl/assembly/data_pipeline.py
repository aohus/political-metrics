import logging

from .bill_processor import process
from .assembly_extractor import extract

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

    await process(
        config=config,  # TODO: remove config
        data_paths=data_paths,
        output_dir=assembly_temp_formatted,
    )

    # UpsertDBProcessor.process(assembly_temp_formatted)
    # CleanDirProcessor.process()
