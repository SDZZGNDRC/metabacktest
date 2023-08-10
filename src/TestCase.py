from typing import Dict, List, Tuple
from Book import Book
from instruction import Instruction
from src.Balance import BalancesHistory

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
        pass