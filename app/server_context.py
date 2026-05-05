import time
from dataclasses import dataclass
from typing import Optional, TypeAlias, Union


class RedisString:
    def __init__(self, value: bytes) -> None:
        self.value = value


class RedisList:
    def __init__(self) -> None:
        self.values = []

    def rpush(self, value: bytes) -> None:
        self.values.append(value)

    def lpush(self, value: bytes) -> None:
        self.values.insert(0, value)


RedisDataStruct: TypeAlias = Union[RedisString, RedisList]


@dataclass
class RedisValue:
    data: RedisDataStruct
    expiry: Optional[int] = None


class ServerContext:
    def __init__(self) -> None:
        self._kv_store: dict[bytes, RedisValue] = {}

    def set(
        self, key: bytes, value: RedisDataStruct, expiry: Optional[int] = None
    ) -> None:
        self._kv_store[key] = RedisValue(data=value, expiry=expiry)

    def get(self, key: bytes) -> Optional[RedisDataStruct]:
        value = self._kv_store.get(key)
        if value is None:
            return None
        if value.expiry and (time.time_ns() // 1_000) > value.expiry:
            del self._kv_store[key]
            return None
        return value.data
