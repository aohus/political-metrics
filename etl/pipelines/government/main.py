import asyncio

from client import Client, Config
from document import GovGoalJobConfigRegistry
from jobloop import JobLoop


async def run_jobloop():
    jobloop = JobLoop()
    return jobloop


def create_client(jobloop):
    config = Config(target_dir="/Users/aohus/Workspaces/github/politics/etl/data/government/국정과제/tasks_data",
                    tmp_dir="/Users/aohus/Workspaces/github/politics/etl/data/government/국정과제/tasks_data/tmp",
                    doc_configs={
                            'gov': {
                                'req_list': [
                                    ('2024', '기재부'), 
                                    ('2025', '기재부'), 
                                    ('2022', '교육부'), 
                                    ('2023', '교육부'), 
                                    ('2024', '교육부'), 
                                ],
                                'job_configs': GovGoalJobConfigRegistry()
                            }
                        })
    client = Client(jobloop, config)
    client.register_docs()


async def main():
    jobloop = await run_jobloop()
    create_client(jobloop)
    await jobloop.run()

if __name__ == '__main__':
    asyncio.run(main())
