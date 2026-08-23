"""Gemini Structured Output 검증에 사용하는 Pydantic 모델."""

from pydantic import BaseModel, Field


class LectureSection(BaseModel):
    start_time: str = Field(
        description="구간 시작 시각. MM:SS 또는 HH:MM:SS 형식의 근사값"
    )
    topic: str = Field(description="해당 구간에서 다루는 핵심 주제")
    summary: str = Field(description="해당 구간 내용을 2~3문장으로 요약")
    key_terms: list[str] = Field(
        description="해당 구간에서 등장한 핵심 용어/개념 목록"
    )


class LectureSummary(BaseModel):
    topic_guess: str = Field(
        description="영상에서 다루는 주제. 제목을 확신할 수 없으면 내용 기반으로 추정한 주제명"
    )
    overall_summary: str = Field(description="강의 전체 내용을 3~5문장으로 요약")
    sections: list[LectureSection] = Field(
        description="시간 순서대로 정리한 구간별 요약 목록"
    )
    key_takeaways: list[str] = Field(
        description="이 강의에서 반드시 기억해야 할 핵심 포인트 목록"
    )
    review_questions: list[str] = Field(
        description="복습용 자가 점검 질문 목록. 강의 내용을 이해했는지 스스로 확인할 수 있는 질문"
    )
    uncertain_items: list[str] = Field(
        description="음성/자막이 불명확하거나 확정하기 어려운 부분 목록"
    )