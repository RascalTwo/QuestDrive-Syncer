import httpx

QUEST_DRIVE_URL = "http://192.168.254.75:7123/"


def is_online() -> bool:
    try:
        response = httpx.get(QUEST_DRIVE_URL)
        return response.status_code == 200
    except httpx.ConnectError:
        return False


def main() -> None:
    if not is_online():
        print(f'QuestDrive not found at "{QUEST_DRIVE_URL}"')
        exit(3)
