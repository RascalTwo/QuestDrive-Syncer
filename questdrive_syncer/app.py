from questdrive_syncer.api import is_online
from questdrive_syncer.constants import QUEST_DRIVE_URL


def main() -> None:
    if not is_online():
        print(f'QuestDrive not found at "{QUEST_DRIVE_URL}"')
        exit(3)
