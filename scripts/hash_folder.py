"""
Copyright (c) Cutleast

Script to index a folder and calculate the hashes of all files within.
"""

import argparse
import hashlib
import json
import time
import traceback
from concurrent.futures import Future, ProcessPoolExecutor, as_completed
from pathlib import Path


def calculate_hash(file_path: Path) -> str:
    """
    Calculates the SHA256 hash of a file.

    Args:
        file_path (Path): Path to the file.

    Returns:
        str: SHA256 hash of the file.
    """

    print(f"Hashing '{file_path}'...")

    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def run(args: argparse.Namespace) -> None:
    folder = Path(args.folder).resolve()
    out_file: Path = (
        Path(args.out_file) if args.out_file else Path(f"{folder.name}.json")
    )

    print(f"Indexing '{folder}'...")
    start_time: float = time.time()

    files: dict[str, str] = {}
    with ProcessPoolExecutor() as executor:
        futures: dict[Future[str], Path] = {
            executor.submit(calculate_hash, path): path
            for path in folder.rglob("*")
            if path.is_file()
        }
        for future in as_completed(futures):
            path: Path = futures[future]
            try:
                files[str(path)] = future.result()
            except Exception as ex:
                print(f"Failed to hash '{path}'!")
                traceback.print_exception(type(ex), ex, ex.__traceback__)

    with out_file.open("w", encoding="utf-8") as file:
        file.write(json.dumps(files, indent=4, sort_keys=True))

    print(f"Output written to '{out_file}'.")
    print(f"Completed in {time.time() - start_time:.2f} seconds.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Indexes a folder and calculates the hashes of all files within."
    )
    parser.add_argument("folder", type=str, help="Folder to index.")
    parser.add_argument(
        "--out-file",
        type=str,
        help="Path to a JSON file for the output. Defaults to <folder_name>.json",
    )

    run(parser.parse_args())


if __name__ == "__main__":
    main()
    input("Press ENTER to exit...")
