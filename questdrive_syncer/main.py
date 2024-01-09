"""Main function."""
import sys
import time

from questdrive_syncer.api import (
    fetch_homepage_html,
    fetch_video_list_html,
    is_online,
    update_actively_recording,
)
from questdrive_syncer.config import CONFIG
from questdrive_syncer.constants import (
    ACTIVELY_RECORDING_EXIT_CODE,
    FAILURE_EXIT_CODE,
    NOT_ENOUGH_BATTERY_EXIT_CODE,
    QUESTDRIVE_POLL_RATE_MINUTES,
    TOO_MUCH_SPACE_EXIT_CODE,
)
from questdrive_syncer.download import download_and_delete_videos
from questdrive_syncer.helpers import lock
from questdrive_syncer.parsers import parse_homepage_html, parse_video_list_html


@lock(mode="fail")
def main() -> None:
    """Perform all actions."""
    if CONFIG.wait_for_questdrive:
        while not is_online():
            print(f'Waiting for QuestDrive at "{CONFIG.questdrive_url}"...')
            time.sleep(QUESTDRIVE_POLL_RATE_MINUTES * 60)
    elif not is_online():
        print(f'QuestDrive not found at "{CONFIG.questdrive_url}"')
        sys.exit(FAILURE_EXIT_CODE)

    print(f'QuestDrive found running at "{CONFIG.questdrive_url}"')

    if (
        CONFIG.only_run_if_space_less != float("inf")
        or CONFIG.only_run_if_battery_above > 0
    ):
        homepage_html = fetch_homepage_html()
        battery_percentage, free_space = parse_homepage_html(homepage_html)
        if free_space > CONFIG.only_run_if_space_less:
            print(
                f"QuestDrive reports {free_space:,} MB free space, which is more than the configured limit of {CONFIG.only_run_if_space_less:,} MB. Exiting.",
            )
            sys.exit(TOO_MUCH_SPACE_EXIT_CODE)
        if battery_percentage < CONFIG.only_run_if_battery_above:
            print(
                f"QuestDrive reports {battery_percentage}% battery remaining, which is less than the configured minimum of {CONFIG.only_run_if_battery_above}%. Exiting.",
            )
            sys.exit(NOT_ENOUGH_BATTERY_EXIT_CODE)

    videos = parse_video_list_html(fetch_video_list_html())
    time.sleep(1)
    print(f"Found {len(videos)} video{'' if len(videos) == 1 else 's'}:")

    update_actively_recording(videos, parse_video_list_html(fetch_video_list_html()))

    videos = sorted(
        videos,
        key=lambda video: getattr(video, CONFIG.sort_by),
        reverse=CONFIG.sort_order == "descending",
    )

    if not CONFIG.run_while_actively_recording and any(
        video.actively_recording for video in videos
    ):
        print("Quest is actively recording, exiting.")
        sys.exit(ACTIVELY_RECORDING_EXIT_CODE)

    download_and_delete_videos(
        videos,
        delete=CONFIG.delete_videos,
        download=CONFIG.download_videos,
        simple_output=CONFIG.simple_output,
    )
