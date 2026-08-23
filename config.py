"""환경설정 로드를 담당하는 모듈."""

import os
import re
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
    url_path: str
    output_dir: Path

    @classmethod
    def load(cls, cli_url: str | None = None) -> "Settings":
        """.env 파일에서 API 키를 읽고, 유튜브 URL은 cli_url(커맨드라인 인자)이
        있으면 그걸 쓰고, 없으면 VIDEO_URL.txt + VIDEO_KEY 조합으로 읽는다.
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

        if cli_url:
            url_path = _normalize_youtube_url(cli_url)
        else:
            if not URL_FILE.exists():
                raise FileNotFoundError(
                    f"{URL_FILE.name} 파일을 찾을 수 없습니다. "
                    "이 파일을 만들고 '제목=URL' 형식으로 한 줄 이상 적거나, "
                    "python main.py <유튜브URL> 형태로 URL을 직접 넘기세요."
                )

            entries = _parse_video_url_file(URL_FILE.read_text(encoding="utf-8"))
            if not entries:
                raise ValueError(
                    f"{URL_FILE.name} 파일이 비어 있습니다. "
                    "'제목=URL' 형식으로 한 줄 이상 적어두세요."
                )

            video_key = os.getenv("VIDEO_KEY")
            if video_key:
                if video_key not in entries:
                    available = ", ".join(entries.keys())
                    raise ValueError(
                        f"VIDEO_KEY='{video_key}'는 {URL_FILE.name}에 없는 제목입니다. "
                        f"사용 가능한 제목: {available}"
                    )
                selected_url = entries[video_key]
            elif len(entries) == 1:
                selected_url = next(iter(entries.values()))
            else:
                available = ", ".join(entries.keys())
                raise ValueError(
                    f"{URL_FILE.name}에 항목이 여러 개 있습니다. "
                    f".env에 VIDEO_KEY=<제목> 을 지정하거나 "
                    f"python main.py <유튜브URL> 로 직접 넘기세요. 사용 가능한 제목: {available}"
                )
            url_path = _normalize_youtube_url(selected_url)

        output_dir = BASE_DIR / "output"
        output_dir.mkdir(exist_ok=True)

        return cls(
            api_key=api_key,
            model_name=model_name,
            url_path=url_path,
            output_dir=output_dir,
        )


def record_video_entry(title: str, url: str) -> None:
    """분석에 성공한 영상을 VIDEO_URL.txt에 '제목 = URL' 형식으로 기록한다.

    지금까지 분석한 영상 목록을 누적해두는 용도이며,
    이미 같은 URL이 기록되어 있으면 중복 추가하지 않는다.
    """
    existing_text = URL_FILE.read_text(encoding="utf-8") if URL_FILE.exists() else ""
    existing_entries = _parse_video_url_file(existing_text)

    if url in existing_entries.values():
        return

    key = title.strip() or "untitled"
    base_key = key
    suffix = 2
    while key in existing_entries:
        key = f"{base_key} ({suffix})"
        suffix += 1

    with URL_FILE.open("a", encoding="utf-8") as f:
        if existing_text and not existing_text.endswith("\n"):
            f.write("\n")
        f.write(f"{key} = {url}\n")