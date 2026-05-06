from enum import Enum


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
