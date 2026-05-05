import asyncio
from typing import List, Optional

from commands.base import CommandRegistry
from server_context import ServerContext
from util.resp import RESPKind


class RedisServer:
    def __init__(self, host="localhost", port=6379):
        self.host = host
        self.port = port
        self.context = ServerContext()

    async def start(self):
        server = await asyncio.start_server(
            self._client_connected_cb, self.host, self.port
        )

        async with server:
            await server.serve_forever()

    async def _client_connected_cb(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        await self.handle_connection(reader, writer)

    async def handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        while True:
            try:
                command_parts = await self.resp_decode(reader)
                if not command_parts:
                    break
            except ConnectionResetError:
                print("Client disconnected")
                break
            except ValueError:
                writer.write(b"-ERR invalid command format\r\n")
                await writer.drain()
                continue

            try:
                command_func = CommandRegistry.parse_command(command_parts)
                response = command_func.execute(self.context)
                writer.write(response)
            except RuntimeError as e:
                writer.write(b"-ERR " + str(e).encode() + b"\r\n")

            await writer.drain()

        writer.close()
        await writer.wait_closed()

    async def resp_decode(self, reader: asyncio.StreamReader) -> Optional[List[bytes]]:
        try:
            kind = RESPKind(await reader.readexactly(1))
            match kind:
                case RESPKind.ARRAY:
                    num_elements = int((await reader.readuntil(b"\r\n"))[:-2])
                    command_parts: List[bytes] = []

                    for _ in range(num_elements):
                        bulk_kind = RESPKind(await reader.readexactly(1))
                        if bulk_kind != RESPKind.BULK_STRING:
                            raise ValueError("Expected bulk string in array")

                        length = int((await reader.readuntil(b"\r\n"))[:-2])
                        string_data = await reader.readexactly(
                            length + 2
                        )  # consume the trailing \r\n
                        command_parts.append(string_data[:-2])  # remove trailing \r\n

                    return command_parts
                case RESPKind.SIMPLE_STRING:
                    return [(await reader.readuntil(b"\r\n"))[:-2]]
                case _:
                    raise ValueError("Unsupported RESP type")
        except asyncio.LimitOverrunError:
            return None
        except asyncio.IncompleteReadError:
            return None
