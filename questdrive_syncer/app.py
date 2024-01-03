from questdrive_syncer.api import (
    is_online,
    fetch_video_list_html,
    parse_video_list_html,
    update_actively_recording,
    download_and_delete_video,
)
from questdrive_syncer.constants import QUEST_DRIVE_URL
import time


def main() -> None:
    if not is_online():
        print(f'QuestDrive not found at "{QUEST_DRIVE_URL}"')
        exit(3)
    print(f"QuestDrive found running at {QUEST_DRIVE_URL}")

    url, html = fetch_video_list_html()
    time.sleep(1)

    videos = parse_video_list_html(url, html)
    print(f"Found {len(videos)} video{'' if len(videos) == 1 else 's'}:")

    update_actively_recording(videos)

    videos = sorted(videos, key=lambda video: video.mb_size)

    for video in videos:
        print(video)
        download_and_delete_video(video)
