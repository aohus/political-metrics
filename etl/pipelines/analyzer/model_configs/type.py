from dataclasses import dataclass

import torch


@dataclass
class ModelConfig:
    """모델 설정 클래스"""
    name: str
    display_name: str
    memory_4bit: float  # 4bit 양자화 시 메모리 (GB)
    memory_8bit: float  # 8bit 양자화 시 메모리 (GB)
    recommended_batch_size: int
    temperature: float
    max_new_tokens: int
    context_length: int
    specialties: list[str]
    license: str
    description: str

@dataclass
class GenerationConfig:
    """생성 설정 클래스"""
    max_new_tokens: int = 400
    temperature: float = 0.6
    top_p: float = 0.9
    repetition_penalty: float = 1.05
    do_sample: bool = True
    early_stopping: bool = True

@dataclass
class QuantizationConfig:
    """양자화 설정 클래스"""
    load_in_4bit: bool = True
    bnb_4bit_compute_dtype: torch.dtype = torch.bfloat16
    bnb_4bit_use_double_quant: bool = True
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_quant_storage: torch.dtype = torch.uint8
