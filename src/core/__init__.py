from typing import Dict, List
from PIL import Image
import base64
import io


from typing import Generic, TypeVar
from annotated_types import Not
from typing_extensions import Any, Optional


def str_to_bool(value: str) -> bool:
    """
    Convert a string to a boolean.
    Returns True if the string is 'true' (case-insensitive),
    False if the string is 'false' (case-insensitive).
    Raises a ValueError for any other value.
    """
    if value.lower() == "true":
        return True
    elif value.lower() == "false":
        return False
    else:
        raise ValueError(
            f"Cannot convert '{value}' to a boolean. Expected 'true' or 'false'."
        )


# Define a type variable
R = TypeVar("R")
E = TypeVar("E")


class Result(Generic[R]):
    """
    Generic class to represent the result of an operation that can either succeed or fail.
    Works like Rust's Result type.
    """

    @staticmethod
    def Ok(value: E = None) -> "Result[E]":
        return Result(value=value, error=None)

    @staticmethod
    def Err(error: Exception) -> "Result[Any]":
        return Result(value=None, error=error)

    def __init__(self, value: Optional[R] = None, error: Optional[Exception] = None):
        self.__value = value
        self.__error = error

    def is_ok(self) -> bool:
        return self.__value is not None or (
            self.__value is None and self.__error is None
        )

    def get_ok(self) -> R:
        if self.is_ok() is Not:
            raise ValueError("value not found")
        return self.__value  # type: ignore

    def is_error(self) -> bool:
        return self.__error is not None

    def get_error(self) -> Exception:
        if self.__error is None:
            raise ValueError("value not found")
        return self.__error

    def propagate_exception(self) -> "Result[Any]":
        if self.__error is None:
            raise ValueError("value not found")
        return self


def count_elements_in_array(values: List[str]) -> List[str]:
    values_map: Dict[str, int] = {}
    highest_count = 0
    key = ""
    for value in values:
        if values_map.get(value):
            values_map[value] = values_map[value] + 1
        else:
            values_map[value] = 1
        if values_map[value] > highest_count:
            highest_count = values_map[value]
            key = value
    if highest_count == 1:
        return values
    return [key]


def image_to_base64(image_path: str) -> str:
    if image_path.endswith("tif"):
        tif_image = Image.open(image_path)
        png_bytes = io.BytesIO()
        tif_image.save(png_bytes, format="PNG")
        png_bytes.seek(0)
        png_data = png_bytes.getvalue()
        return base64.b64encode(png_data).decode("utf-8")
    else:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        return base64.b64encode(image_data).decode("utf-8")
