"""환경설정 로드를 담당하는 모듈."""

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
URL_FILE = BASE_DIR / "VIDEO_URL.txt"


def _normalize_youtube_url(url: str) -> str:
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
            "VIDEO_URL.txt에 올바른 유튜브 링크가 들어있는지 확인하세요."
        )

    return f"https://www.youtube.com/watch?v={video_id}"


@dataclass(frozen=True)
class Settings:
    """스크립트 실행에 필요한 설정값을 한 곳에 모아둔 객체.

    frozen=True 로 만들어서, 한 번 로드한 뒤에는
    실수로 다른 값으로 덮어쓰지 못하게 막아둔다.
    """

    api_key: str
    model_name: str
    url_path: str
    output_dir: Path

    @classmethod
    def load(cls) -> "Settings":
        """.env 파일에서 API 키를, video_url.txt 파일에서 유튜브 URL을 읽어
        Settings 객체로 만든다.
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

        if not URL_FILE.exists():
            raise FileNotFoundError(
                f"{URL_FILE.name} 파일을 찾을 수 없습니다. "
                "이 파일을 만들고 요약할 유튜브 영상 URL을 한 줄로 적어두세요."
            )

        url_path = URL_FILE.read_text(encoding="utf-8").strip()
        if not url_path:
            raise ValueError(
                f"{URL_FILE.name} 파일이 비어 있습니다. "
                "요약할 유튜브 영상 URL을 한 줄로 적어두세요."
            )

        url_path = _normalize_youtube_url(url_path)

        output_dir = BASE_DIR / "output"
        output_dir.mkdir(exist_ok=True)

        return cls(
            api_key=api_key,
            model_name=model_name,
            url_path=url_path,
            output_dir=output_dir,
        )