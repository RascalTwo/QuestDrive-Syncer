"""Parsers for QuestDrive's HTML pages."""
from __future__ import annotations

from datetime import datetime

from .structures import Video


def raw_size_to_mb(raw_size: str, unit: str) -> float:
    """Convert a raw size & unit to MB."""
    return float(raw_size) * (1000 if unit == "GB" else 1) * 1.048576


def parse_homepage_html(html: str) -> tuple[int, float]:
    """Parse the battery percentage & free space from the homepage HTML."""
    return (
        int(html.split("Battery:")[1].split(">")[1].split("<")[0].split("%")[0]),
        raw_size_to_mb(
            *html.split("Free Space:")[1].split(">")[1].split("<")[0].split(" "),
        ),
    )


def parse_video_list_html(from_url: str, html: str) -> list[Video]:
    """Parse the video list HTML into a list of videos."""
    table_html = html.split("<tbody>")[1].split("</tbody>")[0]

    videos: list[Video] = []
    for row_html in table_html.split("<tr>")[2:]:
        raw_cells = [
            ">".join(raw_cell.split("</td>")[0].split(">")[1:])
            for raw_cell in row_html.split("<td")[1:]
        ]
        filename = raw_cells[0].split("</a>")[1].replace("&nbsp;", "").strip()
        created_at = datetime.strptime(
            "-".join(filename.split("-")[-2:]).split(".")[0],
            "%Y%m%d-%H%M%S",
        )
        modified_at = datetime.strptime(raw_cells[1], "%m/%d/%Y %H:%M:%S")
        filepath = raw_cells[3].split("href='/download/")[1].split("'")[0]

        mb_size = raw_size_to_mb(*raw_cells[2].split(" "))

        videos.append(
            Video(
                filepath=filepath,
                filename=filename,
                created_at=created_at,
                modified_at=modified_at,
                mb_size=mb_size,
                listing_url=from_url,
            ),
        )
    return videos
