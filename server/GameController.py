from "./coupenv.py" import CoupEnv



necessary_card_for_action = {Action.TAX : Card.DUKE, Action.ASSASSINATE: Card.ASSA, Action.STEAL: Card.CAPT, Action.EXCHANGE: Card.AMBA}
necessary_card_for_counteraction = {Counteraction.BLOCK_FOREIGN_AID : [Card.DUKE], Counteraction.BLOCK_ASSASSINATE: [Card.CONT], Counteraction.BLOCK_STEAL: [Card.CAPT,Card.AMBA]}

action_counteraction_map = {Action.STEAL: Counteraction.BLOCK_STEAL, Action.ASSASSINATE : Counteraction.BLOCK_ASSASSINATE}


INCONTESTABLE_ACTIONS = [Action.INCOME, Action.COUP]



def log(func):
        def wrapper(*args, **kwargs):
            print(f"[LOG] Calling {func.__name__} with args={args}, kwargs={kwargs}")
            result = func(*args, **kwargs)
            print(f"[LOG] {func.__name__} returned {result}")
            return result
        return wrapper
    
    
class GameClient:
    
    MAX_ATTEMPTS = 10
    
    def __init__(self, is_cpu = True):
        self.is_cpu = is_cpu
        self.rng = None
        if self.is_cpu:
            self.rng = np.random.default_rng()
    
    
    
    def ask_input(self,options:list):
        return self.rng.choice(options)
        
            
   
        
      
    
class GameController:
    
    def __init__(self, num_players=3):
        self.num_players = num_players
        self.env = CoupEnv(num_players)
        self.reset()
    
    def reset(self): 
        self.turn_order = [i for i in range(self.num_players)]
        self.game_over = False
        self.turn_num = 0
        self.clients = {player_id: GameClient() for player_id in range(self.num_players)}
        
        
    def game_loop(self):
        while not self.game_over:
            for player_id in self.turn_order:
                print("-"*50)
                print(f"\nTurn number {self.turn_num}: player {player_id} go:" )
                self.take_turn(player_id)
                self.env.update_player_lives()
            
                
                

                if self.env.is_terminal():
                    self.game_over = True
                    break
                
            self.turn_num+=1
        print(f" player {self.env.get_winner()} won!")
        
    def take_turn(self,player_id):
    
        
        
        print(f"player {player_id} has {len(self.env.player_states[player_id]["cards"])} {self.env.player_states[player_id]["cards"]} and {self.env.player_states[player_id]["coins"]} coins")
        
        
        curr_player_action = self.request_player_action(player_id)


        curr_player_action_type = curr_player_action["action_type"]
        
        print(f"player {player_id} tries action: {curr_player_action_type}")

        if curr_player_action_type in INCONTESTABLE_ACTIONS:
            self.finish_turn(curr_player_action)
            print("action uncontestable therefore passed")
            
            # next turn
            return
        
        # else action is contestable

        contest = self.propose_action(curr_player_action)

        if not contest:
            self.finish_turn(curr_player_action)

            print("action uncontested therefore passed")
            # next turn
            return

        contest_type = contest["type"]
        challenger = contest["from_player"]
        
        if contest_type == Action_Response.CHALLENGE:
            
            revealed_card = self.request_card_reveal(player_id) # p is prompted to reveal a card
            self.env.remove_player_card(player_id,revealed_card)
            
            if revealed_card == necessary_card_for_action[curr_player_action_type]: #where necessary card is a dict mapping an action to the card needed for it -- will
                #p wins the challenge
                
                penalty_card = self.request_card_reveal(challenger) # challenger has to reveal a card if their challenge is wrong
                self.env.remove_player_card(challenger, penalty_card)
                
                self.env.give_player_new_card(player_id) #p gets a new card
                self.env.deck.append(revealed_card) # the old card has to go back into the deck
                self.finish_turn(curr_player_action) #action goes through anyway

                print("action challenged but challenge failed therefore passed")
            #else ie if revealed card shows p's bluff or they choose not to reveal their card
            # accuser wins challenge
            # nothing has to happen since request_card_reveal removed the card from the player p. We don't apply the action, just pass to the next turn
            else:
                
                print("accuser wins challenge -  action discarded")

            # next turn
            return
            
        #an action and counteraction have a 1:1 relationship, right? 
        if contest_type == Action_Response.COUNTERACT:

            counteraction = contest["counteraction"]
            counteract_challenge = self.propose_counteraction({"player_id": challenger, "action_type": counteraction}) #prompt all other players for a response to the counteraction
            
            if not counteract_challenge:
                self.finish_turn(curr_player_action, no_effect = True) #the action is blocked so it should cost p money but have no effect

                print("action blocked because counteract was not challenged")
                # next turn
                return
                
            
            #else it is challenged ie. assassin from p, blocked by contessa from counteracter, someone says you don't have contessa 
            revealed_counteraction_card = self.request_card_reveal(challenger) # ask the counteractor to reveal a card
            self.env.remove_player_card(challenger,revealed_counteraction_card)
            
            if revealed_counteraction_card in necessary_card_for_counteraction[counteraction]:
                
                penalty_card = self.request_card_reveal(counteract_challenge["from_player"])
                self.env.remove_player_card(counteract_challenge["from_player"], penalty_card)
                
                self.env.give_player_new_card(challenger) #the successful counteractor gets a new card
                self.env.deck.append(revealed_counteraction_card)
                
                self.finish_turn(curr_player_action, no_effect = True) 
                print("action blocked because counteract was challenge and passed")
                
                # next turn
                return

            #else the counteractor bluffed, they dont get a card back after revealing it
            
            self.finish_turn(curr_player_action)
        
    @log
    def finish_turn(self, action, no_effect = False):
        
        new_cards = None
        killed_card = None

        #action options that only happen after turn is finalized
        if (not no_effect):
            if action["action_type"] == Action.EXCHANGE:
                new_cards = self.request_exchange(action["player_id"])
                
            elif action["action_type"] in [Action.ASSASSINATE, Action.COUP]:
                killed_card = self.request_card_reveal(action["target_player_id"])
        
        
        
        action["new_cards"] = new_cards
        action["killed_card"] = killed_card
            
            
        self.env.apply_action(action, no_effect)
       


    
    @log
    def request_player_action(self, player_id) -> dict:
        
        actions = self.env._get_legal_actions(player_id)
        
        action_type = Action(self.clients[player_id].ask_input(actions))
        
        target_id = None
        

        target_id = None
        if action_type in [Action.COUP, Action.STEAL, Action.ASSASSINATE]:
            
            target_id = int(self.clients[player_id].ask_input(self.env.get_targets(player_id)))



        return {"player_id": player_id, "action_type": action_type, "target_player_id":target_id}


    @log
    def request_card_reveal(self, player_id)-> int:

       
        revealed_card = Card(self.clients[player_id].ask_input(self.env.player_states[player_id]["cards"]))
        
        return revealed_card


    #returns the chosen cards
    @log
    def request_exchange(self, player_id) -> list[int]:

        player_cards = self.env.player_states[player_id]["cards"]
        num_player_cards = len(player_cards)
        
        first = self.env._deal_card()
        second = self.env._deal_card()
        
        show_these = [first, second] + player_cards

        user_new_card_1 = Card(self.clients[player_id].ask_input(show_these))
        
        show_these.remove(user_new_card_1)
        
        user_new_card_2 = Card(self.clients[player_id].ask_input(show_these))
        
        user_picked = [user_new_card_1, user_new_card_2]
        
        to_go_back = set(show_these) - set(user_picked)
        
        for card in to_go_back:
            self.env.deck.append(card)

        return list(user_picked) 

    @log
    def request_action_response(self, player_id, valid_responses):
        
        res = Action_Response(self.clients[player_id].ask_input(valid_responses))
        
        return res
    
    def propose_counteraction(self, action):
        player_id = action["player_id"]
        action_type = action["action_type"]
        
        other_players = self.env.get_targets(player_id)
        
        for other_id in other_players:
            res = self.request_action_response(other_id, [Action_Response.PASS, Action_Response.CHALLENGE])
            if res != Action_Response.PASS:
                    return {"type": res, "from_player": other_id, "counteraction": None}
                
        return None
        
        
    def propose_action(self, action) -> dict | None:
        
        
       
        action_type = action["action_type"]
        player_id = action["player_id"]
        target_player_id = action["target_player_id"]
        
        other_players = self.env.get_targets(player_id)
        
        
       
        if action_type == Action.FOREIGN_AID:
            for other_id in other_players:
                res = self.request_action_response(other_id, [Action_Response.PASS, Action_Response.COUNTERACT])
                if res != Action_Response.PASS:
                     return {"type": res, "from_player": other_id, "counteraction": Counteraction.BLOCK_FOREIGN_AID}
        else:
            for other_id in other_players:
                
                valid_responses = [Action_Response.PASS, Action_Response.CHALLENGE]
                
                is_target = target_player_id and (other_id == target_player_id)
                
                if is_target:
                    valid_responses.append(Action_Response.COUNTERACT)
                
                
                res = self.request_action_response(other_id, valid_responses)
                
                if res != Action_Response.PASS:
                    
                    if res == Action_Response.CHALLENGE:
                        return {"type": res, "from_player": other_id, "counteraction": None}
                    else:
                        return {"type": res, "from_player" : other_id, "counteraction" : action_counteraction_map[action_type]}
        
        
            
        #contest is a None, or a dict of {"type": in [challenge, counteract] , "from_player:int": player_id, "counteraction" : in [block foreign aid, block steal, block assassinate]}

        
        return None
    #end functions that require user input
    
    
        