# ShipWar
100% not BattleShip

## W.I.P.

This is a project I am working on to make a pygame recreation of a navy game, where you attmpt to blindly guess where on a grid the opponent has placed there ships, sending missles to these areas in an attempt to blow up all their ships before they can blow up all of yours. I am currently attempting to make this with `pygame` for the client side, and a `Websocket` server housed in a `docker` container.

## Installation
In order for the program to work, at the moment, you will need `Python`, and `pygame`.
If your downloading on `MacOS` or a `Linux` distro, hopefully you know how to do that, cause I don't.
To download on `Windows 10+` run the following commands in your terminal.

```
winget install -e --id Python.Python.3.13
```
```
pip install pygame
```
```
pip install websockets
```

If you want to house the server on your device:
```
winget install -e --id Docker.DockerCLI
```
Then go to the path of the application, and run the command:
```
docker compose up -d
```
To turn off the server just type in the same path:
```
docker compose down
```

## Future
I hope to in the future, allow spectators to watch a match, and allow for servers to be hosted locally on ones device rather than in a docker container.
This will not be supporting `MacOS`, or and `IOS` of any kind, if you want to figure out how to set it up for that, good luck. 
