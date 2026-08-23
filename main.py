"""엔트리 포인트."""

import sys

from config import Settings, record_video_entry
from exporters import JSONExporter, MarkdownExporter
from gemini_client import GeminiVideoClient
from summarizer import LectureSummarizer
from utils import get_youtube_title, print_title, sanitize_filename


def main() -> None:
    cli_url = sys.argv[1] if len(sys.argv) > 1 else None
    settings = Settings.load(cli_url=cli_url)

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

    video_title = get_youtube_title(settings.url_path)
    video_output_dir = settings.output_dir / sanitize_filename(video_title)
    video_output_dir.mkdir(parents=True, exist_ok=True)

    json_path = video_output_dir / "lecture_summary.json"
    md_path = video_output_dir / "lecture_summary.md"

    JSONExporter().export(result, json_path)
    MarkdownExporter().export(result, md_path)

    record_video_entry(video_title, settings.url_path)

    print_title("저장 완료")
    print(f"JSON              : {json_path}")
    print(f"Markdown 복습 노트 : {md_path}")


if __name__ == "__main__":
    main()
