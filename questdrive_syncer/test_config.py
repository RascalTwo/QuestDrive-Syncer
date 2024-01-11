"""Tests for the config module."""
from typing import Generator

import pytest
from pytest_mock import MockerFixture

from questdrive_syncer.config import CONFIG, Config, init_config, parse_args


@pytest.fixture()
def _reset_config() -> Generator[None, None, None]:
    """Reset the global configuration."""
    old_config = Config(**CONFIG.__dict__)
    yield
    CONFIG.__dict__.update(old_config.__dict__)


@pytest.mark.usefixtures("_reset_config")
def test_init_config_updates_global_config() -> None:
    """init_config() updates the global configuration."""
    assert CONFIG.questdrive_url == "https://example.com/"

    init_config("--questdrive-url=url")

    assert CONFIG.questdrive_url == "url/"


class TestParseArgs:
    """Tests for parse_args()."""

    @staticmethod
    def test_reads_version(
        mocker: MockerFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Returns the version."""
        mock_version = mocker.patch("importlib.metadata.version", return_value="1.0.0")
        with pytest.raises(SystemExit) as exec_info:
            parse_args("--version")

        assert exec_info.value.code == 0
        assert "1.0.0" in capsys.readouterr().out
        mock_version.assert_called_once_with("questdrive-syncer")

    @staticmethod
    def test_default_questdrive_url(
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Prints an error message if --questdrive-url is not provided."""
        with pytest.raises(SystemExit):
            parse_args()

        assert "required: --questdrive-url" in capsys.readouterr().err

    @staticmethod
    def test_custom_questdrive_url() -> None:
        """Returns the provided questdrive_url."""
        config = parse_args("--questdrive-url=url")

        assert config.questdrive_url == "url/"

    @staticmethod
    def test_default_output_path() -> None:
        """Returns a default output_path of "output/"."""
        config = parse_args("--questdrive-url=url")

        assert config.output_path == "output/"

    @staticmethod
    def test_custom_output_path() -> None:
        """Returns the provided output_path."""
        config = parse_args("--questdrive-url=url", "--output=./wherever/")

        assert config.output_path == "./wherever/"

    @staticmethod
    def test_default_wait_for_questdrive() -> None:
        """Returns False for wait_for_questdrive by default."""
        config = parse_args("--questdrive-url=url")

        assert config.wait_for_questdrive is False

    @staticmethod
    def test_provided_wait_for_questdrive() -> None:
        """Returns True if provided --wait-for-questdrive."""
        config = parse_args("--questdrive-url=url", "--wait-for-questdrive")

        assert config.wait_for_questdrive is True

    @staticmethod
    def test_default_dont_run_while_actively_recording() -> None:
        """Returns False for --dont-run-while-actively-recording by default."""
        config = parse_args("--questdrive-url=url")

        assert config.run_while_actively_recording is True

    @staticmethod
    def test_provided_dont_run_while_actively_recording() -> None:
        """Returns True if --dont-run-while-actively-recording is provided."""
        config = parse_args(
            "--questdrive-url=url",
            "--dont-run-while-actively-recording",
        )

        assert config.run_while_actively_recording is False

    @staticmethod
    def test_default_dont_delete() -> None:
        """Returns False for --dont-delete by default."""
        config = parse_args("--questdrive-url=url")

        assert config.delete_videos is True

    @staticmethod
    def test_provided_dont_delete() -> None:
        """Returns True if --dont-delete is provided."""
        config = parse_args("--questdrive-url=url", "--dont-delete")

        assert config.delete_videos is False

    @staticmethod
    def test_default_simple_output(
        mocker: MockerFixture,
    ) -> None:
        """Returns the TTY state for --simple-output by default."""
        for value in (True, False):
            mocker.patch("sys.stdout.isatty", return_value=value)
            config = parse_args("--questdrive-url=url")

            assert config.simple_output is value

    @staticmethod
    def test_provided_simple_output() -> None:
        """Returns True if --simple-output is provided."""
        config = parse_args("--questdrive-url=url", "--simple-output")

        assert config.simple_output is True

    @staticmethod
    def test_default_dont_download() -> None:
        """Returns False for --dont-download by default."""
        config = parse_args("--questdrive-url=url")

        assert config.download_videos is True

    @staticmethod
    def test_provided_dont_download(
        mocker: MockerFixture,
    ) -> None:
        """Returns True if --dont-download is provided."""
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

    @staticmethod
    def test_default_only_run_if_space_less() -> None:
        """Returns None for only_run_if_space_less by default."""
        config = parse_args("--questdrive-url=url")

        assert config.only_run_if_space_less == float("inf")

    @staticmethod
    def test_custom_only_run_if_space_less() -> None:
        """Returns the provided only_run_if_space_less."""
        config = parse_args("--questdrive-url=url", "--only-run-if-space-less=1")

        assert config.only_run_if_space_less == 1

    @staticmethod
    def test_only_run_if_space_less_must_be_greater_then_0(
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Prints an error message if --only-run-if-space-less is less than 0."""
        with pytest.raises(SystemExit):
            parse_args("--questdrive-url=url", "--only-run-if-space-less=-1")

        assert (
            "argument --only-run-if-space-less: can't be less then 0"
            in capsys.readouterr().err
        )

    @staticmethod
    def test_default_only_run_if_battery_above() -> None:
        """Returns 0 for only_run_if_battery_above by default."""
        config = parse_args("--questdrive-url=url")

        assert config.only_run_if_battery_above == 0

    @staticmethod
    def test_custom_only_run_if_battery_above() -> None:
        """Returns the provided only_run_if_battery_above."""
        config = parse_args("--questdrive-url=url", "--only-run-if-battery-above=75")

        assert config.only_run_if_battery_above == 75  # noqa: PLR2004

    @staticmethod
    @pytest.mark.parametrize(
        "percentage",
        [
            -1,
            101,
        ],
    )
    def test_only_run_if_battery_above_must_within_0_100(
        percentage: int,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Prints an error message if --only-run-if-battery-above is outside of 0-100 range."""
        with pytest.raises(SystemExit):
            parse_args(
                "--questdrive-url=url",
                f"--only-run-if-battery-above={percentage}",
            )

        assert (
            "argument --only-run-if-battery-above: must be between 0 and 100"
            in capsys.readouterr().err
        )

    @staticmethod
    def test_sort_by_default() -> None:
        """Returns the default sort_by."""
        config = parse_args("--questdrive-url=url")

        assert config.sort_by == "mb_size"

    @staticmethod
    @pytest.mark.parametrize(
        "sort_by",
        [
            "filename",
            "created_at",
            "modified_at",
            "mb_size",
            "application_name",
            "duration",
        ],
    )
    def test_custom_sort_by(sort_by: str) -> None:
        """Returns the provided sort_by."""
        config = parse_args("--questdrive-url=url", f"--sort-by={sort_by}")

        assert config.sort_by == sort_by

    @staticmethod
    def test_sort_by_must_be_valid(
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Prints an error message if --sort-by is invalid."""
        with pytest.raises(SystemExit):
            parse_args("--questdrive-url=url", "--sort-by=invalid")

        assert (
            "argument --sort-by: invalid choice: 'invalid'" in capsys.readouterr().err
        )

    @staticmethod
    def test_sort_order_default() -> None:
        """Returns the default sort_order."""
        config = parse_args("--questdrive-url=url")

        assert config.sort_order == "ascending"

    @staticmethod
    @pytest.mark.parametrize(
        "sort_order",
        ["ascending", "descending"],
    )
    def test_custom_sort_order(sort_order: str) -> None:
        """Returns the provided sort_order."""
        config = parse_args("--questdrive-url=url", f"--sort-order={sort_order}")

        assert config.sort_order == sort_order

    @staticmethod
    def test_sort_order_must_be_valid(
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Prints an error message if --sort-order is invalid."""
        with pytest.raises(SystemExit):
            parse_args("--questdrive-url=url", "--sort-order=invalid")

        assert (
            "argument --sort-order: invalid choice: 'invalid' (choose from 'ascending', 'descending')"
            in capsys.readouterr().err
        )

    @staticmethod
    def test_default_minimum_free_space() -> None:
        """Returns the default minimum_free_space_mb."""
        config = parse_args("--questdrive-url=url")

        assert config.minimum_free_space_mb == 1024  # noqa: PLR2004

    @staticmethod
    def test_custom_minimum_free_space() -> None:
        """Returns a custom minimum_free_space_mb."""
        config = parse_args("--questdrive-url=url", "--minimum-free-space=1")

        assert config.minimum_free_space_mb == 1

    @staticmethod
    def test_custom_minimum_free_space_must_be_greater_then_0(
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Prints an error message if --minimum-free-space is less than 0."""
        with pytest.raises(SystemExit):
            parse_args("--questdrive-url=url", "--minimum-free-space=-1")

        assert (
            "argument --minimum-free-space: can't be less then 0"
            in capsys.readouterr().err
        )

    @staticmethod
    def test_warn_if_deleting_without_downloading(mocker: MockerFixture) -> None:
        """Warns if deleting videos without downloading."""
        mock_print = mocker.patch("builtins.print")
        mock_sleep = mocker.patch("time.sleep")

        parse_args("--questdrive-url=url", "--dont-download")

        mock_print.assert_called_once()
        assert (
            "Current configuration will delete videos without downloading"
            in mock_print.mock_calls[0].args[0]
        )
        mock_sleep.assert_called_once_with(15)
