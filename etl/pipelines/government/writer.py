import asyncio
import logging
from pathlib import Path

import aiofiles

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class StreamWriter:
    def __init__(self):
        self.writers: list[Writer] = []

    async def loop(self):
        while 1:
            for writer in self.writers:
                if writer.data_queue > writer.chunk_size:
                    await writer.upsert()


class Writer:
    def __init__(self, job_type, header, chunk_size=100):
        self.BASEDIR = Path('/Users/aohus/Workspaces/github/politics/etl/data/government/국정과제/tasks_data')
        self.job_type = job_type.name
        self.chunk_size = chunk_size
        self.filepath = self.BASEDIR / Path(f'{job_type.name}.csv')
        self.data_queue = asyncio.Queue()
        self._initial_write(header)

    def _initial_write(self, header):
        with open(self.filepath, 'w', encoding='utf-8') as f:
            f.write(header)

    async def add(self, data):
        self.data_queue.put_nowait(data)

    async def upsert(self, data_size: int):
        data = '\n'.join([self.data_queue.pop() for _ in range(data_size)])
        await self.write_file(data)

    async def write_file(self, data):
        async with aiofiles.open(self.filepath, "a+", encoding="utf-8") as f:
            await f.write()
        logger.info(f"Write {self.job_type}: {len(data)} Successfully! File: {self.filepath}")

    async def clear(self):
        if self.data_queue:
            await self.upsert(self.data_queue.qsize())

