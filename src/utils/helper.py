import requests
import json
from typing import List

proxies = {
   'http': 'http://127.0.0.1:7890',
   'https': 'http://127.0.0.1:7890',
}

def get_significant_digits(num):
    '''
    给定形如0.0001的数字, 判断它的有效位数
    '''
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