from enum import Enum

class ActionType(Enum):
    INCOME = "income"
    FOREIGN_AID = "foreign_aid"
    COUP = "coup"
    TAX = "tax"
    EXCHANGE = "exchange"
    STEAL = "steal"
    ASSASSINATE = "assassinate"


class ReactionType(Enum):
    CHALLENGE = "challenge"
    COUNTERACT = "counteract"
    PASS = "pass"


class CardType(Enum):
    DUKE = "duke"
    CAPTAIN = "captain"
    AMBASSADOR = "ambassador"
    ASSASSIN = "assassin"
    CONTESSA = "contessa"


class Action:
    

    _PROPERTIES = {
        ActionType.INCOME: {
            "needed_card": None,
            "counter_card": None,
            "target_required": False,
            "challengeable": False,
            "counterable": False,
            "all_reactions": [ReactionType.PASS],
            "target_reactions": [ReactionType.PASS],
        },
        ActionType.FOREIGN_AID: {
            "needed_card": None,
            "counter_card": CardType.DUKE,
            "target_required": False,
            "challengeable": False,
            "counterable": True,
            "all_reactions": [ReactionType.COUNTERACT, ReactionType.PASS],
            "target_reactions": [ReactionType.PASS],
        },
        ActionType.COUP: {
            "needed_card": None,
            "counter_card": None,
            "target_required": True,
            "challengeable": False,
            "counterable": False,
            "all_reactions": [ReactionType.PASS],
            "target_reactions": [ReactionType.PASS],
        },
        ActionType.TAX: {
            "needed_card": CardType.DUKE,
            "counter_card": None,
            "target_required": False,
            "challengeable": True,
            "counterable": False,
            "all_reactions": [ReactionType.CHALLENGE, ReactionType.PASS],
            "target_reactions": [ReactionType.PASS],
        },
        ActionType.EXCHANGE: {
            "needed_card": CardType.AMBASSADOR,
            "counter_card": None,
            "target_required": False,
            "challengeable": True,
            "counterable": False,
            "all_reactions": [ReactionType.CHALLENGE, ReactionType.PASS],
            "target_reactions": [ReactionType.PASS],
        },
        ActionType.STEAL: {
            "needed_card": CardType.CAPTAIN,
            "counter_card": [CardType.CAPTAIN, CardType.AMBASSADOR],
            "target_required": True,
            "challengeable": True,
            "counterable": True,
            "all_reactions": [ReactionType.CHALLENGE, ReactionType.PASS],
            "target_reactions": [ReactionType.CHALLENGE, ReactionType.COUNTERACT, ReactionType.PASS],
        },
        ActionType.ASSASSINATE: {
            "needed_card": CardType.ASSASSIN,
            "counter_card": CardType.CONTESSA,
            "target_required": True,
            "challengeable": True,
            "counterable": True,
            "all_reactions": [ReactionType.CHALLENGE, ReactionType.PASS],
            "target_reactions": [ReactionType.CHALLENGE, ReactionType.COUNTERACT, ReactionType.PASS],
        },
    }

    def __init__(self, action_type: ActionType):
        if action_type not in self._PROPERTIES:
            raise ValueError(f"Unknown action type: {action_type}")
        self.type = action_type

    @property
    def needed_card(self): return self._PROPERTIES[self.type]["needed_card"]
    @property
    def counter_card(self): return self._PROPERTIES[self.type]["counter_card"]
    @property
    def target_required(self): return self._PROPERTIES[self.type]["target_required"]
    @property
    def challengeable(self): return self._PROPERTIES[self.type]["challengeable"]
    @property
    def counterable(self): return self._PROPERTIES[self.type]["counterable"]
    @property
    def all_reactions(self): return self._PROPERTIES[self.type]["all_reactions"]
    @property
    def target_reactions(self): return self._PROPERTIES[self.type]["target_reactions"]

    def __repr__(self):
        return f"<Action {self.type.value}>"
