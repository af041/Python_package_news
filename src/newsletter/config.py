from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml


VALID_MODES = {"custom_only", "custom_and_top", "top_only"}


def _env_default(key: str, default: str) -> str:
    return os.getenv(key, default)


@dataclass
class Config:
    mode: str = "custom_only"
    top_n: int = 0
    custom_packages: List[str] = field(default_factory=list)
    newsletter_output_dir: str = "newsletters"
    state_file: str = "state.json"
    since_days: int = 30
    min_importance_score: float = 3.0
    github_token_env: str = "GITHUB_TOKEN"

    @property
    def github_token(self) -> str | None:
        token = os.getenv(self.github_token_env)
        if token:
            return token.strip()
        return None


def load_config(path: str | Path) -> Config:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f) or {}
        except yaml.YAMLError as exc:
            raise ValueError(f"Failed to parse config: {exc}") from exc

    config = Config(**{**Config().__dict__, **data})  # type: ignore[arg-type]

    if config.mode not in VALID_MODES:
        raise ValueError(f"Invalid mode '{config.mode}'. Valid options: {', '.join(sorted(VALID_MODES))}")

    Path(config.newsletter_output_dir).mkdir(parents=True, exist_ok=True)
    Path(config.state_file).parent.mkdir(parents=True, exist_ok=True)

    logging.debug("Loaded configuration: %s", config)
    return config
