"""Gemini API 호출을 감싸는 얇은 클라이언트 래퍼."""

from google import genai


class GeminiVideoClient:
    """유튜브 영상을 Gemini에 넘기고 Structured Output을 요청하는 역할만 담당한다."""

    def __init__(self, api_key: str, model_name: str):
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name

    def request_structured_video_analysis(
        self,
        youtube_url: str,
        prompt: str,
        json_schema: dict,
    ):
        """유튜브 URL + 프롬프트 + JSON 스키마로 Structured Output 요청을 보낸다.

        반환값은 interaction 객체이며, 실제 텍스트는 .output_text 로 꺼낸다.
        영상은 다운로드/업로드하지 않고 URL만 전달한다 (공개 영상만 가능).
        """
        return self._client.interactions.create(
            model=self._model_name,
            input=[
                {"type": "video", "uri": youtube_url},
                {"type": "text", "text": prompt},
            ],
            generation_config={"thinking_level": "low"},
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": json_schema,
            },
        )