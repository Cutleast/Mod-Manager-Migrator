"""
Copyright (c) Cutleast

Script to create a BBCode description from a markdown file.

**Not working at the moment!**
"""

import argparse
from pathlib import Path

from md2bbcode.main import process_readme


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a BBCode description for Nexus Mods"
    )
    parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Path to the markdown file",
    )
    parser.add_argument(
        "--out-file",
        type=str,
        required=True,
        help="Path to the output file",
    )
    parser.add_argument(
        "--domain",
        type=str,
        default="",
        help="Base URL to insert before relative paths",
    )

    run(parser.parse_args())


def run(args: argparse.Namespace) -> None:
    markdown_text: str = Path(args.file).read_text(encoding="utf-8")
    domain: str = args.domain
    bbcode_text: str = process_readme(markdown_text, domain)  # type: ignore
    Path(args.out_file).write_text(bbcode_text, encoding="utf-8")


if __name__ == "__main__":
    main()
