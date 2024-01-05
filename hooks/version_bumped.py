"""Ensure the version in pyproject.toml has been increased."""
from __future__ import annotations

import subprocess
import sys


def get_old_and_new_versions() -> None | tuple[list[int], list[int]]:
    """Return the staged old and new versions."""
    stdout = subprocess.run(
        ["git", "diff", "--staged", "pyproject.toml"],  # noqa: S603,S607
        capture_output=True,
        text=True,
        check=False,
    ).stdout

    if "-version" not in stdout or "+version" not in stdout:
        return None

    old_version, new_version = (
        list(map(int, stdout.split(prefix + 'version = "')[1].split('"')[0].split(".")))
        for prefix in "-+"
    )
    return old_version, new_version


def is_version_bumped(old_version: list[int], new_version: list[int]) -> bool:
    """Return if the version has been bumped."""
    for old, new in zip(old_version, new_version):
        if new > old:
            return True
        if new < old:
            return False
    return False


def check() -> None:
    """Check that the version is bumped."""
    versions = get_old_and_new_versions()
    if versions is None or not is_version_bumped(*versions):
        print("You must bump the version in pyproject.toml before committing.")
        sys.exit(1)

    print(
        "Version bumped from {} to {}.".format(
            *(".".join(map(str, version)) for version in versions),
        ),
    )


if __name__ == "__main__":  # pragma: no cover
    check()
