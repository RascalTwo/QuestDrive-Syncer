"""Main function."""
import sys
import time

from .api import (
    download_and_delete_video,
    fetch_video_list_html,
    is_online,
    update_actively_recording,
)
from .constants import FAILURE_EXIT_CODE, QUEST_DRIVE_URL
from .helpers import has_enough_free_space
from .parsers import parse_video_list_html


def main() -> None:
    """Perform all actions."""
    if not is_online():
        print(f'QuestDrive not found at "{QUEST_DRIVE_URL}"')
        sys.exit(FAILURE_EXIT_CODE)
    print(f"QuestDrive found running at {QUEST_DRIVE_URL}")

    videos = parse_video_list_html(*fetch_video_list_html())
    time.sleep(1)
    print(f"Found {len(videos)} video{'' if len(videos) == 1 else 's'}:")

    update_actively_recording(videos, parse_video_list_html(*fetch_video_list_html()))

    videos = sorted(videos, key=lambda video: video.mb_size)

    for video in videos:
        print(video)
        if has_enough_free_space(video.mb_size):
            download_and_delete_video(video)
        else:
            print(
                f'Skipping download of "{video.filename}" because there is not enough free space',
            )
