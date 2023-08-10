import requests
import json
import random
from typing import List, Union, Dict, Callable

proxies = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890',
}

def get_significant_digits(num : Union[str, float]) -> int:
    '''
    给定形如0.0001的数字(字符串), 判断它的有效位数
    '''
    try:
        float(num)
    except ValueError:
        return -1 # Invalid Input
    
    # FIXME: 对于极小的float, 字符串后可能使用科学计数法表示, 例如1e-8, 此时会出错
    str_num = str(num)
    if 'e' in str_num:
        raise ValueError(f'Invalid Input: {num} -> {str_num}')
    if '.' not in str_num:
        return -1 * (len(str_num)-1)
    str_num = str_num.rstrip('0')  # 去除末尾的零
    return len(str_num) - str_num.index('.') - 1

def get_tickers(instType: str) -> List:
    '''
    获取所有产品行情信息
    产品类型
    SPOT: 币币
    SWAP: 永续合约
    FUTURES: 交割合约
    OPTION: 期权
    '''
    params = {
        'instType': instType,
    }
    response = requests.get('https://www.okx.com/api/v5/market/tickers', params=params, proxies=proxies)
    return json.loads(response.text)['data']

def get_lastPrice(instType: str) -> Dict[str, float]:
    '''
    获取最新的成交价格
    '''
    result: Dict[str, float] = {}
    tickers = get_tickers(instType)
    for ticker in tickers:
        result[ticker['instId']] = float(ticker['last'])
    
    return result


def generate_random_valueInt(v0, deviation) -> int:
    '''
    result = v0*(1+x), x in [-deviation, deviation].
    '''
    delta = v0 * deviation
    x = random.uniform(-delta, delta) # 均匀分布
    return int(v0 + x)

def generate_order_seq(a0, step, count, is_increasing: bool = True) -> List[float]:
    '''
    随机生成一串以a0为首项的递增或递减的随机数序列
    '''
    seq = [a0]
    for _ in range(1, count):
        while True:
            if is_increasing:
                delta = max(0, random.normalvariate(step, step/3))
            else:
                delta = min(0, random.normalvariate(step, step/3))
            if delta != 0:
                break
        a = seq[-1] + delta
        seq.append(a)
    return seq

def generate_random_seq(
                        mu: float, 
                        sigma: float, 
                        count: int, 
                        lotSz: float,
                        minSz: float,
                        ) -> List[float]:
    '''
    随机生成一串均值为mu, 方差为sigma, 长度为count的正随机数序列
    '''
    seq = []
    for _ in range(count):
        t = round(random.normalvariate(mu, sigma), get_significant_digits(lotSz))
        v = max(minSz, t)
        seq.append(v)
    return seq

def valid_Ccy(ccy: str) -> bool:
    '''
    检查币种是否合法
    '''
    # all char in ccy should be in [a-zA-Z, 0-9]
    # TODO: check if ccy is in the list of supported ccy
    for c in ccy:
        if not (c.isalpha() or c.isdigit()):
            return False
    return True

def validate_currency(method: Callable) -> Callable:
    def wrapper(self, key: str, *args, **kwargs):
        assert valid_Ccy(key), f"Invalid currency {key}"
        return method(self, key, *args, **kwargs)
    return wrapper