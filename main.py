"""엔트리 포인트."""

import json
from datetime import date, datetime

from config import (
    Settings,
    extract_youtube_video_id,
    normalize_youtube_url,
    record_video_entry,
)
from exporters import JSONExporter, MarkdownExporter
from gemini_client import GeminiVideoClient
from summarizer import LectureSummarizer
from utils import get_youtube_title, print_title, sanitize_filename


def _prompt_for_url() -> str:
    while True:
        raw_url = input("URL을 넣어주세요 : ex) https://www.youtube.com/watch?v=영상ID\n> ").strip()
        if raw_url:
            return raw_url
        print("URL이 비어 있습니다. 다시 입력해주세요.\n")


def main() -> None:
    settings = Settings.load()
    url = normalize_youtube_url(_prompt_for_url())

    client = GeminiVideoClient(
        api_key=settings.api_key,
        model_name=settings.model_name,
    )
    summarizer = LectureSummarizer(client)

    print_title("유튜브 강의 분석 시작")
    result = summarizer.summarize(url)
    print_title("Structured Output 검증 완료")
    print(f"주제 : {result.topic_guess}")
    print(f"구간 수 : {len(result.sections)}")

    video_title = get_youtube_title(url)
    video_id = extract_youtube_video_id(url)

    folder_name = sanitize_filename(video_title)
    if video_id:
        folder_name = f"{folder_name}_{video_id}"

    date_dir = date.today().strftime("%y.%m.%d")
    video_output_dir = settings.output_dir / date_dir / folder_name
    video_output_dir.mkdir(parents=True, exist_ok=True)

    json_path = video_output_dir / "lecture_summary.json"
    md_path = video_output_dir / "lecture_summary.md"
    meta_path = video_output_dir / "meta.json"

    JSONExporter().export(result, json_path)
    MarkdownExporter().export(result, md_path)

    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "title": video_title,
                "url": url,
                "video_id": video_id,
                "analyzed_at": datetime.now().isoformat(timespec="seconds"),
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    record_video_entry(video_title, url, date_dir, video_output_dir)

    print_title("저장 완료")
    print(f"JSON              : {json_path}")
    print(f"Markdown 복습 노트 : {md_path}")
    print(f"메타데이터         : {meta_path}")


if __name__ == "__main__":
    main()
