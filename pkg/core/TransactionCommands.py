from dataclasses import dataclass

@dataclass
class Command_SPLIT:
    ticker:int
    amount:float
    date:str
