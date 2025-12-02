from __future__ import annotations

import textwrap
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from .models import ReleaseInfo


CATEGORY_HEADINGS = {
    "breaking_major": "Breaking & Major Changes",
    "deprecations": "Deprecations",
    "security": "Security & Critical Fixes",
    "other": "Other Notable Changes",
}


def summarize_notes(notes: str, max_lines: int = 5) -> List[str]:
    if not notes:
        return ["No detailed notes provided."]
    lines = [line.strip("- ") for line in notes.splitlines() if line.strip()]
    if not lines:
        return [notes[:120] + "..." if len(notes) > 120 else notes]
    return lines[:max_lines]


def render_markdown(releases: List[ReleaseInfo], output_path: str) -> None:
    today = datetime.utcnow().date().isoformat()
    grouped: Dict[str, List[ReleaseInfo]] = defaultdict(list)
    for rel in releases:
        category = (rel.categories or ["other"])[0]
        grouped[category].append(rel)

    content = [f"# Python Package Release Highlights – {today}\n"]
    content.append(
        textwrap.dedent(
            """
            Automated summary of notable Python package releases. This digest focuses on major updates, breaking changes, deprecations,
            and security fixes detected since the last run.
            """
        ).strip()
    )
    content.append("")

    for key in ["breaking_major", "deprecations", "security", "other"]:
        section = grouped.get(key, [])
        if not section:
            continue
        content.append(f"## {CATEGORY_HEADINGS.get(key, key.title())}\n")
        for rel in section:
            content.append(f"### {rel.package} {rel.version} ({rel.release_date.date().isoformat()})")
            bullets = summarize_notes(rel.notes)
            for bullet in bullets:
                content.append(f"- {bullet}")
            content.append("")
            content.append(f"[Release notes]({rel.url})")
            content.append("")

    Path(output_path).write_text("\n".join(content), encoding="utf-8")
