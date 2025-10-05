"""
Copyright (c) Cutleast

Script to calculate differences between two folders. This includes:
- New files
- Moved/renamed files
- Deleted files

The script calculates the SHA256 hash of each file to determine if files are identical.

TODO: Optimize this by implementing concurrent hashing

Usage:
    python compare_folders.py <folder1> <folder2> [--out-file differences.json]
"""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def calculate_hash(file_path: Path) -> str:
    """
    Calculates the SHA256 hash of a file.

    Args:
        file_path (Path): Path to the file.

    Returns:
        str: SHA256 hash of the file.
    """

    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def scan_folder(folder: Path) -> dict[str, Path]:
    """
    Scans a folder recursively and returns a dict of hashes -> file paths.

    Args:
        folder (Path): Path to the folder.

    Returns:
        dict[str, Path]: Mapping of file hashes to file paths.
    """

    file_map: dict[str, Path] = {}
    for file in folder.rglob("*"):
        if file.is_file():
            file_map[calculate_hash(file)] = file.relative_to(folder)

    return file_map


def run(args: argparse.Namespace) -> None:
    folder1 = Path(args.folder1).resolve()
    folder2 = Path(args.folder2).resolve()
    out_file: Path | None = Path(args.out_file) if args.out_file else None

    print(f"Comparing '{folder1}' and '{folder2}'...")

    map1: dict[str, Path] = scan_folder(folder1)
    map2: dict[str, Path] = scan_folder(folder2)

    hashes1: set[str] = set(map1.keys())
    hashes2: set[str] = set(map2.keys())

    new_files: list[str] = [str(map2[h]) for h in hashes2 - hashes1]
    deleted_files: list[str] = [str(map1[h]) for h in hashes1 - hashes2]
    moved_files: list[dict[str, str]] = [
        {"from": str(map1[h]), "to": str(map2[h])}
        for h in hashes1 & hashes2
        if map1[h] != map2[h]
    ]

    new_files.sort()
    deleted_files.sort()
    moved_files.sort(key=lambda x: (x["from"], x["to"]))

    result: dict[str, Any] = {
        "new_files": new_files,
        "deleted_files": deleted_files,
        "moved_or_renamed_files": moved_files,
    }

    if out_file is not None:
        with out_file.open("w", encoding="utf-8") as file_stream:
            file_stream.write(json.dumps(result, indent=4))

        print(f"\nResults written to '{out_file}'")

    else:
        print("\nNew files:")
        for new_file in new_files:
            print(f"  {new_file}")

        print("\nDeleted files:")
        for deleted_file in deleted_files:
            print(f"  {deleted_file}")

        print("\nMoved/Renamed files:")
        for entry in moved_files:
            print(f"  {entry['from']}  ->  {entry['to']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compares two folders and lists new, deleted, and moved/renamed files."
    )
    parser.add_argument("folder1", type=str, help="First folder to compare.")
    parser.add_argument("folder2", type=str, help="Second folder to compare.")
    parser.add_argument(
        "--out-file",
        type=str,
        help="Optional path to a JSON file for structured output.",
    )

    run(parser.parse_args())


if __name__ == "__main__":
    main()
