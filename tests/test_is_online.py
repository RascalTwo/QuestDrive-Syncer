from questdrive_syncer.app import is_online
import httpx
from pytest_httpx import HTTPXMock


def test_normal(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=200)
    assert is_online() is True


def test_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_exception(httpx.ConnectError(""))
    assert is_online() is False


def test_non_200(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=404)
    assert is_online() is False
