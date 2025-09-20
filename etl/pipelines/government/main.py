import asyncio

from document import Document, GovGoalJobConfigRegistry
from fileio import Reader, TargetWriter, Writer
from jobloop import JobLoop
from utils.doc_reader import GoalDocReader


async def run_jobloop():
    jobloop = JobLoop()
    return jobloop


def create_writer(target_writer, tmp_dir):
    writer = Writer(target_writer, tmp_dir)
    return writer


def create_reader(tmp_dir):
    reader = Reader(tmp_dir)
    return reader


def create_document(name, jobloop, target_writer, tmp_dir="tmp", doc_type=None):
    reader = create_reader(tmp_dir)
    writer = create_writer(target_writer, tmp_dir)
    job_configs = GovGoalJobConfigRegistry()

    return Document(name, jobloop, job_configs, reader, writer)


def create_target_writer():
    base_dir = '/Users/aohus/Workspaces/github/politics/etl/data/government/국정과제/tasks_data'
    return TargetWriter(base_dir=base_dir)


async def main():
    jobloop = await run_jobloop()
    target_writer = create_target_writer()

    tmp_dir = '/Users/aohus/Workspaces/github/politics/etl/data/government/국정과제/tasks_data/tmp'
    doc_0 = create_document('gov_0', jobloop, target_writer, tmp_dir=tmp_dir)
    doc_1 = create_document('gov_1', jobloop, target_writer, tmp_dir=tmp_dir)
    doc_2 = create_document('gov_2', jobloop, target_writer, tmp_dir=tmp_dir)

    req_list = [
        (doc_0, '2022', '교육부'), 
        (doc_1, '2023', '교육부'), 
        (doc_2, '2024', '교육부')
    ]

    for doc, year, ministry in req_list:
        filepath = GoalDocReader.get_filepath(year, ministry)
        doc.register(fk=f"{year}, {ministry}", job_type='goal', filepath=filepath)
    await jobloop.run()



if __name__ == '__main__':
    asyncio.run(main())
