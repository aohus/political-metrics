import asyncio
import logging

from fileio import WriteEvent

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class AbstractJob:
    async def execute(self):
        raise NotImplementedError

    def _get_or_create_data(self, title, data):
        raise NotImplementedError

    def _create_data(self, title, data):
        raise NotImplementedError

    def _create_and_register(self, title, section, section_title):
        raise NotImplementedError

    def _make_filepath(self, fk, job_type):
        raise NotImplementedError

    def _get_job_type(self, title: str):
        raise NotImplementedError

    async def write_rows(self, job_type, header, data):
        raise NotImplementedError

    async def write_section(self, filepath, section):
        raise NotImplementedError


class Job(AbstractJob):
    def __init__(self, doc, job_type, reader, writer, processor, fk, dataclass_factory, filepath):
        self.doc = doc
        self.job_type = job_type
        self.reader = reader
        self.writer = writer
        self.processor = processor
        self.fk: str = fk
        self.dataclass_factory = dataclass_factory
        self.filepath: str = filepath
        self._memo = {}
        self._data = []

    async def execute(self):
        section = await self.reader.read(self.filepath)
        if not section:
            logger.info(f'no data from filepath: {self.filepath}, doc: {self.doc.name}, fk: {self.fk}')
            return
        
        for event, data in self.processor.process(section):
            if event == 'register_job':
                self._create_and_register(**data)
            elif event == 'create_data':
                self._create_data(data)
            else:
                logger.info(f"Unvalid event type {event}")

        if not self._data:
            logger.info(f'path: {self.filepath}')
        else:
            await self.write_rows()

    def _get_or_create_data(self, obj: dict) -> str:
        if id := self._memo.get(str(obj)):
            return id
        return self._create_data(obj)

    def _create_data(self, obj: dict) -> str:
        data = self.dataclass_factory(fk=self.fk, **obj)
        if not data:
            logger.info(f"Fail to create data {self.job_type}, {obj}")
            return 
        self._data.append(data)
        self._memo[str(obj)] = data.id
        return data.id

    def _create_and_register(self, obj, job_type, section, section_title):
        if not section:
            logger.info(f'section {job_type} / {section_title} has nothing: doc: {self.doc.name}, fk: {self.fk}')
            return 
        id = self._get_or_create_data(obj)
        filepath = self._make_filepath(id, job_type)
        task = asyncio.create_task(self.write_section(filepath, section))
        task.add_done_callback(lambda f: register_job(f, self.doc, id, job_type, filepath))

    def _make_filepath(self, fk, job_type):
        return f"{self.doc.name}_{fk}_{job_type}"

    async def write_rows(self):
        if not self._data:
            logger.info(f"no data {self.fk}, {self.job_type.name}")
            return 
        
        header = self._data[0].header
        csv_rows = '\n'.join([obj.to_csv_row for obj in self._data])
        await self.writer.write(WriteEvent(type='insert', 
                                           info={'filename': f"{self.job_type.name}.csv", 
                                                 'data': csv_rows,
                                                 'header': header}))

    async def write_section(self, filepath, section):
        await self.writer.write(WriteEvent(type='tmp', 
                                           info={'filename': filepath, 
                                                 'data': section})) 


def register_job(future, *args):
    doc, id, job_type, filepath = args
    doc.register(id, job_type, filepath)


class AbstractJobLoop:
    async def run(self):
        raise NotImplementedError

    async def shutdown(self):
        raise NotImplementedError


class AbstractProcessor:
    def process(self, content: str):
        raise NotImplementedError

    def _process_lines(self, content: any): 
        raise NotImplementedError

    def _process_data(self, data: dict):
        raise NotImplementedError

    def _update_data(self, data: dict, obj: dict): 
        raise NotImplementedError


class AbstractParser:
    def parse(self, content: str, is_line: bool = False): 
        raise NotImplementedError

    def _parse(self, lines: list): 
        raise NotImplementedError


class AbstractDataClass:
    def to_dict(self): 
        raise NotImplementedError

