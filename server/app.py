import asyncio
import json
import http
import os
import numpy as np
import secrets
import signal

from websockets.asyncio.server import broadcast, serve



from coupenv import CoupEnv

from action import ActionType, ReactionType, CardType, Action
    
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
        
        self.token_validation = {}
        self.num_players = 0
        self.turn_counter = 0
        
        self.player_ws = {}
        self.player_input_queues = {}
        
        self.player_meta_info = {}
    
    def connect_player(self,player_name,websocket):
        
        session_token = secrets.token_urlsafe(10)
        player_id = self.num_players
        self.num_players+=1
        
        player_colour = CoupGame.colours[player_id % len(CoupGame.colours)]
        
        
        self.token_validation[session_token] = player_id
        
        self.player_ws[player_id] = websocket
        self.player_input_queues[player_id] = asyncio.Queue()    
        
        self.player_meta_info[player_id] = {"colour": player_colour, "name": player_name} 
        
        return {"id": player_id, "token": session_token, "colour": player_colour, "name": player_name}
    
    def start_game(self):
        
        self.env = CoupEnv(self.num_players)
        self.turn_order = [i for i in range(self.num_players)]
        
        self._can_move = {id:False for id in self.player_meta_info.keys()}
        
        self.game_over = False
        self.turn_counter = 0
        self.started = True
        self.start_event.set()
            
        asyncio.create_task(self.run_game_loop())
    
    async def run_game_loop(self):
        print("game start")
        while not self.game_over:
            for player_id in self.turn_order:
                
                self._can_move[player_id]= True
                
                if self.env.is_terminal():
                    self.game_over = True
                    break
                
                await self.player_turn(player_id)
                
                self.env.update_player_lives()
                
                
                broadcast(self.player_ws.values(), json.dumps({"type":"state_update", "state": self.env.serializable_state()}))
                
                
                
            self.turn_counter+=1
        
        print("game over")
        
    async def player_turn(self, player_id):
        
        ws = self.player_ws[player_id] 
        
        await ws.send(json.dumps({"type": "input_request", "input_type": "action"}))
        
        
        q = self.player_input_queues[player_id]
        
        #todo something when the timeout happens
        try:
            msg = await asyncio.wait_for(q.get(),60.0)
        except TimeoutError:
            msg = {"type": "input_fulfill", "player": player_id ,"action": ActionType.INCOME, "target": None}
            await error(ws, "you timed out. Default action chosen.")
        
        self._can_move[player_id] = False
        
        assert(msg["type"] == "input_fulfill"),"didn't recieve input fulfill"
        
         
         
        
        #broadcast(self.player_ws.values(), json.dumps({"type":"turn_played", "msg": msg}))





    def can_move(self, id):
        assert id in self._can_move.keys(), "Player not found"
            
        
        return (self._can_move[id])
        
        
        
       

    
    
        
    


JOIN = {}
MAX_GAMES = 5

async def error(websocket, message):
    event = {
        "type": "error",
        "message": message
    }
    await websocket.send(json.dumps(event))


async def process_inputs(websocket, game, connected,id):
    
    
    async for message in websocket:
        
        event = json.loads(message)
        
        token = event["token"]
        
        if not (game.token_validation[token] == id):
            await error(websocket,"Invalid credential")
            continue
        
        if not game.can_move(id):
            await error(websocket, "Game not waiting for your input")
        else:
            game.player_input_queues[id].put_nowait(event)
            
        
        
        
        
        
        


async def start_game(websocket, game, connected):
    
    
    message = await websocket.recv()
    event = json.loads(message)
    
    assert event["type"] == "start_game"
    num_players = len(connected)
    
   
    
    event = {
        "type" : "start_game",
        "num_players" : num_players
    }
    
    #send out the game information so the ui can setup properly
    broadcast(connected, json.dumps(event | game.player_meta_info))
    
    #now the players are unblocked and the game starts
    game.start_game()
    

    

async def create(websocket, player_name):
    
    if len(JOIN) > MAX_GAMES:
        await error(websocket, "Max games on server reached. Try again later.")
        return
    
    game = CoupGame()
    player_info = game.connect_player(player_name,websocket)
    
    connected = {websocket}
    
    join_key = secrets.token_urlsafe(12)
    JOIN[join_key] = game, connected

    try:
        event = { #event sent to the host after they created the game
            "type": "init",
            "join": join_key
        }
        await websocket.send(json.dumps(event | player_info))
        
        await start_game(websocket, game, connected)
        
        
        await process_inputs(websocket, game, connected, player_info["id"])
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
    
    player_info = game.connect_player(player_name, websocket)
    
    connected.add(websocket)
    try:
        event = {
            "type": "init"
        }
        await websocket.send(json.dumps(event | player_info))
        
        await game.start_event.wait()
        
        await process_inputs(websocket, game, connected, player_info["id"])
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