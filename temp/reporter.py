class PerformanceReporter:
    """실적 보고서 생성기"""

    @staticmethod
    def generate_report(profile: MemberProfile, metrics: PerformanceMetrics) -> str:
        """종합 실적 보고서 생성"""
        report = f"""
                {'='*60}
                국회의원 활동 실적 분석 보고서
                {'='*60}

                📋 기본 정보
                - 성명: {profile.name}
                - 소속 정당: {profile.party}
                - 지역구: {profile.district}
                - 선수: {profile.term}선
                - 소속 위원회: {profile.committee}

                ⚖️ 입법 활동 실적
                - 대표발의 법안: {metrics.representative_bills}건
                - 공동발의 법안: {metrics.co_sponsored_bills}건
                - 법안 가결률: {metrics.bill_passage_rate:.1f}%
                - 평균 처리기간: {metrics.avg_processing_days:.1f}일

                🗳️ 표결 참여 활동
                - 본회의 표결 참여율: {metrics.voting_participation_rate:.1f}%
                - 정당 일치도: {metrics.party_loyalty_rate:.1f}%

                💬 회의 참여 활동
                - 본회의 발언: {metrics.plenary_speeches}회
                - 위원회 질의: {metrics.committee_questions}회
                - 평균 발언 길이: {metrics.avg_speech_length:.0f}자

                🔍 국정감사 활동
                - 국감 질의: {metrics.audit_questions}건
                - 감사 지적사항: {metrics.audit_findings}건

                📈 정책 활동
                - 정책 세미나 개최: {metrics.policy_seminars}회
                - SNS 활동: {metrics.sns_activities}건

                📊 전문 분야 분석
                """

        if metrics.field_specialization:
            for field, count in sorted(
                metrics.field_specialization.items(), key=lambda x: x[1], reverse=True
            ):
                report += f"- {field}: {count}건\n"

        if metrics.voting_patterns:
            report += "\n🗳️ 표결 패턴\n"
            for pattern, count in metrics.voting_patterns.items():
                report += f"- {pattern}: {count}회\n"

        report += f"\n{'='*60}\n"
        return report

    @staticmethod
    def export_to_csv(
        members_data: List[Tuple[MemberProfile, PerformanceMetrics]],
        filename: str = "member_performance.csv",
    ):
        """CSV 파일로 내보내기"""
        data = []

        for profile, metrics in members_data:
            row = {
                "성명": profile.name,
                "정당": profile.party,
                "지역구": profile.district,
                "선수": profile.term,
                "위원회": profile.committee,
                "대표발의": metrics.representative_bills,
                "공동발의": metrics.co_sponsored_bills,
                "가결률(%)": round(metrics.bill_passage_rate, 1),
                "평균처리일": round(metrics.avg_processing_days, 1),
                "표결참여율(%)": round(metrics.voting_participation_rate, 1),
                "본회의발언": metrics.plenary_speeches,
                "위원회질의": metrics.committee_questions,
                "국감질의": metrics.audit_questions,
                "정책세미나": metrics.policy_seminars,
                "SNS활동": metrics.sns_activities,
            }
            data.append(row)

        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"분석 결과가 '{filename}'에 저장되었습니다.")


# 사용 예시
def main():
    """메인 실행 함수"""
    # API 키 설정 (실제 사용시 발급받은 키 입력)
    API_KEY = "YOUR_API_KEY_HERE"

    # API 클라이언트 초기화
    api_client = NationalAssemblyAPI(API_KEY)
    calculator = PerformanceCalculator(api_client)

    # 분석할 의원 목록
    members_to_analyze = ["김철수", "박영희", "이민수"]  # 예시 의원명

    results = []

    for member_name in members_to_analyze:
        try:
            # 의원 기본 정보 조회
            profile = api_client.get_member_profile(member_name)
            if not profile:
                print(f"의원 '{member_name}' 정보를 찾을 수 없습니다.")
                continue

            # 활동 실적 계산
            metrics = calculator.calculate_comprehensive_metrics(member_name)

            # 보고서 생성
            report = PerformanceReporter.generate_report(profile, metrics)
            print(report)

            results.append((profile, metrics))

        except Exception as e:
            print(f"의원 '{member_name}' 분석 중 오류 발생: {e}")

    # CSV 파일로 결과 저장
    if results:
        PerformanceReporter.export_to_csv(results)


if __name__ == "__main__":
    main()
