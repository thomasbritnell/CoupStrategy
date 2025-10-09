import asyncio
import http
import json
import os
import secrets
import signal

from websockets.asyncio.server import broadcast, serve

PLAYER1 = "red"
PLAYER2 = "blue"


class GameStub:
    def __init__(self):
        self.moves = []
        self.winner = None
        self.turn_counter = 0
    
    def play(self,player:str,move):
        self.moves.append([[player,move]])
        self.turn_counter += 1
        
    def winner(self):
        if self.turn_counter < 10:
            return None
        else:
            return "red" 


JOIN = {}

async def error(websocket, message):
    event = {
        "type": "error",
        "message": message
    }
    await websocket.send(json.dumps(event))

async def replay(websocket, game):
    
    for player, move in game.moves.copy():
        event = {
            "type" : "play",
            "player" : player,
            "move" : move
        }
        await websocket.send(json.dumps(event))
        
async def play(websocket, game, player, connected):
    #indefinitely listens while websocket is connected for messages
    async for message in websocket:
        event = json.loads(message)
        assert event["type"] == "play"
        column = event["column"]
        
        try:
            move = game.play(player, column)
        except ValueError as exc:
            await error(websocket, str(exc))
            continue

        event = {
            "type":"play",
            "player": player,
            "move":column
        }
        broadcast(connected, json.dumps(event))
        
        if game.winner is not None:
            event = {
                "type":"win",
                "player": game.winner
            }
            broadcast(connected, json.dumps(event))

async def start(websocket):
    game = GameStub()
    connected = {websocket}
    
    join_key = secrets.token_urlsafe(12)
    JOIN[join_key] = game, connected

    try:
        event = {
            "type": "init",
            "join": join_key
        }
        await websocket.send(json.dumps(event))
        
        await play(websocket, game, PLAYER1, connected)
    finally:
        del JOIN[join_key]

async def join(websocket, join_key):
    try:
        game, connected = JOIN[join_key]
    except KeyError:
        await error(websocket, "Game not found.")
        return
    
    connected.add(websocket)
    try:
        await replay(websocket, game)
        await play(websocket, game, PLAYER2, connected)
    finally:
        connected.remove(websocket)
        

async def handler(websocket):
    
    message = await websocket.recv()
    event = json.loads(message)
    assert event["type"] == "init"
    
    if "join" in event:
        await join(websocket, event["join"])
    else:
        await start(websocket)
        
def health_check(connection, request):
    if request.path == "/healthz":
        return connection.respond(http.HTTPStates.OK, "OK\n")


async def main():
    port = "8001"
    async with serve(handler, "", port, process_request=health_check) as server:
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGTERM, server.close)
        await server.wait_closed()
    
if __name__ == "__main__":    
    asyncio.run(main())