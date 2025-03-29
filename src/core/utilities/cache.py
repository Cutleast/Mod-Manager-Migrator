"""
Copyright (c) Cutleast
"""

import functools
from typing import Callable


def cache[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """
    Wrapper for `functools.cache` to maintain Python >3.12 type annotations
    for static type checkers like mypy.

    Returns:
        Callable[P, R]: wrapped function
    """

    wrapped: Callable[P, R] = functools.cache(func)  # type: ignore[attr-defined]

    return wrapped
