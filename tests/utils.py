"""
Copyright (c) Cutleast
"""

from collections.abc import Callable
from typing import Any, Optional


class Utils:
    """
    Class with utility methods to be used by tests.
    """

    @staticmethod
    def get_private_method[**P, R](
        obj: object, method_name: str, method_type: Callable[P, R]
    ) -> Callable[P, R]:
        """
        Gets a private method from an object.
        **Note that the method's signature is not validated!**

        Args:
            obj (object): The object to get the method from.
            method_name (str): The name of the method.
            method_type (Callable[P, R]):
                A method or function stub specifying the returned callable's signature.

        Raises:
            AttributeError: when the method is not found.
            TypeError: when the method is not callable

        Returns:
            Callable[P, R]: The method.
        """

        method_name = f"_{obj.__class__.__name__}__{method_name}"

        if not hasattr(obj, method_name):
            raise AttributeError(f"Method {method_name!r} not found!")

        field: Optional[Any] = getattr(obj, method_name, None)

        if not callable(field):
            raise TypeError(f"{method_name!r} ({type(field)}) is not callable!")

        method: Callable[P, R] = field

        return method

    @staticmethod
    def get_private_field[T](obj: object, field_name: str, field_type: type[T]) -> T:
        """
        Gets a private field from an object.

        Args:
            obj (object): The object to get the field from.
            field_name (str): The name of the field.
            field_type (type[T]): The type of the field.

        Raises:
            AttributeError: when the field is not found.
            TypeError: when the field is not of the specified type.

        Returns:
            T: The field value.
        """

        field_name = f"_{obj.__class__.__name__}__{field_name}"

        if not hasattr(obj, field_name):
            raise AttributeError(f"Field {field_name!r} not found!")

        field: Optional[Any] = getattr(obj, field_name, None)

        if not isinstance(field, field_type):
            raise TypeError(f"{field_name!r} ({type(field)}) is not a {field_type}!")

        return field
