# ShipWar
100% not BattleShip

## W.I.P.

This is a project I am working on to make a pygame recreation of a navy game, where you attmpt to blindly guess where on a grid the opponent has placed there ships, sending missles to these areas in an attempt to blow up all their ships before they can blow up all of yours. I am currently attempting to make this with `pygame` for the client side, and a `Websocket` server housed in a `docker` container, or just normally on your computer. This by default hosts on port `6363`

## Installation
In order for the program to work, at the moment, you will need `Python`, and `pygame`.
If your downloading on `MacOS` or a `Linux` distro, hopefully you know how to do that, cause I don't.
To download on `Windows 10+` run the following commands in your terminal.

### Basic
```
winget install -e --id Python.Python.3.13
```
```
pip install pygame
```
```
pip install websockets
```

#### If you want to house the server in a docker container:
```
winget install -e --id Docker.DockerCLI
```
Then go to the path of the application, and run the command:
```
PORT=1234 docker compose up -d
```
To turn off the server just type in the same path:
```
docker compose down
```

#### If you want to host on your own computer
Just run the `Server.py` file on your laptop, it will output the IP and ask you for a port number.
Enter any port number you want, and you can connect as long as you remember those two numbers.

Please Note: If you can't connect to the server after inputting the port, it is likely that you are already using the port for something.
Another Note: If you have mutiple IPs show up, then you can probably use any of them for connecting to the server, but you might want to check that.

##### Ports I Suggest
```
4444
```
```
1234
```
```
6363
```
```
8888
```

## Future
I hope to in the future, allow spectators to watch a match.

This will not be supporting `MacOS`, or an `IOS` of any kind, if you want to figure out how to set it up for that, good luck. 