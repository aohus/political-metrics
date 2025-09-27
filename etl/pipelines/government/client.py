import logging

from document import Document
from fileio import Reader, TargetWriter, Writer
from utils.doc_reader import GoalDocReader

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class Config:
    def __init__(self, target_dir, tmp_dir, doc_configs):
        self.target_dir = target_dir
        self.tmp_dir = tmp_dir
        self.doc_configs = doc_configs


class Client:
    def __init__(self, _jobloop, configs=None):
        self._jobloop = _jobloop
        self._target_writer = None
        self._reader = None
        self._writer = None
        self.configs = configs
        self._docs = []
        self._initialize()

    def _initialize(self):
        self._target_writer = self._create_target_writer(base_dir=self.configs.target_dir)
        self._reader = self._create_reader(tmp_dir=self.configs.tmp_dir)
        self._writer = self._create_writer(tmp_dir=self.configs.tmp_dir)

    def _create_target_writer(self, base_dir):
        return TargetWriter(base_dir=base_dir)

    def _create_writer(self, tmp_dir):
        return Writer(self._target_writer, tmp_dir)

    def _create_reader(self, tmp_dir):
        return Reader(tmp_dir)

    def _create_document(self, name, job_configs):
        return Document(name=name, 
                        job_configs=job_configs,
                        _jobloop=self._jobloop,
                        reader=self._reader,
                        writer=self._writer)

    def register_docs(self):
        for doc_name, doc_config in self.configs.doc_configs.items():
            job_configs = doc_config.get('job_configs')
            doc = self._create_document(doc_name, job_configs)
            self._docs.append(doc)
            self._run(doc, doc_config.get('req_list'))
    
    def _run(self, doc, req_list):
        for year, ministry in req_list:
            doc.register(fk=f"{year}, {ministry}", 
                         job_type='goal',
                         filepath=GoalDocReader.get_filepath(year, ministry))
            logger.info(f'{year} {ministry} registered')
    
    @property
    def doc_count(self):
        return len(self._docs)
    
    @property
    def docs(self):
        return self._docs

