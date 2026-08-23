"""유튜브 강의 영상을 분석해 검증까지 마친 LectureSummary로 바꿔주는 오케스트레이션 클래스."""

from pydantic import ValidationError

from gemini_client import GeminiVideoClient
from models import LectureSummary


LECTURE_PROMPT = """
첨부된 유튜브 강의 영상을 처음부터 끝까지 시청/청취하고
개인 복습에 사용할 학습 노트를 구조화된 형태로 작성하라.

영상 특성 관련 지침:
- 이 영상은 유튜브 강의이므로, 화면에 나오는 슬라이드/코드/판서/자막 등
  시각 자료의 내용도 발화 내용과 함께 반영한다.
- 영상 초반의 채널 소개, 구독/좋아요 요청, 스폰서 광고, 영상 후반의
  마무리 인사/다음 영상 예고 등은 강의 본론이 아니므로 sections에서 제외한다.
- 유튜브 챕터(영상 하단 타임라인에 구간 제목이 표시되는 기능)가 이미
  적용된 영상이라면, 그 챕터 구분을 최대한 참고해서 sections를 나눈다.
  챕터가 없다면 주제 전환이 일어나는 지점을 기준으로 자연스럽게 나눈다.

원칙:
- 영상에서 실제로 확인되는 내용만 사용한다.
- 확실하지 않은 용어나 발화는 임의로 지어내지 말고 uncertain_items에 기록한다.
- 시간 흐름에 따라 sections를 구성하되, 자연스러운 주제 전환 단위로 나눈다
  (초 단위로 억지로 잘게 쪼개지 않는다).
- key_takeaways는 시험/복습에 나올 법한 핵심만 간결하게 정리한다.
- review_questions는 스스로 이해도를 점검할 수 있는 질문 형태로 작성한다.
- Markdown 설명을 추가하지 말고 Structured Output만 반환한다.
"""


class LectureSummarizer:
    """GeminiVideoClient를 이용해 유튜브 영상을 LectureSummary로 변환한다."""

    def __init__(self, client: GeminiVideoClient, max_retries: int = 1):
        self._client = client
        self._max_retries = max_retries

    def summarize(self, youtube_url: str) -> LectureSummary:
        """유튜브 URL 하나를 받아 검증된 LectureSummary 객체를 반환한다.

        Gemini가 스키마에 어긋난 JSON을 만들면 ValidationError가 나는데,
        이 경우 max_retries 횟수만큼 다시 요청한다.
        그래도 계속 실패하면 RuntimeError를 발생시킨다.
        """
        schema = LectureSummary.model_json_schema()

        last_error = None
        total_attempts = self._max_retries + 1  # 최초 1회 + 재시도

        for attempt in range(1, total_attempts + 1):
            interaction = self._client.request_structured_video_analysis(
                youtube_url=youtube_url,
                prompt=LECTURE_PROMPT,
                json_schema=schema,
            )
            raw_json = interaction.output_text

            try:
                return LectureSummary.model_validate_json(raw_json)
            except ValidationError as error:
                last_error = error
                print(f"[{attempt}/{total_attempts}번째 시도] JSON 검증 실패, 재요청합니다.")

        raise RuntimeError("Structured Output 검증에 계속 실패했습니다.") from last_error