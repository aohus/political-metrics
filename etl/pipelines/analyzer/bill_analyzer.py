import asyncio
import glob
import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import List, Union

import aiofiles
import pandas as pd
from utils.file.fileio import read_file

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BillInfo:
    """법안 기본 정보 구조체"""

    title: str
    bill_number: str
    proposal_date: str
    main_content: str
    reason: str


@dataclass
class AnalysisResult:
    """분석 결과 구조체"""

    bill_info: BillInfo
    policy_field: str
    sub_policy_fields: List[str]
    beneficiary_groups: List[str]
    economic_layers: List[str]
    political_spectrum: dict[str, float]
    policy_approach: str
    political_implications: List[str]
    ideology_score: float
    urgency_level: str
    social_impact: str


class PoliticalBillAnalyzer:
    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_tasks)
        self.keywords = self.load_keywords()

        self.policy_fields = self.keywords.policy_fields
        self.beneficiary_patterns = self.keywords.beneficiary_patterns
        self.political_spectrum_keywords = self.keywords.political_spectrum_keywords
        self.urgency_keywords = self.keywords.urgency_keywords
        self.social_impact_keywords = self.keywords.social_impact_keywords

    def load_keywords(self) -> dict[str, any]:
        from .keywords import KeywordDict
        return KeywordDict()

    def classify_policy_field(self, text: str, title_text: str, reason_text: str) -> tuple[str, List[str]]:
        """정책 분야 분류 (주 분야 + 부분야)"""
        field_scores = {}

        # 가중치 적용 (제목과 이유에 더 높은 가중치)
        title_weight = 3.0
        reason_weight = 2.0
        content_weight = 1.0

        for field, keywords in self.policy_fields.items():
            score = 0
            for keyword in keywords:
                # 제목에서 키워드 검색
                score += len(re.findall(keyword, title_text, re.IGNORECASE)) * title_weight
                # 이유에서 키워드 검색
                score += len(re.findall(keyword, reason_text, re.IGNORECASE)) * reason_weight
                # 전체 내용에서 키워드 검색
                score += len(re.findall(keyword, text, re.IGNORECASE)) * content_weight

            field_scores[field] = score

        # 주 분야 결정
        main_field = max(field_scores, key=field_scores.get) if field_scores else "기타"

        # 부분야 결정 (점수가 높은 상위 3개)
        sorted_fields = sorted(field_scores.items(), key=lambda x: x[1], reverse=True)
        sub_fields = [field for field, score in sorted_fields[:3] if score > 0 and field != main_field]

        return main_field, sub_fields

    def analyze_beneficiaries(self, text: str) -> tuple[List[str], List[str]]:
        """수혜층 분석 (개선된 알고리즘)"""
        beneficiary_groups = []
        economic_layers = []

        # 가중치 적용 분석
        for group, patterns in self.beneficiary_patterns.items():
            group_score = 0
            for pattern in patterns:
                # 정확한 매칭에 더 높은 점수
                exact_matches = len(re.findall(f"\\b{pattern}\\b", text, re.IGNORECASE))
                partial_matches = len(re.findall(pattern, text, re.IGNORECASE)) - exact_matches

                group_score += exact_matches * 2 + partial_matches

            if group_score > 0:
                beneficiary_groups.append((group, group_score))

        # 점수 기준으로 정렬하고 상위 결과만 선택
        beneficiary_groups.sort(key=lambda x: x[1], reverse=True)
        beneficiary_groups = [group for group, score in beneficiary_groups[:10]]

        # 경제적 계층 분류 (더 정확한 분류)
        economic_mapping = {
            "서민층": ["저소득층", "농민", "소상공인", "자영업", "근로자", "프리랜서", "배달기사", "택시기사"],
            "중산층": ["중산층", "일반 국민", "공무원", "전문직", "직장인"],
            "고소득층": ["고소득층", "자산가"],
            "기업층": ["중소기업", "중견기업", "대기업", "스타트업", "플랫폼기업", "제조업", "서비스업"],
        }

        for layer, groups in economic_mapping.items():
            if any(group in beneficiary_groups for group in groups):
                economic_layers.append(layer)

        return beneficiary_groups, economic_layers

    def analyze_political_spectrum(self, text: str) -> dict[str, float]:
        """정치적 이념 스펙트럼 분석 (개선된 알고리즘)"""
        progressive_score = 0
        conservative_score = 0

        # 가중치 적용 분석
        for category, keywords in self.political_spectrum_keywords["진보"].items():
            category_weight = 1.5 if category in ["경제", "사회"] else 1.0
            for keyword in keywords:
                matches = len(re.findall(keyword, text, re.IGNORECASE))
                progressive_score += matches * category_weight

        for category, keywords in self.political_spectrum_keywords["보수"].items():
            category_weight = 1.5 if category in ["경제", "안보"] else 1.0
            for keyword in keywords:
                matches = len(re.findall(keyword, text, re.IGNORECASE))
                conservative_score += matches * category_weight

        total_score = progressive_score + conservative_score
        if total_score == 0:
            return {"진보": 0.5, "보수": 0.5, "중도": 1.0}

        prog_ratio = progressive_score / total_score
        cons_ratio = conservative_score / total_score

        # 중도 성향 계산 (양극화 정도의 역수)
        polarization = abs(prog_ratio - cons_ratio)
        moderate_ratio = 1 - polarization

        return {"진보": prog_ratio, "보수": cons_ratio, "중도": moderate_ratio}

    def analyze_policy_approach(self, text: str) -> str:
        """정책 방식 분석 (더 정확한 분석)"""
        approach_patterns = {
            "새로운 제도 신설": ["신설", "새로", "새롭게", "도입", "창설", "제정"],
            "기존 제도 연장": ["연장", "일몰", "기한", "연기", "유예", "유지"],
            "기존 제도 확대": ["확대", "확장", "늘려", "증가", "증대", "강화"],
            "기존 제도 개정": ["개정", "수정", "변경", "보완", "개선", "정비"],
            "기존 제도 폐지": ["폐지", "삭제", "없애", "철폐", "중단", "종료"],
            "기존 제도 완화": ["완화", "완충", "경감", "축소", "감축", "감소"],
        }

        approach_scores = {}
        for approach, patterns in approach_patterns.items():
            score = 0
            for pattern in patterns:
                score += len(re.findall(pattern, text, re.IGNORECASE))
            approach_scores[approach] = score

        if approach_scores:
            return max(approach_scores, key=approach_scores.get)
        return "기타"

    def analyze_urgency_level(self, text: str) -> str:
        """긴급성 수준 분석"""
        urgency_scores = {}

        for level, keywords in self.urgency_keywords.items():
            score = 0
            for keyword in keywords:
                score += len(re.findall(keyword, text, re.IGNORECASE))
            urgency_scores[level] = score

        if urgency_scores:
            return max(urgency_scores, key=urgency_scores.get)
        return "보통"

    def analyze_social_impact(self, text: str) -> str:
        """사회적 영향 분석"""
        impact_scores = {}

        for impact, keywords in self.social_impact_keywords.items():
            score = 0
            for keyword in keywords:
                score += len(re.findall(keyword, text, re.IGNORECASE))
            impact_scores[impact] = score

        if impact_scores:
            return max(impact_scores, key=impact_scores.get)
        return "보통"

    def derive_political_implications(self, analysis_result: AnalysisResult) -> List[str]:
        """정치적 함의 도출 (확장된 분석)"""
        implications = []

        # 정책 분야별 함의
        field_implications = {
            "디지털정책": "디지털 전환과 4차 산업혁명 대응",
            "지역개발": "지역 균형발전과 분권화 정책",
            "경제정책": "경제성장과 산업 경쟁력 강화",
            "사회정책": "사회적 형평성과 복지 확대",
            "기술혁신": "미래 성장 동력과 혁신 생태계 구축",
            "환경정책": "지속가능한 발전과 기후변화 대응",
            "주택정책": "주거 안정과 부동산 시장 조절",
            "교육정책": "교육 격차 해소와 인재 양성",
            "보건의료": "의료 접근성과 공공보건 강화",
            "노동정책": "노동자 권익 보호와 고용 안정",
            "금융정책": "금융 안정과 서민 금융 지원",
            "문화정책": "문화 향유권과 창조경제 활성화",
            "국방정책": "국가 안보와 방위력 강화",
            "외교정책": "국제 협력과 국익 증진",
            "농업정책": "농업 경쟁력과 농촌 발전",
            "교통정책": "교통 인프라와 이동권 보장",
        }

        if analysis_result.policy_field in field_implications:
            implications.append(field_implications[analysis_result.policy_field])

        # 수혜층별 함의
        if "서민층" in analysis_result.economic_layers:
            implications.append("서민 생활 안정과 소득 재분배")
        if "기업층" in analysis_result.economic_layers:
            implications.append("기업 활동 지원과 투자 촉진")
        if "중산층" in analysis_result.economic_layers:
            implications.append("중산층 보호와 안정적 성장")
        if "고소득층" in analysis_result.economic_layers:
            implications.append("고소득층 대상 정책 조정")

        # 정치적 스펙트럼별 함의
        if analysis_result.political_spectrum["진보"] > 0.6:
            implications.append("진보적 가치 추구와 사회 개혁")
        elif analysis_result.political_spectrum["보수"] > 0.6:
            implications.append("안정성 중시와 기존 질서 유지")
        else:
            implications.append("실용적 정책 접근과 중도 지향")

        # 긴급성별 함의
        if analysis_result.urgency_level == "매우 긴급":
            implications.append("즉각적 대응이 필요한 사회 현안")
        elif analysis_result.urgency_level == "긴급":
            implications.append("신속한 정책 대응 필요")
        elif analysis_result.urgency_level == "장기":
            implications.append("장기적 관점의 정책 추진")

        # 사회적 영향별 함의
        if analysis_result.social_impact == "광범위":
            implications.append("전 국민 대상의 포괄적 정책")
        elif analysis_result.social_impact == "상당함":
            implications.append("사회 전반에 상당한 영향")
        elif analysis_result.social_impact == "제한적":
            implications.append("특정 계층 대상의 맞춤형 정책")

        return implications

    async def get_bill_info(self, path) -> BillInfo:
        text = await read_file(path)
        reason = text.get("sections", {}).get("제안이유", "이유 미확인")
        if len(reason) < 10:
            reason = text.get("sections", {}).get("주요내용", "이유 미확인")
        return BillInfo(
            title=text.get("title", "제목 미확인"),
            bill_number=text.get("bill_number", "번호 미확인"),
            proposal_date=text.get("proposal_date", "날짜 미확인"),
            main_content=text.get("full_text", "내용 미확인"),
            reason=reason,
        )

    async def analyze_single_bill(self, pdf_path: str) -> AnalysisResult:
        """단일 법안 분석 (비동기)"""
        async with self.semaphore:
            bill_info = await self.get_bill_info(pdf_path)
            if not bill_info:
                raise ValueError("PDF 텍스트 추출 실패")
            text = bill_info.main_content

            # 각종 분석 수행
            policy_field, sub_policy_fields = self.classify_policy_field(text, bill_info.title, bill_info.reason)
            beneficiary_groups, economic_layers = self.analyze_beneficiaries(text)
            political_spectrum = self.analyze_political_spectrum(text)
            policy_approach = self.analyze_policy_approach(text)
            urgency_level = self.analyze_urgency_level(text)
            social_impact = self.analyze_social_impact(text)

            # 이념 점수 계산 (진보 -1, 보수 +1 스케일)
            ideology_score = political_spectrum["보수"] - political_spectrum["진보"]

            # 분석 결과 생성
            analysis_result = AnalysisResult(
                bill_info=bill_info,
                policy_field=policy_field,
                sub_policy_fields=sub_policy_fields,
                beneficiary_groups=beneficiary_groups,
                economic_layers=economic_layers,
                political_spectrum=political_spectrum,
                policy_approach=policy_approach,
                political_implications=[],
                ideology_score=ideology_score,
                urgency_level=urgency_level,
                social_impact=social_impact,
            )

            # # 정치적 함의 도출
            analysis_result.political_implications = self.derive_political_implications(analysis_result)
            return analysis_result

    async def analyze_multiple_bills(self, pdf_paths: List[str], progress_callback=None) -> List[AnalysisResult]:
        """여러 법안 일괄 분석 (비동기)"""
        results = []
        failed_files = []

        tasks = []
        for i, pdf_path in enumerate(pdf_paths):
            task = asyncio.create_task(self._analyze_with_progress(pdf_path, i, len(pdf_paths), progress_callback))
            tasks.append(task)

        # 모든 작업 완료 대기
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(completed_tasks):
            if isinstance(result, Exception):
                failed_files.append(pdf_paths[i])
                logger.error(f"법안 분석 실패 ({pdf_paths[i]}): {result}")
            else:
                results.append(result)

        if failed_files:
            logger.warning(f"총 {len(failed_files)}개 파일 분석 실패")

        logger.info(f"전체 분석 완료: {len(results)}개 성공, {len(failed_files)}개 실패")
        return results

    async def _analyze_with_progress(self, pdf_path: str, index: int, total: int, progress_callback) -> AnalysisResult:
        """진행률 콜백과 함께 분석"""
        result = await self.analyze_single_bill(pdf_path)

        if progress_callback:
            progress_callback(index + 1, total, pdf_path)

        return result

    async def save_analysis_results(
        self, results: Union[AnalysisResult, List[AnalysisResult]], output_path: str, format_type: str = "json"
    ):
        """분석 결과 저장 (비동기)"""
        if isinstance(results, AnalysisResult):
            results = [results]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format_type == "json":
            output_file = f"{output_path}_analysis_{timestamp}.json"
            await self._save_as_json(results, output_file)
        elif format_type == "excel":
            output_file = f"{output_path}_analysis_{timestamp}.xlsx"
            await self._save_as_excel(results, output_file)
        elif format_type == "text":
            output_file = f"{output_path}_analysis_{timestamp}.txt"
            await self._save_as_text(results, output_file)

        logger.info(f"분석 결과 저장 완료: {output_file}")
        return output_file

    async def _save_as_json(self, results: List[AnalysisResult], file_path: str):
        """JSON 형식으로 저장 (비동기)"""
        json_data = []
        for result in results:
            json_data.append(
                {
                    "bill_info": {
                        "title": result.bill_info.title,
                        "bill_number": result.bill_info.bill_number,
                        "proposal_date": result.bill_info.proposal_date,
                        "reason": result.bill_info.reason,
                    },
                    "analysis": {
                        "policy_field": result.policy_field,
                        "sub_policy_fields": result.sub_policy_fields,
                        "beneficiary_groups": result.beneficiary_groups,
                        "economic_layers": result.economic_layers,
                        "political_spectrum": result.political_spectrum,
                        "policy_approach": result.policy_approach,
                        "political_implications": result.political_implications,
                        "ideology_score": result.ideology_score,
                        "urgency_level": result.urgency_level,
                        "social_impact": result.social_impact,
                    },
                }
            )

        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(json_data, ensure_ascii=False, indent=2))

    async def _save_as_excel(self, results: List[AnalysisResult], file_path: str):
        """Excel 형식으로 저장 (비동기)"""

        def _create_dataframe():
            data = []
            for result in results:
                data.append(
                    {
                        "법안명": result.bill_info.title,
                        "의안번호": result.bill_info.bill_number,
                        "발의일자": result.bill_info.proposal_date,
                        "주정책분야": result.policy_field,
                        "부정책분야": ", ".join(result.sub_policy_fields),
                        "수혜층": ", ".join(result.beneficiary_groups),
                        "경제계층": ", ".join(result.economic_layers),
                        "정책방식": result.policy_approach,
                        "진보성향": result.political_spectrum["진보"],
                        "보수성향": result.political_spectrum["보수"],
                        "중도성향": result.political_spectrum["중도"],
                        "이념점수": result.ideology_score,
                        "긴급성": result.urgency_level,
                        "사회적영향": result.social_impact,
                        "정치적함의": "; ".join(result.political_implications),
                    }
                )
            return pd.DataFrame(data)

        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(self.executor, _create_dataframe)
        await loop.run_in_executor(self.executor, df.to_excel, file_path, False)

    async def _save_as_text(self, results: List[AnalysisResult], file_path: str):
        """텍스트 형식으로 저장 (비동기)"""
        content = []
        for i, result in enumerate(results, 1):
            content.append(f"=== 법안 {i} 분석 결과 ===\n")
            content.append(f"📋 법안 정보\n")
            content.append(f"- 제목: {result.bill_info.title}\n")
            content.append(f"- 의안번호: {result.bill_info.bill_number}\n")
            content.append(f"- 발의일자: {result.bill_info.proposal_date}\n\n")

            content.append(f"🎯 분석 결과\n")
            content.append(f"- 주정책분야: {result.policy_field}\n")
            content.append(f"- 부정책분야: {', '.join(result.sub_policy_fields)}\n")
            content.append(f"- 수혜층: {', '.join(result.beneficiary_groups)}\n")
            content.append(f"- 경제계층: {', '.join(result.economic_layers)}\n")
            content.append(f"- 정책방식: {result.policy_approach}\n")
            content.append(f"- 이념점수: {result.ideology_score:.2f}\n")
            content.append(f"- 긴급성: {result.urgency_level}\n")
            content.append(f"- 사회적영향: {result.social_impact}\n\n")

            content.append(f"🏛️ 정치적 스펙트럼\n")
            for spectrum, score in result.political_spectrum.items():
                content.append(f"- {spectrum}: {score:.2f}\n")

            content.append(f"\n💡 정치적 함의\n")
            for implication in result.political_implications:
                content.append(f"- {implication}\n")

            content.append(f"\n{'='*50}\n\n")

        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write("".join(content))

    def close(self):
        """리소스 정리"""
        self.executor.shutdown(wait=True)


# 진행률 콜백 함수
def progress_callback(current, total, current_file):
    """진행률 표시 콜백"""
    progress = (current / total) * 100
    print(f"\r진행률: {progress:.1f}% ({current}/{total}) - {os.path.basename(current_file)}", end="", flush=True)
    if current == total:
        print()  # 완료 시 새 줄


async def main():
    """메인 실행 함수"""
    analyzer = PoliticalBillAnalyzer(max_concurrent_tasks=20)

    try:
        # 단일 법안 분석 예제
        # print("=== 단일 법안 분석 ===")
        # result = await analyzer.analyze_single_bill("example_bill.pdf")
        # await analyzer.save_analysis_results(result, "single_bill_analysis", "json")
        # print("단일 법안 분석 완료")

        # 여러 법안 일괄 분석 예제
        print("\n=== 여러 법안 일괄 분석 ===")
        filelist = glob.glob(f"{os.path.basename(os.path.__file__)}/*.txt")  # PDF 파일 경로 설정
        pdf_files = filelist[:10]  # 예시로 10개 파일만 분석

        start_time = time.time()
        results = await analyzer.analyze_multiple_bills(pdf_files, progress_callback)
        end_time = time.time()

        await analyzer.save_analysis_results(results, "multiple_bills_analysis", "excel")
        print(f"총 {len(results)}개 법안 분석 완료 (소요시간: {end_time - start_time:.2f}초)")

    except Exception as e:
        print(f"분석 실패: {e}")
    finally:
        analyzer.close()


if __name__ == "__main__":
    asyncio.run(main())
