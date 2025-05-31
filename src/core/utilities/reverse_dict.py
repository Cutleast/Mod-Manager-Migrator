"""
Copyright (c) Cutleast
"""


def reverse_dict[K, V](d: dict[K, V], /) -> dict[V, K]:
    """
    Swaps the keys and values of a dictionary.

    Args:
        d (dict[K, V]): The dictionary to reverse.

    Returns:
        dict[V, K]: The reversed dictionary.
    """

    return {v: k for k, v in d.items()}
