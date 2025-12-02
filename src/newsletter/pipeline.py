from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from packaging import version

from .config import Config
from .filtering import ImportanceResult, evaluate_importance
from .github_client import fetch_github_releases
from .models import PackageSelection, ReleaseInfo
from .pypi_client import fetch_pypi_releases, fetch_top_pypi_packages
from .state import load_state, save_state, update_state
from .render import render_markdown


class Pipeline:
    def __init__(self, config: Config):
        self.config = config
        self.state = load_state(config.state_file)

    def select_packages(self) -> List[PackageSelection]:
        custom = [pkg.strip() for pkg in self.config.custom_packages if pkg.strip()]
        top: List[str] = []
        if self.config.mode in {"custom_and_top", "top_only"} and self.config.top_n > 0:
            top = fetch_top_pypi_packages(self.config.top_n)
        packages: List[str]
        if self.config.mode == "custom_only":
            packages = custom
        elif self.config.mode == "custom_and_top":
            packages = list(dict.fromkeys(custom + top))
        else:
            packages = top
        logging.info("Selected %s packages (%s custom, %s top)", len(packages), len(custom), len(top))
        return [PackageSelection(name=pkg) for pkg in packages]

    def _previous_version(self, releases: List[ReleaseInfo], target_version: str) -> Optional[str]:
        versions_sorted = sorted({r.version for r in releases}, key=version.parse)
        try:
            idx = versions_sorted.index(target_version)
        except ValueError:
            return None
        if idx == 0:
            return None
        return versions_sorted[idx - 1]

    def process_package(self, pkg: PackageSelection) -> List[ReleaseInfo]:
        releases, github_repo = fetch_pypi_releases(pkg.name)
        if github_repo:
            pkg.github_repo = github_repo
        if not releases:
            return []

        github_releases: Dict[str, ReleaseInfo] = {}
        if pkg.github_repo:
            for rel in fetch_github_releases(pkg.github_repo, self.config.github_token):
                github_releases[rel.version] = rel

        last_seen_version = self.state.get(pkg.name).last_seen_version if pkg.name in self.state else None
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.config.since_days)

        new_releases = []
        for rel in releases:
            if last_seen_version and version.parse(rel.version) <= version.parse(last_seen_version):
                continue
            if not last_seen_version and rel.release_date.replace(tzinfo=timezone.utc) < cutoff:
                continue
            gh_rel = github_releases.get(rel.version)
            if gh_rel:
                rel.notes = gh_rel.notes or rel.notes
                rel.url = gh_rel.url or rel.url
                rel.summary = gh_rel.summary or rel.summary
            new_releases.append(rel)

        important: List[ReleaseInfo] = []
        for rel in new_releases:
            prev_version = last_seen_version or self._previous_version(releases, rel.version)
            importance: ImportanceResult = evaluate_importance(rel, prev_version)
            rel.importance_score = importance.score
            rel.categories = importance.categories
            if importance.score >= self.config.min_importance_score:
                important.append(rel)

        if new_releases:
            newest_version = sorted(new_releases, key=lambda r: version.parse(r.version))[-1].version
            update_state(self.state, pkg.name, newest_version)
        return important

    def run(self) -> List[ReleaseInfo]:
        selected = self.select_packages()
        all_important: List[ReleaseInfo] = []
        for pkg in selected:
            important = self.process_package(pkg)
            logging.info("%s important releases found for %s", len(important), pkg.name)
            all_important.extend(important)

        all_important.sort(key=lambda r: r.release_date, reverse=True)

        today_str = datetime.utcnow().date().isoformat()
        newsletter_path = f"{self.config.newsletter_output_dir}/{today_str}.md"
        if all_important:
            render_markdown(all_important, newsletter_path)
            logging.info("Wrote newsletter to %s", newsletter_path)
        else:
            logging.info("No important releases to report.")

        save_state(self.config.state_file, self.state)
        return all_important
