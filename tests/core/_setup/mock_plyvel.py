"""
Copyright (c) Cutleast
"""

from types import TracebackType
from typing import Generator, Optional, Self


class MockPlyvelDB:
    """
    Mock implementation of plyvel.DB to use JSON for storage instead of LevelDB.
    """

    __data: dict[str, str]

    def __init__(self, data: dict[str, str] = {}) -> None:
        self.__data = data

    def iterator(
        self, prefix: Optional[bytes] = None
    ) -> Generator[tuple[bytes, bytes], None, None]:
        for key, value in self.__data.items():
            if not prefix or key.startswith(prefix.decode()):
                yield key.encode(), value.encode()

    def put(self, key: bytes, value: bytes) -> None:
        self.__data[key.decode()] = value.decode()

    def get(self, key: bytes) -> Optional[bytes]:
        if key.decode() in self.__data:
            return self.__data[key.decode()].encode()

        return None

    def write_batch(self) -> Self:
        return self

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self, exc_type: type[Exception], exc_val: Exception, exc_tb: TracebackType
    ) -> None:
        pass
