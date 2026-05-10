from dataclasses import dataclass
from typing import Self

from state import ServerContext
from util import to_integer
from util.encoder import to_array

from .base import RedisCommand
from .registry import CommandRegistry


@CommandRegistry.register("RPUSH")
@dataclass(frozen=True)
class RPushCommand(RedisCommand):
    key: bytes
    elements: list[bytes]

    def execute(self, context: ServerContext) -> bytes:
        length = context.rpush(self.key, self.elements)
        return to_integer(length)

    @classmethod
    def parse_args(cls, args: list[bytes]) -> Self:
        if len(args) < 2:
            raise RuntimeError("RPUSH command requires at least two arguments")
        return cls(key=args[0], elements=args[1:])


@CommandRegistry.register("LPUSH")
@dataclass(frozen=True)
class LPushCommand(RedisCommand):
    key: bytes
    elements: list[bytes]

    def execute(self, context: ServerContext) -> bytes:
        length = context.lpush(self.key, self.elements)
        return to_integer(length)

    @classmethod
    def parse_args(cls, args: list[bytes]) -> Self:
        if len(args) < 2:
            raise RuntimeError("LPUSH command requires at least two arguments")
        return cls(key=args[0], elements=args[1:])


@CommandRegistry.register("LRANGE")
@dataclass(frozen=True)
class LRangeCommand(RedisCommand):
    key: bytes
    start: int
    stop: int

    def execute(self, context: ServerContext) -> bytes:
        elements = context.lrange(self.key, self.start, self.stop)
        return to_array(elements)

    @classmethod
    def parse_args(cls, args: list[bytes]) -> Self:
        if len(args) != 3:
            raise RuntimeError("LRANGE command requires exactly three arguments")
        return cls(key=args[0], start=int(args[1]), stop=int(args[2]))


@CommandRegistry.register("LLEN")
@dataclass(frozen=True)
class LLenCommand(RedisCommand):
    key: bytes

    def execute(self, context: ServerContext) -> bytes:
        length = context.llen(self.key)
        return to_integer(length)

    @classmethod
    def parse_args(cls, args: list[bytes]) -> Self:
        if len(args) != 1:
            raise RuntimeError("LRANGE command requires exactly one arguments")
        return cls(key=args[0])
