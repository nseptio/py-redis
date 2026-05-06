from dataclasses import dataclass
from typing import Self

from state import ServerContext
from util import to_integer

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
