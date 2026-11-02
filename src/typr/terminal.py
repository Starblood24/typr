"""Fullscreen launchers for terminals we can identify without guessing."""
import atexit
import ctypes
import os
from pathlib import Path
import shutil
import subprocess
import sys


def windows_console():
    if sys.platform != "win32":
        return None
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    user = ctypes.WinDLL("user32", use_last_error=True)
    kernel.GetConsoleWindow.restype = ctypes.c_void_p
    user.IsWindowVisible.argtypes = [ctypes.c_void_p]
    user.GetClassNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
    window = kernel.GetConsoleWindow()
    name = ctypes.create_unicode_buffer(128)
    user.GetClassNameW(window, name, len(name))
    # A delegated PseudoConsoleWindow can report visible despite having no on-screen content.
    return kernel if name.value == "ConsoleWindowClass" and user.IsWindowVisible(window) else None


def windows_terminal():
    """Recognize Windows' default-terminal delegation, which may omit WT_SESSION."""
    if sys.platform != "win32":
        return False
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    user = ctypes.WinDLL("user32", use_last_error=True)
    kernel.GetConsoleWindow.restype = ctypes.c_void_p
    user.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    user.GetAncestor.restype = ctypes.c_void_p
    user.GetClassNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
    window = user.GetAncestor(kernel.GetConsoleWindow(), 3)  # GA_ROOTOWNER
    name = ctypes.create_unicode_buffer(128)
    user.GetClassNameW(window, name, len(name))
    return name.value == "CASCADIA_HOSTING_WINDOW_CLASS"


def fullscreen_console():
    console = windows_console()
    if console is None:
        return
    mode = ctypes.c_uint32()
    if not console.GetConsoleDisplayMode(ctypes.byref(mode)) or mode.value & 1:
        return
    console.GetStdHandle.argtypes = [ctypes.c_uint32]
    console.GetStdHandle.restype = ctypes.c_void_p
    console.SetConsoleDisplayMode.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p]
    handle = console.GetStdHandle(-11)
    if console.SetConsoleDisplayMode(handle, 1, None):
        atexit.register(console.SetConsoleDisplayMode, handle, 2, None)
    else:
        print("typr: console fullscreen unavailable; using this window.", file=sys.stderr)


def current_terminal():
    env = os.environ
    if (any(env.get(key) for key in ("SSH_CONNECTION", "SSH_CLIENT", "SSH_TTY", "TMUX", "STY"))
            or env.get("TERM", "").startswith(("screen", "tmux"))):
        return None
    # A real local console takes precedence over markers inherited from its parent terminal.
    if windows_console() is not None:
        return "conhost"
    if env.get("KITTY_WINDOW_ID") and env.get("TERM") == "xterm-kitty":
        return "kitty" if sys.platform in ("linux", "darwin") else None
    program = env.get("TERM_PROGRAM", "").lower()
    if program == "wezterm":
        return "wezterm"
    if program:
        return None
    if env.get("WEZTERM_PANE"):
        return "wezterm"
    if sys.platform == "win32" and env.get("WT_SESSION"):
        return "wt"
    if windows_terminal():
        return "wt"
    return None


def launch_fullscreen():
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return None
    terminal = current_terminal()
    if terminal is None:
        return None
    if terminal == "conhost":
        fullscreen_console()
        return None
    if os.environ.get("TYPR_FULLSCREEN") == "1":
        return None
    executable = shutil.which(terminal)
    if not executable and terminal == "wezterm" and sys.platform == "win32":
        candidate = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "WezTerm/wezterm.exe"
        if candidate.is_file():
            executable = str(candidate)
    if not executable:
        return None
    # The argument also prevents recursion when an existing terminal process drops our environment.
    child = [sys.executable, "-m", "typr", "--windowed", *sys.argv[1:]]
    env = os.environ | {"TYPR_FULLSCREEN": "1"}
    if terminal == "wezterm":
        config = Path(__file__).parent / "assets/wezterm-fullscreen.lua"
        env["TYPR_WEZTERM_CONFIG"] = os.environ.get("WEZTERM_CONFIG_FILE", "")
        command = [executable, "--config-file", str(config), "start", "--always-new-process",
                   "--cwd", str(Path.cwd()), "--", *child]
    elif terminal == "wt":
        command = [executable, "--window", "new", "--fullscreen", "new-tab",
                   "--inheritEnvironment", "--startingDirectory", str(Path.cwd()),
                   *child]
    else:
        command = [executable, "--start-as=fullscreen", "--directory", str(Path.cwd()), *child]
    try:
        result = subprocess.run(command, env=env, check=False)
    except OSError as error:
        print(f"typr: unable to open fullscreen ({error}); using this terminal.", file=sys.stderr)
        return None
    if result.returncode != 0:
        print("typr: fullscreen launch failed; using this terminal.", file=sys.stderr)
        return None
    return 0
