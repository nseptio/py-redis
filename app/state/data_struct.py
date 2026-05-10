from dataclasses import dataclass
from typing import Optional, TypeAlias, Union


class RedisString:
    def __init__(self, value: bytes) -> None:
        self.value = value


class RedisList:
    def __init__(self) -> None:
        self.values: list[bytes] = []

    def rpush(self, value: bytes) -> None:
        self.values.append(value)

    def lpush(self, value: bytes) -> None:
        self.values.insert(0, value)

    def lpop(self) -> Optional[bytes]:
        if not self.values:
            return None
        return self.values.pop(0)


RedisDataStruct: TypeAlias = Union[RedisString, RedisList]


@dataclass
class RedisValue:
    data: RedisDataStruct
    expiry: Optional[int] = None
