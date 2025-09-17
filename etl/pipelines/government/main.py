import asyncio

from job_factory import CacheObj, JobFactory
from manager import Manager
from utils.doc_reader import GoalDocReader
from writer import StreamWriter, Writer


async def run_manager():
    stream_writer = StreamWriter()

    def create_writer(job_type, header, chunk_size=100):
        writer = Writer(job_type, header, chunk_size)
        stream_writer.writers.append(writer)
        return writer

    cache_obj = CacheObj()
    job_factory = JobFactory(cache_obj=cache_obj, create_writer=create_writer)
    manager = Manager(writers=stream_writer, job_factory=job_factory)
    return manager


async def main():
    manager = await run_manager()

    doc_reader = GoalDocReader()
    req_list = [('2022', '교육부')]
    for year, ministry in req_list:
        content = await doc_reader.read(year, ministry)
        await manager.add('goal', content, f"{year}, {ministry}")
    await manager.parsing()

    # parsing_task.add_done_callback(doc_reader.result)

if __name__ == '__main__':
    asyncio.run(main())
