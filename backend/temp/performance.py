class PerformanceCalculator:
    """의원 활동 실적 계산기"""

    def __init__(self, api_client: NationalAssemblyAPI):
        self.api = api_client

    def calculate_legislative_metrics(self, member_name: str) -> Dict:
        """입법 활동 지표 계산"""
        # 대표발의 법안
        representative_bills = self.api.get_bills_by_member(member_name, "의원")

        # 공동발의 법안 (더 복잡한 조회 필요)
        co_sponsored_bills = self.api.get_bills_by_member(member_name, "공동")

        metrics = {
            "representative_bills": len(representative_bills),
            "co_sponsored_bills": len(co_sponsored_bills),
            "bill_passage_rate": 0.0,
            "avg_processing_days": 0.0,
            "field_specialization": defaultdict(int),
        }

        # 가결률 계산
        if representative_bills:
            passed_bills = [
                bill
                for bill in representative_bills
                if bill.get("RGS_CONF_RSLT") == "가결"
            ]
            metrics["bill_passage_rate"] = (
                len(passed_bills) / len(representative_bills) * 100
            )

        # 평균 처리 기간 계산
        processing_days = []
        for bill in representative_bills:
            propose_date = bill.get("PPSL_DT")
            promulgate_date = bill.get("PROM_DT")

            if propose_date and promulgate_date:
                try:
                    propose_dt = datetime.strptime(propose_date, "%Y%m%d")
                    promulgate_dt = datetime.strptime(promulgate_date, "%Y%m%d")
                    days = (promulgate_dt - propose_dt).days
                    processing_days.append(days)
                except ValueError:
                    continue

        if processing_days:
            metrics["avg_processing_days"] = sum(processing_days) / len(processing_days)

        # 분야별 발의 분석
        for bill in representative_bills:
            committee = bill.get("JRCMIT_NM", "기타")
            metrics["field_specialization"][committee] += 1

        return metrics

    def calculate_voting_metrics(self, member_name: str) -> Dict:
        """표결 참여 지표 계산"""
        voting_records = self.api.get_voting_records(member_name)

        metrics = {
            "voting_participation_rate": 0.0,
            "voting_patterns": defaultdict(int),
            "party_loyalty_rate": 0.0,
        }

        if not voting_records:
            return metrics

        # 표결 참여율 계산 (실제로는 전체 표결 수와 비교 필요)
        total_votes = len(voting_records)
        participated_votes = [
            vote
            for vote in voting_records
            if vote.get("VOTE_RSLT") in ["찬성", "반대", "기권"]
        ]

        if total_votes > 0:
            metrics["voting_participation_rate"] = (
                len(participated_votes) / total_votes * 100
            )

        # 찬반 패턴 분석
        for vote in participated_votes:
            result = vote.get("VOTE_RSLT", "기타")
            metrics["voting_patterns"][result] += 1

        # 정당 일치도 계산 (정당 표결과 비교 필요)
        # 이는 더 복잡한 로직이 필요함

        return metrics

    def calculate_meeting_metrics(self, member_name: str) -> Dict:
        """회의 참여 지표 계산"""
        plenary_records = self.api.get_plenary_minutes(member_name)
        committee_records = self.api.get_committee_minutes(member_name)

        metrics = {
            "plenary_speeches": len(plenary_records),
            "committee_questions": len(committee_records),
            "avg_speech_length": 0.0,
        }

        # 평균 발언 길이 계산
        all_speeches = plenary_records + committee_records
        speech_lengths = []

        for speech in all_speeches:
            content = speech.get("SPEAK_CONT", "")
            if content:
                speech_lengths.append(len(content))

        if speech_lengths:
            metrics["avg_speech_length"] = sum(speech_lengths) / len(speech_lengths)

        return metrics

    def calculate_audit_metrics(self, member_name: str) -> Dict:
        """국정감사 활동 지표 계산"""
        audit_records = self.api.get_audit_reports(member_name)

        metrics = {"audit_questions": 0, "audit_findings": 0}

        # 국감 질의 및 지적사항 계산
        for record in audit_records:
            # 질의 시간이나 발언 횟수 계산
            if record.get("QUESTION_CNT"):
                metrics["audit_questions"] += int(record.get("QUESTION_CNT", 0))

            # 지적사항 건수
            if record.get("FINDING_CNT"):
                metrics["audit_findings"] += int(record.get("FINDING_CNT", 0))

        return metrics

    def calculate_policy_metrics(self, member_name: str) -> Dict:
        """정책 활동 지표 계산"""
        seminars = self.api.get_policy_seminars(member_name)
        sns_activities = self.api.get_sns_activities(member_name)

        metrics = {
            "policy_seminars": len(seminars),
            "sns_activities": len(sns_activities),
            "legislative_previews": 0,  # 별도 API 필요
        }

        return metrics

    def calculate_comprehensive_metrics(self, member_name: str) -> PerformanceMetrics:
        """종합 실적 지표 계산"""
        print(f"의원 '{member_name}' 활동 실적 분석 중...")

        # 각 분야별 지표 계산
        legislative = self.calculate_legislative_metrics(member_name)
        voting = self.calculate_voting_metrics(member_name)
        meeting = self.calculate_meeting_metrics(member_name)
        audit = self.calculate_audit_metrics(member_name)
        policy = self.calculate_policy_metrics(member_name)

        # PerformanceMetrics 객체 생성
        return PerformanceMetrics(
            representative_bills=legislative["representative_bills"],
            co_sponsored_bills=legislative["co_sponsored_bills"],
            bill_passage_rate=legislative["bill_passage_rate"],
            avg_processing_days=legislative["avg_processing_days"],
            field_specialization=dict(legislative["field_specialization"]),
            voting_participation_rate=voting["voting_participation_rate"],
            voting_patterns=dict(voting["voting_patterns"]),
            party_loyalty_rate=voting["party_loyalty_rate"],
            plenary_speeches=meeting["plenary_speeches"],
            committee_questions=meeting["committee_questions"],
            avg_speech_length=meeting["avg_speech_length"],
            audit_questions=audit["audit_questions"],
            audit_findings=audit["audit_findings"],
            policy_seminars=policy["policy_seminars"],
            sns_activities=policy["sns_activities"],
            legislative_previews=policy["legislative_previews"],
        )


ß
