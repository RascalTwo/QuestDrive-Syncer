"""Test the parsers module."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pytest

from questdrive_syncer.parsers import (
    parse_homepage_html,
    parse_video_list_html,
    raw_size_to_mb,
)
from questdrive_syncer.structures import Video

if TYPE_CHECKING:  # pragma: no cover
    from pytest_mock import MockerFixture


@pytest.mark.parametrize(
    ("raw_size", "unit", "expected"),
    [
        ("2.345", "MB", 2.45891072),
        ("1,012.99", "MB", 1062.19700224),
        ("2.345", "GB", 2458.91072),
    ],
)
def test_raw_size_to_mb(raw_size: str, unit: str, expected: float) -> None:
    """raw_size_to_mb function returns the expected value."""
    assert raw_size_to_mb(raw_size, unit) == expected


def test_parse_homepage_html(mocker: MockerFixture) -> None:
    """parse_homepage_html function parses battery & calls raw_size_to_mb with expected values."""
    mock_raw_size_to_mb = mocker.patch(
        "questdrive_syncer.parsers.raw_size_to_mb",
        return_value=1,
    )
    assert parse_homepage_html(
        """
    Battery:
    <b>50%</b>
    Free Space:
    <b>2.345 GB</b>
    """,
    ) == (50, 1)
    mock_raw_size_to_mb.assert_called_once_with("2.345", "GB")


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
            2.345 * 1.048576,
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
            2345 * 1.048576,
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
            html,
        )
        == expected
    )
