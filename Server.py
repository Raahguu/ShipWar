import asyncio
import json
import websockets
import websockets.asyncio
import websockets.asyncio.server
import sys
import os

DEFAULT_PORT = 6363
MAX_PLAYERS = 2
connected_clients : list[websockets.asyncio.server.ServerConnection] = []
players : list = [None, None]

class DisconnectError(Exception): pass

async def get_client_message(socket : websockets.ClientConnection, expected_type : str):
    reply = json.loads(await socket.recv())
    print(reply)
    try:
        reply["type"]
    except:
        print("Server Error: Corrupted Server Message didn't specify type attribute")
    if reply["type"] == expected_type:
        return reply
    else:
        if reply["type"] == "error": print(reply["message"])
        elif reply["type"] == "disconnection": 
            global connected_clients
            connected_clients[connected_clients.index(socket)].send(json.dumps({"type":"disconnection"}))
            raise DisconnectError
        else: print(f"Server Error: unexpected message of type {reply["type"]}")
        return False

async def handle_client(socket : websockets.asyncio.server.ServerConnection):
    print("handling client")
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
    #Get the players username
    try:
        message = await get_client_message(socket, "username")
        if message == False: 1/0
        players[player_id - 1] = message["name"]
    except:
        await socket.send(json.dumps({"type": "error", "message": "Invalid username"}))
        await socket.close()
        print("Player connected, but didn't provide name")

    print(f"Player {players[player_id - 1]} joined")
    #Wait till all players have joined
    if None not in players:
        game_ready.set()
    else:
        await game_ready.wait()
    await socket.send(json.dumps({"type": "username", "name": players[player_id * -1 + 2]}))

    #Actual game loop
    #If player is not player 1
    if player_id != 1:
        await guess_sent.wait()
        data = guess
        guess = None
        guess_sent.clear()
        if data["position"] in [[i, i] for i in range(9)]: # temporary hit/miss code just for testing 
            await socket.send(json.dumps({"type": "enemy_guess_result", "result": 2, "position": data["position"]}))
        else: await socket.send(json.dumps({"type": "enemy_guess_result", "result": 1, "position": data["position"]}))
    #Rest of the game
    try:
        while game_ready.is_set():
            #Get the players guess
            data = await get_client_message("guess")
            print("sending result")
            #TODO: Actual hit detection, which would first requre ships to actually be placed somewhere first
            if data["position"] in [[i, i] for i in range(9)]: # temporary hit/miss code just for testing 
                print("hit")
                await socket.send(json.dumps({"type": "guess_result", "result": 2, "position": data["position"]}))
            else: 
                print("miss")
                await socket.send(json.dumps({"type": "guess_result", "result": 1, "position": data["position"]}))
            print("result sent")
            #Send out that the guess occured
            guess = data
            guess_sent.set()
            await asyncio.sleep(1)
            #Get the other players guess
            await guess_sent.wait()
            data = guess
            guess = None
            guess_sent.clear()
            if data["position"] in [[i, i] for i in range(9)]: # temporary hit/miss code just for testing 
                    await socket.send(json.dumps({"type": "enemy_guess_result", "result": 2, "position": data["position"]}))
            else: await socket.send(json.dumps({"type": "enemy_guess_result", "result": 1, "position": data["position"]}))
        await socket.send(json.dumps({"type": "disconnection"}))
    except websockets.exceptions.ConnectionClosed:
        print(f"Player {players[player_id - 1]} disconnected")
        connected_clients.remove(socket)

async def start_server(port : int):
    if type(port) != int: raise TypeError(f"You must supply a an integer port number, not: {port}")
    print("Server up")
    async with websockets.asyncio.server.serve(handle_client, "localhost", port) as server:
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