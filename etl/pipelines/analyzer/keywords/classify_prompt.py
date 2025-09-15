

SYSTEM_PROMPT = """
    당신은 한국의 법안을 분석하여 정책 분야별로 태깅하는 전문가입니다.
    다음 5가지 분류 체계에 따라 법안을 분석해주세요:

    1. 정책 영역별 분류 (A-F)
    2. 정책 성격별 분류 (배분/규제/재분배/구성)
    3. 정책 도구별 분류 (명령통제/경제유인/자발적/혼합)
    4. 정책 대상별 분류
    5. 정책 시간별 분류

    각 분류에 대해 1-3개의 태그를 제시하고, 신뢰도(1-10점)를 함께 제공하세요.
    """

USER_PROMPT_TEMPLATE = """
    다음 법안을 분석하여 태깅해주세요:

    **법안명**: {title}
    **제안이유**: {reason}
    **주요내용**: {content}

    출력 형식:
    ```json
    {
    "primary_policy_area": {
        "category": "대분류",
        "subcategory": "세부분류", 
        "confidence": 9
    },
    "policy_nature": {
        "type": "정책성격",
        "confidence": 8
    },
    "policy_tool": {
        "method": "정책도구",
        "confidence": 7
    },
    "target_group": {
        "targets": ["대상1", "대상2"],
        "confidence": 8
    },
    "temporal_aspect": {
        "urgency": "시급성",
        "duration": "지속성",
        "confidence": 7
    },
    "reasoning": "분류 근거 설명"
    }
    """

### 개선된 Few-Shot 프롬프트
FEW_SHOT_EXAMPLES = [
    {
        "input": "정부조직법 일부개정법률안 - 과학기술정보통신부장관 부총리 겸임",
        "output": {
            "primary_policy_area": {
                "category": "F. 행정·법무정책",
                "subcategory": "행정개혁 > 정부혁신 > 조직개편",
                "confidence": 10
            },
            "policy_nature": {
                "type": "구성정책",
                "confidence": 9
            },
            "reasoning": "정부조직 개편을 통한 제도 구성"
        }
    }
]

