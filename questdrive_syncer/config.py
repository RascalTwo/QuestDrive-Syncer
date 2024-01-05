"""Configuration for QuestDrive Syncer."""
import argparse

from .structures import Config

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

    return Config(**vars(parser.parse_args(args)))


def init_config(*args: str) -> None:
    """Initialize the global configuration."""
    CONFIG.__dict__.update(parse_args(*args).__dict__)
