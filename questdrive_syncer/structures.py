from dataclasses import dataclass
from datetime import datetime


@dataclass
class Video:
    filepath: str
    filename: str
    created_at: datetime
    modified_at: datetime
    mb_size: float
    listing_url: str
    actively_recording: bool = False

    def __str__(self) -> str:
        string = f"{self.filename} at {self.mb_size} MB - {self.created_at} -> {self.modified_at}"
        if self.actively_recording:
            string += " (actively recording)"
        return string


class MissingVideo(Exception):
    pass
