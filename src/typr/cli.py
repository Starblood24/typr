import argparse
from pathlib import Path

from platformdirs import user_data_path
from .terminal import launch_fullscreen


def main():
    parser = argparse.ArgumentParser(description="typr — a terminal typing utility")
    parser.add_argument("--data-dir", type=Path, help="local database directory")
    parser.add_argument("--skip-boot", action="store_true", help="skip the starOS presentation")
    parser.add_argument("--windowed", action="store_true", help="run in the current terminal without opening a fullscreen window")
    args = parser.parse_args()
    exit_code = None if args.windowed else launch_fullscreen()
    if exit_code is not None:
        raise SystemExit(exit_code)
    from .app import TyprApp

    path = args.data_dir or user_data_path("typr", appauthor=False)
    TyprApp(path, skip_boot=args.skip_boot).run()
