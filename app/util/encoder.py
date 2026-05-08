from enum import Enum
from typing import Optional


class RESPKind(Enum):
    SIMPLE_STRING = b"+"
    INTEGER = b":"
    BULK_STRING = b"$"
    ARRAY = b"*"
    ERROR = b"-"


def to_simple_string(s: bytes) -> bytes:
    return RESPKind.SIMPLE_STRING.value + s + b"\r\n"


def to_bulk_string(s: bytes) -> bytes:
    return RESPKind.BULK_STRING.value + str(len(s)).encode() + b"\r\n" + s + b"\r\n"


def to_null_bulk_string() -> bytes:
    return RESPKind.BULK_STRING.value + b"-1" + b"\r\n"


def to_integer(i: int) -> bytes:
    return RESPKind.INTEGER.value + str(i).encode() + b"\r\n"


def to_array(elements: Optional[list[bytes]]) -> bytes:
    if elements is None or len(elements) == 0:
        return RESPKind.ARRAY.value + b"0" + b"\r\n"
    result = RESPKind.ARRAY.value + str(len(elements)).encode() + b"\r\n"
    for element in elements:
        result += to_bulk_string(element)
    return result
