import asyncio
import logging

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
        await self.req_queue.put(job_type, content, fk)

    async def create_job(self, job_type, content, fk):
        try:
            job = await self.job_factory.create_job(
                manager=self,
                job_type=job_type,
                content=content,
                fk=fk
            )
            await self.job_queue.put(job)
            logger.info(f"Created job: {job}")
        except ValueError as e:
            logger.error(f"Error: {e}")

    async def parsing(self):
        while self.job_tasks:
            await self.run_jobs()
            await self.create_jobs()
            
            job_tasks, self.job_tasks = self.job_tasks, asyncio.Queue()
            while job_tasks:
                task = job_tasks.get_nowait()
                if not task.is_done():
                    self.job_tasks.put(task)

            if not (self.job_queue or self.req_queue or self.job_tasks) and self.is_done:
                await self.shutdown()

    async def run_jobs(self):
        job_queue, self.job_queue = self.job_queue, asyncio.Queue()
        while job_queue:
            job = job_queue.get_nowait()
            task = asyncio.create_task(job.process())
            self.job_tasks.append(task)

    async def create_jobs(self):
        req_queue, self.req_queue = self.req_queue, asyncio.Queue()
        while req_queue:
            job_type, content, fk = req_queue.get_nowait()
            await self.create_job(job_type, content, fk)

    async def shutdown(self):
        clear_tasks = [writer.clear() for writer in self.cache_obj._writer_cache.values()]
        results = await asyncio.gather(*clear_tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(str(result))
