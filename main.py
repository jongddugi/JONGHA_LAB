"""엔트리 포인트."""

from config import Settings
from exporters import JSONExporter, MarkdownExporter
from gemini_client import GeminiVideoClient
from summarizer import LectureSummarizer
from utils import print_title


def main() -> None:
    settings = Settings.load()

    client = GeminiVideoClient(
        api_key=settings.api_key,
        model_name=settings.model_name,
    )
    summarizer = LectureSummarizer(client)

    print_title("유튜브 강의 분석 시작")
    result = summarizer.summarize(settings.url_path)
    print_title("Structured Output 검증 완료")
    print(f"주제 : {result.topic_guess}")
    print(f"구간 수 : {len(result.sections)}")

    json_path = settings.output_dir / "lecture_summary.json"
    md_path = settings.output_dir / "lecture_summary.md"

    JSONExporter().export(result, json_path)
    MarkdownExporter().export(result, md_path)

    print_title("저장 완료")
    print(f"JSON              : {json_path}")
    print(f"Markdown 복습 노트 : {md_path}")


if __name__ == "__main__":
    main()