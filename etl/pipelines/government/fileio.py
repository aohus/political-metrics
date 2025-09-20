import asyncio
import logging
import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import aiofiles

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class TargetWriter:
    def __init__(self, base_dir=None):
        self.exist = set()
        self.queue = asyncio.Queue()
        self.BASE_DIR = Path(base_dir)
    
    async def _get_data(self):
        info = await self.queue.get()
        filepath = self.BASE_DIR / Path(info.get('filename'))

        if filepath not in self.exist:
            self.exist.add(filepath)
            await self._initial_write(filepath, info.get('header'))
        return filepath, info.data

    async def insert(self, info):
        filename = info.get('filename')
        data = '\n' + info.get('data')

        if filename not in self.exist:
            header = info.get('header')
            data = header + data
            self.exist.add(filename)
        
        filepath = self.BASE_DIR / Path(filename)
        await self.write(filepath, data)

    async def write_all(self):
        group = {k: [] for k in self.exist}
        if self.queue:
            filepath, data = await self._get_data()
            group[filepath].extend(data)
        await self.convert_to_text(group)
    
    async def convert_to_text(self, group: dict):
        for filepath, data in group.items():
            text = '\n'.join([obj.to_csv_row for obj in data])
            await self.write(filepath, text)

    async def write(self, filepath: str, text: str):
        async with aiofiles.open(filepath, "a", encoding="utf-8", errors='replace') as f:
            await f.write(text)
        # logger.info(f"Write '{filepath}' len: {len(text)} Successfully!")


@dataclass
class WriteEvent:
    type: str
    info: dict[str, str]


class Writer:
    def __init__(self, target_writer, tmp_dir=None):
        self.TMP_DIR = Path(tmp_dir)
        self.target_writer = target_writer
        self.exist = set()
        self.chunk_size = None

    async def write(self, event):
        if event.type == "tmp":
            filename = event.info.get('filename')
            data = event.info.get('data')
            await self.write_file(filename, data)
        if event.type == "insert":
            await self.target_writer.insert(event.info)
            # self.queue.put_nowait(event.info)

    async def write_file(self, filename: str, data: str):
        filepath = self.TMP_DIR / Path(filename)
        async with aiofiles.open(filepath, "w", encoding="utf-8", errors='replace') as f:
            await f.write(data)
            # logger.info(f"Write '{filename}' len: {len(data)} Successfully!")


class Reader:
    def __init__(self, tmp_dir=None):
        self.TMP_DIR = Path(tmp_dir)

    async def read(self, filename: str):
        if isinstance(filename, str):
            init, path = False, self.TMP_DIR / Path(filename)
        else:
            init, path = True, filename
        try:
            async with aiofiles.open(path, 'r', encoding='utf-8', errors='replace') as f:
                data = await f.read()
                
                if not data:
                    logger.error("Read None")
                
                if not init:
                    try:
                        os.remove(path)
                    except FileNotFoundError:
                        logger.warning(f"File not found for deletion: {path}")
                    except Exception as e:
                        logger.error(f"Error deleting file {path}: {e}")
                return data
        except:
            print(filename)


class GoalDocReader:
    BASE_DIR = Path("/Users/aohus/Workspaces/github/politics/etl/data/government/국정과제/부처별/")

    async def read(self, year, ministry):
        filename = Path(f"{ministry}/성과관리시행계획_{ministry}_{year}.txt")
        with open(self.BASE_DIR / filename, 'r') as f:
            return f.read()

    async def read_goal_ref():
        pass
        # with open(f'/Users/aohus/Workspaces/github/politics/etl/data/government/국정과제/교육부_전략_과제_{filepath}.json', 'r') as f:
        #     yearly_tasks = json.load(f)

        # goals = {}
        # for 전략목표 in yearly_tasks:
        #     전략목표번호 = 전략목표['전략목표'][0]
        #     for 성과목표, 관리과제 in 전략목표['성과목표'].items():
        #         성과목표번호 = f'{전략목표번호}-{성과목표[0]}'
        #         성과목표전체 = f'{전략목표번호}-{성과목표}'
        #         goals[성과목표번호] = [title for title in 관리과제['관리과제']]
    
    @staticmethod
    async def result():
        pathdir = Path('/Users/aohus/Workspaces/github/politics/etl/data/government/국정과제/tasks_data/')
        for fname in os.listdir(pathdir):
            with open(f"{pathdir}/{fname}", 'r') as f:
                data = f.read()
                print(fname, len(data))

    @classmethod
    def get_filepath(cls, year, ministry):
        return Path(f"{ministry}/성과관리시행계획_{ministry}_{year}.txt")
