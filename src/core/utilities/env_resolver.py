"""
Copyright (c) Cutleast
"""

import re
from os import getenv
from pathlib import Path
from typing import Optional, overload


def resolve_path(obj: Path, sep: tuple[str, str] = ("%", "%"), **vars: str) -> Path:
    """
    Resolves all (environment) variables in a path.

    Args:
        obj (Path): Path with (environment) variables
        sep (tuple[str, str], optional): Variable indicators, for eg. `("{", "}")`
        vars (str): Additional variables to resolve

    Returns:
        Path: Resolved real path
    """

    # Lower keys of additional vars (environment vars are already case-insensitive)
    norm_vars: dict[str, str] = {key.lower(): value for key, value in vars.items()}

    pattern: re.Pattern[str] = re.compile(f"^{sep[0]}([a-zA-Z0-9_]*){sep[1]}$")
    parts: list[str] = []
    for part in obj.parts:
        match: Optional[re.Match[str]] = pattern.match(part)

        if match is not None:
            var_name: str = match.groups()[0]
            var_value: Optional[str] = norm_vars.get(var_name.lower(), getenv(var_name))
            if var_value is not None:
                parts.append(var_value)
            else:
                parts.append(part)
        else:
            parts.append(part)

    return Path().joinpath(*parts)


def resolve_str(obj: str, sep: tuple[str, str] = ("%", "%"), **vars: str) -> str:
    """
    Resolves all (environment) variables in a string.

    Args:
        obj (str): String with (environment) variables
        sep (tuple[str, str], optional): Variable indicators, for eg. `("{", "}")`
        vars (str): Additional variables to resolve

    Returns:
        str: Resolved string
    """

    # Lower keys of additional vars (environment vars are already case-insensitive)
    norm_vars: dict[str, str] = {key.lower(): value for key, value in vars.items()}

    pattern: re.Pattern[str] = re.compile(f"{sep[0]}([a-zA-Z0-9_]*){sep[1]}")
    matches: list[re.Match[str]] = list(pattern.finditer(obj))
    for match in matches:
        var_name: str = match.groups()[0]
        var_value: Optional[str] = norm_vars.get(var_name.lower(), getenv(var_name))
        if var_value is not None:
            obj = obj.replace(f"%{var_name}%", var_value, 1)

    return obj


@overload
def resolve(obj: str, sep: tuple[str, str] = ("%", "%"), **vars: str) -> str:
    """
    Resolves all (environment) variables in a string.

    Args:
        obj (str): String with (environment) variables
        sep (tuple[str, str], optional): Variable indicators, for eg. `("{", "}")`
        vars (str): Additional variables to resolve

    Returns:
        str: String with resolved variables
    """


@overload
def resolve(obj: Path, sep: tuple[str, str] = ("%", "%"), **vars: str) -> Path:
    """
    Resolves all (environment) variables in a path.

    Args:
        obj (Path): Path with (environment) variables
        sep (tuple[str, str], optional): Variable indicators, for eg. `("{", "}")`
        vars (str): Additional variables to resolve

    Returns:
        Path: Resolved real path
    """


def resolve(
    obj: str | Path, sep: tuple[str, str] = ("%", "%"), **vars: str
) -> str | Path:
    if isinstance(obj, Path):
        return resolve_path(obj, sep, **vars)
    else:
        return resolve_str(obj, sep, **vars)
