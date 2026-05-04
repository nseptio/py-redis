from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Self, Type
from util.resp import toSimpleString


class RedisCommand(ABC):
    @abstractmethod
    def execute(self) -> bytes:
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
    def execute(self) -> bytes:
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

    def execute(self) -> bytes:
        return toSimpleString(self.message.encode())

    @classmethod
    def parse_args(cls, args: list[bytes]) -> Self:
        if len(args) != 1:
            raise RuntimeError("ECHO command requires exactly one argument")
        return cls(message=args[0].decode())


class SetCommand(RedisCommand):
    def execute(self) -> bytes:
        # The actual logic for setting the key-value pair will be handled in main.py
        return toSimpleString(b"OK")

    @classmethod
    def parse_args(cls, args: list[bytes]) -> Self:
        if len(args) < 2:
            raise RuntimeError("SET command requires at least two arguments")
        return cls()


# if command == b"SET":
#             _, key, value, *options = command_parts
#             STORAGE[key] = value
#             if len(options) > 1:
#                 option = options[0].upper()
#                 now = time.time_ns() // 1_000_000
#                 if option == b"EX":
#                     ttl = int(options[1]) * 1_000
#                     EXPIRES_STORAGE[key] = now + ttl
#                 elif option == b"PX":
#                     ttl = int(options[1])
#                     EXPIRES_STORAGE[key] = now + ttl
#             writer.write(b"+OK\r\n")
#         elif command == b"GET":
#             key = command_parts[1]
#             value = STORAGE.get(key)
#             bulk_string_prefix = RESPKind.BULK_STRING.value.encode()
#             if value is None:
#                 writer.write(bulk_string_prefix + b"-1\r\n")
#                 continue
#             ttl = EXPIRES_STORAGE.get(key)
#             if ttl is not None:
#                 if time.time_ns() // 1_000_000 >= ttl:
#                     writer.write(bulk_string_prefix + b"-1\r\n")
#                     continue
#             response = (
#                 bulk_string_prefix + f"{len(value)}\r\n".encode() + value + b"\r\n"
#             )
#             writer.write(response)
#         else:
#             writer.write(b"-ERR unknown command\r\n")
