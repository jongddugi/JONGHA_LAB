"""LectureSummary 결과를 파일로 저장하는 Exporter 클래스들."""

import json
from pathlib import Path

from models import LectureSummary


class JSONExporter:
    """LectureSummary를 JSON 파일로 저장한다."""

    def export(self, result: LectureSummary, path: Path) -> Path:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)
        return path


class MarkdownExporter:
    """LectureSummary를 사람이 읽기 좋은 복습 노트(Markdown)로 저장한다."""

    def export(self, result: LectureSummary, path: Path) -> Path:
        lines = self._build_lines(result)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return path

    def _build_lines(self, result: LectureSummary) -> list[str]:
        lines: list[str] = []

        lines.append(f"# {result.topic_guess}\n")

        lines.append("## 전체 요약\n")
        lines.append(f"{result.overall_summary}\n")

        lines.append("## 구간별 정리\n")
        for section in result.sections:
            lines.append(f"### [{section.start_time}] {section.topic}")
            lines.append(f"{section.summary}")
            if section.key_terms:
                lines.append(f"- 핵심 용어: {', '.join(section.key_terms)}")
            lines.append("")

        lines.append("## 핵심 포인트\n")
        for point in result.key_takeaways:
            lines.append(f"- {point}")
        lines.append("")

        lines.append("## 복습 질문\n")
        for question in result.review_questions:
            lines.append(f"- {question}")
        lines.append("")

        if result.uncertain_items:
            lines.append("## 확인이 필요한 부분\n")
            for item in result.uncertain_items:
                lines.append(f"- {item}")
            lines.append("")

        return lines