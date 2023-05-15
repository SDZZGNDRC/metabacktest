from typing import List, Dict
from instruction import Instruction
class MetaTest:
    '''
    元测试类
    '''
    def __init__(self, 
                 start : int, 
                 end : int,
                 insts : List[Instruction],
                 balance : Dict[float],
                 ) -> None:
        self.start = start # 回测开始时间, Unix毫秒级时间戳
        self.end = end # 回测结束时间, Unix毫秒级时间戳
        self.insts = insts # 回测中涉及到的交易指令
        self.balance = balance # 账户初始余额

    def asdict() -> dict:
        '''
        字典化
        '''
        return {}