from dataclasses import dataclass

import torch

from .type import GenerationConfig, ModelConfig, QuantizationConfig


class ModelRegistry:
    """모델 레지스트리 - 지원되는 모델들을 관리"""
    
    MODELS = {
        "deepseek_r1_1.5b": ModelConfig(
            name="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
            display_name="DeepSeek R1 1.5B",
            memory_4bit=1.2,
            memory_8bit=2.0,
            recommended_batch_size=8,
            temperature=0.6,
            max_new_tokens=500,
            context_length=32768,
            specialties=["reasoning", "legal_analysis", "chain_of_thought"],
            license="MIT",
            description="추론에 특화된 경량 모델, 법안 분석에 최적화"
        ),
        
        "qwen2.5_3b": ModelConfig(
            name="Qwen/Qwen2.5-3B-Instruct",
            display_name="Qwen2.5 3B",
            memory_4bit=2.2,
            memory_8bit=3.5,
            recommended_batch_size=4,
            temperature=0.3,
            max_new_tokens=400,
            context_length=32768,
            specialties=["multilingual", "korean", "general_purpose"],
            license="Apache-2.0",
            description="다국어 지원 우수, 한국어 성능 뛰어남"
        ),
        
        "phi3.5_mini": ModelConfig(
            name="microsoft/Phi-3.5-mini-instruct",
            display_name="Phi-3.5 Mini",
            memory_4bit=2.8,
            memory_8bit=4.2,
            recommended_batch_size=2,
            temperature=0.3,
            max_new_tokens=400,
            context_length=4096,
            specialties=["efficiency", "stability", "instruction_following"],
            license="MIT",
            description="Microsoft의 안정적인 소형 모델"
        ),
        
        "qwen2.5_1.5b": ModelConfig(
            name="Qwen/Qwen2.5-1.5B-Instruct",
            display_name="Qwen2.5 1.5B",
            memory_4bit=1.1,
            memory_8bit=1.8,
            recommended_batch_size=8,
            temperature=0.3,
            max_new_tokens=400,
            context_length=32768,
            specialties=["efficiency", "multilingual", "korean"],
            license="Apache-2.0",
            description="가장 경량화된 다국어 모델"
        )
    }
    
    @classmethod
    def get_model_config(cls, model_key: str) -> ModelConfig:
        """모델 설정 반환"""
        if model_key not in cls.MODELS:
            raise ValueError(f"지원되지 않는 모델: {model_key}. 지원 모델: {list(cls.MODELS.keys())}")
        return cls.MODELS[model_key]
    
    @classmethod
    def list_models(cls) -> dict[str, ModelConfig]:
        """지원되는 모든 모델 목록 반환"""
        return cls.MODELS
    
    @classmethod
    def recommend_model(cls, gpu_memory_gb: float, priority: str = "reasoning") -> ModelConfig:
        """GPU 메모리와 우선순위에 따른 모델 추천"""
        suitable_models = []
        
        for key, config in cls.MODELS.items():
            if config.memory_4bit <= gpu_memory_gb - 1:  # 1GB 여유 공간
                suitable_models.append((key, config))
        
        if not suitable_models:
            raise ValueError(f"GPU 메모리 {gpu_memory_gb}GB로는 실행 가능한 모델이 없습니다.")
        
        # 우선순위에 따른 정렬
        if priority == "reasoning":
            # 추론 능력 우선
            priority_order = ["deepseek_r1_1.5b", "qwen2.5_3b", "qwen2.5_1.5b", "phi3.5_mini"]
        elif priority == "korean":
            # 한국어 성능 우선
            priority_order = ["qwen2.5_3b", "qwen2.5_1.5b", "deepseek_r1_1.5b", "phi3.5_mini"]
        elif priority == "speed":
            # 속도 우선 (작은 모델)
            priority_order = ["qwen2.5_1.5b", "deepseek_r1_1.5b", "qwen2.5_3b", "phi3.5_mini"]
        else:
            # 균형 잡힌 선택
            priority_order = ["deepseek_r1_1.5b", "qwen2.5_3b", "qwen2.5_1.5b", "phi3.5_mini"]
        
        # 우선순위에 따라 정렬
        suitable_models.sort(key=lambda x: priority_order.index(x[0]) if x[0] in priority_order else 999)
        
        return suitable_models[0][1]
