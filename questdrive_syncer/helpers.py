"""Collection of helper functions."""
import os
from pathlib import Path

from .config import CONFIG


def has_enough_free_space(mb_size: float) -> bool:
    """Return if there is enough free space to download the video."""
    Path(CONFIG.output_path).mkdir(parents=True, exist_ok=True)
    statvfs = os.statvfs(CONFIG.output_path)
    free_space = statvfs.f_frsize * statvfs.f_bavail
    free_space_after_download = free_space - mb_size * 1024**2
    return free_space_after_download >= CONFIG.minimum_free_space_mb * 1024**2
