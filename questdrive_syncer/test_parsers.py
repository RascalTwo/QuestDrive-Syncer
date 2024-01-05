"""Test the parsers module."""
from __future__ import annotations

from datetime import datetime

import pytest

from .parsers import parse_video_list_html
from .structures import Video

html_expected_mappings = {
    "normal": [
        """
                <tr>
                    <td><a></a>&nbsp; filename-20240101-111213.mp4</td>
                    <td>01/01/2024 12:13:14</td>
                    <td>2.345 MB</td>
                    <td>
                        <a href='/download/full%2Fpathtofile.mp4'></a>
                    </td>
                </tr>
        """,
        Video(
            "full%2Fpathtofile.mp4",
            "filename-20240101-111213.mp4",
            datetime(2024, 1, 1, 11, 12, 13),
            datetime(2024, 1, 1, 12, 13, 14),
            2.345,
            "from_url",
        ),
    ],
    "gb": [
        """
                <tr>
                    <td><a></a>&nbsp; filename-20240101-111213.mp4</td>
                    <td>01/01/2024 12:13:14</td>
                    <td>2.345 GB</td>
                    <td>
                        <a href='/download/full%2Fpathtofile.mp4'></a>
                    </td>
                </tr>""",
        Video(
            "full%2Fpathtofile.mp4",
            "filename-20240101-111213.mp4",
            datetime(2024, 1, 1, 11, 12, 13),
            datetime(2024, 1, 1, 12, 13, 14),
            2345,
            "from_url",
        ),
    ],
}


@pytest.mark.parametrize(
    ("html", "expected"),
    [
        (
            """
            <tbody>
                <tr></tr>
            </tbody>
        """,
            [],
        ),
        (
            f"""
            <tbody>
                <tr></tr>
                {html_expected_mappings["normal"][0]}
            </tbody>
        """,
            [html_expected_mappings["normal"][1]],
        ),
        (
            f"""
            <tbody>
                <tr></tr>
                {html_expected_mappings["normal"][0]}
                {html_expected_mappings["normal"][0]}
            </tbody>
        """,
            [
                html_expected_mappings["normal"][1],
                html_expected_mappings["normal"][1],
            ],
        ),
        (
            f"""
            <tbody>
                <tr></tr>
                {html_expected_mappings["gb"][0]}
            </tbody>
        """,
            [html_expected_mappings["gb"][1]],
        ),
    ],
)
def test_parse_video_list_html(
    html: str,
    expected: list[Video],
) -> None:
    """parse_video_list_html function returns the expected list of Video objects."""
    assert (
        parse_video_list_html(
            "from_url",
            html,
        )
        == expected
    )
