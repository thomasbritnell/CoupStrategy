import numpy as np
from enum import IntEnum

class Card(IntEnum):
    DUKE = 0
    ASSA = 1
    CAPT = 2
    AMBA = 3
    CONT = 4
    
    def __str__(self):
        return self.name
    
class Actions(IntEnum):
    INCOME = 0
    FOREIGN_AID = 1
    COUP = 2
    TAX = 3
    ASSASSINATE = 4
    STEAL = 5
    EXCHANGE = 6
    
    def __str__(self):
        return self.name

class Counteractions(IntEnum):
    BLOCK_STEAL = 7
    BLOCK_ASSASSINATE = 8
    BLOCK_FOREIGN_AID = 9      

class Rules:
    STARTING_COINS = 2
    INCOME_AMT = 1
    FOREIGN_AID_AMT = 2
    TAX_AMT = 3
    STEAL_AMT = 2
    COUP_COST = 7
    ASSASSINATE_COST = 3
    
    
class Action_Response(IntEnum):
    PASS = 0
    CHALLENGE = 1
    COUNTERACT = 2
    
    def __str__(self):
        return self.name

necessary_card_for_action = {Actions.TAX : Card.DUKE, Actions.ASSASSINATE: Card.ASSA, Actions.STEAL: Card.CAPT, Actions.EXCHANGE: Card.AMBA}
necessary_card_for_counteraction = {Counteractions.BLOCK_FOREIGN_AID : [Card.DUKE], Counteractions.BLOCK_ASSASSINATE: [Card.CONT], Counteractions.BLOCK_STEAL: [Card.CAPT,Card.AMBA]}

action_counteraction_map = {Actions.STEAL: Counteractions.BLOCK_STEAL, Actions.ASSASSINATE : Counteractions.BLOCK_ASSASSINATE}



DECK_LAYOUT = {
    Card.DUKE : 3,
    Card.ASSA : 3,
    Card.CAPT : 3,
    Card.AMBA : 3,
    Card.CONT : 3
}

ALL_ACTIONS = list(Actions)

INCONTESTABLE_ACTIONS = [Actions.INCOME, Actions.COUP]






# class PlayerState:
#     def __init__(self,id):
#         self.id = id
#         self.coins = 0
#         self.cards = []
        
#     def give_card(self,card):
#         self.cards.append(card)
        
#     def __str__(self):
#         return f"Player {self.id}"
        
# class PlayerState:
#     def __init__(self, coins:int = 2, card_1:Card, card_2:Card):
#         self.coins = coins
#         self.cards = [card_1, card_2]
#         self.alive = True
    
#     def is_alive(self) -> bool:
#         return self.alive

#     def num_cards(self) -> int:
#         return len(self.cards)
    
#     def kill(self):
#         assert(not self.alive), "Player is already dead"
#         self.alive = False

#     def remove_card(self, card:Card):
#         assert(card in self.cards), "Player doesn't have that card"
#         self.cards.remove(card)
        
#     def add_card(self, card:Card):
#         assert(self.num_cards() < 2), "Player has too many cards"
#         self.cards.append(card)
        
#     def mod_coins(self, diff:int):
#         new_total = diff + self.coins
#         assert(new_total >= 0), "Player cannot go below 0 coins"
#         self.coins = new_total

    

class CoupEnv:
    def __init__(self, num_players: int = 3, seed: int | None = None):
        
        self.rng = np.random.default_rng(seed)
        self.num_players = num_players
        self.deck = []
        self.reset()

    def reset(self):

        self.deck.clear()

        #supply the deck with cards according to their frequency
        for card,freq in DECK_LAYOUT.items():
            for _ in range(freq):
                self.deck.append(card)
        
        self.player_states = {}

        #dole each player two cards and two coins to start the game
        for i in range(self.num_players):

            card_1 = self._deal_card()
            card_2 = self._deal_card()
            
            self.player_states[i] = {
                "coins" : Rules.STARTING_COINS,
                "cards" : [card_1, card_2],
                "alive" : True
            }
   
    
    def apply_action(self, action, no_effect=False):
        #action should be {"player_id": id, "action_type" : int, "target_player_id": None|int, "new_cards": None|list[int]}
        
        action_function = self._get_action_function(action)
        
        action_function(no_effect)

    #action function should already have all the info it needs, and is just applying it
    # ie for assassinate it should remove the revealed card from the target player
    # for steal it should facillitate the money exchange
    # for exchange it should give the player the cards they want
    def _get_action_function(self, action):

        action_type = action["action_type"]
        player_id = action["player_id"]
        target_player_id = action["target_player_id"]
        new_cards = action["new_cards"]
        killed_card = action["killed_card"]
        
        if action_type == Actions.INCOME:
            return lambda no_effect: self._mod_player_coins(player_id, change = Rules.INCOME_AMT)
            
        elif action_type == Actions.FOREIGN_AID:
            return lambda no_effect: self._mod_player_coins(player_id, change = Rules.FOREIGN_AID_AMT)

        elif action_type == Actions.COUP:
            def coup_function(no_effect):
                self._mod_player_coins(player_id, change = -Rules.COUP_COST)
                self.remove_player_card(target_player_id, killed_card)
            return coup_function
            
        elif action_type == Actions.TAX:
            def tax_function(no_effect):
                if not no_effect:
                    self._mod_player_coins(player_id, change = Rules.TAX_AMT)
            return tax_function
            
        elif action_type == Actions.ASSASSINATE:
            def assassinate_function(no_effect):
                self._mod_player_coins(player_id, change = -Rules.ASSASSINATE_COST)
                if not no_effect:
                    self.remove_player_card(target_player_id, killed_card)
            return assassinate_function

        elif action_type == Actions.STEAL:
            def steal_function(no_effect):
                if not no_effect:
                    coins_to_steal = min(Rules.STEAL_AMT, self.player_states[target_player_id]["coins"])
                    self._mod_player_coins(target_player_id, change = -coins_to_steal)
                    self._mod_player_coins(player_id, change = coins_to_steal)
            return steal_function
            
        elif action_type == Actions.EXCHANGE:
            def exchange_function(no_effect):
                if not no_effect:
                    self.player_states[player_id]["cards"] = new_cards
            return exchange_function            
        
        else:
            raise Exception("invalid input")    
            
        
            #part of player state class
    def _mod_player_coins(self, player_id, change):
        if (self.player_states[player_id]["coins"] + change) < 0:
            raise Exception("action invalid- coins goes below 0")
        
        self.player_states[player_id]["coins"] += change
        # part of player state class
    def give_player_new_card(self, player_id):
        
        assert(len(self.player_states[player_id]["cards"]) < 2), "Player has too many cards" 
        
        new_card = self._deal_card()

        self.player_states[player_id]["cards"].append(new_card)
        
    def remove_player_card(self, player_id, card):
        
        self.player_states[player_id]["cards"].remove(card)

    
    #part of env class is fine 
    def _get_legal_actions(self, player_id: int) -> list[int]:
        """Return list of legal actions for the given player, considering coins and board state."""
        state = self.player_states[player_id]

        if state["coins"] >= 10:
            return [Actions.COUP]

        actions = ALL_ACTIONS.copy()
        
        
        if state["coins"] < 7:
            actions.remove(Actions.COUP)
            
            if state["coins"] < 3:
                actions.remove(Actions.ASSASSINATE)
        
        return actions
    
    
    def get_targets(self, player_id:int) -> list[int]:
        return [id for id in self.player_states.keys() if id != player_id and self.player_states[id]["alive"]]

#part of deck class?
    def _deal_card(self)-> int:
        assert(self.deck and len(self.deck) > 0), "Deck Empty or Not Yet Initialized"

        card = Card(self.rng.choice(self.deck))
        self.deck.remove(card)

        return card
        
        #part of player state class 
    def update_player_lives(self):
        for id,player in self.player_states.items():
            if (len(player["cards"]) == 0) and (player["alive"]):
                self.player_states[id]["alive"] = False
                print(f"player {id} died")
        

    def is_terminal(self) -> bool:

        #check that all but one player is dead
        one_player_alive = False
        
        for state in self.player_states.values():
            
            if one_player_alive and state['alive']:
                return False
            
            if state["alive"]:
                one_player_alive = True
        
        return True
            
            
        """Check if the game is over."""
        
    def get_winner(self) -> int|None:
        assert(self.is_terminal()), "Game not won yet"
        
        
        for id,state in self.player_states.items():
            if state['alive']:
                return id
            
        return None

    