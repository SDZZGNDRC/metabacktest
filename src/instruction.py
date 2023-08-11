from typing import Dict

LIMITORDER = 'LimitOrder'
MARKETORDER = 'MarketOrder'
BUY = 'BUY'
SELL = 'SELL'

class Instruction:
    '''
    策略发出的交易指令
    '''
    def __init__(self, 
                ordType : str,
                side : str, 
                ts : int, 
                ) -> None:
        self.ordType = ordType # 订单类型
        self.side = side # 交易方向
        self.ts = ts # 该指令发出时Unix毫秒级时间戳的值
        self.price: float = 0 # 对于MARKETORDER, 该值无意义
        self.value: float = 0 # 委托量
        self.pair: str = '' # 交易对

    @property
    def baseCcy(self) -> str:
        return self.pair.split('-')[0]
    
    @property
    def quoteCcy(self) -> str:
        return self.pair.split('-')[1]
    
    def asdict(self):
        return {
            'ordType': self.ordType,
            'side': self.side,
            'ts': self.ts,
            'price': self.price,
            'value': self.value,
            'pair': self.pair
        }
