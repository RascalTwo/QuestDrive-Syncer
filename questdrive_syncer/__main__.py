"""Main entry point for the QuestDrive Syncer application."""
import sys

from questdrive_syncer.config import init_config
from questdrive_syncer.main import main

if __name__ == "__main__":
    init_config(*sys.argv[1:])
    main()
