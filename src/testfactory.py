from copy import deepcopy
from typing import List, Dict, Set, Tuple
from utils.instruments import defaultInstruments
from utils.helper import *
from instruction import *
import sys
import random

DefaultSuccessRate = 0.001
DefaultValuePerCcy = 1000

TypeInstructions = List[Instruction]
TypeAskBids = List[Tuple[int, Tuple[float, float]]]
TypeBalance = Dict[str, float]
TypeBalanceHist = List[Tuple[int, TypeBalance]]
TypeBookItem = Tuple[float, float] # (价格, 委托量)
TypeBook = Tuple[List[TypeBookItem], List[TypeBookItem]] # (Asks, Bids)
TypeBooks = List[Tuple[int, TypeBook]] # (timestamp, TypeBook)

class TestFactory:
    '''
    该类根据配置参数生成metatest
    '''
    defaultPairsFilters = ['-USDC']
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
            instrument = self.getInstrument(pair)
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
        NOTICE: 只支持 MarketOrder 类型的交易指令
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
            # instType = LimitOrder if random.randint(0,1) else MarketOrder
            instType = MarketOrder # 暂时只支持市价单
            direct = BUY if random.randint(0,1) else SELL
            inst = Instruction(instType, direct, i)

            # 随机决定该指令的交易对
            totalPairs = self.getTotalPairs(filters=['USDT-', 'USDC-'])
            inst.pair = random.choice(totalPairs)
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
        tickSz = self.getTickSz(pair)
        
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
    
    def fillInsts(self, 
                  totalAskBids: Dict[str, TypeAskBids], 
                  insts: TypeInstructions
                  ) -> TypeInstructions:
        '''
        填充交易指令的剩余部分
        NOTICE: 只支持 MarketOrder
        NOTICE: 当前的MetaTest只支持发出'即时性'的交易指令, 
                即, 如果某个时刻发出的交易指令(特指LimitOrder)未能马上完成
                则该交易指令会马上被撤销
        NOTICE: 前的MetaTest假设交易的成交不会对订单簿产生影响(当然这只在交易量非常小的情况下近似成立).
                此外, 不同的时刻的订单簿都是相互独立的, 彼此间没有连续性可言(这当然是不成立的, 
                但用于测试回测系统的正确性应该是足够了)
        '''
        prices = get_lastPrice()
        for inst in insts:
            askbids = totalAskBids[inst.pair] # 选择指定的askbids
            askbid = list(filter(lambda x: x[0] == inst.ts, askbids))[0]
            if inst.direct == BUY:
                inst.price = askbid[0]
            else:
                inst.price = askbid[1]
            
            # 随机生成委托量, 基准值为 10 USDT
            instrument = self.getInstrument(pair=inst.pair)
            raw_value = max(random.normalvariate(10, 5), 1) / prices[inst.pair]
            raw_value = round(raw_value, get_significant_digits(instrument['lotSz']))
            value = max(float(instrument['minSz']), raw_value)
            inst.value = value
            
        return insts

    def calBalanceHist(self, 
                       insts: TypeInstructions,
                       original_balance: TypeBalance,
                       ) -> TypeBalanceHist:
        '''
        计算不同时刻下的Balance的值
        NOTICE: 当前只支持OKX的市价单手续费
        NOTICE: 当前只支持 SPOT
        '''
        commission = { # 手续费
            MarketOrder: {
                'MAKER': 0.0008,
                'TAKER': 0.0010,
            }
        }
        balanceHist: TypeBalanceHist = []
        nextBalance = deepcopy(original_balance)
        for inst in insts:
            assert inst.instType == MarketOrder
            baseCcy, quoteCcy = inst.pair.split('-')
            if inst.direct == BUY: # get baseCcy
                nextBalance[baseCcy] = (nextBalance[baseCcy] + inst.value)
                nextBalance[baseCcy] = round(nextBalance[baseCcy]*(1-commission[MarketOrder]['TAKER']), \
                                            self.getLotSz())
                nextBalance[quoteCcy] = nextBalance[quoteCcy] - (inst.value*inst.price) # NOTICE: 也许需要进行舍入?
            elif inst.direct == SELL: # get quoteCcy
                nextBalance[baseCcy] = nextBalance[baseCcy] - inst.value
                nextBalance[quoteCcy] = nextBalance[quoteCcy] + (inst.value*inst.price) # NOTICE: 也许需要进行舍入?
            
            balanceHist.append((inst.ts, deepcopy(nextBalance)))
        
        return balanceHist

    def genBooks(self, 
                 time_period: Tuple[int, int],
                 insts: TypeInstructions,
                 askbids: TypeAskBids,
                 pair: str,
                 ) -> TypeBooks:
        '''
        随机生成订单簿
        NOTICE: 当前只假定一个交易指令可以被一档订单消耗完成
        NOTICE: 假定订单簿深度为 20
        '''
        Depth = 20 # 订单簿深度
        time_range = int((time_period[1]-time_period[0])/1000) + 1
        
        books = []
        for t in time_range:
            askbid = askbids[t][1] # 卖一价; 买一价
            assert askbid[t][0] == 1000*t + time_period[0]
            inst = self.getInstructions(t, insts)
            if inst == None: # 该时间戳下不存在交易指令; 随机生成整个订单簿
                ask_ps = generate_order_seq(askbid[0], 2, Depth)
                bid_ps = generate_order_seq(askbid[1], 2, Depth, False)
                ask_v = generate_random_seq(10, 10/3, Depth, self.getLotSz(pair), self.getMinSz(pair))
                bid_v = generate_random_seq(10, 10/3, Depth, self.getLotSz(pair), self.getMinSz(pair))
                asks = []
                bids = []
                for i in range(Depth):
                    asks.append((ask_ps[i], ask_v[i]))
                    bids.append((bid_ps[i], bid_v[i]))
                books.append((1000*t + time_period[0], (asks, bids)))
            elif inst.pair == pair: # 该时间戳下存在对应交易对的交易指令
                
                    
    def getTotalPairs(self, filters: List[str] = []) -> List[str]:
        '''
        获取全体交易对
        '''
        totalPairs = [i['instId'] for i in self.instruments] # 全体交易对
        all_filters = self.defaultPairsFilters + filters
        if all_filters != []:
            result = []
            for pair in totalPairs:
                for filter in all_filters:
                    if filter not in pair:
                        result.append(pair)
                        break
            return result
        else:
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
    
    def getLotSz(self, pair: str) -> float:
        '''
        获取下单数量精度
        '''
        instrument = self.getInstrument(pair)
        return float(instrument['lotSz'])

    def getTickSz(self, pair: str) -> float:
        '''
        获取下单价格精度
        '''
        instrument = self.getInstrument(pair)
        return float(instrument['tickSz'])
    
    def getMinSz(self, pair: str) -> float:
        '''
        获取最小下单数量
        '''
        instrument = self.getInstrument(pair)
        return float(instrument['minSz'])
    
    def getInstrument(self, pair: str) -> Dict:
        '''
        获取指定交易对的信息
        '''
        return list(filter(lambda x: x['instId']==pair, self.instruments))[0]
    
    def getInstructions(self, ts: int, instructions: TypeInstructions) -> Instruction:
        '''
        获取指定时间戳的交易指令, 如果不存在, 返回 None
        '''
        for inst in instructions:
            if inst.ts == ts:
                return inst
        
        return None # 不存在则返回 None