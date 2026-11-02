import argparse
from pathlib import Path

from platformdirs import user_data_path


def main():
    parser = argparse.ArgumentParser(description="typr — a terminal typing utility")
    parser.add_argument("--data-dir", type=Path, help="local database directory")
    parser.add_argument("--skip-boot", action="store_true", help="skip the starOS presentation")
    args = parser.parse_args()
    from .app import TyprApp

    path = args.data_dir or user_data_path("typr", appauthor=False)
    TyprApp(path, skip_boot=args.skip_boot).run()
