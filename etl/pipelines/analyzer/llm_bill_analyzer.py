import gc
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

import torch
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from .model_configs.model_registry import ModelRegistry
from .model_configs.type import GenerationConfig, ModelConfig, QuantizationConfig


class LLMBillAnalyzer:
    def __init__(self, model_name: str = "deepseek_r1_1.5b", custom_config: Optional[ModelConfig] = None):
        """
        Args:
            model_key: ModelRegistry의 모델 키
            custom_config: 사용자 정의 모델 설정
        """
        if custom_config:
            self.model_config = custom_config
        else:
            self.model_config = ModelRegistry.get_model_config(model_name)
        
        self.model = None
        self.tokenizer = None
        self.generation_config = GenerationConfig(
            max_new_tokens=self.model_config.max_new_tokens,
            temperature=self.model_config.temperature
        )
        self.batch_size = 1  # 동적으로 계산됨
        
        self.setup_model()
    
    def setup_model(self):
        """모델 설정 및 로드"""
        print(f"🚀 {self.model_config.display_name} 로딩 중...")
        print(f"📝 {self.model_config.description}")
        
        # 양자화 설정
        quant_config = QuantizationConfig()
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=quant_config.load_in_4bit,
            bnb_4bit_compute_dtype=quant_config.bnb_4bit_compute_dtype,
            bnb_4bit_use_double_quant=quant_config.bnb_4bit_use_double_quant,
            bnb_4bit_quant_type=quant_config.bnb_4bit_quant_type,
            bnb_4bit_quant_storage=quant_config.bnb_4bit_quant_storage
        )
        
        # 토크나이저 로드
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_config.name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # 모델 로드
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_config.name,
            quantization_config=quantization_config,
            device_map="cuda:0",
            torch_dtype=torch.bfloat16,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            use_cache=False
        )
        
        # 메모리 사용량 확인 및 배치 크기 계산
        self._calculate_optimal_batch_size()
        
        print(f"✅ 모델 로드 완료!")
        print(f"💾 예상 메모리: {self.model_config.memory_4bit:.1f}GB")
        print(f"📦 최적 배치 크기: {self.batch_size}")
        print(f"🏷️ 특화 분야: {', '.join(self.model_config.specialties)}")
    
    def _calculate_optimal_batch_size(self):
        """최적 배치 크기 계산"""
        try:
            memory_used = torch.cuda.memory_allocated() / 1024**3
            total_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            memory_free = total_memory - memory_used
            
            print(f"💾 GPU 메모리: {memory_used:.1f}GB / {total_memory:.1f}GB")
            print(f"🆓 여유 메모리: {memory_free:.1f}GB")
            
            # 배치 크기 계산
            if memory_free > 3:
                self.batch_size = min(self.model_config.recommended_batch_size, 8)
            elif memory_free > 2:
                self.batch_size = min(self.model_config.recommended_batch_size, 4)
            elif memory_free > 1:
                self.batch_size = min(self.model_config.recommended_batch_size, 2)
            else:
                self.batch_size = 1
                
        except Exception as e:
            print(f"⚠️ 메모리 계산 실패: {e}")
            self.batch_size = 1
    
    def create_legal_prompt(self, json_data: Dict) -> str:
        """법안 분석용 프롬프트"""
        title = json_data.get("title", "")
        main_content = json_data.get("sections", {}).get("제안이유_및_주요내용", "")
        
        # 모델별 최대 길이 조정
        max_content_length = min(1500, self.model_config.context_length // 4)
        if len(main_content) > max_content_length:
            main_content = main_content[:max_content_length] + "..."
        
        prompt = f"""<|im_start|>system
                당신은 정책 분류 전문가입니다. 주어진 법률안을 분석하여 정확하고 일관된 분류를 제공해주세요.<|im_end|>
                <|im_start|>user
                다음 법률안을 분석하여 분류해주세요:

                **법률안 제목:** {title}

                **제안 이유:**
                {main_content}


                다음 형식으로 분류 결과를 JSON으로 제시해주세요:

                ```json
                {{
                "policy_domain_main": "경제|사회|외교국방|교육|환경|보건의료|법무행정|농림수산|국토교통|과학기술",
                "policy_domain_sub": ["세부영역1", "세부영역2", "세부영역3"],
                "government_ministry": ["관련부처1", "관련부처2"],
                "target_scope": "전국민|특정지역|특정집단|기업|공공기관",
                "target_group": ["구체적대상1", "구체적대상2"],
                "regulation_type": "규제강화|규제완화|규제중립|신규규제",
                "regulation_intensity": 1-5,
                "market_intervention": 1-5,
                "fiscal_impact": "예산증가|예산중립|예산절감|미상",
                "policy_instrument": "직접규제|경제적유인|정보제공|조직개편|기타"
                }}
                ```<|im_end|>
                <|im_start|>assistant
                ```json
                """
        return prompt
    
    def analyze_single(self, json_data: Dict) -> Dict:
        """단일 문서 분석"""
        try:
            prompt = self.create_legal_prompt(json_data)
            
            # 토큰화
            inputs = self.tokenizer(
                prompt, 
                return_tensors="pt", 
                truncation=True, 
                max_length=min(2048, self.model_config.context_length // 2),
                padding=False
            ).to(self.model.device)
            
            # 생성
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.generation_config.max_new_tokens,
                    temperature=self.generation_config.temperature,
                    do_sample=self.generation_config.do_sample,
                    top_p=self.generation_config.top_p,
                    repetition_penalty=self.generation_config.repetition_penalty,
                    pad_token_id=self.tokenizer.eos_token_id,
                    use_cache=False,
                    early_stopping=self.generation_config.early_stopping
                )
            
            # 결과 처리
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            answer = response[len(prompt):].strip()
            
            # JSON 파싱
            result = self._parse_json_response(answer)
            
            # 메타데이터 추가
            result["model_info"] = {
                "name": self.model_config.display_name,
                "specialties": self.model_config.specialties,
                "temperature": self.generation_config.temperature
            }
            
            # 메모리 정리
            del inputs, outputs
            torch.cuda.empty_cache()
            
            return result
            
        except Exception as e:
            return {"error": str(e), "model": self.model_config.display_name}
    
    def _parse_json_response(self, answer: str) -> Dict:
        """JSON 응답 파싱"""
        try:
            json_start = answer.find('{')
            json_end = answer.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = answer[json_start:json_end]
                return json.loads(json_str)
            else:
                return {"error": "JSON 형식을 찾을 수 없음", "raw": answer}
        except json.JSONDecodeError:
            return {"error": "JSON 파싱 실패", "raw": answer}
    
    def analyze_batch(self, json_files: List[Dict], output_path: str, delay: float = 0.5) -> List[Dict]:
        """배치 분석"""
        print(f"📊 {len(json_files)}개 파일 분석 시작...")
        print(f"🤖 모델: {self.model_config.display_name}")
        print(f"⚙️ 설정: T={self.generation_config.temperature}, 배치={self.batch_size}")
        
        results = []
        start_time = time.time()
        
        for i, file_data in enumerate(tqdm(json_files, desc="분석 중")):
            result = self.analyze_single(file_data['data'])
            result['source_file'] = file_data.get('file_path', f'file_{i}')
            results.append(result)
            
            # 진행 상황 리포트
            if (i + 1) % 100 == 0:
                self._report_progress(results, i + 1, len(json_files), start_time)
            
            # 메모리 관리
            if i % 50 == 0:
                gc.collect()
                torch.cuda.empty_cache()
            
            if delay > 0:
                time.sleep(delay)
        
        # 결과 저장
        self._save_results(results, output_path)
        self._print_final_stats(results, start_time)
        
        return results
    
    def _report_progress(self, results: list, completed: int, total: int, start_time: float):
        """진행 상황 리포트"""
        elapsed = time.time() - start_time
        avg_time = elapsed / completed
        remaining = (total - completed) * avg_time
        success_rate = len([r for r in results[-100:] if "error" not in r]) if len(results) >= 100 else "계산중"
        
        print(f"⏱️ 진행: {completed}/{total} ({completed/total*100:.1f}%)")
        print(f"📈 평균: {avg_time:.1f}초/개, 남은시간: {remaining/3600:.1f}시간")
        print(f"✅ 최근 100개 성공률: {success_rate}%")
    
    def _save_results(self, results: List[Dict], output_path: str):
        """결과 저장"""
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 전체 결과
        with open(output_path / "analysis_results.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 설정 정보 저장
        config_info = {
            "model_config": {
                "name": self.model_config.name,
                "display_name": self.model_config.display_name,
                "specialties": self.model_config.specialties,
                "memory_usage": f"{self.model_config.memory_4bit:.1f}GB",
                "license": self.model_config.license
            },
            "generation_config": {
                "temperature": self.generation_config.temperature,
                "max_new_tokens": self.generation_config.max_new_tokens,
                "top_p": self.generation_config.top_p
            },
            "batch_size": self.batch_size
        }
        
        with open(output_path / "model_config.json", 'w', encoding='utf-8') as f:
            json.dump(config_info, f, ensure_ascii=False, indent=2)
    
    def _print_final_stats(self, results: List[Dict], start_time: float):
        """최종 통계 출력"""
        total_time = time.time() - start_time
        success_count = len([r for r in results if "error" not in r])
        
        print(f"\n🎉 분석 완료!")
        print(f"📊 성공: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
        print(f"⏱️ 총 시간: {total_time/3600:.1f}시간")
        print(f"⚡ 평균 속도: {total_time/len(results):.1f}초/개")
        print(f"🤖 사용 모델: {self.model_config.display_name}")


def main():
    """메인 실행 함수"""
    
    # 지원되는 모델 목록 출력
    print("🤖 지원되는 모델들:")
    for key, config in ModelRegistry.list_models().items():
        print(f"  {key}: {config.display_name} ({config.memory_4bit:.1f}GB) - {config.description}")
    
    # GPU 메모리에 따른 모델 추천
    gpu_memory = 6.0
    print(f"\n💾 {gpu_memory}GB GPU 추천 모델:")
    
    for priority in ["reasoning", "korean", "speed"]:
        try:
            recommended = ModelRegistry.recommend_model(gpu_memory, priority)
            print(f"  {priority}: {recommended.display_name}")
        except ValueError as e:
            print(f"  {priority}: {e}")
    
    # 분석기 초기화 (추론 우선)
    print(f"\n🚀 분석기 초기화...")
    analyzer = BaseLLMBillAnalyzer("deepseek_r1_1.5b")
    
    # 테스트 데이터
    test_data = [{
        "file_path": "test.json", 
        "data": {
            "title": "테스트_법률안", 
            "sections": {
                "제안이유_및_주요내용": "채무자의 생계비 보호를 위한 압류금지 계좌 도입"
            }
        }
    }]
    
    # 분석 실행
    results = analyzer.analyze_batch(
        test_data, 
        output_path="legal_analysis_results",
        delay=0.5
    )
    
    print("🎉 테스트 완료!")

if __name__ == "__main__":
    main()


# 사용 예시 및 성능 테스트
def test_performance(classifier, model_name):
    """성능 테스트"""
    
    # 테스트 데이터
    test_data = {
        "title": "2200068_은행법_일부개정법률안",
        "sections": {
            "제안이유_및_주요내용": "현행 「민사집행법」 제246조제1항제8호에 의하면, 채무자의 1월간생계유지에 필요한 예금의 경우 해당 채권을 압류하지 못함. 그러나실무상 압류 단계에서 특정 예금채권의 최저생계비 여부를 확정하기곤란하다는 이유로, 일단 압류가 이루어지고 그 이후 해당 예금채권의최저생계비 여부에 관한 다툼이 이어지는 경우가 일반적임. 하지만 전국민 대부분의 경제활동이 예금계좌를 기초로 이루어지기때문에, 일단 압류가 이루어지면 그 효력이 계속되는 동안 채무자의신용카드대금, 임차료, 전기ㆍ수도ㆍ가스요금 납부 등 기본적 생계유지를 위한 활동이 사실상 어려워지게 됨. 이에 은행으로 하여금 자연인인 채무자에 한하여 1인당 전 은행을 통틀어 1개의 생계비계좌를 개설할 수 있도록 하고, 이 계좌에 해당하는 예금채권을 압류하지 못하도록 하며, 해당 계좌에 압류금지생계비초과 금액이 예치되면 자동으로 그 초과분을 예비계좌로 송금하도록하도록 하여 채무자의 생계비를 보호하려고 하는 것임(안 제30조의3신설).",
            "법률_제_호": "제30조의3(생계비계좌) ① 은행은 예금자(자연인에 한한다. 이하 이조에서 같다)의 요청에 따라 예금자에게 필요한 1월간의 생계비로서 대통령령으로 정하는 금액(이하 이 조에서 \"압류금지생계비\"라 한다)을 초과하여 예치할 수 없는 계좌(이하 이 조에서 \"생계비계좌\"라 한다)를 개설할 수 있다."
        }
    }
    
    print("=" * 80)
    print("6GB GPU 최적화 정책분류 시스템 테스트")
    print("=" * 80)
    
    # 분류기 초기화
    classifier = classifier(model_name)
    
    # 분류 수행
    print("\n분류 수행 중...")
    result = classifier.classify_fast(test_data)
    
    print("\n" + "=" * 80)
    print("분류 결과:")
    print("=" * 80)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result



if __name__ == "__main__":
#     # 성능 테스트 실행
    classifier = LLMBillAnalyzer
    model_name = "model_name"
    result = test_performance(classifier, model_name)
    
#     # 배치 처리 예시
#     batch_data = [test_data] * 5  # 5개 문서 테스트
#     batch_results = classifier.batch_classify(batch_data)