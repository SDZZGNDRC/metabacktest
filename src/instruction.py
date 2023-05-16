from typing import Dict

LimitOrder = 'LimitOrder'
MarketOrder = 'MarketOrder'
BUY = 'BUY'
SELL = 'SELL'

class Instruction:
    '''
    策略发出的交易指令
    '''
    def __init__(self, 
                 instType : str,
                 direct : str, 
                 ts : int, 
                 ) -> None:
        self.instType = instType # 指令类型
        self.direct = direct # 交易方向
        self.ts = ts # 该指令发出时Unix毫秒级时间戳的值
        self.price: float = 0 # LimitOrder: 限价; MarketOrder: 市价
        self.value: float = 0 # 委托量
        self.pair: str = '' # 交易对
    
    def asdict() -> Dict:
        return {}    