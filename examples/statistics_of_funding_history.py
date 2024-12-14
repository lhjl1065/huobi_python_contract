import asyncio
import os
import re

import requests
import pandas as pd
from datetime import datetime

from binance.cm_futures import CMFutures
from binance.um_futures import UMFutures
from okx import PublicData, Account
from openpyxl.utils import get_column_letter

from alpha.platforms.huobi_coin_swap.restapi.rest_account_coin_swap import HuobiCoinSwapRestAccountAPI
from alpha.platforms.huobi_coin_swap.restapi.rest_market_coin_swap import HuobiCoinSwapRestMarketAPI
from alpha.platforms.huobi_coin_swap.restapi.rest_reference_coin_swap import HuobiCoinSwapRestReferenceAPI
from tests_huobi.config import config

symbol_mapping = {
    'BTCUSD': {
        'Huobi': 'BTC-USD',
        'Binance': 'BTCUSD_PERP',
        'Okx': 'DOGE-USD-SWAP'
    },
    'ETHUSD': {
        'Huobi': 'ETH-USD',
        'Binance': 'ETHUSD_PERP',
        'Okx': 'ETH-USD-SWAP'
    },
    'DOGEUSD': {
        'Huobi': 'DOGE-USD',
        'Binance': 'DOGEUSD_PERP',
        'Okx': 'DOGE-USD-SWAP'
    },
    'XRPUSD': {
        'Huobi': 'XRP-USD',
        'Binance': 'XRPUSD_PERP',
        'Okx': 'XEP-USD-SWAP'
    },
    'ADAUSD': {
        'Huobi': 'ADA-USD',
        'Binance': 'ADAUSD_PERP',
        'Okx': 'ADA-USD-SWAP'
    },
    'DOTUSD': {
        'Huobi': 'DOT-USD',
        'Binance': 'DOTUSD_PERP',
        'Okx': 'DOT-USD-SWAP'
    }
}


def camel_to_snake(name):
    """
    将驼峰形式字符串转换为下划线形式
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def convert_columns_to_snake_case(df):
    """
    将DataFrame的列名从驼峰命名转换为下划线命名
    """
    df.columns = [camel_to_snake(col) for col in df.columns]
    return df


# 定义获取资金费率的函数
def get_funding_rates(exchange, generic_symbol):
    global time
    symbol = symbol_mapping[generic_symbol][exchange]
    if exchange == 'Huobi':
        df = get_all_funding_rates_huobi(symbol)
    elif exchange == 'Binance':
        df = get_all_funding_rates_binance(symbol)
    elif exchange == 'Okx':
        df = get_all_funding_rates_okx(symbol)

    return df


def get_all_funding_rates_huobi(symbol):
    page_index = 1
    page_size = 100  # 假设API最多允许每页100条数据
    all_data = []

    while True:
        response = loop.run_until_complete(
            huobi_api['reference'].get_swap_historical_funding_rate(symbol, page_size=100, page_index=page_index))
        data = response[0]

        if data['status'] == 'ok':
            all_data.extend(data['data']['data'])
            total_pages = data['data']['total_page']
            if page_index >= total_pages:
                break
            page_index += 1
        else:
            print("API请求错误:", data['status'])
            break
    all_data_sorted = sorted(all_data, key=lambda x: int(x['funding_time']))
    for item in all_data_sorted:
        # 转换时间戳（毫秒）到 datetime 对象
        timestamp = int(item['funding_time']) / 1000
        item['funding_time'] = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        item['avg_premium_index_show'] = f"{float(item['avg_premium_index']) * 100:.4f}%"
        item['funding_rate_show'] = f"{float(item['funding_rate']) * 100:.4f}%"
        item['funding_rate'] = float(item['funding_rate']) * 100000
    df = pd.DataFrame(all_data_sorted)
    df = df.drop(['realized_rate', 'fee_asset', 'symbol'], axis=1)
    # 列出所有列名，将 'funding_time' 放在第一位
    columns_ordered = ['funding_time', 'contract_code', 'avg_premium_index_show', 'funding_rate_show',
                       'avg_premium_index', 'funding_rate']
    # 使用新的列顺序重新索引 DataFrame
    df = df[columns_ordered]
    return df


def get_all_funding_rates_binance(symbol):
    all_data = []
    api = binance_api['coin' if symbol.endswith('PERP') else 'usdt']
    statTime = 1597075200000  # 设置初始的 statTime
    endTime = 1597075200000 + 999 * 8 * 3600 * 1000  # 设置初始的 endTime
    limit = 1000

    while True:
        if limit == 0 or limit == 1:
            break  # 历史数据获取完毕
        # 请求数据
        rate_response = api.funding_rate(symbol=symbol, limit=limit, statTime=statTime, endTime=endTime)

        # 检查返回的数据

        # 添加数据到 all_data 列表
        all_data.extend(rate_response)

        # 更新 statTime 为最后一条记录的 fundingTime 加上8小时的毫秒数
        last_funding_time = rate_response[-1]['fundingTime']
        statTime = last_funding_time + 8 * 3600 * 1000  # 8小时的毫秒数
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_timestamp = int(today.timestamp() * 1000)
        endTime = min(statTime + 999 * 8 * 3600 * 1000, today_timestamp)
        limit = int(((endTime - statTime) / (8 * 3600 * 1000)) + 1)
    all_data_sorted = sorted(all_data, key=lambda x: int(x['fundingTime']))
    for item in all_data_sorted:
        # 转换时间戳（毫秒）到 datetime 对象
        timestamp = int(item['fundingTime']) / 1000
        item['fundingTime'] = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        item['fundingRateShow'] = f"{float(item['fundingRate']) * 100:.4f}%"
        item['fundingRate'] = float(item['fundingRate']) * 100000
    df = pd.DataFrame(all_data_sorted)
    # 列出所有列名，将 'funding_time' 放在第一位
    columns_ordered = ['fundingTime', 'symbol', 'fundingRateShow', 'markPrice', 'fundingRate']
    # 使用新的列顺序重新索引 DataFrame
    df = df[columns_ordered]
    df = convert_columns_to_snake_case(df)
    return df

def get_all_funding_rates_okx(symbol):
    all_data = []
    api = okx_api['public_data']
    rate_response = api.funding_rate_history(symbol, before=1672560000, after=1672531200)
    time = datetime.fromtimestamp(float(rate_response['data'][0]['fundingTime']) / 1000)
    rate = float(rate_response['data'][0]['fundingRate'])
    rate_show_str = f"{rate * 100:.4f}%"
    record_response = self.okx_api['account'].get_account_bills(instType='SWAP', ccy=contract.split('-')[0], type=8,
                                                                limit=1, )
    price = float(record_response['data'][0]['px'])
    amount = float(record_response['data'][0]['balChg'])

    while True:
        if limit == 0 | limit == 1:
            break  # 历史数据获取完毕
        # 请求数据
        rate_response = api.funding_rate(symbol=symbol, limit=limit, statTime=statTime, endTime=endTime)

        # 检查返回的数据

        # 添加数据到 all_data 列表
        all_data.extend(rate_response)

        # 更新 statTime 为最后一条记录的 fundingTime 加上8小时的毫秒数
        last_funding_time = rate_response[-1]['fundingTime']
        statTime = last_funding_time + 8 * 3600 * 1000  # 8小时的毫秒数
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_timestamp = int(today.timestamp() * 1000)
        endTime = min(statTime + 999 * 8 * 3600 * 1000, today_timestamp)
        limit = int(((endTime - statTime) / (8 * 3600 * 1000)) + 1)
    all_data_sorted = sorted(all_data, key=lambda x: int(x['fundingTime']))
    for item in all_data_sorted:
        # 转换时间戳（毫秒）到 datetime 对象
        timestamp = int(item['fundingTime']) / 1000
        item['fundingTime'] = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        item['fundingRateShow'] = f"{float(item['fundingRate']) * 100:.4f}%"
        item['fundingRate'] = float(item['fundingRate']) * 100000
    df = pd.DataFrame(all_data_sorted)
    # 列出所有列名，将 'funding_time' 放在第一位
    columns_ordered = ['fundingTime', 'symbol', 'fundingRateShow', 'markPrice', 'fundingRate']
    # 使用新的列顺序重新索引 DataFrame
    df = df[columns_ordered]
    df = convert_columns_to_snake_case(df)
    return df


# 初始化
loop = asyncio.get_event_loop()
huobi_api = {
    'reference': HuobiCoinSwapRestReferenceAPI(config["huobi_host"], config["huobi_access_key"],
                                               config["huobi_secret_key"]),
    'account': HuobiCoinSwapRestAccountAPI(config["huobi_host"], config["huobi_access_key"],
                                           config["huobi_secret_key"]),
    'market': HuobiCoinSwapRestMarketAPI(config["huobi_host"], config["huobi_access_key"],
                                         config["huobi_secret_key"]),
}
binance_api = {
    'coin': CMFutures(key=config["binance_access_key"], secret=config["binance_secret_key"]),
    'usdt': UMFutures(key=config["binance_access_key"], secret=config["binance_secret_key"]),
}
okx_api = {
    'public_data': PublicData.PublicAPI(config["okx_access_key"], config["okx_secret_key"], config["okx_passphrase"],
                                        flag="0"),
    'account': Account.AccountAPI(config["okx_access_key"], config["okx_secret_key"], config["okx_passphrase"],
                                  flag="0"),
}
# 设置查询参数
exchanges = ['Binance', 'Huobi']
generic_symbols = ['BTCUSD', 'ETHUSD', 'DOGEUSD', 'ADAUSD', 'XRPUSD', 'DOTUSD']

# 收集所有数据
all_data = []
for exchange in exchanges:
    for generic_symbol in generic_symbols:
        df = get_funding_rates(exchange, generic_symbol)
        df['funding_rate'] = pd.to_numeric(df['funding_rate'], errors='coerce')
        average_rates = df['funding_rate'].mean()
        average_rates_show = f"{average_rates / 1000:.4f}%"
        print("exchange: " + exchange + ", code:" + generic_symbol + ", average_rates" + average_rates_show)
        file_name = 'funding_rate_history.xlsx'
        # 检查文件是否存在以决定模式
        if os.path.isfile(file_name):
            mode = 'a'  # 文件存在，使用追加模式
        else:
            mode = 'w'  # 文件不存在，使用写模式

        with pd.ExcelWriter(file_name, engine='openpyxl', mode=mode) as writer:
            # 将DataFrame写入Excel文件
            df.to_excel(writer, sheet_name=exchange + '-' + generic_symbol, index=False)

            # 获取工作簿和工作表对象
            workbook = writer.book
            worksheet = workbook[exchange + '-' + generic_symbol]

            # 设置列宽
            column_widths = [30, 10, 16, 18, 20, 20]  # 每列的宽度
            for i, column_width in enumerate(column_widths, start=1):
                worksheet.column_dimensions[get_column_letter(i)].width = column_width
