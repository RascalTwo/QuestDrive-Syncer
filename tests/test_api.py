from questdrive_syncer.api import is_online, fetch_video_list_html
import httpx
from pytest_httpx import HTTPXMock
import pytest


@pytest.fixture
def assert_all_responses_were_requested() -> bool:
    return True


def test_normal(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=200)
    assert is_online() is True


def test_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_exception(httpx.ConnectError(""))
    assert is_online() is False


def test_non_200(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=404)
    assert is_online() is False


def test_fetch_video_list_html(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=200, text="html")
    assert fetch_video_list_html() == "html"
