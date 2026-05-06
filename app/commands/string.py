import time
from dataclasses import dataclass
from typing import Optional, Self

from state import RedisString, ServerContext
from util import to_bulk_string, to_null_bulk_string, to_simple_string

from .base import RedisCommand
from .registry import CommandRegistry


@CommandRegistry.register("SET")
@dataclass(frozen=True)
class SetCommand(RedisCommand):
    key: bytes
    value: bytes
    px: Optional[int] = None

    def execute(self, context: ServerContext) -> bytes:
        context.set(self.key, RedisString(self.value), self.px)
        return to_simple_string(b"OK")

    @classmethod
    def parse_args(cls, args: list[bytes]) -> Self:
        if len(args) < 2:
            raise RuntimeError("SET command requires at least two arguments")
        key, value, *options = args
        px = None
        if len(options) > 0:
            option = options[0].decode().upper()
            if option not in ("EX", "PX"):
                raise RuntimeError(
                    f"SET command: invalid option '{option}', expected EX or PX"
                )
            if len(options) < 2:
                raise RuntimeError(f"SET command: option '{option}' requires a value")
            ttl_value = int(options[1])
            now = time.time_ns() // 1_000_000  # current time in milliseconds
            match option:
                case "PX":
                    px = now + ttl_value
                case "EX":
                    px = now + ttl_value * 1_000  # convert seconds to milliseconds
                case _:
                    raise RuntimeError(
                        f"SET command: invalid option '{option}', expected EX or PX"
                    )
        return cls(key=key, value=value, px=px)


@CommandRegistry.register("GET")
@dataclass(frozen=True)
class GetCommand(RedisCommand):
    key: bytes

    def execute(self, context: ServerContext) -> bytes:
        value = context.get(self.key)
        if value is None:
            return to_null_bulk_string()

        if not isinstance(value, RedisString):
            raise RuntimeError("WRONGTYPE")

        return to_bulk_string(value.value)

    @classmethod
    def parse_args(cls, args: list[bytes]) -> Self:
        if len(args) != 1:
            raise RuntimeError("GET command requires exactly one argument")
        return cls(key=args[0])
