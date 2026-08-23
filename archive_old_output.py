"""오래된 output/<yy.mm.dd>/ 결과 폴더를 zip으로 묶어 archive/로 옮기는 정리 스크립트.

main.py 실행 시 자동으로 돌지 않으며, 필요할 때 직접 실행한다:
    python3 archive_old_output.py                 # 30일 지난 폴더 정리
    python3 archive_old_output.py --days 60        # 60일 기준으로 정리
    python3 archive_old_output.py --dry-run        # 실제로 옮기지 않고 대상만 확인
"""

import argparse
import re
import shutil
import zipfile
from datetime import date, datetime
from pathlib import Path

from config import BASE_DIR

OUTPUT_DIR = BASE_DIR / "output"
ARCHIVE_DIR = OUTPUT_DIR / "archive"
DATE_DIR_PATTERN = re.compile(r"^\d{2}\.\d{2}\.\d{2}$")


def _find_old_date_dirs(days: int) -> list[Path]:
    if not OUTPUT_DIR.exists():
        return []

    cutoff = date.today()
    old_dirs = []
    for entry in OUTPUT_DIR.iterdir():
        if not entry.is_dir() or not DATE_DIR_PATTERN.match(entry.name):
            continue
        try:
            folder_date = datetime.strptime(entry.name, "%y.%m.%d").date()
        except ValueError:
            continue
        if (cutoff - folder_date).days > days:
            old_dirs.append(entry)
    return sorted(old_dirs)


def _zip_dir(src_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in src_dir.rglob("*"):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(src_dir.parent))


def archive_old_outputs(days: int, dry_run: bool) -> None:
    old_dirs = _find_old_date_dirs(days)

    if not old_dirs:
        print(f"{days}일보다 오래된 output 폴더가 없습니다.")
        return

    if not dry_run:
        ARCHIVE_DIR.mkdir(exist_ok=True)

    for folder in old_dirs:
        zip_path = ARCHIVE_DIR / f"{folder.name}.zip"
        if dry_run:
            print(f"[dry-run] {folder} -> {zip_path}")
            continue

        _zip_dir(folder, zip_path)
        shutil.rmtree(folder)
        print(f"압축 완료: {folder} -> {zip_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--days", type=int, default=30, help="이 일수보다 오래된 폴더를 정리 (기본 30일)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="실제로 옮기지 않고 대상 폴더만 출력"
    )
    args = parser.parse_args()

    archive_old_outputs(days=args.days, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
