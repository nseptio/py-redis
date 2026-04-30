import asyncio
import time
from enum import Enum
from typing import List, Optional

STORAGE: dict[bytes, bytes] = {}
EXPIRES_STORAGE: dict[bytes, int] = {}


class RESPKind(Enum):
    SIMPLE_STRING = "+"
    INTEGER = ":"
    BULK_STRING = "$"
    ARRAY = "*"
    ERROR = "-"


async def parse_resp(reader: asyncio.StreamReader) -> Optional[List[bytes]]:
    try:
        line = await reader.readuntil(b"\r\n")
        if not line:
            return None

        kind = RESPKind(line[0:1].decode())
        if kind == RESPKind.ARRAY:
            num_elements = int(line[1:-2])
            command_parts: List[bytes] = []

            for _ in range(num_elements):
                bulk_line = await reader.readuntil(b"\r\n")
                bulk_kind = RESPKind(bulk_line[0:1].decode())
                if bulk_kind != RESPKind.BULK_STRING:
                    raise ValueError("Expected bulk string in array")

                length = int(bulk_line[1:-2])
                string_data = await reader.readexactly(
                    length + 2
                )  # consume the trailing \r\n
                command_parts.append(string_data[:-2])  # remove trailing

            return command_parts
        elif kind == RESPKind.SIMPLE_STRING:
            return [line[1:-2]]
        else:
            raise ValueError("Unsupported RESP type")
    except asyncio.IncompleteReadError:
        return None


async def handle_client(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter
) -> None:
    while True:
        command_parts = await parse_resp(reader)
        if not command_parts:
            break

        command = command_parts[0].upper()
        if command == b"PING":
            writer.write(b"+PONG\r\n")
        elif command == b"ECHO":
            argument = command_parts[1]
            bulk_string_prefix = RESPKind.BULK_STRING.value.encode()
            response = (
                bulk_string_prefix
                + f"{len(argument)}\r\n".encode()
                + argument
                + b"\r\n"
            )
            writer.write(response)
        elif command == b"SET":
            _, key, value, *options = command_parts
            STORAGE[key] = value
            if len(options) > 0:
                option = options[0].upper()
                if option == b"EX":
                    ttl = int(time.time()) + int(option[1])
                    EXPIRES_STORAGE[key] = ttl
                elif option == b"PX":
                    ttl = time.time_ns() // 1_000_000 + int(option[1])
                    EXPIRES_STORAGE[key] = ttl
            writer.write(b"+OK\r\n")
        elif command == b"GET":
            key = command_parts[1]
            value = STORAGE.get(key)
            bulk_string_prefix = RESPKind.BULK_STRING.value.encode()
            if value is None:
                writer.write(bulk_string_prefix + b"-1\r\n")
                return
            ttl = EXPIRES_STORAGE.get(key)
            if ttl is not None:
                if time.time_ns() > ttl:
                    writer.write(bulk_string_prefix + b"-1\r\n")
                    return
            response = (
                bulk_string_prefix + f"{len(value)}\r\n".encode() + value + b"\r\n"
            )
            writer.write(response)
        else:
            writer.write(b"-ERR unknown command\r\n")
        await writer.drain()

    writer.close()
    await writer.wait_closed()


async def main() -> None:
    print("Starting Redis-like server on localhost:6379...")
    server = await asyncio.start_server(handle_client, "localhost", 6379)

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
