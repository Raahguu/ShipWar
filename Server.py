import asyncio
import json
import websockets
import websockets.asyncio
import websockets.asyncio.server
import sys
import os

DEFAULT_PORT = 6363
MAX_PLAYERS = 2
global connected_clients
connected_clients : list[websockets.asyncio.server.ServerConnection] = []
global players
players : list = [None, None]

class DisconnectError(Exception): pass

def guess_result(reply : dict):
    if reply["position"] in [[i, i] for i in range(10)]:
        return 2
    return 1

async def client_listner(socket: websockets.asyncio.server.ServerConnection):
    global connected_clients, players
    player_id = connected_clients.index(socket)
    try:
        other_socket = connected_clients[player_id * -1 + 1]
    except: other_socket = None

    while socket in connected_clients:
        try:
            reply = json.loads(await socket.recv())
            if other_socket == None:
                try: other_socket = connected_clients[player_id * -1 + 1]
                except: pass
            print("Received:", reply)
            if reply["type"] == "username":
                players[player_id] = reply["name"]
                print(f"{reply["name"]} joined")
                print(players)
                if players[player_id * -1 + 1] != None:
                    await socket.send(json.dumps({"type": "username", "name": players[player_id * -1 + 1]}))
                    if other_socket != None:
                        await other_socket.send(json.dumps({"type":"username", "name": players[player_id]}))
            elif reply["type"] == "guess":
                result = guess_result(reply)
                await socket.send(json.dumps({"type": "guess_result", "position": reply["position"], "result": result}))
                if other_socket != None:
                    await other_socket.send(json.dumps({"type": "enemy_guess_result", "position": reply["position"], "result": result}))
            elif reply["type"] == "disconnection":
                print(f"{players[player_id]} disconnected")
                if other_socket != None:
                    other_socket.send(json.dumps({"type":"disconnection"}))
                raise DisconnectError
            elif reply["type"] == "error":
                print(reply["message"])
                return
            else:
                print(f"Unexpected message type: {reply['type']}")
                return
        except Exception as e:
            print(f"Error received from {players[player_id]}: {e}")
            raise e

async def handle_client(socket : websockets.asyncio.server.ServerConnection):
    global connected_clients
    global game_ready
    global players
    global guess
    global guess_sent

    #Check the number of players isn't already too many
    if len(connected_clients) >= MAX_PLAYERS:
        await socket.send(json.dumps({"type": "error", "message": "Match full"}))
        await socket.close()
        print("Player attempted to connect, but match is full")
    #Send the player a welcome message
    connected_clients.append(socket)
    player_id = len(connected_clients)
    await socket.send(json.dumps({"type": "welcome", "player": player_id}))
    try:
        asyncio.create_task(client_listner(socket))
    except Exception as e: raise e
    while True: await asyncio.sleep(1) 

async def start_server(port : int):
    if type(port) != int: raise TypeError(f"You must supply a an integer port number, not: {port}")
    print("Server up")
    async with websockets.asyncio.server.serve(handle_client, "localhost", port, ping_timeout=120) as server:
        while True:
            try:
                await server.serve_forever()
            except DisconnectError: 
                global players 
                players = [None, None]
                global connected_clients 
                connected_clients = []
                global game_ready
                game_ready.clear()
                global guess_sent
                guess_sent.clear()
                global guess
                guess = None
                

if __name__ == "__main__":
    global game_ready
    game_ready = asyncio.Event()

    global guess_sent
    guess_sent = asyncio.Event()

    global guess
    guess = None

    try:
        if sys.argv[1] != "Docker": 1/0
        #this means the server is running in a docker container
        asyncio.run(start_server(DEFAULT_PORT))
    except:
        port = 0
        while True:
            port = input("What port would you like to host the server on: ").strip()
            try: 
                if port == "":
                    port = 6363
                    break
                port = int(port)
                if port < 1: 1/0
                break
            except: 
                print("The port needs to be an integer greater than 0")
        ips = os.system('ipconfig | find "IPv4 Address"')
        if ips == 0: print(ips)
        else: print(os.system('ifconfig | grep inet"'))
        print(f"Port: {port}")
        asyncio.run(start_server(port))
        game_ready.clear()