import asyncio


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    while True:
        data = await reader.read(1024)
        if not data:
            break

        writer.write(b"+PONG\r\n")
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
