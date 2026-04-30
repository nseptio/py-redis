import asyncio
from enum import Enum
from typing import List, Optional

DATA = {}


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
            key, value = command_parts[1], command_parts[2]
            DATA[key] = value
            writer.write(b"+OK\r\n")
        elif command == b"GET":
            key = command_parts[1]
            value = DATA.get(key)
            bulk_string_prefix = RESPKind.BULK_STRING.value.encode()
            if value is None:
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
