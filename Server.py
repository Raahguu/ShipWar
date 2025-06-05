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
    connected_clients += [socket]
    player_id = len(connected_clients)
    await socket.send(json.dumps({"type": "welcome", "player": player_id}))
    #Get the players username
    try:
        message = json.loads(await socket.recv())
        if message["type"] != "username": 1/0
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
            await socket.send(json.dumps({"type": "enemy_guess_result", "result": 2}))
        else: await socket.send(json.dumps({"type": "enemy_guess_result", "result": 1}))
    #Rest of the game
    try:
        while game_ready.is_set():
            #Get the players guess
            message = await socket.recv()
            try:
                if message["type"] != "guess": 1/0
            except: 1/0
            data = json.loads(message)
            print(data)
            if data["type"] == "guess":
                #TODO: Actual hit detection, which would first requre ships to actually be placed somewhere first
                if data["position"] in [[i, i] for i in range(9)]: # temporary hit/miss code just for testing 
                    await socket.send(json.dumps({"type": "guess_result", "result": 2}))
                else: await socket.send(json.dumps({"type": "guess_result", "result": 1}))
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
                    await socket.send(json.dumps({"type": "enemy_guess_result", "result": 2}))
            else: await socket.send(json.dumps({"type": "enemy_guess_result", "result": 1}))
        await socket.send(json.dumps({"type": "disconnection"}))
    except websockets.exceptions.ConnectionClosed:
        print(f"Player {players[player_id - 1]} disconnected")
        connected_clients.remove(socket)

async def start_server(port : int):
    if type(port) != int: raise TypeError(f"You must supply a an integer port number, not: {port}")
    print("Server up")
    async with websockets.asyncio.server.serve(handle_client, "localhost", port) as server:
        await server.serve_forever()

if __name__ == "__main__":
    global game_ready
    game_ready = asyncio.Event()

    global guess_sent
    guess_sent = asyncio.Event()

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