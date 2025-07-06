import os
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class PathConfig:
    """설정 파일 기반 경로 관리"""
    
    def __init__(self, config_file: str = None):
        self.base_path = Path(__file__).parent
        self.config_file = config_file or 'configs/config.yaml' or 'config.yaml'
        self.config_data = self._load_config()
        self._setup_paths()
    
    def _load_config(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        config_path = Path(self.config_file)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _setup_paths(self):
        """경로 설정"""
        data_root = self.base_path / Path(self.config_data['etl_paths']['data_root'])
        
        # Assembly 경로들
        self.assembly_temp = data_root / self.config_data['etl_paths']['assembly']['temp']
        self.assembly_ref = data_root / self.config_data['etl_paths']['assembly']['ref']
        self.assembly_raw = data_root / self.config_data['etl_paths']['assembly']['raw']
        self.assembly_formatted = data_root / self.config_data['etl_paths']['assembly']['formatted']
        
        # Document 경로들
        self.document_pdf = data_root / self.config_data['etl_paths']['document']['pdf']
        self.document_json = data_root / self.config_data['etl_paths']['document']['json']
        
        # Law 경로들
        self.law_raw = data_root / self.config_data['etl_paths']['law']['raw']
    
    def create_directories(self):
        """디렉토리 생성"""
        paths = [
            self.assembly_temp, self.assembly_ref, self.assembly_raw,
            self.assembly_formatted, self.document_json, 
            self.document_pdf, self.law_raw
        ]
        
        for path in paths:
            path.mkdir(parents=True, exist_ok=True)
    
    def get_path(self, category: str, subcategory: str = None) -> Path:
        """동적 경로 접근"""
        if subcategory:
            return getattr(self, f"{category}_{subcategory}")
        else:
            return getattr(self, category)