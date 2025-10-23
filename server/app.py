import asyncio
import http
import json
import os
import numpy as np
import secrets
import signal

from websockets.asyncio.server import broadcast, serve

from './coupenv.py' import CoupEnv


class GameClient:
    
    def __init__(self, name, player_id, token, player_colour):
        self.name = name
        self.id = player_id
        self.rng = np.random.default_rng()
        self.token = token
        self.colour = player_colour
        
    
    def to_json(self):
        return {
            "name" : self.name,
            "id" : self.id,
            "colour" : self.colour
        }
    
    def ask_input(self,options:list):
        return self.rng.choice(options)
        

class CoupGame:
    
    colours = [
    "#E63946",  # red
    "#F1FAEE",  # off white
    "#A8DADC",  # light blue
    "#457B9D",  # steel blue
    "#1D3557",  # navy
    "#FFB703",  # amber
    "#FB8500",  # orange
    "#8E44AD",  # purple
    "#2ECC71",  # green
    "#F5B7B1",  # pink
    "#34495E",  # dark gray
    "#95A5A6",  # light gray
    ]
    
    def __init__(self):
        
        self.start_event = asyncio.Event()
        self.started = False
        self.clients = {}
        self.turn_events = {}
        self.num_players = 0
        self.turn_counter = 0
    
    def connect_player(self,player_name):
        
        session_token = secrets.token_urlsafe(10)
        player_id = self.num_players
        self.num_players+=1
        self.clients[player_id] = GameClient(player_name, player_id, session_token)
        self.turn_events[player_id] = asyncio.Event()
        
        return {"id": player_id, "token": session_token, "colour": colours[player_id]}
    
    def start_game(self):
        
        self.env = CoupEnv(self.num_players)
        self.turn_order = [i for i in range(self.num_players)]
        self.game_over = False
        self.turn_num = 0
        self.started = True
        self.start_event.set()
            
            
    
    def play(self,player,move):
        pass
        
    def get_player_info(self):
        ps = self.env.player_states()
        
        pi = ps.copy()
        
        #make the actual card values anonymous
        for p in pi:
            n = len(p["cards"])
            p["cards"] = n
        
        
        
    def winner(self):
        if self.env.is_terminal():
            return self.env.get_winner()
        else:
            return None
        
    


JOIN = {}
MAX_GAMES = 5

async def error(websocket, message):
    event = {
        "type": "error",
        "message": message
    }
    await websocket.send(json.dumps(event))

# async def replay(websocket, game):
    
#     for player, move in game.moves.copy():
#         event = {
#             "type" : "play",
#             "player" : player,
#             "move" : move
#         }
#         await websocket.send(json.dumps(event))
        
        
  # play event is the start of a turn
  # then whether or not it is needed, we need to get other player input
  # {"type" : "play", "player_id": player_id, }      
        
async def play(websocket, game, connected):
   
    #individual game loop here
    
    
    
    # wait for your turn via an event?
    # when its your turn, send the turn request 
    
    # async for message in websocket:
    #     event = json.loads(message)
    #     assert event["type"] == "play"
        
    #     move = event["move"]
        
    #     try:
    #         game.play(player, move)
    #     except ValueError as exc:
    #         await error(websocket, str(exc))
    #         continue

    #     event = {
    #         "type":"play",
    #         "player": player,
    #         "move":move
    #     }
    #     broadcast(connected, json.dumps(event))
        
        
        #if game is won logic here
        


async def start_game(websocket, game, connected):
    message = await websocket.recv()
    event = json.loads(message)
    
    assert event["type"] == "start_game"
    
    
    
    event = {
        "type" : "start_game",
        "num_players" : num_players
    }
    
    #send out the game information so the ui can setup properly
    broadcast(connected, json.dumps(event))
    
    #now the players are unblocked and the game starts
    game.start_game()
    
    
    
    

    

async def create(websocket, player_name):
    
    if len(JOIN) > MAX_GAMES:
        await error(websocket, "Max games on server reached. Try again later.")
        return
    
    game = CoupGame()
    player_info = game.connect_player(player_name)
    
    
    
    connected = {websocket}
    
    join_key = secrets.token_urlsafe(12)
    JOIN[join_key] = game, connected

    try:
        event = { #event sent to the host after they created the game
            "type": "init",
            "join": join_key
        }
        await websocket.send(json.dumps(event))
        
        await start_game(websocket, game, connected)
        
        
        await play(websocket, game, connected)
    finally:
        del JOIN[join_key]

async def join(websocket, join_key, player_name):
    try:
        game, connected = JOIN[join_key]
    except KeyError:
        await error(websocket, "Game not found.")
        return
    
    if game.started:
        await error(websocket, "Game already started.")
        return
    
    connected.add(websocket)
    try:
        #await replay(websocket, game)
        event = {
            "type": "init"
        }
        await websocket.send(json.dumps(event))
        
        await game.start_event.wait()
        
        await play(websocket, game, connected)
    finally:
        connected.remove(websocket)
        

async def handler(websocket):
    
    message = await websocket.recv()
    event = json.loads(message)
    assert event["type"] == "init"
    
    if "join" in event:
        await join(websocket, event["join"], event["player_name"])
    else:
        await create(websocket, event["player_name"])
        
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