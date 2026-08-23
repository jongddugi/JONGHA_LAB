"""공통 유틸리티 함수 모음."""

import json
import re
import urllib.parse
import urllib.request


def print_title(title: str) -> None:
    """구분선과 함께 제목을 출력한다."""
    print("=" * 100)
    print(f"{title}")
    print("=" * 100)
    print()


def get_youtube_title(video_url: str) -> str:
    """유튜브 oEmbed API로 영상의 실제 제목을 가져온다.
    실패하면(비공개 영상/네트워크 오류 등) video id를 대신 반환한다.
    """
    oembed_url = "https://www.youtube.com/oembed?" + urllib.parse.urlencode(
        {"url": video_url, "format": "json"}
    )
    try:
        with urllib.request.urlopen(oembed_url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data["title"]
    except Exception:
        parsed = urllib.parse.urlparse(video_url)
        query = urllib.parse.parse_qs(parsed.query)
        return query.get("v", ["untitled"])[0]


def sanitize_filename(name: str) -> str:
    """디렉터리/파일명으로 쓸 수 없는 문자를 제거하고 길이를 제한한다."""
    name = re.sub(r'[\\/:*?"<>|]', "", name).strip().rstrip(".")
    name = re.sub(r"\s+", " ", name)
    return name[:100] if name else "untitled"
