from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests

from .models import ReleaseInfo

TOP_PYPI_URL = "https://hugovk.github.io/top-pypi-packages/top-pypi-packages-30-days.min.json"


def fetch_top_pypi_packages(top_n: int) -> List[str]:
    try:
        resp = requests.get(TOP_PYPI_URL, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        rows = data.get("rows", [])
        packages = [row.get("project") for row in rows if row.get("project")]
        return packages[:top_n]
    except Exception as exc:  # noqa: BLE001
        logging.error("Failed to fetch top PyPI packages: %s", exc)
        return []


def _parse_release_date(release_data: List[Dict]) -> Optional[datetime]:
    if not release_data:
        return None
    dates = []
    for item in release_data:
        ts = item.get("upload_time_iso_8601") or item.get("upload_time")
        if ts:
            try:
                dates.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
            except ValueError:
                continue
    if not dates:
        return None
    return max(dates)


def find_github_repo(info: Dict) -> Optional[str]:
    def extract(url: str) -> Optional[str]:
        if "github.com" not in url:
            return None
        parts = url.split("github.com/")
        if len(parts) < 2:
            return None
        repo_path = parts[1].strip("/")
        repo_parts = repo_path.split("/")
        if len(repo_parts) >= 2:
            return f"{repo_parts[0]}/{repo_parts[1]}"
        return None

    project_urls = info.get("project_urls") or {}
    candidates = list(project_urls.values()) if isinstance(project_urls, dict) else []
    home_page = info.get("home_page")
    if home_page:
        candidates.append(home_page)
    for url in candidates:
        if not isinstance(url, str):
            continue
        repo = extract(url)
        if repo:
            return repo
    return None


def fetch_pypi_releases(package: str) -> Tuple[List[ReleaseInfo], Optional[str]]:
    url = f"https://pypi.org/pypi/{package}/json"
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        logging.error("Failed to fetch PyPI data for %s: %s", package, exc)
        return [], None

    info = data.get("info", {})
    releases = data.get("releases", {})
    github_repo = find_github_repo(info)
    results: List[ReleaseInfo] = []
    for version, files in releases.items():
        release_date = _parse_release_date(files)
        if not release_date:
            continue
        results.append(
            ReleaseInfo(
                package=package,
                version=version,
                release_date=release_date,
                url=f"https://pypi.org/project/{package}/{version}/",
                source="pypi",
                summary=info.get("summary", ""),
            )
        )
    results.sort(key=lambda r: r.release_date)
    return results, github_repo
