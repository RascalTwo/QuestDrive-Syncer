import httpx
from questdrive_syncer.constants import QUEST_DRIVE_URL, VIDEO_SHOTS_PATH


def is_online() -> bool:
    try:
        response = httpx.get(QUEST_DRIVE_URL)
        return response.status_code == 200
    except httpx.ConnectError:
        return False


def fetch_video_list_html() -> str:
    response = httpx.get(QUEST_DRIVE_URL + VIDEO_SHOTS_PATH)
    return response.text
