import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class Manager:
    def __init__(self, writers, job_factory):
        self.job_tasks = asyncio.Queue()
        self.req_queue = asyncio.Queue()
        self.job_queue = asyncio.Queue()
        self.writers = writers
        self.job_factory = job_factory
        self.is_done = False

    async def add(self, job_type, content, fk):
        self.req_queue.put_nowait((job_type, content, fk))

    async def create_job(self, job_type, content, fk):
        try:
            job = await self.job_factory.create_job(
                manager=self,
                job_type=job_type,
                content=content,
                fk=fk
            )
            self.job_queue.put_nowait(job)
            logger.info(f"Created job: {job}")
        except ValueError as e:
            logger.error(f"Error: {e}")

    async def parsing(self):
        while 1:
            await self.create_jobs()
            
            # job_tasks, self.job_tasks = self.job_tasks, asyncio.Queue()
            # while job_tasks.qsize() > 0:
            #     task = await job_tasks.get()
                # if not task.is_done():
                #     await self.job_tasks.put_nowait(task)

            if not (self.job_queue or self.req_queue or self.job_tasks) and self.is_done:
                await self.shutdown()

    async def run_jobs(self):
        logging.info("run jobs")
        if self.job_queue.empty():
            return 
        
        job_queue, self.job_queue = self.job_queue, asyncio.Queue()
        while job_queue.qsize() > 0: 
            job = await job_queue.get()
            task = asyncio.create_task(job.process())
            self.job_tasks.put_nowait(task)

    async def create_jobs(self):
        logging.info("create jobs")
        while 1:
            job_type, content, fk = await self.req_queue.get()
            await self.create_job(job_type, content, fk)
            await self.run_jobs()

    async def shutdown(self):
        clear_tasks = [writer.clear() for writer in self.cache_obj._writer_cache.values()]
        results = await asyncio.gather(*clear_tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(str(result))
