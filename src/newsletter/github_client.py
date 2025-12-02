from __future__ import annotations

import logging
from typing import Dict, List, Optional

import requests

from .models import ReleaseInfo


def normalize_tag(tag: str) -> str:
    return tag.lstrip("v").strip()


def fetch_github_releases(repo: str, token: Optional[str]) -> List[ReleaseInfo]:
    url = f"https://api.github.com/repos/{repo}/releases"
    headers: Dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code == 403:
            logging.warning("GitHub API rate limited or unauthorized for %s", repo)
            return []
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        logging.error("Failed to fetch GitHub releases for %s: %s", repo, exc)
        return []

    releases: List[ReleaseInfo] = []
    for rel in data:
        try:
            tag = rel.get("tag_name") or ""
            published = rel.get("published_at")
            if not published:
                continue
            releases.append(
                ReleaseInfo(
                    package=repo.split("/")[-1],
                    version=normalize_tag(tag),
                    release_date=_parse_iso_datetime(published),
                    url=rel.get("html_url") or rel.get("url") or url,
                    source="github",
                    notes=rel.get("body") or "",
                    summary=rel.get("name") or rel.get("body") or "",
                )
            )
        except Exception as exc:  # noqa: BLE001
            logging.debug("Skipping release for %s: %s", repo, exc)
            continue
    releases.sort(key=lambda r: r.release_date)
    return releases


def _parse_iso_datetime(value: str):
    from datetime import datetime

    return datetime.fromisoformat(value.replace("Z", "+00:00"))
