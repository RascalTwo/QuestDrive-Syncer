import os

import httpx

from questdrive_syncer.constants import (
    OUTPUT_PATH,
    QUEST_DRIVE_URL,
    VIDEO_SHOTS_PATH,
)

from .parsers import parse_video_list_html
from .structures import MissingVideo, Video


def is_online() -> bool:
    try:
        response = httpx.get(QUEST_DRIVE_URL)
        return response.status_code == 200
    except httpx.ConnectError:
        return False


def fetch_video_list_html() -> tuple[str, str]:
    url = QUEST_DRIVE_URL + VIDEO_SHOTS_PATH
    response = httpx.get(url)
    return url, response.text


# TODO - update to receive latest videos
def update_actively_recording(videos: list[Video]) -> None:
    latest_videos = parse_video_list_html(*fetch_video_list_html())

    for video in videos:
        latest_video = next(
            (
                latest_video
                for latest_video in latest_videos
                if latest_video.filepath == video.filepath
            ),
            None,
        )

        if latest_video is None:
            raise MissingVideo(f'Video "{video.filepath}" no longer found in list')

        if latest_video.modified_at != video.modified_at:
            video.actively_recording = True


def download_and_delete_video(video: Video) -> None:
    if not os.path.exists(OUTPUT_PATH):
        os.mkdir(OUTPUT_PATH)

    url = QUEST_DRIVE_URL + "download/" + video.filepath
    response = httpx.get(url)
    with open(f"{OUTPUT_PATH}/{video.filename}", "wb") as f:
        f.write(response.content)
    os.utime(
        f"{OUTPUT_PATH}/{video.filename}",
        (video.created_at.timestamp(), video.modified_at.timestamp()),
    )

    if video.actively_recording:
        return print(f'"{video.filename}" is actively recording, not deleting')

    content_length_diff = len(response.content) - int(
        response.headers.get("Content-Length", len(response.content))
    )
    if content_length_diff:
        if content_length_diff > 0:
            print(
                f'Received {content_length_diff} bytes more than expected during the download of "{video.filename}"'
            )
        else:
            print(
                f'Received {-content_length_diff} bytes less than expected during the download of "{video.filename}"'
            )
        return

    written_length = os.path.getsize(f"{OUTPUT_PATH}/{video.filename}")
    written_length_diff = len(response.content) - written_length
    if written_length_diff:
        if written_length_diff > 0:
            print(
                f'Wrote {written_length_diff} bytes more than received during the download of "{video.filename}"'
            )
        else:
            print(
                f'Wrote {-written_length_diff} bytes less than received during the download of "{video.filename}"'
            )
        return

    httpx.get(QUEST_DRIVE_URL + "delete/" + video.filepath)
