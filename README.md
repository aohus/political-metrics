실행 방법
1. 백엔드 실행
bash# 필요한 패키지 설치
pip install fastapi uvicorn aiohttp

# 서버 실행
python main.py
# 또는
uvicorn main:app --reload --host 0.0.0.0 --port 8000
2. 프론트엔드 실행

HTML 파일을 웹서버에서 실행 (Live Server 등)
API_BASE_URL을 백엔드 주소로 설정

확장 가능한 구조
새로운 데이터 소스 추가
pythonasync def collect_new_data_source(self, politician_name: str):
    # 새로운 API 연동 로직
    return collected_data
새로운 평가 지표 추가
pythondef calculate_new_metric(self, data: Dict) -> Metric:
    # 새로운 평가 로직
    return Metric(score=calculated_score, details=details)
이제 실제 API 연동과 자동 계산이 가능한 완전한 정치인 평가 시스템이 완성되었습니다! 백엔드는 실시간으로 데이터를 수집하고 분석하며, 프론트엔드는 사용자 친화적인 대시보드를 제공합니다.