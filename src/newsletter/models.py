from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class PackageSelection:
    name: str
    github_repo: Optional[str] = None


@dataclass
class ReleaseInfo:
    package: str
    version: str
    release_date: datetime
    url: str
    source: str
    notes: str = ""
    summary: str = ""
    importance_score: float = 0.0
    categories: List[str] | None = None


@dataclass
class StateEntry:
    last_seen_version: str
    last_checked_at: datetime
