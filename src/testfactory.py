from typing import List, Dict
from utils.instruments import defaultInstruments
import sys
import random

DefaultSuccessRate = 0.001

class TestFactory:
    '''
    该类根据配置参数生成metatest
    '''
    def __init__(self, 
                 testNum = 100,
                 maxSec = 86400, 
                 minSec = 1000, 
                 secPerInst = 10,
                 maxPairs = sys.maxsize,
                 minPairs = 0,
                 successRate = DefaultSuccessRate,
                 destPath = './',
                 instruments : List[Dict] = defaultInstruments,
                 ) -> None:
        self.testNum : int = testNum # 生成的metatest的数量
        self.maxSec : int = maxSec # 最长回测时长(单位: 秒), 默认最长一天
        self.minSec : int = minSec # 最短回测时长(单位: 秒), 默认最短一小时
        self.secPerInst : int = secPerInst # 平均发出一次指令的时间间隔(单位: 秒)
        self.maxPairs = maxPairs # 回测涉及到的交易对的最大数量
        self.minPairs = minPairs # 回测涉及到的交易对的最小数量
        self.successRate = successRate # 交易指令成功的概率
        self.destPath = destPath # 测例存放的路径
        self.instruments = instruments # 产品信息
    
    def setDestPath(self, newDestPath : str):
        '''
        设置测例存放的路径
        '''
        self.destPath = newDestPath
    
    def genPairs(self) -> List[str]:
        '''
        随机生成回测涉及的交易对
        '''
        totalPairs = self.getTotalPairs()
        k = random.randint(self.minPairs, self.maxPairs)
        result = random.sample(totalPairs, k)
        return result
    
    def genBalance(self) -> Dict[str, float]:
        '''
        随机生成策略的初始账户余额
        NOTICE: 目前只支持SPOT
        '''
        
    
    def getTotalPairs(self) -> List[str]:
        '''
        获取全体交易对
        '''
        totalPairs = [i['instId'] for i in self.instruments] # 全体交易对
        return totalPairs
        
        
