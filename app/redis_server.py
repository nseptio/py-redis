import asyncio

from commands import CommandRegistry
from state import ServerContext
from util import resp_decode


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
                command_parts = await resp_decode(reader)
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
