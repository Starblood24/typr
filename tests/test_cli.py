import sys
from unittest.mock import Mock

import pytest

from typr import cli


def test_main_exits_after_launch_instead_of_starting_second_app(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["typr"])
    monkeypatch.setattr(cli, "launch_fullscreen", lambda: 0)
    with pytest.raises(SystemExit) as result:
        cli.main()
    assert result.value.code == 0


def test_windowed_runs_app_without_launcher(monkeypatch, tmp_path):
    from typr.app import TyprApp
    monkeypatch.setattr(sys, "argv", ["typr", "--windowed", "--skip-boot", "--data-dir", str(tmp_path)])
    launcher = Mock()
    monkeypatch.setattr(cli, "launch_fullscreen", launcher)
    run = Mock()
    monkeypatch.setattr(TyprApp, "run", run)
    cli.main()
    launcher.assert_not_called()
    run.assert_called_once()
