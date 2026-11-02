from pathlib import Path
from unittest.mock import Mock

import pytest

from typr import cli


def test_windows_launcher_forwards_arguments_and_prevents_recursion(monkeypatch, tmp_path):
    executable = tmp_path / "Wez Term.exe"
    executable.touch()
    monkeypatch.setattr(cli.sys, "platform", "win32")
    monkeypatch.delenv("TYPR_FULLSCREEN", raising=False)
    monkeypatch.setattr(cli.shutil, "which", lambda _: str(executable))
    arguments = ["typr", "--skip-boot", "--data-dir", "profile with spaces/übertragung"]
    monkeypatch.setattr(cli.sys, "argv", arguments)
    run = Mock(return_value=Mock(returncode=7))
    monkeypatch.setattr(cli.subprocess, "run", run)
    assert cli.launch_fullscreen() == 7
    command = run.call_args.args[0]
    assert command[0] == str(executable)
    assert Path(command[2]).is_file()
    assert command[3:8] == ["start", "--always-new-process", "--cwd", str(Path.cwd()), "--"]
    assert command[8:] == [cli.sys.executable, "-m", "typr", *arguments[1:]]
    assert run.call_args.kwargs["env"]["TYPR_FULLSCREEN"] == "1"
    assert "TYPR_FULLSCREEN" not in cli.os.environ
    monkeypatch.setenv("TYPR_FULLSCREEN", "1")
    assert cli.launch_fullscreen() is None
    run.assert_called_once()


@pytest.mark.parametrize("platform,installed", [("linux", True), ("win32", False)])
def test_launcher_falls_back_without_supported_terminal(monkeypatch, tmp_path, platform, installed):
    executable = tmp_path / "wezterm.exe"
    if installed:
        executable.touch()
    monkeypatch.setattr(cli.sys, "platform", platform)
    monkeypatch.delenv("TYPR_FULLSCREEN", raising=False)
    monkeypatch.setattr(cli.shutil, "which", lambda _: str(executable))
    run = Mock()
    monkeypatch.setattr(cli.subprocess, "run", run)
    assert cli.launch_fullscreen() is None
    run.assert_not_called()


def test_main_exits_after_launch_instead_of_starting_second_app(monkeypatch):
    monkeypatch.setattr(cli.sys, "argv", ["typr"])
    monkeypatch.setattr(cli, "launch_fullscreen", lambda: 7)
    with pytest.raises(SystemExit) as result:
        cli.main()
    assert result.value.code == 7
