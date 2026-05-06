import asyncio
from typing import List, Optional

from .encoder import RESPKind


async def resp_decode(reader: asyncio.StreamReader) -> Optional[List[bytes]]:
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
                    string_data = await reader.readexactly(length + 2)
                    command_parts.append(string_data[:-2])

                return command_parts
            case RESPKind.SIMPLE_STRING:
                return [(await reader.readuntil(b"\r\n"))[:-2]]
            case _:
                raise ValueError("Unsupported RESP type")
    except asyncio.LimitOverrunError:
        return None
    except asyncio.IncompleteReadError:
        return None
