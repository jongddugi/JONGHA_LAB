"""환경설정 로드를 담당하는 모듈."""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
URL_FILE = BASE_DIR / "VIDEO_URL.txt"


def normalize_youtube_url(url: str) -> str:
    """다양한 형태의 유튜브 URL을 Gemini API가 요구하는
    'https://www.youtube.com/watch?v=<id>' 형식으로 통일한다.

    Gemini의 video URI 파서는 이 형식만 "YouTube URI"로 인식하고,
    youtu.be 단축 링크나 shorts 링크는 거부하기 때문이다.
    유튜브 도메인이 아닌 URL(File API URL, gs:// URI, 일반 mp4 HTTPS 링크 등)은
    건드리지 않고 그대로 반환한다.
    """
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if host in ("youtu.be", "www.youtu.be"):
        video_id = parsed.path.lstrip("/")
    elif host.endswith("youtube.com"):
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [None])[0]
        elif parsed.path.startswith(("/shorts/", "/embed/", "/live/")):
            video_id = parsed.path.split("/")[2] if len(parsed.path.split("/")) > 2 else None
        else:
            video_id = None
    else:
        return url

    if not video_id:
        raise ValueError(
            f"유튜브 URL에서 video id를 추출하지 못했습니다: {url}\n"
            "입력한 URL이 올바른 유튜브 링크인지 확인하세요."
        )

    return f"https://www.youtube.com/watch?v={video_id}"


def extract_youtube_video_id(url: str) -> str | None:
    """normalize_youtube_url()을 거친 URL에서 video id만 뽑아낸다.

    유튜브 형식이 아닌 URL(File API/gs:// 등)이면 None을 반환한다.
    """
    parsed = urlparse(url)
    if not parsed.netloc.endswith("youtube.com"):
        return None
    return parse_qs(parsed.query).get("v", [None])[0]


def _parse_video_url_file(text: str) -> dict[str, str]:
    """'제목=URL' 형식의 줄들을 파싱해 {제목: URL} 딕셔너리로 만든다.

    빈 줄과 '#'으로 시작하는 주석 줄은 무시한다.
    제목 자체에 '='가 들어갈 수 있으므로(예: "1+1=1임을 증명하는 영상"),
    첫 '='가 아니라 'http(s)://'가 시작되는 위치를 기준으로 제목/URL을 나눈다.
    """
    entries: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.search(r"https?://\S+", line)
        if not match:
            raise ValueError(
                f"{URL_FILE.name}의 다음 줄에서 URL을 찾을 수 없습니다: {line}"
            )
        url = match.group(0)
        key = line[: match.start()].strip().rstrip("=").strip()
        if not key:
            raise ValueError(
                f"{URL_FILE.name}의 다음 줄에 제목이 없습니다: {line}"
            )
        entries[key] = url
    return entries


@dataclass(frozen=True)
class Settings:
    """스크립트 실행에 필요한 설정값을 한 곳에 모아둔 객체.

    frozen=True 로 만들어서, 한 번 로드한 뒤에는
    실수로 다른 값으로 덮어쓰지 못하게 막아둔다.
    """

    api_key: str
    model_name: str
    output_dir: Path

    @classmethod
    def load(cls) -> "Settings":
        """.env 파일에서 API 키와 모델명을 읽어 Settings 객체로 만든다.

        분석할 유튜브 URL은 실행 시 CLI에서 직접 입력받으므로 여기서 다루지 않는다.
        """
        env_path = BASE_DIR / ".env"
        load_dotenv(dotenv_path=env_path)

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다. "
                ".env 파일에 GEMINI_API_KEY=... 형태로 추가하세요."
            )

        model_name = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")

        output_dir = BASE_DIR / "output"
        output_dir.mkdir(exist_ok=True)

        return cls(
            api_key=api_key,
            model_name=model_name,
            output_dir=output_dir,
        )


def record_video_entry(title: str, url: str, date_dir: str, output_path: Path) -> None:
    """CLI로 입력받아 분석에 성공한 영상을 VIDEO_URL.txt에 기록한다.

    형식: '제목 = URL | 날짜 | 저장 경로'
    지금까지 분석한 영상의 날짜/저장 위치까지 한 파일에서 찾아볼 수 있는
    카탈로그 용도(기록 전용, 조회/선택에는 쓰지 않음)이며,
    이미 같은 URL이 기록되어 있으면 중복 추가하지 않는다.
    """
    existing_text = URL_FILE.read_text(encoding="utf-8") if URL_FILE.exists() else ""
    existing_entries = _parse_video_url_file(existing_text)

    existing_normalized_urls = {normalize_youtube_url(u) for u in existing_entries.values()}
    if url in existing_normalized_urls:
        return

    key = title.strip() or "untitled"
    base_key = key
    suffix = 2
    while key in existing_entries:
        key = f"{base_key} ({suffix})"
        suffix += 1

    try:
        relative_path = output_path.relative_to(BASE_DIR)
    except ValueError:
        relative_path = output_path

    with URL_FILE.open("a", encoding="utf-8") as f:
        if existing_text and not existing_text.endswith("\n"):
            f.write("\n")
        f.write(f"{key} = {url} | {date_dir} | {relative_path}\n")