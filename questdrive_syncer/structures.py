"""Common structures."""
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Video:
    """Video representation."""

    filepath: str
    filename: str
    created_at: datetime
    modified_at: datetime
    mb_size: float
    actively_recording: bool = False

    def __str__(self: "Video") -> str:
        """Return a string representation of the video."""
        string = f"{self.filename} at {round(self.mb_size, 2):,} MB - {self.created_at} -> {self.modified_at}"
        if self.actively_recording:
            string += " (actively recording)"
        return string

    @property
    def duration(self: "Video") -> timedelta:
        """Return the duration of the video as a timedelta."""
        return self.modified_at - self.created_at

    @property
    def application_name(self: "Video") -> str:
        """Return the application name of the video."""
        return self.filename.split("-")[0]


class MissingVideoError(Exception):
    """Raised when a video is missing."""

    def __init__(self: "MissingVideoError", video_filepath: str) -> None:
        """Initialize the exception."""
        super().__init__(f'Video "{video_filepath}" is missing.')
