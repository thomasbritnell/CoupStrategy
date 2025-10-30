import numpy as np
from enum import IntEnum
import copy

from constants import Rules

from action import CardType, ActionType

class CoupEnv:
    def __init__(self, num_players, seed: int | None = None):
        
        self.rng = np.random.default_rng(seed)
        self.num_players = num_players
        self.deck = []
        self.reset()
        
    def serializable_state(self):
        states = copy.deepcopy(self.player_states)
        
        for id,state in states.items():
            n = len(state["cards"])
            states[id]["cards"] = n
        
        return states

    def reset(self):

        self.deck.clear()

        #supply the deck with cards according to their frequency
        for card in list(CardType):
            for _ in range(3):
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
        
        if action_type == ActionType.INCOME:
            return lambda no_effect: self._mod_player_coins(player_id, change = Rules.INCOME_AMT)
            
        elif action_type == ActionType.FOREIGN_AID:
            return lambda no_effect: self._mod_player_coins(player_id, change = Rules.FOREIGN_AID_AMT)

        elif action_type == ActionType.COUP:
            def coup_function(no_effect):
                self._mod_player_coins(player_id, change = -Rules.COUP_COST)
                self.remove_player_card(target_player_id, killed_card)
            return coup_function
            
        elif action_type == ActionType.TAX:
            def tax_function(no_effect):
                if not no_effect:
                    self._mod_player_coins(player_id, change = Rules.TAX_AMT)
            return tax_function
            
        elif action_type == ActionType.ASSASSINATE:
            def assassinate_function(no_effect):
                self._mod_player_coins(player_id, change = -Rules.ASSASSINATE_COST)
                if not no_effect:
                    self.remove_player_card(target_player_id, killed_card)
            return assassinate_function

        elif action_type == ActionType.STEAL:
            def steal_function(no_effect):
                if not no_effect:
                    coins_to_steal = min(Rules.STEAL_AMT, self.player_states[target_player_id]["coins"])
                    self._mod_player_coins(target_player_id, change = -coins_to_steal)
                    self._mod_player_coins(player_id, change = coins_to_steal)
            return steal_function
            
        elif action_type == ActionType.EXCHANGE:
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
            return [ActionType.COUP]

        actions = list(ActionType)
        
        
        if state["coins"] < 7:
            actions.remove(ActionType.COUP)
            
            if state["coins"] < 3:
                actions.remove(ActionType.ASSASSINATE)
        
        return actions
    
    
    def get_targets(self, player_id:int) -> list[int]:
        return [id for id in self.player_states.keys() if id != player_id and self.player_states[id]["alive"]]

    #part of deck class?
    def _deal_card(self)-> int:
        assert(self.deck and len(self.deck) > 0), "Deck Empty or Not Yet Initialized"

        card = self.rng.choice(self.deck)
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

    