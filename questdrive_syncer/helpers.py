"""Collection of helper functions."""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Callable, Literal

from questdrive_syncer.config import CONFIG


def has_enough_free_space(mb_size: float) -> bool:
    """Return if there is enough free space to download the video."""
    Path(CONFIG.output_path).mkdir(parents=True, exist_ok=True)
    statvfs = os.statvfs(CONFIG.output_path)
    free_space = statvfs.f_frsize * statvfs.f_bavail
    free_space_after_download = free_space - mb_size * 1024**2
    return free_space_after_download >= CONFIG.minimum_free_space_mb * 1024**2


class LockError(Exception):
    """Raised when a lock is already in place."""

    def __init__(self: LockError, pid: int, lock_file_path: str) -> None:
        """Initialize the error."""
        super().__init__(
            f'Another process ({pid}) is already running according to "{lock_file_path}" lockfile.',
        )


def lock(
    mode: Literal["fail", "wait"] = "fail",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Lock the function so that it can only be run once at a time."""
    lock_file = Path("/".join(__file__.split("/")[:-1])) / "questdrive_syncer.lock"

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            if lock_file.exists():
                if mode == "fail":
                    with lock_file.open("r") as f:
                        raise LockError(int(f.read()), str(lock_file.absolute()))
                elif mode == "wait":
                    while lock_file.exists():
                        time.sleep(1)

            with lock_file.open("w") as f:
                f.write(str(os.getpid()))
            try:
                return func(*args, **kwargs)
            finally:
                lock_file.unlink()

        return wrapper

    return decorator
