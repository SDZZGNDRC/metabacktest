from typing import List, Dict

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
                 ) -> None:
        self.instType = instType # 指令类型
        self.direct = direct # 交易方向
    
    def asdict() -> Dict:
        return {}    