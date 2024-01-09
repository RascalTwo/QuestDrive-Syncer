"""Configuration for QuestDrive Syncer."""
from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from rich_argparse import HelpPreviewAction, RichHelpFormatter


@dataclass
class Config:
    """Configuration."""

    questdrive_url: str
    output_path: str = "output/"
    minimum_free_space_mb: float = 1024
    wait_for_questdrive: bool = False
    run_while_actively_recording: bool = True
    delete_videos: bool = True
    download_videos: bool = True
    simple_output: bool = False
    only_run_if_space_less: float = float("inf")
    only_run_if_battery_above: int = 0
    sort_by: Literal["mb_size" | "filename" | "created_at" | "modified_at"] = "mb_size"
    sort_order: Literal["ascending" | "descending"] = "ascending"


CONFIG = Config(questdrive_url="https://example.com/")


def float_gte_zero(value: str) -> float:
    """Return a float greater than or equal to 0."""
    float_value = float(value)
    if float_value < 0:
        message = "can't be less then 0"
        raise argparse.ArgumentTypeError(
            message,
        )
    return float_value


def str_with_trailing_forward_slash(value: str) -> str:
    """Return a string with a trailing forward slash."""
    if not value.endswith("/"):
        value += "/"
    return value


def percentage(value: str) -> int:
    """Return a int between 0 and 100."""
    int_value = int(value)
    if int_value < 0 or int_value > 100:  # noqa: PLR2004
        message = "must be between 0 and 100"
        raise argparse.ArgumentTypeError(
            message,
        )
    return int_value


def parse_args(*args: str) -> Config:
    """Parse the command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Sync your Quest's recordings to your computer via QuestDrive",
        formatter_class=RichHelpFormatter,
    )

    default_config = Config(questdrive_url="")

    parser.add_argument(
        "--generate-help-preview",
        action=HelpPreviewAction,
        path="help-preview.svg",
    )
    with (Path(__file__).parent.parent / "pyproject.toml").open("r") as pyproject:
        version = pyproject.read().split('version = "')[1].split('"')[0]
    parser.add_argument(
        "--version",
        action="version",
        version=f"[argparse.prog]%(prog)s[/] version [i]{version}[/]",
    )
    parser.add_argument(
        "--questdrive-url",
        type=str_with_trailing_forward_slash,
        required=True,
        help="URL of running QuestDrive instance",
    )
    parser.add_argument(
        "--output",
        type=str_with_trailing_forward_slash,
        default=default_config.output_path,
        help="Directory to save videos to",
        dest="output_path",
    )
    parser.add_argument(
        "--minimum-free-space",
        type=float_gte_zero,
        default=default_config.minimum_free_space_mb,
        help="Minimum system free space in MB to continue downloading videos",
        dest="minimum_free_space_mb",
    )
    parser.add_argument(
        "--wait-for-questdrive",
        action="store_true",
        default=default_config.wait_for_questdrive,
        help="Instead of failing if QuestDrive is not found, wait for it to come online",
    )
    parser.add_argument(
        "--dont-run-while-actively-recording",
        action="store_false",
        default=default_config.run_while_actively_recording,
        help="Don't run if the Quest is actively recording",
        dest="run_while_actively_recording",
    )
    parser.add_argument(
        "--dont-delete",
        action="store_false",
        default=default_config.delete_videos,
        help="Don't delete videos from the Quest",
        dest="delete_videos",
    )
    parser.add_argument(
        "--dont-download",
        action="store_false",
        default=default_config.download_videos,
        help="Don't download videos from the Quest",
        dest="download_videos",
    )
    parser.add_argument(
        "--simple-output",
        action="store_true",
        default=sys.stdout.isatty(),
        help="Print simple output instead of a progress bar",
    )
    parser.add_argument(
        "--only-run-if-space-less",
        type=float_gte_zero,
        default=default_config.only_run_if_space_less,
        help="Only run if QuestDrive reports less than this amount of free space in MB",
    )
    parser.add_argument(
        "--only-run-if-battery-above",
        type=percentage,
        default=default_config.only_run_if_battery_above,
        help="Only run if QuestDrive reports a battery percentage above this value",
    )
    parser.add_argument(
        "--sort-by",
        choices=["filename", "created_at", "modified_at", "mb_size"],
        default=default_config.sort_by,
        help="Video attribute to sort by",
    )
    parser.add_argument(
        "--sort-order",
        choices=["ascending", "descending"],
        default=default_config.sort_order,
        help="Order to sort videos by",
    )

    config = Config(**vars(parser.parse_args(args)))

    if config.delete_videos and not config.download_videos:
        print(
            "Current configuration will delete videos without downloading.\nIf this is really what you want, simply wait 15 seconds and the program will continue.",
        )
        time.sleep(15)

    return config


def init_config(*args: str) -> None:
    """Initialize the global configuration."""
    CONFIG.__dict__.update(parse_args(*args).__dict__)
