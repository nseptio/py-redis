from typing import Callable, Type

from .base import RedisCommand


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
