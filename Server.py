import asyncio
import json
import websockets
import websockets.asyncio
import websockets.asyncio.server
import sys
import os

def guess_result(reply : dict):
    if reply["position"] in [[i, i] for i in range(10)]:
        return 2
    return 1

async def disconnect(player_id : int):
    global players
    global connected_clients
    print(f"{players[player_id]} Disconnected")
    try: other_socket = connected_clients[player_id * -1 + 1]
    except: other_socket = None
    if other_socket != None: await other_socket.send(json.dumps({"type":"disconnection"}))
    
    players[player_id] = None
    connected_clients = []

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
                await disconnect(player_id)
                return
            elif reply["type"] == "error":
                print(reply["message"])
                return
            else:
                print(f"Unexpected message type: {reply['type']}")
                return
        except websockets.exceptions.ConnectionClosedError:
            await disconnect(player_id)
            return
        except websockets.exceptions.ConnectionClosedOK:
            await disconnect(player_id)
            return
        except Exception as e:
            print(f"Error received from {players[player_id]}: {e}")
            raise e

async def handle_client(socket : websockets.asyncio.server.ServerConnection):
    global connected_clients
    global players

    #Check the number of players isn't already too many
    if len(connected_clients) >= MAX_PLAYERS:
        await socket.send(json.dumps({"type": "error", "message": "Match full"}))
        await socket.close()
        print("Client attempted to connect, but match is full")
        return
    #Send the player a welcome message
    connected_clients.append(socket)
    player_id = len(connected_clients)
    await socket.send(json.dumps({"type": "welcome", "player": player_id}))

    asyncio.create_task(client_listner(socket))
    while socket in connected_clients: await asyncio.sleep(1) 

async def start_server(port : int):
    if type(port) != int: raise TypeError(f"You must supply a an integer port number, not: {port}")
    print("Server up")
    async with websockets.asyncio.server.serve(handle_client, "localhost", port) as server:
        await server.serve_forever()
                

if __name__ == "__main__":
    DEFAULT_PORT = 6363
    MAX_PLAYERS = 2
    global connected_clients
    connected_clients : list[websockets.asyncio.server.ServerConnection] = []
    global players
    players : list = [None, None]

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