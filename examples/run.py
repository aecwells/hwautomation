#!/usr/bin/env python3
"""
Unified example runner. Lists available examples and runs one by name.
Usage:
  python -m examples.run --list
  python -m examples.run firmware_manager_smoke -- --target-ip 192.168.1.100
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


EXCLUDE = {"run.py", "_common.py", "README.md", "__init__.py"}


def discover() -> dict[str, Path]:
    root = Path(__file__).resolve().parent
    items: dict[str, Path] = {}
    for p in sorted(root.glob("*.py")):
        if p.name in EXCLUDE:
            continue
        items[p.stem] = p
    return items


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser(description="Run HWAutomation examples")
    parser.add_argument("example", nargs="?", help="Example name (without .py)")
    parser.add_argument("--list", action="store_true", help="List available examples")
    parser.add_argument("--", dest="dashdash", nargs=argparse.REMAINDER, help="Args after -- are passed to the example")
    args = parser.parse_args(argv)

    items = discover()
    if args.list or not args.example:
        print("Available examples:")
        for name in items:
            print(f"  - {name}")
        if not args.example:
            return 0

    if args.example not in items:
        print(f"Unknown example: {args.example}")
        return 1

    cmd = [sys.executable, str(items[args.example])]
    if args.dashdash:
        # Drop the leading '--'
        cmd.extend(args.dashdash[1:] if args.dashdash and args.dashdash[0] == "--" else args.dashdash)
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
