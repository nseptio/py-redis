import time
from typing import Optional

from state import RedisDataStruct, RedisList, RedisString, RedisValue


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
        if value.expiry and (time.time_ns() // 1_000_000) > value.expiry:
            del self._kv_store[key]
            return None
        return value.data

    def rpush(self, key: bytes, element: list[bytes]) -> int:
        val = self._kv_store.get(key)
        if val is not None and isinstance(val.data, RedisString):
            raise RuntimeError("WRONGTYPE Operation against a key holding")
        if val is None:
            val = RedisValue(data=RedisList())
            self._kv_store[key] = val

        if isinstance(val.data, RedisList):
            for i in element:
                val.data.rpush(i)
            return len(val.data.values)

        return -1
