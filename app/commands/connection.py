from dataclasses import dataclass
from typing import Self

from state import ServerContext
from util import to_simple_string

from .base import RedisCommand
from .registry import CommandRegistry


@CommandRegistry.register("PING")
class PingCommand(RedisCommand):
    def execute(self, context: ServerContext) -> bytes:
        return to_simple_string(b"PONG")

    @classmethod
    def parse_args(cls, args: list[bytes]) -> Self:
        if len(args) > 1:
            raise RuntimeError("PING command takes at most one argument")
        return cls()


@CommandRegistry.register("ECHO")
@dataclass(frozen=True)
class EchoCommand(RedisCommand):
    message: str

    def execute(self, context: ServerContext) -> bytes:
        return to_simple_string(self.message.encode())

    @classmethod
    def parse_args(cls, args: list[bytes]) -> Self:
        if len(args) != 1:
            raise RuntimeError("ECHO command requires exactly one argument")
        return cls(message=args[0].decode())
