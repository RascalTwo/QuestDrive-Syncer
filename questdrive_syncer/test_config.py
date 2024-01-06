"""Tests for the config module."""
from typing import Generator

import pytest
from pytest_mock import MockerFixture

from .config import CONFIG, Config, init_config, parse_args


@pytest.fixture()
def _reset_config() -> Generator[None, None, None]:
    """Reset the global configuration."""
    old_config = Config(**CONFIG.__dict__)
    yield
    CONFIG.__dict__.update(old_config.__dict__)


@pytest.mark.usefixtures("_reset_config")
def test_init_config_updates_global_config(mocker: MockerFixture) -> None:
    """init_config() updates the global configuration."""
    assert CONFIG.questdrive_url == "https://example.com/"

    init_config("--questdrive-url=url")

    assert CONFIG.questdrive_url == "url/"


def test_parse_args_default_questdrive_url(
    mocker: MockerFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """parse_args() prints an error message if --questdrive-url is not provided."""
    with pytest.raises(SystemExit):
        parse_args()

    assert "required: --questdrive-url" in capsys.readouterr().err


def test_parse_args_custom_questdrive_url(mocker: MockerFixture) -> None:
    """parse_args() returns the provided questdrive_url."""
    config = parse_args("--questdrive-url=url")

    assert config.questdrive_url == "url/"


def test_parse_args_default_output_path(mocker: MockerFixture) -> None:
    """parse_args() returns a default output_path of "output/"."""
    config = parse_args("--questdrive-url=url")

    assert config.output_path == "output/"


def test_parse_args_custom_output_path(mocker: MockerFixture) -> None:
    """parse_args() returns the provided output_path."""
    config = parse_args("--questdrive-url=url", "--output=./wherever/")

    assert config.output_path == "./wherever/"


def test_parse_args_default_wait_for_questdrive(mocker: MockerFixture) -> None:
    """parse_args() returns False for wait_for_questdrive by default."""
    config = parse_args("--questdrive-url=url")

    assert config.wait_for_questdrive is False


def test_parse_args_provided_wait_for_questdrive(mocker: MockerFixture) -> None:
    """parse_args() returns True if provided --wait-for-questdrive."""
    config = parse_args("--questdrive-url=url", "--wait-for-questdrive")

    assert config.wait_for_questdrive is True


def test_parse_args_default_dont_run_while_actively_recording(
    mocker: MockerFixture,
) -> None:
    """parse_args() returns False for --dont-run-while-actively-recording by default."""
    config = parse_args("--questdrive-url=url")

    assert config.run_while_actively_recording is True


def test_parse_args_provided_dont_run_while_actively_recording(
    mocker: MockerFixture,
) -> None:
    """parse_args() returns True if --dont-run-while-actively-recording is provided."""
    config = parse_args("--questdrive-url=url", "--dont-run-while-actively-recording")

    assert config.run_while_actively_recording is False


def test_parse_args_default_dont_delete(
    mocker: MockerFixture,
) -> None:
    """parse_args() returns False for --dont-delete by default."""
    config = parse_args("--questdrive-url=url")

    assert config.delete_videos is True


def test_parse_args_provided_dont_delete(
    mocker: MockerFixture,
) -> None:
    """parse_args() returns True if --dont-delete is provided."""
    config = parse_args("--questdrive-url=url", "--dont-delete")

    assert config.delete_videos is False


def test_parse_args_default_dont_download(
    mocker: MockerFixture,
) -> None:
    """parse_args() returns False for --dont-download by default."""
    config = parse_args("--questdrive-url=url")

    assert config.download_videos is True


def test_parse_args_provided_dont_download(
    mocker: MockerFixture,
) -> None:
    """parse_args() returns True if --dont-download is provided."""
    mock_print = mocker.patch("builtins.print")
    mock_sleep = mocker.patch("time.sleep")

    config = parse_args("--questdrive-url=url", "--dont-download")

    mock_print.assert_called_once()
    assert (
        "Current configuration will delete videos without downloading"
        in mock_print.mock_calls[0].args[0]
    )
    mock_sleep.assert_called_once_with(15)
    assert config.download_videos is False


def test_parse_args_default_minimum_free_space(mocker: MockerFixture) -> None:
    """parse_args() returns the default minimum_free_space_mb."""
    config = parse_args("--questdrive-url=url")

    assert config.minimum_free_space_mb == 1024  # noqa: PLR2004


def test_parse_args_custom_minimum_free_space(mocker: MockerFixture) -> None:
    """parse_args() returns a custom minimum_free_space_mb."""
    config = parse_args("--questdrive-url=url", "--minimum-free-space=1")

    assert config.minimum_free_space_mb == 1


def test_parse_args_custom_minimum_free_space_must_be_greater_then_0(
    mocker: MockerFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """parse_args() prints an error message if --minimum-free-space is less than 0."""
    with pytest.raises(SystemExit):
        parse_args("--questdrive-url=url", "--minimum-free-space=-1")

    assert (
        "argument --minimum-free-space: can't be less then 0" in capsys.readouterr().err
    )


def test_parse_args_warn_if_deleting_without_downloading(
    mocker: MockerFixture,
) -> None:
    """parse_args() warns if deleting videos without downloading."""
    mock_print = mocker.patch("builtins.print")
    mock_sleep = mocker.patch("time.sleep")

    parse_args("--questdrive-url=url", "--dont-download")

    mock_print.assert_called_once()
    assert (
        "Current configuration will delete videos without downloading"
        in mock_print.mock_calls[0].args[0]
    )
    mock_sleep.assert_called_once_with(15)
