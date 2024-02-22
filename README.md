# QuestDrive Syncer

![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)
![Coverage](https://img.shields.io/badge/any_text-100%25-green?label=coverage)
![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)
![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)
![Version](https://img.shields.io/badge/2.5.4-blue?label=version)
![GitHub License](https://img.shields.io/github/license/RascalTwo/QuestDrive-Syncer)

This tool allows syncing data from a Quest device running QuestDrive to a local directory.

The primary use for this is moving recorded videos from a Quest - as it has limited space - to an external device for storage.

https://github.com/RascalTwo/QuestDrive-Syncer/assets/9403665/19c7ebb1-373e-4ea5-8bc2-d639dbd98c1a

![help output](https://github.com/RascalTwo/QuestDrive-Syncer/assets/9403665/a6401393-6bc5-47ad-a51a-950130d117cd)

## How it's made

**Tech used**: Python, Poetry, pre-commit, httpx, mypy, ruff

Empowered by the [QuestDrive](https://sidequestvr.com/app/220/questdrive) application, this Python script interacts with the QuestDrive web interface to obtain information about the Quest, available videos, and how to download/delete them.

Developed with Test-Driven Development - via `pytest` - with consistency & safety brought by `mypy`, `typeguard`, `ruff`, and various other `pre-commits` hooks - for a total of 60 hooks!

Other notable usages include the built-in `argparse` for CLI parsing, `httpx` for HTTP requests, and `rich` for both the pretty progress bars & CLI interface.

The most valuable `pytest` plugins used are `pytest-cov` for coverage, `pytest-mock` for reasonable mocking, and `pytest-network` to ensure all network requests are mocked.

### Development

To perform all checks manually, one can run the following:

```shell
poetry run pre-commit run --all-files
```

### Usage

## Pre-requisites

A Quest device running QuestDrive, and a computer with Python 3.9+ and enough space to store the synced data.

## Execution

```shell
poetry run python questdrive_syncer --questdrive-url=URL_OF_QUESTDRIVE_INSTANCE
```

You can additionally use the `--help` flag to see all available options.

### Automated

Process-locking has been implemented, so you can run this script on a schedule without worrying about it overlapping executions.

To do so with `cron` for example, you can use the following:

```shell
0 * * * * ABSOLUTE_PATH_TO_POETRY run python ABSOLUTE_PATH_TO_THIS_REPO --simple-output
```

To add instant logging for example, you can use the following:

```shell
0 * * * * ABSOLUTE_PATH_TO_POETRY run python ABSOLUTE_PATH_TO_THIS_REPO --simple-output >> ABSOLUTE_PATH_TO_LOGFILE 2>&1
```

> There are various options to customize the circumstances under which the script will run, so be sure to check out the help output.

## Optimizations

Only two features were never implemented:

- The ability to resume interrupted downloads
  - Impossible to do in a performant manner as QuestDrive does not support range requests
- Live updates on consumed/free space both locally and on the Quest
  - Given the time & effort to implement and - lack of - demand for this feature, it was not implemented
