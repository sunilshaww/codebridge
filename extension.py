import asyncio
import json
import os
import uuid
from typing import Optional

WORKSPACE_ID = str(uuid.uuid4())[:8].upper()

async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    data = await reader.read(1024)
    message = data.decode()
    try:
        request = json.loads(message)
        if request.get("action") == "connect":
            if request.get("workspace_id") == WORKSPACE_ID:
                response = {"status": "connected", "message": f"Connected to workspace {WORKSPACE_ID}"}
            else:
                response = {"status": "error", "message": "Invalid workspace ID"}
        elif request.get("action") == "execute":
            response = {"status": "executed", "result": "Code executed"}
        else:
            response = {"status": "unknown"}
    except:
        response = {"status": "error", "message": "Invalid request"}
    
    writer.write(json.dumps(response).encode())
    await writer.drain()
    writer.close()

async def start_extension_server(port: int = 8765):
    server = await asyncio.start_server(handle_client, "0.0.0.0", port)
    print(f"Extension server running on port {port}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(start_extension_server())