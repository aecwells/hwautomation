#!/usr/bin/env python3
"""
Release management script for HWAutomation.

This script handles version bumping, changelog generation, and release tagging.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Tuple


class ReleaseManager:
    """Manage project releases with version bumping and changelog generation."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.pyproject_path = self.repo_path / "pyproject.toml"
        self.package_json_path = self.repo_path / "package.json"

    def get_current_version(self) -> str:
        """Get current version from pyproject.toml."""
        try:
            with open(self.pyproject_path, "r") as f:
                content = f.read()

            match = re.search(r'version\s*=\s*"([^"]+)"', content)
            if match:
                return match.group(1)
            else:
                raise ValueError("Version not found in pyproject.toml")
        except Exception as e:
            print(f"Error reading version: {e}")
            return "0.0.0"

    def bump_version(self, current_version: str, bump_type: str) -> str:
        """Bump version according to semantic versioning."""
        parts = current_version.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {current_version}")

        major, minor, patch = map(int, parts)

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")

        return f"{major}.{minor}.{patch}"

    def update_pyproject_version(self, new_version: str) -> None:
        """Update version in pyproject.toml."""
        with open(self.pyproject_path, "r") as f:
            content = f.read()

        updated_content = re.sub(
            r'version\s*=\s*"[^"]+"', f'version = "{new_version}"', content
        )

        with open(self.pyproject_path, "w") as f:
            f.write(updated_content)

        print(f"Updated pyproject.toml version to {new_version}")

    def update_package_json_version(self, new_version: str) -> None:
        """Update version in package.json."""
        if not self.package_json_path.exists():
            return

        try:
            with open(self.package_json_path, "r") as f:
                data = json.load(f)

            data["version"] = new_version

            with open(self.package_json_path, "w") as f:
                json.dump(data, f, indent=2)
                f.write("\n")  # Add trailing newline

            print(f"Updated package.json version to {new_version}")
        except Exception as e:
            print(f"Warning: Could not update package.json: {e}")

    def generate_changelog(self, version: str) -> None:
        """Generate changelog for the new version."""
        try:
            subprocess.run(
                ["python3", "tools/generate_changelog.py", "--version", version],
                cwd=self.repo_path,
                check=True,
            )
            print(f"Generated changelog for version {version}")
        except subprocess.CalledProcessError as e:
            print(f"Error generating changelog: {e}")

    def create_git_tag(self, version: str, message: str = None) -> None:
        """Create and push git tag."""
        tag_name = f"v{version}"

        if not message:
            message = f"Release {tag_name}"

        try:
            # Create annotated tag
            subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", message],
                cwd=self.repo_path,
                check=True,
            )

            print(f"Created git tag: {tag_name}")

            # Ask if user wants to push
            response = input(f"Push tag {tag_name} to remote? (y/N): ")
            if response.lower() in ["y", "yes"]:
                subprocess.run(
                    ["git", "push", "origin", tag_name], cwd=self.repo_path, check=True
                )
                print(f"Pushed tag {tag_name} to remote")

        except subprocess.CalledProcessError as e:
            print(f"Error creating/pushing tag: {e}")

    def check_working_directory_clean(self) -> bool:
        """Check if working directory is clean."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
            )

            return len(result.stdout.strip()) == 0
        except subprocess.CalledProcessError:
            return False

    def commit_version_changes(self, version: str) -> None:
        """Commit version bump changes."""
        try:
            # Add changed files
            subprocess.run(
                ["git", "add", "pyproject.toml", "package.json", "CHANGELOG.md"],
                cwd=self.repo_path,
                check=True,
            )

            # Commit changes
            subprocess.run(
                ["git", "commit", "-m", f"chore(release): bump version to {version}"],
                cwd=self.repo_path,
                check=True,
            )

            print(f"Committed version bump to {version}")

        except subprocess.CalledProcessError as e:
            print(f"Error committing changes: {e}")

    def release(self, bump_type: str, dry_run: bool = False) -> None:
        """Perform a complete release."""
        # Check working directory
        if not dry_run and not self.check_working_directory_clean():
            print(
                "Error: Working directory is not clean. Commit or stash changes first."
            )
            sys.exit(1)

        # Get current version
        current_version = self.get_current_version()
        new_version = self.bump_version(current_version, bump_type)

        print(f"Current version: {current_version}")
        print(f"New version: {new_version}")

        if dry_run:
            print("DRY RUN - No changes will be made")
            return

        # Confirm with user
        response = input(f"Proceed with release {new_version}? (y/N): ")
        if response.lower() not in ["y", "yes"]:
            print("Release cancelled")
            return

        try:
            # Update version files
            self.update_pyproject_version(new_version)
            self.update_package_json_version(new_version)

            # Generate changelog
            self.generate_changelog(new_version)

            # Commit changes
            self.commit_version_changes(new_version)

            # Create tag
            self.create_git_tag(new_version)

            print(f"✅ Release {new_version} completed successfully!")
            print(f"Next steps:")
            print(f"  1. Push commits: git push origin main")
            print(f"  2. Create GitHub release from tag v{new_version}")
            print(f"  3. Update deployment environments")

        except Exception as e:
            print(f"❌ Release failed: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Manage project releases")
    parser.add_argument(
        "bump_type", choices=["major", "minor", "patch"], help="Type of version bump"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument("--repo", "-r", default=".", help="Repository path")

    args = parser.parse_args()

    manager = ReleaseManager(args.repo)
    manager.release(args.bump_type, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
