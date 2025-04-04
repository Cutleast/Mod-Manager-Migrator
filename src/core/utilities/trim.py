"""
Copyright (c) Cutleast
"""


def trim_string(text: str, max_length: int = 100) -> str:
    """
    Returns raw representation (for eg. "\\n" instead of a line break) of a text
    trimmed to a specified number of characters.
    Appends "..." suffix if the text was longer than the specified length.

    Args:
        text (str): String to trim.
        max_length (int, optional): Maximum length of trimmed string. Defaults to 100.

    Returns:
        str: Trimmed string
    """

    if len(text) > max_length:
        trimmed_text = text[: max_length - 3] + "..."
        return f"{trimmed_text!r}"[1:-1]

    return f"{text!r}"[1:-1]
