import subprocess
from typing import Optional, Tuple


def get_old_and_new_versions() -> Optional[Tuple[list[int], list[int]]]:
    stdout = subprocess.run(
        ["git", "diff", "--staged", "pyproject.toml"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout

    if "-version" not in stdout or "+version" not in stdout:
        return None

    old_version, new_version = (
        list(map(int, stdout.split(prefix + 'version = "')[1].split('"')[0].split(".")))
        for prefix in "-+"
    )
    return old_version, new_version


def is_version_bumped(old_version: list[int], new_version: list[int]) -> bool:
    for old, new in zip(old_version, new_version):
        if new > old:
            return True
        elif new < old:
            return False
    return False


def check() -> None:
    versions = get_old_and_new_versions()
    if versions is None or not is_version_bumped(*versions):
        print("You must bump the version in pyproject.toml before committing.")
        exit(1)

    print(
        "Version bumped from {} to {}.".format(
            *(".".join(map(str, version)) for version in versions)
        )
    )


if __name__ == "__main__":  # pragma: no cover
    check()
