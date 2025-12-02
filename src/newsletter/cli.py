from __future__ import annotations

import argparse
import logging

from .config import load_config
from .pipeline import Pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Python package newsletter generator")
    parser.add_argument("command", choices=["run-once", "print-config"], help="Command to execute")
    parser.add_argument("--config", default="config.yaml", help="Path to configuration file")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(asctime)s %(levelname)s: %(message)s")

    config = load_config(args.config)
    pipeline = Pipeline(config)

    if args.command == "print-config":
        print(config)
        return 0

    if args.command == "run-once":
        pipeline.run()
        return 0

    parser.error(f"Unknown command {args.command}")
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
