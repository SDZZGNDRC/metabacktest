from typing import List
import json
import sys

from utils.helper import get_instruments

'''
命令行参数: 原始数据的路径, 目标文件的路径
该脚本主要用于将原始的GET /api/v5/public/instruments?instId=SPOT数据提取特定的字段到指定的文件
'''

def extract(filePath: str, toPath = None) -> List[dict]:
    # Read json file
    with open(filePath, 'r', encoding='utf-8') as f:
        json_data = f.read()
    data_dict = json.loads(json_data)
    instruments = data_dict['data']
    result : List[dict] = []
    for i in instruments:
        d = {}
        d['instId'] = i['instId']
        d['baseCcy'] = i['baseCcy']
        d['quoteCcy'] = i['quoteCcy']
        d['listTime'] = int(i['listTime'])
        d['tickSz'] = i['tickSz']
        d['lotSz'] = i['lotSz']
        d['minSz'] = i['minSz']
        d['state'] = i['state']
        result.append(d)
    if toPath != None:
        final_data = {'instruments': result}
        with open(toPath, 'w', encoding='utf-8') as f:
            f.write(json.dumps(final_data, indent=4))
    return result

# defaultInstruments = extract(r'D:\Project\metabacktest\tmp\raw-okx-instruments-SPOT.json')
defaultInstruments = get_instruments('SPOT')['data']

if __name__ == "__main__":
    if len(sys.argv) == 3:
        extract(sys.argv[1], sys.argv[2])

        