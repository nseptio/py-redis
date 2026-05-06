from abc import ABC, abstractmethod
from typing import Self

from state import ServerContext


class RedisCommand(ABC):
    @abstractmethod
    def execute(self, context: ServerContext) -> bytes:
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    @abstractmethod
    def parse_args(cls, args: list[bytes]) -> Self:
        raise NotImplementedError("Subclasses must implement this method")
