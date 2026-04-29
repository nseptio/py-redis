import asyncio
from enum import Enum
from typing import Optional, List


class RESPKind(Enum):
    SIMPLE_STRING = "+"
    INTEGER = ":"
    BULK_STRING = "$"
    ARRAY = "*"
    ERROR = "-"


# *2
# $<len>
# ECHO <case-insensitive>
# $<len>
# <argument>

# *2\r\n    $4\r\n  ECHO\r\n    $3\r\n  hey\r\n
# ["ECHO", "hey"]

# for _ in range(count):
#     bulk_line = await reader.readuntil(b"\r\n")
#     if not bulk_line:
#         return None
#     bulk_kind = RESPKind(bulk_line[0:1].decode())
#     if bulk_kind != RESPKind.BULK_STRING:
#         raise ValueError("Expected bulk string in array")
#     length = int(bulk_line[1:-2])
#     data = await reader.readexactly(length + 2)  # Read data + \r\n
#     elements.append(data[:-2].decode())  # Remove \r\n


async def parse_resp(reader: asyncio.StreamReader) -> Optional[List[bytes]]:
    try:
        line = await reader.readuntil(b"\r\n")  # *2 \r\n
        if not line:
            return None

        kind = RESPKind(line[0:1].decode())  # *
        if kind == RESPKind.ARRAY:
            num_elements = int(line[1:-2])  # 2
            command_parts: List[bytes] = []

            for _ in range(num_elements):
                bulk_line = await reader.readuntil(b"\r\n")  # $4
                bulk_kind = RESPKind(bulk_line[0:1].decode())
                if bulk_kind != RESPKind.BULK_STRING:
                    raise ValueError("Expected bulk string in array")

                length = int(bulk_line[1:-2])  # 4
                string_data = await reader.readexactly(
                    length + 2
                )  # consume the trailing \r\n
                command_parts.append(string_data[:-2])  # remove trailing

            return command_parts
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

        command = command_parts[0].lower()
        if command == b"PING":
            # should handle simple string RESP, instead of `b'PING'`
            writer.write(b"+PONG\r\n")
        elif command == b"echo":
            argument = command_parts[1]
            kind = RESPKind.BULK_STRING.value.encode()
            response = kind + f"{len((argument))}\r\n".encode() + argument + b"\r\n"
            writer.write(response)
        else:
            writer.write(b"-ERR unknown command\r\n")
        await writer.drain()

    writer.close()
    await writer.wait_closed()


async def main():
    print("Starting Redis-like server on localhost:6379...")
    server = await asyncio.start_server(handle_client, "localhost", 6379)

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
