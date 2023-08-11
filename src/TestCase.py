import json
from typing import Dict, List, Tuple, Any
from Book import Book
from instruction import Instruction
from Balance import BalancesHistory

class TestCase:
    
    def __init__(self, 
                books: Dict[str, Book],
                insts: List[Instruction],
                referredBalance: BalancesHistory
                ) -> None:
        self.books = books
        self.insts = insts
        self.referredBalance = referredBalance
    
    
    def to_files(self, path) -> None:
        with open(path, 'w') as f:
            json.dump(self.asdict(), f)
    
    def asdict(self) -> Dict[str, Any]:
        return {
            'books': {k: v.asdict() for k, v in self.books.items()},
            'insts': [x.asdict() for x in self.insts],
            'referredBalance': self.referredBalance.asdict()
        }
