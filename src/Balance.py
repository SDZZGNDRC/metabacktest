from typing import List, Dict, Tuple
from utils.helper import validate_currency

class Balance:
    def __init__(self) -> None:
        self._balances: Dict[str, float] = {}
    
    
    @validate_currency
    def __getitem__(self, key: str) -> float:
        return self._balances[key]
    
    
    @validate_currency
    def __setitem__(self, key: str, value: float) -> None:
        assert value >= 0, "Balance must be not negative"
        self._balances[key] = value

    def in_USD(self) -> float:
        '''TODO: Calculate total USD value of all currencies'''
        return -1.0
    
    def __str__(self) -> str:
        sorted_balances = sorted(self._balances.items(), key=lambda x: x[0], reverse=False)
        return str(dict(sorted_balances))

    def asdict(self):
        return self._balances

class BalancesHistory:
    def __init__(self) -> None:
        self.slice: List[Tuple[int, Balance]] = []

    def append(self, timestamp: int, balance: Balance) -> None:
        self.slice.append((timestamp, balance))
        self.slice.sort(key=lambda x: x[0], reverse=False)
    
    
    def at(self, timestamp: int) -> Balance:
        for i in range(len(self.slice)):
            if self.slice[i][0] > timestamp:
                return self.slice[i-1][1]
        raise ValueError(f"Timestamp {timestamp} is out of range")
    
    def __str__(self) -> str:
        self.slice.sort(key=lambda x: x[0], reverse=False)
        return str({x[0]: str(x[1]) for x in self.slice})

    def asdict(self):
        return {x[0]: x[1].asdict() for x in self.slice}