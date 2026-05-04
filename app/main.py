import asyncio
from redis_server import RedisServer

async def main() -> None:
    print("Starting Redis-like server on localhost:6379...")
    server = RedisServer()
    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram stopped by user")