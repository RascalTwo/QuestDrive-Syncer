"""Main function."""
import sys
import time

from questdrive_syncer.config import init_config

from .api import (
    download_and_delete_video,
    fetch_video_list_html,
    is_online,
    update_actively_recording,
)
from .config import CONFIG
from .constants import (
    ACTIVELY_RECORDING_EXIT_CODE,
    FAILURE_EXIT_CODE,
    QUESTDRIVE_POLL_RATE_MINUTES,
)
from .helpers import has_enough_free_space
from .parsers import parse_video_list_html


def main() -> None:
    """Perform all actions."""
    init_config(*sys.argv[1:])

    if CONFIG.dry:
        print("Dry run enabled, no actions will be performed.")

    if CONFIG.wait_for_questdrive:
        while not is_online():
            print(f'Waiting for QuestDrive at "{CONFIG.questdrive_url}"...')
            time.sleep(QUESTDRIVE_POLL_RATE_MINUTES * 60)
    elif not is_online():
        print(f'QuestDrive not found at "{CONFIG.questdrive_url}"')
        sys.exit(FAILURE_EXIT_CODE)

    print(f'QuestDrive found running at "{CONFIG.questdrive_url}"')

    videos = parse_video_list_html(*fetch_video_list_html())
    time.sleep(1)
    print(f"Found {len(videos)} video{'' if len(videos) == 1 else 's'}:")

    update_actively_recording(videos, parse_video_list_html(*fetch_video_list_html()))

    videos = sorted(videos, key=lambda video: video.mb_size)

    if not CONFIG.run_while_actively_recording and any(
        video.actively_recording for video in videos
    ):
        print("Quest is actively recording, exiting.")
        sys.exit(ACTIVELY_RECORDING_EXIT_CODE)

    for video in videos:
        if has_enough_free_space(video.mb_size):
            download_and_delete_video(
                video,
                dry=CONFIG.dry,
                delete=CONFIG.delete_videos,
                download=CONFIG.download_videos,
            )
        else:
            print(
                f'Skipping download of "{video.filename}" because there is not enough free space',
            )
