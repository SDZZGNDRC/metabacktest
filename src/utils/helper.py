import requests
import json
import random
from typing import List, Union, Dict

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
    
    str_num = str(num)
    if '.' not in str_num:
        return len(str_num)
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
    result = {}
    tickers = get_tickers(instType)
    for ticker in tickers:
        result[ticker['instId']] = float(ticker['last'])
    
    return result


def generate_random_valueInt(v0, deviation) -> int:
    delta = v0 * deviation
    x = random.uniform(-delta, delta)
    return int(v0 + x)