# QuestDrive Syncer

This tool allows syncing data from a Quest device running QuestDrive to a local directory.

The primary use for this is moving recorded videos from a Quest - as it has limited space - to an external device for storage.

## Pre-requisites

A Quest device running QuestDrive, and a computer with Python 3.9+ and enough space to store the synced data.

```shell
poetry run python questdrive_syncer
```

## Development

Poetry and pre-commit are heavily used, so ensure to start off with a `poetry install` and `pre-commit install`.

From then you can glance at `.pre-commit-config.yaml` to see all the used hooks, and most notably, the custom ones.

Linting is handled by `ruff`, type checking by `mypy` and `typeguard`, and testing by `pytest`.

To run all hooks, one can either attempt a commit, or run the `poetry run pre-commit run --all-files` command.

Running an individual hook can be done via `poetry run pre-commit run --all-files <hook_id>`.

Finally to run any arbitrary command, one can use `poetry run`, or to enter the virtual environment, `poetry shell`.
