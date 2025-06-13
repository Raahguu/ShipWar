import asyncio
import json
import websockets
import websockets.asyncio
import websockets.asyncio.server
import sys
import os

def guess_result(reply : dict, index : int) -> int:
    if reply["type"] != "guess": return 0

    global players_ships
    opponents_ships = players_ships[1 - index]
    for ship_locations in opponents_ships:
        for location in ship_locations:
            if location[:2] == reply["position"]: 
                location[-1] = 1
                return 2 # the result was a hit
    return 1

def check_for_sinking(index : int) -> list[list[int, int]] | None:
    global players_ships
    opponents_ships = players_ships[1 - index]
    for ship in opponents_ships:
        if sum([location[2] for location in ship]) == len(ship):
            players_ships[1 - index].remove(ship)
            return ship
    
async def send_guess_result(socket : websockets.asyncio.server.ServerConnection, other_socket : websockets.asyncio.server.ServerConnection, position : list[int, int], result : int):
    await socket.send(json.dumps({"type": "guess_result", "position": [int(i) for i in position], "result": result}))
    if other_socket != None:
        await other_socket.send(json.dumps({"type": "enemy_guess_result", "position": [int(i) for i in position], "result": result}))

def ship_handling(index : int, reply : dict):
    if reply["type"] != "ships": return False

    global players_ships
    reply_with_hit_record = []
    for ship in reply["message"]:
        for location in ship:
            location.append(0)
        reply_with_hit_record.append(ship)
    players_ships[index] = reply_with_hit_record

async def disconnect(player_id : int):
    global players
    global connected_clients
    print(f"{players[player_id]} Disconnected")
    try: other_socket = connected_clients[1 - player_id]
    except: other_socket = None
    if other_socket != None: await other_socket.send(json.dumps({"type":"disconnection"}))
    
    players[player_id] = None
    connected_clients = []

    global players_ships
    players_ships = [None, None]

    global game_over
    game_over = False

async def client_listner(socket: websockets.asyncio.server.ServerConnection):
    global connected_clients, players, players_ships, game_over
    player_id = connected_clients.index(socket)
    try:
        other_socket = connected_clients[1 - player_id]
    except: other_socket = None

    while socket in connected_clients:
        try:
            reply = json.loads(await socket.recv())
            if other_socket == None:
                try: other_socket = connected_clients[1 - player_id]
                except: pass
            print("Received:", reply)
            if reply["type"] == "username":
                players[player_id] = reply["name"]
                print(f"{reply["name"]} joined")
                if players[1 - player_id] != None:
                    await socket.send(json.dumps({"type": "username", "name": players[1 - player_id]}))
                    if other_socket != None:
                        await other_socket.send(json.dumps({"type":"username", "name": players[player_id]}))
            elif reply["type"] == "ships": 
                ship_handling(player_id, reply)
            elif reply["type"] == "guess":
                result = guess_result(reply, player_id)
                if result == 2: 
                    sinking = check_for_sinking(player_id)
                    if sinking != None:
                        for i in sinking:
                            await send_guess_result(socket, other_socket, i[:2], 3)
                        continue
                await send_guess_result(socket, other_socket, reply["position"], result)
            elif reply["type"] == "disconnection":
                if game_over: return
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
    global players_ships

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
    while socket in connected_clients and None in players_ships: await asyncio.sleep(1)
    print("!!! 'players_ships' does not contain None !!!")
    while socket in connected_clients and players_ships[0] != [] and players_ships[1] != []: await asyncio.sleep(1)
    print("Checking who won")
    print(players_ships)
    if players_ships[player_id - 1] == []: await socket.send(json.dumps({"type": "done", "result": 0})); print("Lost message")
    if players_ships[2 - player_id] == []: await socket.send(json.dumps({"type": "done", "result": 1})); print("Win message")

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
    global players_ships
    players_ships : list[list[list[list[int, int]]]] = [None, None]
    global game_over
    game_over = False

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