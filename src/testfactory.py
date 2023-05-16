from typing import List, Dict, Set, Tuple
from utils.instruments import defaultInstruments
from utils.helper import get_lastPrice, get_significant_digits, generate_random_valueInt
from instruction import *
import sys
import random

DefaultSuccessRate = 0.001
DefaultValuePerCcy = 1000

TypeInstructions = List[Instruction]
TypeAskBids = List[Tuple[int, Tuple[float, float]]]
TypeBalance = Dict[str, float]

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
                 valuePerCcy : float = DefaultValuePerCcy,
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
        self.valuePerCcy = valuePerCcy # Balance中每个币种初始额度(单位: USDT)
    
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
    
    def genBalance(self) -> TypeBalance:
        '''
        根据valuePerCcy生成策略的初始账户余额
        NOTICE: 目前只支持SPOT; 后续应该考虑随机化生成
        '''
        balance = {}
        totalCcy = self.getTotalCcy()
        lastPrices = get_lastPrice('SPOT')
        for ccy in totalCcy:
            pair = '-'.join(ccy, 'USDT')
            instrument = list(filter(lambda x: x['instId'] == pair, self.instruments))[0]
            price = lastPrices[pair]
            value = round(self.valuePerCcy/price, get_significant_digits(instrument['lotSz']))
            balance[pair] = value
    
    def genTime(self) -> Tuple[int, int]:
        '''
        随机生成一个回测的开始和结束时间, 时间粒度为 1 sec.
        使用Unix毫秒级时间戳表示
        '''
        start = 1684154233000 # 由于在回测中, 时间段所在的位置并没有什么影响, 故而可以固定为一个值
        length = random.randint(self.minSec, self.maxSec) # 随机决定回测的时间长度
        end = start + length*1000
        return (start, end)
    
    def genInsts(self, time_period : Tuple[int, int]) -> TypeInstructions:
        '''
        随机生成一次回测中策略发出的交易指令
        NOTICE: 只填充 instType 和 direct 字段
        NOTICE: 只支持 LimitOrder 和 MarketOrder 类型的交易指令
        '''

        # 确定交易指令的发出时刻和数量
        ts = []
        t = time_period[0]
        while t <= time_period[1]:
            ts.append(t)
            t = t + 1000*generate_random_valueInt(self.secPerInst, 0.5) # 随机生成间隔, 基准为secPerInst, 最大偏离50%
        
        # 生成交易指令
        result = []
        for i in ts:
            instType = LimitOrder if random.randint(0,1) else MarketOrder
            direct = BUY if random.randint(0,1) else SELL
            inst = Instruction(instType, direct, i)
            result.append(inst)
        
        return result
    
    def genAskBids(self, 
                  pair: str, 
                  p0: float, 
                  time_period : Tuple[int, int], 
                  sigma: float) -> TypeAskBids:
        '''
        随机生成AskBid序列
        NOTICE: 生成的AskBid序列的一阶差分符合正态分布
        '''
        # 获取下单精度
        tickSz = float(List(filter(lambda x: x['instId']==pair), self.instruments)[0]['tickSz'])
        
        # 生成基准价格
        time_range = int((time_period[1]-time_period[0])/1000) + 1
        prices = [(time_period[0], p0)]
        for i in range(1, time_range):
            delta_percent = random.normalvariate(0, sigma) # 变化百分比, 符合正态分布
            delta_percent = max(delta_percent, -0.8) # 最小的变化百分比为 -0.8
            delta_percent = min(delta_percent, 0.8) # 最小的变化百分比为 0.8
            
            delta = prices[-1] * delta_percent # 变化绝对值
            next_price = prices[-1] + delta
            prices.append((time_period[0]+1000*i, next_price))
        
        # 生成 ask 和 bid
        askbids = []
        for p in prices:
            gap_t = round(random.uniform(0, 0.01) * p[1], get_significant_digits(tickSz))
            price_gap = max(tickSz, gap_t) # 生成ask和bid间的价差
            bid = p[1]
            ask = p[1] + price_gap
            askbids.append((p[0], (ask, bid)))
        
        return askbids
    
    def fillInsts(self, askbids: TypeAskBids, insts: TypeInstructions) -> TypeInstructions:
        '''
        填充交易指令的剩余部分
        '''
        
    def getTotalPairs(self) -> List[str]:
        '''
        获取全体交易对
        '''
        totalPairs = [i['instId'] for i in self.instruments] # 全体交易对
        return totalPairs
    
    def getTotalCcy(self) -> Set[str]:
        '''
        获取全体币种
        '''
        result = set()
        totalPairs = self.getTotalPairs()
        for pair in totalPairs:
            baseCcy, quoteCcy = pair.split('-')
            result.add(baseCcy)
            result.add(quoteCcy)
        
        return result
        
