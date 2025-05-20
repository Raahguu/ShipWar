import asyncio
import json
import websockets
import websockets.asyncio
import websockets.asyncio.server

DEFAULT_PORT = 8765
MAX_PLAYERS = 2
connected_clients : list[websockets.ServerConnection] = []

async def handle_client(socket : websockets.ServerConnection):
    global connected_clients

    if len(connected_clients) >= MAX_PLAYERS:
        await socket.send(json.dumps({"type": "error", "message": "Match full"}))
        await socket.close()
    
    connected_clients += [socket]
    player_id = len(connected_clients)
    await socket.send(json.dumps({"type": "welcome", "player": player_id}))

    try:
        while True:
            message = await socket.recv()
            data = json.loads(message)

            for client in connected_clients:
                if client != socket:
                    await client.send(json.dumps({
                        "type": "forward",
                        "from": player_id,
                        "payload": data
                    }))
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Player {player_id} disconnected")
        connected_clients.remove(socket)
        


async def start_server(port : int):
    if type(port) != int: raise TypeError(f"You must supply a an integer port number, not: {port}")
    async with websockets.asyncio.server.serve(handle_client, "localhost", port) as server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(start_server(DEFAULT_PORT))