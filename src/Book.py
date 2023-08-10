from typing import List, Dict, Tuple

class BookItem:
    def __init__(self, price: float, size: float) -> None:
        assert price >= 0, "Price must be not negative"
        assert size > 0, "Size must be not negative"
        self.price: float = price
        self.size: float = size

    def __str__(self) -> str:
        return f"{self.price}:{self.size}"

class BookSlice:
    def __init__(self, asks: List[Tuple[float, float]], bids: List[Tuple[float, float]]) -> None:
        self.asks: List[BookItem] = [BookItem(x[0], x[1]) for x in asks]
        self.bids: List[BookItem] = [BookItem(x[0], x[1]) for x in bids]
    
    
    def add_ask(self, price: float, size: float) -> None:
        self.asks.append(BookItem(price, size))
        self.asks.sort(key=lambda x: x.price, reverse=False)
    
    def add_many_asks(self, asks: List[Tuple[float, float]]) -> None:
        for ask in asks:
            self.add_ask(ask[0], ask[1])
    
    
    def add_bid(self, price: float, size: float) -> None:
        self.bids.append(BookItem(price, size))
        self.bids.sort(key=lambda x: x.price, reverse=True)
    
    
    def add_many_bids(self, bids: List[Tuple[float, float]]) -> None:
        for bid in bids:
            self.add_bid(bid[0], bid[1])
    
    def remove_zero_size(self) -> None:
        self.asks = [x for x in self.asks if x.size > 0]
        self.bids = [x for x in self.bids if x.size > 0]


class Book:
    def __init__(self, pair: str) -> None:
        self.pair: str = pair
        self.slices: List[Tuple[int, BookSlice]] = []
    
    def add_slice(self, timestamp: int, asks: List[Tuple[float, float]], bids: List[Tuple[float, float]]) -> None:
        new_slice = BookSlice(asks, bids)
        self.slices.append((timestamp, new_slice))
        self.slices.sort(key=lambda x: x[0], reverse=False)
    
    def __getitem__(self, index: int) -> Tuple[int, BookSlice]:
        return self.slices[index]
    
    def at(self, timestamp: int) -> BookSlice:
        for i in range(len(self.slices)):
            if self.slices[i][0] > timestamp:
                return self.slices[i-1][1]
        raise ValueError(f"Timestamp {timestamp} is out of range")
    
    def __len__(self) -> int:
        return len(self.slices)
    
    
    def __iter__(self):
        return iter(self.slices)

