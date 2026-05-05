from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Optional, Self, Type

from server_context import RedisString, ServerContext
from util.resp import toBulkString, toNullBulkString, toSimpleString


class RedisCommand(ABC):
    @abstractmethod
    def execute(self, context: ServerContext) -> bytes:
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    @abstractmethod
    def parse_args(cls, args: list[bytes]) -> Self:
        raise NotImplementedError("Subclasses must implement this method")


class CommandRegistry:
    _registry: dict[str, Type[RedisCommand]] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[Type[RedisCommand]], Type[RedisCommand]]:
        def wrapper(command_cls: Type[RedisCommand]) -> Type[RedisCommand]:
            cls._registry[name.upper()] = command_cls
            return command_cls

        return wrapper

    @classmethod
    def parse_command(cls, args: list[bytes]) -> RedisCommand:
        command_name, args = args[0].decode(), args[1:]
        command = cls._registry.get(command_name.upper())
        if not command:
            raise RuntimeError(f"Unknown command: {command_name}")
        return command.parse_args(args)


@CommandRegistry.register("PING")
class PingCommand(RedisCommand):
    def execute(self, context: ServerContext) -> bytes:
        return toSimpleString(b"PONG")

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
        return toSimpleString(self.message.encode())

    @classmethod
    def parse_args(cls, args: list[bytes]) -> Self:
        if len(args) != 1:
            raise RuntimeError("ECHO command requires exactly one argument")
        return cls(message=args[0].decode())


@CommandRegistry.register("SET")
@dataclass(frozen=True)
class SetCommand(RedisCommand):
    key: bytes
    value: bytes
    px: Optional[int] = None

    def execute(self, context: ServerContext) -> bytes:
        context.set(self.key, RedisString(self.value), self.px)
        return toSimpleString(b"OK")

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
            match option:
                case "PX":
                    px = ttl_value
                case "EX":
                    px = ttl_value * 1_000
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
            return toNullBulkString()

        if not isinstance(value, RedisString):
            raise RuntimeError("WRONGTYPE")

        return toBulkString(value.value)

    @classmethod
    def parse_args(cls, args: list[bytes]) -> Self:
        if len(args) != 1:
            raise RuntimeError("GET command requires exactly one argument")
        return cls(key=args[0])
