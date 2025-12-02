from __future__ import annotations

import logging
import re
from typing import Dict, List, Tuple

from packaging import version

from .models import ReleaseInfo

BREAKING_KEYWORDS = ["breaking", "backwards incompatible", "incompatible", "removed", "changed default"]
DEPRECATION_KEYWORDS = ["deprecate", "deprecated", "will be removed", "scheduled for removal"]
SECURITY_KEYWORDS = ["security", "cve-", "vulnerability", "exploit", "xss", "sql injection"]
PERFORMANCE_KEYWORDS = ["performance", "optimization", "faster"]


class ImportanceResult:
    def __init__(self, score: float, categories: List[str]):
        self.score = score
        self.categories = categories

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"ImportanceResult(score={self.score}, categories={self.categories})"


def _version_bump_score(current: str, previous: str | None) -> float:
    if not previous:
        return 2.0  # first observation, moderate importance
    try:
        cur_v = version.parse(current)
        prev_v = version.parse(previous)
    except Exception:  # noqa: BLE001
        return 0.0
    if cur_v.major != prev_v.major:
        return 5.0
    if cur_v.minor != prev_v.minor:
        return 3.0
    if cur_v.micro != prev_v.micro:
        return 1.0
    return 0.5


def _keyword_score(text: str, keywords: List[str], points: float) -> Tuple[float, bool]:
    text_lower = text.lower()
    found = any(word in text_lower for word in keywords)
    return (points if found else 0.0, found)


def evaluate_importance(release: ReleaseInfo, previous_version: str | None) -> ImportanceResult:
    score = _version_bump_score(release.version, previous_version)
    categories: List[str] = []

    kw_scores: Dict[str, Tuple[float, bool]] = {
        "breaking": _keyword_score(release.notes, BREAKING_KEYWORDS, 5.0),
        "deprecation": _keyword_score(release.notes, DEPRECATION_KEYWORDS, 3.0),
        "security": _keyword_score(release.notes, SECURITY_KEYWORDS, 6.0),
        "performance": _keyword_score(release.notes, PERFORMANCE_KEYWORDS, 1.5),
    }

    for name, (points, matched) in kw_scores.items():
        score += points
        if matched:
            categories.append(name)

    if "breaking" in categories or score >= 5:
        categories.append("breaking_major")
    if "deprecation" in categories:
        categories.append("deprecations")
    if "security" in categories:
        categories.append("security")
    if not categories:
        categories.append("other")

    logging.debug("Importance for %s %s -> %s", release.package, release.version, score)
    return ImportanceResult(score=score, categories=categories)
