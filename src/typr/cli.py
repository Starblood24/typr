import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

from platformdirs import user_data_path


def launch_fullscreen():
    if sys.platform != "win32" or os.environ.get("TYPR_FULLSCREEN") == "1":
        return None
    executable = shutil.which("wezterm") or str(
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "WezTerm/wezterm.exe")
    if not Path(executable).is_file():
        return None
    config = Path(__file__).parent / "assets/wezterm-fullscreen.lua"
    result = subprocess.run([
        executable, "--config-file", str(config), "start", "--always-new-process",
        "--cwd", str(Path.cwd()), "--", sys.executable, "-m", "typr", *sys.argv[1:],
    ], env=os.environ | {"TYPR_FULLSCREEN": "1"}, check=False)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="typr — a terminal typing utility")
    parser.add_argument("--data-dir", type=Path, help="local database directory")
    parser.add_argument("--skip-boot", action="store_true", help="skip the starOS presentation")
    args = parser.parse_args()
    exit_code = launch_fullscreen()
    if exit_code is not None:
        raise SystemExit(exit_code)
    from .app import TyprApp

    path = args.data_dir or user_data_path("typr", appauthor=False)
    TyprApp(path, skip_boot=args.skip_boot).run()
