"""Configuration for QuestDrive Syncer."""
import argparse
import time
from dataclasses import dataclass


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


def parse_args(*args: str) -> Config:
    """Parse the command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Sync your Quest's recordings to your computer via QuestDrive",
    )

    default_config = Config(questdrive_url="")

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
