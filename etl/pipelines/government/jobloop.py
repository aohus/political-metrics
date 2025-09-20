import logging
import time

from job import AbstractJobLoop

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class JobLoop(AbstractJobLoop):
    def __init__(self):
        self.docs = []
        self._sleep = 0

    async def run(self):
        while 1:
            docs = self.docs[:]
            if not docs:
                if self._sleep == 2:
                    return
                logger.info("sleep for 10")
                time.sleep(10)
                self._sleep += 1
                continue

            self.docs[:] = []
            for doc in docs:
                if doc.results:
                    logger.info(f"{doc.name} completed with result: {doc.result}")
                    continue 

                self.docs.append(doc)
                if doc.ready_queue:
                    job = await doc.ready_queue.get()
                await job.execute()

    async def shutdown(self):
        pass