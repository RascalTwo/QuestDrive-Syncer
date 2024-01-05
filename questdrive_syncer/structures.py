"""Common structures."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Config:
    """Configuration."""

    questdrive_url: str
    output_path: str = "output/"
    minimum_free_space_mb: float = 1024


@dataclass
class Video:
    """Video representation."""

    filepath: str
    filename: str
    created_at: datetime
    modified_at: datetime
    mb_size: float
    listing_url: str
    actively_recording: bool = False

    def __str__(self: "Video") -> str:
        """Return a string representation of the video."""
        string = f"{self.filename} at {self.mb_size} MB - {self.created_at} -> {self.modified_at}"
        if self.actively_recording:
            string += " (actively recording)"
        return string


class MissingVideoError(Exception):
    """Raised when a video is missing."""

    def __init__(self: "MissingVideoError", video_filepath: str) -> None:
        """Initialize the exception."""
        super().__init__(f'Video "{video_filepath}" is missing.')
