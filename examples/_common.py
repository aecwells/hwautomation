"""
Shared utilities for running examples consistently.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path


def add_src_to_path() -> None:
    """Ensure the project's src/ is importable for examples."""
    repo_root = Path(__file__).resolve().parents[1]
    src_path = repo_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


def default_logger(level: int | str = logging.INFO) -> logging.Logger:
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger("examples")


def common_arg_parser(description: str | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description or "HWAutomation example")
    parser.add_argument("--device-type", default=os.getenv("DEVICE_TYPE", "a1.c5.large"))
    parser.add_argument("--target-ip", default=os.getenv("TARGET_IP"))
    parser.add_argument("--username", default=os.getenv("IPMI_USER", "admin"))
    parser.add_argument("--password", default=os.getenv("IPMI_PASS", "password"))
    parser.add_argument("--dry-run", action="store_true", default=True, help="Do not make changes")
    parser.add_argument("--no-dry-run", dest="dry_run", action="store_false", help="Allow changes")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    return parser
