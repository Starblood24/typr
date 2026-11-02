import ctypes
from pathlib import Path
from unittest.mock import Mock

import pytest

from typr import terminal
from typr.terminal import windows_console, windows_terminal


@pytest.fixture(autouse=True)
def terminal_environment(monkeypatch):
    monkeypatch.setattr(terminal, "windows_console", lambda: None)
    monkeypatch.setattr(terminal, "windows_terminal", lambda: False)
    for key in ("TERM_PROGRAM", "TERM", "WEZTERM_PANE", "WT_SESSION", "KITTY_WINDOW_ID",
                "SSH_CONNECTION", "SSH_CLIENT", "SSH_TTY", "TMUX", "STY", "TYPR_FULLSCREEN",
                "WEZTERM_CONFIG_FILE", "TYPR_WEZTERM_CONFIG"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(terminal.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(terminal.sys.stdout, "isatty", lambda: True)


@pytest.mark.parametrize("platform,environment,expected", [
    ("win32", {"TERM_PROGRAM": "WezTerm", "WT_SESSION": "outer"}, "wezterm"),
    ("linux", {"WEZTERM_PANE": "0"}, "wezterm"),
    ("darwin", {"TERM_PROGRAM": "WezTerm"}, "wezterm"),
    ("win32", {"WT_SESSION": "session"}, "wt"),
    ("linux", {"TERM": "xterm-kitty", "KITTY_WINDOW_ID": "1", "TERM_PROGRAM": "WezTerm"}, "kitty"),
    ("darwin", {"TERM": "xterm-kitty", "KITTY_WINDOW_ID": "1"}, "kitty"),
    ("linux", {"TERM": "xterm-256color"}, None),
    ("win32", {"TERM_PROGRAM": "vscode", "WT_SESSION": "outer", "WEZTERM_PANE": "0"}, None),
    ("darwin", {"TERM_PROGRAM": "Apple_Terminal"}, None),
    ("darwin", {"TERM_PROGRAM": "iTerm.app"}, None),
    ("linux", {"WT_SESSION": "inherited-through-wsl"}, None),
])
def test_detects_host_without_switching_to_installed_terminal(monkeypatch, platform, environment, expected):
    monkeypatch.setattr(terminal.sys, "platform", platform)
    for key, value in environment.items():
        monkeypatch.setenv(key, value)
    assert terminal.current_terminal() == expected


@pytest.mark.parametrize("key,value", [("SSH_CONNECTION", "remote"), ("SSH_CLIENT", "remote"),
    ("SSH_TTY", "/dev/pts/1"), ("TMUX", "session"), ("STY", "session"), ("TERM", "screen-256color")])
def test_remote_and_nested_sessions_stay_in_place(monkeypatch, key, value):
    monkeypatch.setattr(terminal, "windows_console", lambda: Mock())
    monkeypatch.setenv("TERM_PROGRAM", "WezTerm")
    monkeypatch.setenv(key, value)
    assert terminal.current_terminal() is None


@pytest.mark.parametrize("name", ["wezterm", "wt", "kitty"])
def test_launch_preserves_python_arguments_cwd_and_recursion_guard(monkeypatch, name):
    monkeypatch.setattr(terminal, "current_terminal", lambda: name)
    monkeypatch.setattr(terminal.shutil, "which", lambda _: "/terminal with spaces/" + name)
    monkeypatch.setenv("WEZTERM_CONFIG_FILE", "/custom terminal/config.lua")
    arguments = ["typr", "--skip-boot", "--data-dir", "profile with spaces/übertragung"]
    monkeypatch.setattr(terminal.sys, "argv", arguments)
    run = Mock(return_value=Mock(returncode=0))
    monkeypatch.setattr(terminal.subprocess, "run", run)
    assert terminal.launch_fullscreen() == 0
    command = run.call_args.args[0]
    assert command[-7:] == [terminal.sys.executable, "-m", "typr", "--windowed", *arguments[1:]]
    assert str(Path.cwd()) in command
    if name == "wezterm":
        assert Path(command[2]).is_file()
        assert "--always-new-process" in command
        assert run.call_args.kwargs["env"]["TYPR_WEZTERM_CONFIG"] == "/custom terminal/config.lua"
    elif name == "wt":
        assert command[1:6] == ["--window", "new", "--fullscreen", "new-tab", "--inheritEnvironment"]
    else:
        assert command[1] == "--start-as=fullscreen"
    assert run.call_args.kwargs["env"]["TYPR_FULLSCREEN"] == "1"
    assert "TYPR_FULLSCREEN" not in terminal.os.environ
    monkeypatch.setenv("TYPR_FULLSCREEN", "1")
    assert terminal.launch_fullscreen() is None
    run.assert_called_once()


@pytest.mark.parametrize("reason", ["unknown", "missing", "redirected", "error", "nonzero"])
def test_launch_falls_back_to_current_terminal(monkeypatch, reason):
    monkeypatch.setattr(terminal, "current_terminal", lambda: None if reason == "unknown" else "kitty")
    monkeypatch.setattr(terminal.shutil, "which", lambda _: None if reason == "missing" else "/kitty")
    if reason == "redirected":
        monkeypatch.setattr(terminal.sys.stdout, "isatty", lambda: False)
    run = Mock(return_value=Mock(returncode=1))
    if reason == "error":
        run.side_effect = OSError("cannot start terminal")
    monkeypatch.setattr(terminal.subprocess, "run", run)
    assert terminal.launch_fullscreen() is None
    assert run.call_count == (1 if reason in ("error", "nonzero") else 0)


def test_windows_wezterm_uses_install_path_when_not_on_path(monkeypatch, tmp_path):
    executable = tmp_path / "WezTerm/wezterm.exe"
    executable.parent.mkdir()
    executable.touch()
    monkeypatch.setenv("ProgramFiles", str(tmp_path))
    monkeypatch.setattr(terminal.sys, "platform", "win32")
    monkeypatch.setattr(terminal, "current_terminal", lambda: "wezterm")
    monkeypatch.setattr(terminal.shutil, "which", lambda _: None)
    run = Mock(return_value=Mock(returncode=0))
    monkeypatch.setattr(terminal.subprocess, "run", run)
    assert terminal.launch_fullscreen() == 0
    assert run.call_args.args[0][0] == str(executable)


def test_visible_legacy_console_is_detected_without_terminal_markers(monkeypatch):
    monkeypatch.setattr(terminal, "windows_console", Mock(return_value=Mock()))
    assert terminal.current_terminal() == "conhost"


@pytest.mark.parametrize("name,visible,expected", [
    ("ConsoleWindowClass", True, True), ("ConsoleWindowClass", False, False),
    ("PseudoConsoleWindow", True, False), ("PseudoConsoleWindow", False, False),
])
def test_only_real_console_windows_use_legacy_fullscreen(monkeypatch, name, visible, expected):
    kernel, user = Mock(), Mock()
    kernel.GetConsoleWindow.return_value = 123
    user.IsWindowVisible.return_value = visible
    def class_name(handle, buffer, length):
        buffer.value = name
        return len(name)
    user.GetClassNameW.side_effect = class_name
    monkeypatch.setattr(terminal.sys, "platform", "win32")
    monkeypatch.setattr(ctypes, "WinDLL", lambda dll, **_: kernel if dll == "kernel32" else user, raising=False)
    assert (windows_console() is kernel) == expected


@pytest.mark.parametrize("host_class", ["CASCADIA_HOSTING_WINDOW_CLASS", "OtherTerminal", ""])
def test_delegated_host_is_identified_from_its_own_window(monkeypatch, host_class):
    kernel, user = Mock(), Mock()
    kernel.GetConsoleWindow.return_value = 123
    user.GetAncestor.return_value = 456
    def class_name(window, buffer, length):
        assert window == 456
        buffer.value = host_class
        return len(host_class)
    user.GetClassNameW.side_effect = class_name
    monkeypatch.setattr(terminal.sys, "platform", "win32")
    monkeypatch.setattr(ctypes, "WinDLL", lambda dll, **_: kernel if dll == "kernel32" else user, raising=False)
    assert windows_terminal() == (host_class == "CASCADIA_HOSTING_WINDOW_CLASS")
    user.GetAncestor.assert_called_once_with(123, 3)


def test_delegated_windows_terminal_launches_without_environment_markers(monkeypatch):
    monkeypatch.setattr(terminal, "windows_terminal", lambda: True)
    monkeypatch.setattr(terminal.shutil, "which", lambda name: "wt.exe" if name == "wt" else None)
    run = Mock(return_value=Mock(returncode=0))
    monkeypatch.setattr(terminal.subprocess, "run", run)
    assert terminal.current_terminal() == "wt"
    assert terminal.launch_fullscreen() == 0
    assert run.call_args.args[0][:4] == ["wt.exe", "--window", "new", "--fullscreen"]


@pytest.mark.parametrize("markers", [
    {"TERM_PROGRAM": "WezTerm", "WEZTERM_PANE": "0", "TYPR_FULLSCREEN": "1"},
    {"WT_SESSION": "parent", "TYPR_FULLSCREEN": "1"},
    {"TERM_PROGRAM": "vscode"},
])
def test_real_console_overrides_inherited_terminal_and_launch_markers(monkeypatch, markers):
    monkeypatch.setattr(terminal, "windows_console", lambda: Mock())
    for key, value in markers.items():
        monkeypatch.setenv(key, value)
    fullscreen = Mock()
    run = Mock()
    monkeypatch.setattr(terminal, "fullscreen_console", fullscreen)
    monkeypatch.setattr(terminal.subprocess, "run", run)
    assert terminal.current_terminal() == "conhost"
    assert terminal.launch_fullscreen() is None
    fullscreen.assert_called_once_with()
    run.assert_not_called()


@pytest.mark.parametrize("state", ["windowed", "fullscreen", "query_error", "set_error"])
def test_console_fullscreen_restores_only_a_successful_change(monkeypatch, state):
    console = Mock()
    def display_mode(pointer):
        ctypes.cast(pointer, ctypes.POINTER(ctypes.c_uint32))[0] = 1 if state == "fullscreen" else 0
        return state != "query_error"
    console.GetConsoleDisplayMode.side_effect = display_mode
    console.GetStdHandle.return_value = 123
    console.SetConsoleDisplayMode.return_value = state != "set_error"
    monkeypatch.setattr(terminal, "windows_console", lambda: console)
    monkeypatch.setattr(terminal, "current_terminal", lambda: "conhost")
    register = Mock()
    monkeypatch.setattr(terminal.atexit, "register", register)
    run = Mock()
    monkeypatch.setattr(terminal.subprocess, "run", run)
    assert terminal.launch_fullscreen() is None
    run.assert_not_called()
    if state == "windowed":
        console.SetConsoleDisplayMode.assert_called_once_with(123, 1, None)
        register.assert_called_once_with(console.SetConsoleDisplayMode, 123, 2, None)
        callback, *arguments = register.call_args.args
        callback(*arguments)
        assert console.SetConsoleDisplayMode.call_args.args == (123, 2, None)
    else:
        register.assert_not_called()
        if state != "set_error":
            console.SetConsoleDisplayMode.assert_not_called()
