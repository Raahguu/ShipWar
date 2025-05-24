import asyncio
import json
import websockets
import websockets.asyncio
import websockets.asyncio.server
import sys
import os

DEFAULT_PORT = 8765
MAX_PLAYERS = 2
connected_clients : list[websockets.asyncio.server.ServerConnection] = []

async def handle_client(socket : websockets.asyncio.server.ServerConnection):
    print("handeling client")
    global connected_clients

    if len(connected_clients) >= MAX_PLAYERS:
        await socket.send(json.dumps({"type": "error", "message": "Match full"}))
        await socket.close()
        print("Player attempted to connect, but match is full")
    
    connected_clients += [socket]
    player_id = len(connected_clients)
    await socket.send(json.dumps({"type": "welcome", "player": player_id}))
    print(f"Player {player_id} joined")

    try:
        while True:
            message = await socket.recv()
            data = json.loads(message)
            
            if data["type"] == "guess":
                #TODO: Actual hit detection, which would first requre ships to actually be placed somewhere first
                if data["position"] in [[i, i] for i in range(9)]: # temporary hit/miss code just for testing 
                    await socket.send(json.dumps({"type": "guess_result", "result": 2}))
                else: await socket.send(json.dumps({"type": "guess_result", "result": 1}))
                
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Player {player_id} disconnected")
        connected_clients.remove(socket)
        


async def start_server(port : int):
    if type(port) != int: raise TypeError(f"You must supply a an integer port number, not: {port}")
    print("Server up")
    async with websockets.asyncio.server.serve(handle_client, "localhost", port) as server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        if sys.argv[1] != "Docker": 1/0
        #this means the server is running in a docker container
        asyncio.run(start_server(DEFAULT_PORT))
    except:
        port = 0
        while True:
            port = input("What port would you like to host the server on: ")
            try: 
                port = int(port)
                if port < 1: 1/0
                break
            except: 
                print("The port needs to be an integer greater than 0")
        print(os.system('ipconfig | find "IPv4 Address"'))
        print(f"Port: {port}")
        asyncio.run(start_server(DEFAULT_PORT))
