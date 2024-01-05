"""Tests for the config module."""
import pytest
from pytest_mock import MockerFixture

from .config import CONFIG, init_config, parse_args


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
    """parse_args() returns a custom questdrive_url."""
    config = parse_args("--questdrive-url=url")

    assert config.questdrive_url == "url/"


def test_parse_args_default_output_path(mocker: MockerFixture) -> None:
    """parse_args() returns the default output_path."""
    config = parse_args("--questdrive-url=url")

    assert config.output_path == "output/"


def test_parse_args_custom_output_path(mocker: MockerFixture) -> None:
    """parse_args() returns a custom output_path."""
    config = parse_args("--questdrive-url=url", "--output=./wherever/")

    assert config.output_path == "./wherever/"


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
