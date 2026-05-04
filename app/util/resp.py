from enum import Enum


class RESPKind(Enum):
    SIMPLE_STRING = b"+"
    INTEGER = b":"
    BULK_STRING = b"$"
    ARRAY = b"*"
    ERROR = b"-"

def toSimpleString(s: bytes) -> bytes:
    return RESPKind.SIMPLE_STRING.value + s + b"\r\n"

def toBulkString(s: bytes) -> bytes:
    return RESPKind.BULK_STRING.value + str(len(s)).encode() + b"\r\n" + s + b"\r\n"