from copy import deepcopy
from typing import List, Dict, Optional, Set, Tuple
from TestCase import TestCase
from utils.instruments import defaultInstruments
from utils.helper import *
from instruction import *
from Book import *
from Balance import *
import sys
import random

DefaultSuccessRate = 0.001
DefaultValuePerCcy = 1000

# TODO: 封装以下类型
TypeAskBids = List[Tuple[int, Tuple[float, float]]]

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
    
    def genBalance(self, pairs: List[str]) -> Balance:
        '''
        根据valuePerCcy生成策略的初始账户余额
        NOTICE: 目前只支持SPOT; 后续应该考虑随机化生成
        TODO: 各个Ccy的初始余额应该随机化生成
        '''
        balance = Balance()
        totalCcy = set()
        for pair in pairs:
            ccy1, ccy2 = pair.split('-')[:2]
            totalCcy.add(ccy1)
            totalCcy.add(ccy2)
        
        lastPrices = get_lastPrice('SPOT')
        for ccy in totalCcy:
            # TODO: 这里的逻辑需要优化
            if ccy in ['USDT', 'USDC']:
                balance[ccy] = self.valuePerCcy
                continue

            pair = '-'.join([ccy, 'USDT'])
            instrument = self.getInstrument(pair)
            price = lastPrices[pair]
            value = round(self.valuePerCcy/price, get_significant_digits(instrument['lotSz']))
            balance[ccy] = value
        return balance
    
    def genBackTestPeriod(self, point: int = 5000) -> Tuple[int, int]:
        '''
        随机生成一个回测的开始和结束时间, 时间粒度为 1 sec.
        使用Unix毫秒级时间戳表示
        '''
        start = 1684154233000 # 由于在回测中, 时间段所在的位置并没有什么影响, 故而可以固定为一个值
        # length = random.randint(self.minSec, self.maxSec) # 随机决定回测的时间长度
        length = point
        end = start + length*1000
        return (start, end)
    
    def genInsts(self, time_period : Tuple[int, int], pairs: List[str]) -> List[Instruction]:
        '''
        随机生成一次回测中策略发出的交易指令
        NOTICE: 只填充 ordType 和 side 字段
        NOTICE: 目前只支持 MarketOrder 类型的交易指令
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
            # ordType = LimitOrder if random.randint(0,1) else MarketOrder
            ordType = MARKETORDER # 暂时只支持市价单
            side = BUY if random.randint(0,1) else SELL
            inst = Instruction(ordType, side, i)

            # 随机决定该指令的交易对
            # totalPairs = self.getTotalPairs(filters=['USDT-', 'USDC-'])
            inst.pair = random.choice(pairs)
            result.append(inst)
        
        return result
    
    def genAskBids(self, 
                    pair: str, 
                    p0: float, 
                    time_period : Tuple[int, int], 
                    sigma: float = 1.0
                    ) -> TypeAskBids:
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
            delta_percent = max(delta_percent, -0.03) # 限制变化范围
            delta_percent = min(delta_percent, 0.03)
            
            delta = prices[-1][1] * delta_percent # 变化绝对值
            next_price = prices[-1][1] + delta
            prices.append((time_period[0]+1000*i, next_price))
        
        # 生成 ask 和 bid
        askbids = []
        for p in prices:
            # FIXME: 这里生成的ask和bid间的价差通常只差一个tickSz
            gap_t = round(random.uniform(0, 0.01) * p[1], get_significant_digits(tickSz))
            price_gap = max(tickSz, gap_t) # 生成ask和bid间的价差
            bid = p[1]
            ask = p[1] + price_gap
            askbids.append((p[0], (ask, bid)))
        
        return askbids
    
    def fillInsts(self, 
                totalAskBids: Dict[str, TypeAskBids], 
                insts: List[Instruction]
                ) -> List[Instruction]:
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
        prices = get_lastPrice('SPOT') # 目前只支持 SPOT
        for inst in insts:
            askbids = totalAskBids[inst.pair] # 选择指定的askbids
            # FIXME: Remove the following assertion
            assert len(list(filter(lambda x: x[0] == inst.ts, askbids))) == 1
            askbid = list(filter(lambda x: x[0] == inst.ts, askbids))[0]

            # FIXME: 实际上, 对于市价单, 价格应该是没有意义的
            if inst.side == BUY:
                inst.price = askbid[1][0]
            else:
                inst.price = askbid[1][1]
            
            # 随机生成委托量, 基准值为 10 USDT
            instrument = self.getInstrument(pair=inst.pair)
            raw_value = max(random.normalvariate(10, 5), 1) / prices[inst.pair]
            raw_value = round(raw_value, get_significant_digits(instrument['lotSz']))
            value = max(float(instrument['minSz']), raw_value)
            inst.value = value
            
        return insts

    def calBalanceHist(self, 
                        insts: List[Instruction],
                        original_balance: Balance,
                        ) -> BalancesHistory:
        '''
        计算不同时刻下的Balance的值
        NOTICE: 当前只支持OKX的市价单手续费
        NOTICE: 当前只支持 SPOT
        '''
        commission = { # 手续费
            MARKETORDER: {
                'MAKER': 0.0008,
                'TAKER': 0.0010,
            }
        }
        balanceHist = BalancesHistory()
        balanceHist.append(0, original_balance)
        traded_num = 0
        for inst in insts:
            # FIXME: Remove the following assertion
            assert inst.ordType == MARKETORDER
            nextBalance = deepcopy(balanceHist[-1][1])            
            baseCcy = inst.baseCcy
            quoteCcy = inst.quoteCcy
            if inst.side == BUY: # get baseCcy
                
                # Check if the balance is enough
                traded_quoteCcy = nextBalance[quoteCcy] - (inst.value*inst.price)
                if traded_quoteCcy < 0:
                    continue
                else:
                    traded_num += 1
                # print(f'delta: {(inst.value*inst.price)}')
                nextBalance[baseCcy] = nextBalance[baseCcy] + inst.value
                nextBalance[baseCcy] = round(nextBalance[baseCcy]*(1-commission[MARKETORDER]['TAKER']), \
                                            get_significant_digits(self.getLotSz(inst.pair)))
                nextBalance[quoteCcy] = traded_quoteCcy # FIXME: 也许需要进行舍入?

            elif inst.side == SELL: # get quoteCcy
                
                # Check if the balance is enough
                traded_baseCcy = nextBalance[baseCcy] - inst.value
                if traded_baseCcy < 0:
                    continue
                else:
                    traded_num += 1
                # print(f'delta: {inst.value}')
                nextBalance[baseCcy] = traded_baseCcy
                nextBalance[quoteCcy] = nextBalance[quoteCcy] + (inst.value*inst.price) # FIXME: 也许需要进行舍入?
                nextBalance[quoteCcy] = nextBalance[quoteCcy]*(1-commission[MARKETORDER]['TAKER'])
            else:
                raise Exception('Unknown side: {}'.format(inst.side))

            balanceHist.append(inst.ts, nextBalance)
        
        print('Traded number: {}'.format(traded_num))
        return balanceHist

    def genBook(self, 
                time_period: Tuple[int, int],
                insts: List[Instruction],
                askbids: TypeAskBids,
                pair: str,
                ) -> Book:
        '''
        随机生成订单簿
        NOTICE: 当前只假定一个交易指令可以被一档订单消耗完成
        NOTICE: 假定订单簿深度为 20
        '''
        Depth = 20 # 订单簿深度
        time_range = int((time_period[1]-time_period[0])/1000) + 1
        
        books = Book(pair)
        for t in range(time_range):
            askbid = askbids[t][1] # 卖一价; 买一价
            assert askbids[t][0] == 1000*t + time_period[0]
            # FIXME: Remove the following assertion
            filtered_insts = list(filter(lambda x: x.ts == askbids[t][0], insts))
            assert len(filtered_insts) <= 1
            if len(filtered_insts) == 1:
                inst = filtered_insts[0]
            else:
                continue
            asks = []
            bids = []
            if inst.pair == pair: # 该时间戳下存在对应交易对的交易指令
                if inst.side == BUY:
                    asks.append((inst.price, inst.value))
                else:
                    bids.append((inst.price, inst.value))
            ask_ps = generate_order_seq(askbid[0], 1, Depth-len(asks), self.getTickSz(pair))
            bid_ps = generate_order_seq(askbid[1], 1, Depth-len(bids), self.getTickSz(pair), False)
            ask_v = generate_random_seq(1, 1/3, Depth-len(asks), self.getLotSz(pair), self.getMinSz(pair))
            bid_v = generate_random_seq(1, 1/3, Depth-len(bids), self.getLotSz(pair), self.getMinSz(pair))
            for i in range(Depth-len(asks)):
                asks.append((ask_ps[i], ask_v[i]))
            for i in range(Depth-len(bids)):
                bids.append((bid_ps[i], bid_v[i]))
            
            books.add_slice(1000*t + time_period[0], asks, bids)

        return books

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
                    if filter not in pair: # TODO: 修改过滤的逻辑
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
            baseCcy, quoteCcy = pair.split('-')[:2]
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
        filtered_instruments = list(filter(lambda x: x['instId']==pair, self.instruments))
        if len(filtered_instruments) == 0:
            raise Exception('No such instrument: {}'.format(pair))
        return filtered_instruments[0]

    def produce(self, num_pairs: int = 3) -> TestCase:
        '''produce a test case'''
        bt_period = self.genBackTestPeriod()
        pairs = self.genPairs(num_pairs, ['USDT-', 'USDC-'])
        insts = self.genInsts(bt_period, pairs)
        total_pairs = set([inst.pair for inst in insts])
        lastPrices = get_lastPrice('SPOT') # FIXME: 仅支持 SPOT
        p0s = {pair: lastPrices[pair] for pair in total_pairs}
        askbids = {pair: self.genAskBids(pair, p0s[pair], bt_period) for pair in total_pairs}
        insts = self.fillInsts(askbids, insts)
        books: Dict[str, Book] = {}
        # generate books
        print('Total pairs:', len(total_pairs))
        for index, pair in enumerate(total_pairs):
            book = self.genBook(bt_period, insts, askbids[pair], pair)
            books[pair] = book
            print(f'finish generating book for {pair} -> {index+1}/{len(total_pairs)}')
        
        original_balance = self.genBalance(pairs)
        referredBalances = self.calBalanceHist(insts, original_balance)

        return TestCase(books, insts, referredBalances)


    def genPairs(self, num: Optional[int] = None, filters: List[str] = []) -> List[str]:
        '''
        随机生成回测涉及的交易对
        '''
        totalPairs = self.getTotalPairs(filters)
        if num is None:
            k = random.randint(self.minPairs, self.maxPairs)
        else:
            k = num
        result = random.sample(totalPairs, k)
        return result
    

if __name__ == '__main__':
    tf = TestFactory()
    tc = tf.produce(1)
    tc.to_files('./testcase.json')