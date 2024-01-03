from questdrive_syncer.api import (
    is_online,
    fetch_video_list_html,
    parse_video_list_html,
)
from questdrive_syncer.constants import QUEST_DRIVE_URL


def main() -> None:
    if not is_online():
        print(f'QuestDrive not found at "{QUEST_DRIVE_URL}"')
        exit(3)
    print(f"QuestDrive found running at {QUEST_DRIVE_URL}")

    url, html = fetch_video_list_html()
    videos = parse_video_list_html(url, html)
    print(f"Found {len(videos)} video{'' if len(videos) == 1 else 's'}:")
    for video in videos:
        print(video)
