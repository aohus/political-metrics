import logging

from .job import JobFactory

# 로깅 설정
logger = logging.getLogger(__name__)


class Manager:
    def __init__(self):
        self.queue = []
        self.job_factory = JobFactory()

    def add(self, job_type, content, linker):
        job = self.create_job(job_type, content, linker)
        self.queue.add(job)

    def create_job(self, job_type, content, linker):
        try:
            job = self.job_factory.create_job(
                manager=self,
                job_type=job_type,
                content=content,
                linker=linker
            )
            logger.info(f"Created job: {job}")
        except ValueError as e:
            logger.error(f"Error: {e}")

    def parsing(self):
        while True:
            if section := self.section_queue.pop():
                section.parse()
