#!/usr/bin/env python3
"""
Auto-generate changelog from git commits using conventional commit format.

This script analyzes git commit messages and generates a CHANGELOG.md file
following the conventional commits specification.
"""

import argparse
import datetime
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


class ChangelogGenerator:
    """Generate changelog from git commits."""

    # Conventional commit types and their display names
    COMMIT_TYPES = {
        "feat": {"title": "🚀 Features", "order": 1},
        "fix": {"title": "🐛 Bug Fixes", "order": 2},
        "perf": {"title": "⚡ Performance Improvements", "order": 3},
        "refactor": {"title": "♻️ Code Refactoring", "order": 4},
        "docs": {"title": "📚 Documentation", "order": 5},
        "test": {"title": "🧪 Tests", "order": 6},
        "build": {"title": "🏗️ Build System", "order": 7},
        "ci": {"title": "👷 CI/CD", "order": 8},
        "chore": {"title": "🔧 Chores", "order": 9},
        "style": {"title": "💄 Styling", "order": 10},
    }

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)

    def get_git_commits(
        self, since_tag: str = None, until_tag: str = "HEAD"
    ) -> List[Dict]:
        """Get git commits with metadata."""
        cmd = ["git", "log", "--pretty=format:%H|%s|%an|%ad|%b", "--date=short"]

        if since_tag:
            cmd.append(f"{since_tag}..{until_tag}")
        else:
            cmd.append(until_tag)

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.repo_path
            )
            if result.returncode != 0:
                raise RuntimeError(f"Git command failed: {result.stderr}")

            commits = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("|", 4)
                if len(parts) >= 4:
                    commits.append(
                        {
                            "hash": parts[0][:8],
                            "subject": parts[1],
                            "author": parts[2],
                            "date": parts[3],
                            "body": parts[4] if len(parts) > 4 else "",
                        }
                    )
            return commits
        except Exception as e:
            print(f"Error getting git commits: {e}")
            return []

    def parse_conventional_commit(self, commit: Dict) -> Dict:
        """Parse conventional commit format."""
        subject = commit["subject"]

        # Pattern for conventional commits: type(scope): description
        pattern = r"^(\w+)(?:\(([^)]+)\))?(!)?:\s*(.+)$"
        match = re.match(pattern, subject)

        if match:
            commit_type, scope, breaking, description = match.groups()
            return {
                **commit,
                "type": commit_type.lower(),
                "scope": scope,
                "breaking": bool(breaking),
                "description": description.strip(),
                "is_conventional": True,
            }
        else:
            # Non-conventional commit
            return {
                **commit,
                "type": "other",
                "scope": None,
                "breaking": "BREAKING CHANGE" in commit.get("body", ""),
                "description": subject,
                "is_conventional": False,
            }

    def get_latest_tag(self) -> str:
        """Get the latest git tag."""
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def get_all_tags(self) -> List[str]:
        """Get all git tags sorted by version."""
        try:
            result = subprocess.run(
                ["git", "tag", "--sort=-version:refname"],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
            )
            if result.returncode == 0:
                return [tag for tag in result.stdout.strip().split("\n") if tag]
        except Exception:
            pass
        return []

    def generate_section(self, commits: List[Dict], version: str = None) -> str:
        """Generate changelog section for commits."""
        if not commits:
            return ""

        # Group commits by type
        grouped = defaultdict(list)
        breaking_changes = []

        for commit in commits:
            parsed = self.parse_conventional_commit(commit)

            if parsed["breaking"]:
                breaking_changes.append(parsed)

            commit_type = parsed["type"]
            if commit_type in self.COMMIT_TYPES:
                grouped[commit_type].append(parsed)
            elif parsed["is_conventional"]:
                grouped["other"].append(parsed)
            else:
                grouped["other"].append(parsed)

        # Generate section
        lines = []

        # Version header
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        if version:
            lines.append(f"## [{version}] - {date_str}")
        else:
            lines.append(f"## [Unreleased] - {date_str}")
        lines.append("")

        # Breaking changes first
        if breaking_changes:
            lines.append("### ⚠️ BREAKING CHANGES")
            lines.append("")
            for commit in breaking_changes:
                scope_text = f"**{commit['scope']}**: " if commit["scope"] else ""
                lines.append(
                    f"- {scope_text}{commit['description']} ([{commit['hash']}])"
                )
            lines.append("")

        # Regular changes by type
        for commit_type in sorted(
            grouped.keys(),
            key=lambda x: self.COMMIT_TYPES.get(x, {"order": 99})["order"],
        ):
            commits_of_type = grouped[commit_type]
            if not commits_of_type:
                continue

            type_config = self.COMMIT_TYPES.get(
                commit_type, {"title": f"📝 {commit_type.title()}"}
            )
            lines.append(f"### {type_config['title']}")
            lines.append("")

            for commit in commits_of_type:
                scope_text = f"**{commit['scope']}**: " if commit["scope"] else ""
                lines.append(
                    f"- {scope_text}{commit['description']} ([{commit['hash']}])"
                )
            lines.append("")

        return "\n".join(lines)

    def generate_release_notes(self, version: str, since_tag: str = None) -> str:
        """Generate release notes for a specific version."""
        commits = self.get_git_commits(since_tag=since_tag, until_tag=version)
        if not commits:
            return f"## {version}\n\nNo changes recorded for this release."

        section = self.generate_section(commits, version=version)

        # Add additional release note sections
        lines = [section]

        # Add installation instructions
        lines.extend(
            [
                "",
                "### 📦 Installation",
                "",
                "```bash",
                f"pip install hwautomation=={version.lstrip('v')}",
                "```",
                "",
                "### 🔗 Links",
                "",
                f"- [Full Changelog](CHANGELOG.md)",
                f"- [PyPI Package](https://pypi.org/project/hwautomation/{version.lstrip('v')}/)",
                f"- [Documentation](docs/)",
            ]
        )

        return "\n".join(lines)

    def generate_full_changelog(self, output_file: str = "CHANGELOG.md") -> None:
        """Generate complete changelog file."""
        tags = self.get_all_tags()

        lines = [
            "# Changelog",
            "",
            "All notable changes to this project will be documented in this file.",
            "",
            "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),",
            "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).",
            "",
        ]

        if not tags:
            # No tags, generate unreleased section
            commits = self.get_git_commits()
            section = self.generate_section(commits)
            if section:
                lines.append(section)
        else:
            # Generate unreleased section (commits since latest tag)
            latest_tag = tags[0]
            unreleased_commits = self.get_git_commits(since_tag=latest_tag)
            if unreleased_commits:
                unreleased_section = self.generate_section(unreleased_commits)
                lines.append(unreleased_section)

            # Generate sections for each tag
            for i, tag in enumerate(tags):
                since_tag = tags[i + 1] if i + 1 < len(tags) else None
                commits = self.get_git_commits(since_tag=since_tag, until_tag=tag)
                section = self.generate_section(commits, version=tag)
                if section:
                    lines.append(section)

        # Write to file
        output_path = self.repo_path / output_file
        with open(output_path, "w") as f:
            f.write("\n".join(lines))

        print(f"Changelog generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate changelog from git commits")
    parser.add_argument(
        "--output", "-o", default="CHANGELOG.md", help="Output file path"
    )
    parser.add_argument("--repo", "-r", default=".", help="Repository path")
    parser.add_argument("--since", "-s", help="Generate since specific tag")
    parser.add_argument("--version", "-v", help="Version for unreleased section")
    parser.add_argument(
        "--release-notes", action="store_true", help="Generate release notes format"
    )

    args = parser.parse_args()

    generator = ChangelogGenerator(args.repo)

    if args.version and args.release_notes:
        # Generate release notes for CI
        latest_tag = generator.get_latest_tag()
        release_notes = generator.generate_release_notes(
            args.version, since_tag=latest_tag
        )
        print(release_notes)
    elif args.since or args.version:
        # Generate single section
        commits = generator.get_git_commits(since_tag=args.since)
        section = generator.generate_section(commits, version=args.version)
        print(section)
    else:
        # Generate full changelog
        generator.generate_full_changelog(args.output)


if __name__ == "__main__":
    main()
