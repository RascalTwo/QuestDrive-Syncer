"""Collection of helper functions."""
import os
from pathlib import Path

from .constants import MINIMUM_FREE_SPACE_BYTES, OUTPUT_PATH


def has_enough_free_space(mb_size: float) -> bool:
    """Return if there is enough free space to download the video."""
    Path(OUTPUT_PATH).mkdir(parents=True, exist_ok=True)
    statvfs = os.statvfs(OUTPUT_PATH)
    free_space = statvfs.f_frsize * statvfs.f_bavail
    free_space_after_download = free_space - mb_size * 1024**2
    return free_space_after_download >= MINIMUM_FREE_SPACE_BYTES
