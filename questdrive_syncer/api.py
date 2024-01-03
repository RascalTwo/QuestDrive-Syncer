import httpx
import os
from questdrive_syncer.constants import QUEST_DRIVE_URL, VIDEO_SHOTS_PATH, OUTPUT_PATH
from dataclasses import dataclass
from datetime import datetime


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


@dataclass
class Video:
    filepath: str
    filename: str
    created_at: datetime
    modified_at: datetime
    mb_size: float
    listing_url: str
    actively_recording: bool = False

    def __str__(self) -> str:
        string = f"{self.filename} at {self.mb_size} MB - {self.created_at} -> {self.modified_at}"
        if self.actively_recording:
            string += " (actively recording)"
        return string


def parse_video_list_html(from_url: str, html: str) -> list[Video]:
    table_html = html.split("<tbody>")[1].split("</tbody>")[0]

    videos: list[Video] = []
    for row_html in table_html.split("<tr>")[2:]:
        raw_cells = [
            ">".join(raw_cell.split("</td>")[0].split(">")[1:])
            for raw_cell in row_html.split("<td")[1:]
        ]
        filename = raw_cells[0].split("</a>")[1].replace("&nbsp;", "").strip()
        created_at = datetime.strptime(
            "-".join(filename.split("-")[-2:]).split(".")[0], "%Y%m%d-%H%M%S"
        )
        modified_at = datetime.strptime(raw_cells[1], "%m/%d/%Y %H:%M:%S")
        filepath = raw_cells[3].split("href='/download/")[1].split("'")[0]

        raw_size, size_unit = raw_cells[2].split(" ")
        mb_size = float(raw_size) * (1000 if size_unit == "GB" else 1)

        videos.append(
            Video(
                filepath=filepath,
                filename=filename,
                created_at=created_at,
                modified_at=modified_at,
                mb_size=mb_size,
                listing_url=from_url,
            )
        )
    return videos


# custom error called MissingVideo
class MissingVideo(Exception):
    pass


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
