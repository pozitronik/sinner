from sinner.Status import Status, Mood


def test_status(capsys) -> None:
    status = Status()

    status.update_status('test', 'self', Mood.BAD)
    captured = capsys.readouterr()
    assert '👿self: test' == captured.out.strip()
