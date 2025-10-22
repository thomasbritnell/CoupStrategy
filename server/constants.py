
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
    
    def __str__(self):
        return self.name      

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

