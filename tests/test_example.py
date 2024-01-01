from questdrive_syncer.example import example


def test_normal() -> None:
    assert example(1, 2) == 3


def test_extra() -> None:
    assert example(2, 2) == 6
