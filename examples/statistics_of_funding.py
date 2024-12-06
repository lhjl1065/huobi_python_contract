import asyncio
import os
import sys
import unittest

from alpha.platforms.huobi_coin_swap.restapi.rest_account_coin_swap import HuobiCoinSwapRestAccountAPI
from alpha.platforms.huobi_coin_swap.restapi.rest_market_coin_swap import HuobiCoinSwapRestMarketAPI
from alpha.platforms.huobi_coin_swap.restapi.rest_reference_coin_swap import HuobiCoinSwapRestReferenceAPI
import pandas as pd
from datetime import datetime

from binance.cm_futures import CMFutures
from binance.um_futures import UMFutures

from tests_huobi.config import config

sys.path.append('..')


class TestRestAccountCoinSwap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.get_event_loop()
        cls.reference_huobi_api = HuobiCoinSwapRestReferenceAPI(config["huobi_host"], config["huobi_access_key"],
                                                                config["huobi_secret_key"])
        cls.account_huobi_api = HuobiCoinSwapRestAccountAPI(config["huobi_host"], config["huobi_access_key"],
                                                            config["huobi_secret_key"])
        cls.market_huobi_api = HuobiCoinSwapRestMarketAPI(config["huobi_host"], config["huobi_access_key"],
                                                          config["huobi_secret_key"])
        cls.binance_coin_api = CMFutures(key=config["binance_access_key"], secret=config["binance_secret_key"])
        cls.binance_usdt_api = UMFutures(key=config["binance_access_key"], secret=config["binance_secret_key"])

    @classmethod
    def tearDownClass(cls):

        cls.loop.close()  # 关闭事件循环

    def test_get_swap_historical_funding_rate(self):

        self.statistics_of_funding_fees_huobi('Huobi')
        self.statistics_of_funding_fees_binance('Binance')

    def statistics_of_funding_fees_huobi(self, exchange):
        self.statistics_of_funding_fees_huobi_for_contract_code(exchange, "DOGE-USD")
        self.statistics_of_funding_fees_huobi_for_contract_code(exchange, "ADA-USD")
        self.statistics_of_funding_fees_huobi_for_contract_code(exchange, "XRP-USD")

    def statistics_of_funding_fees_binance(self, exchange):
        self.statistics_of_funding_fees_binance_for_contract_code(exchange, "DOGEUSD_PERP")
        self.statistics_of_funding_fees_binance_for_contract_code(exchange, 'ETHUSDT')

    def statistics_of_funding_fees_huobi_for_contract_code(self, exchange, contract_code):
        datetime, huobi_rate, huobi_condition, huobi_record_amount, huobi_price = self.get_funding_rate_huobi(
            contract_code)
        self.ouput_excel(exchange, datetime, contract_code, huobi_rate, huobi_condition, huobi_record_amount,
                         huobi_price)

    def statistics_of_funding_fees_binance_for_contract_code(self, exchange, contract_code):
        date_time, binance_rate, binance_condition, binance_record_amount, binance_price = self.get_funding_rate_binance(
            contract_code)
        self.ouput_excel(exchange, date_time, contract_code, binance_rate, binance_condition, binance_record_amount,
                         binance_price)

    def get_funding_rate_huobi(self, category):
        huobi_rate_result = self.loop.run_until_complete(
            self.reference_huobi_api.get_swap_historical_funding_rate(category))
        print(huobi_rate_result[0]['data']['data'][0]['funding_rate'])
        date_time = datetime.fromtimestamp(float(huobi_rate_result[0]['data']['data'][0]['funding_time']) / 1000)
        huobi_rate = f"{float(huobi_rate_result[0]['data']['data'][0]['funding_rate']) * 100:.4f}%"
        huobi_condition = self.evaluate_funding_rate(float(huobi_rate_result[0]['data']['data'][0]['funding_rate']))

        huobi_record_result = self.loop.run_until_complete(
            self.account_huobi_api.get_swap_financial_record(contract=category, type=30 if float(
                huobi_rate_result[0]['data']['data'][0]['funding_rate']) > 0 else 31, direct="prev"))

        print(huobi_record_result[1]['data'][0]['amount'])

        huobi_price_result = self.loop.run_until_complete(
            self.market_huobi_api.get_swap_mark_price_kline(category, '1min', 1))
        print(huobi_price_result[0]['data'][0]['close'])
        return date_time, huobi_rate, huobi_condition, huobi_record_result[1]['data'][0]['amount'], \
        huobi_price_result[0]['data'][0]['close']

    def get_funding_rate_binance(self, contract_code):
        # get server time

        # Get account information
        if contract_code.endswith('PERP'):
            binance_rate_result = self.binance_coin_api.funding_rate(symbol=contract_code, limit=1)
            binance_record = self.binance_coin_api.get_income_history(symbol=contract_code, limit=1,
                                                                      incomeType="FUNDING_FEE")
            binance_price_result = self.binance_coin_api.ticker_price(symbol=contract_code)
            binance_price = binance_price_result[0]['price']
            binance_amount = float(binance_record[0]['income'])
        else:
            binance_rate_result = self.binance_usdt_api.funding_rate(symbol=contract_code, limit=1)
            binance_record = self.binance_usdt_api.get_income_history(symbol=contract_code, limit=1,
                                                                      incomeType="FUNDING_FEE")
            binance_price_result = self.binance_usdt_api.ticker_price(symbol=contract_code)
            binance_price = binance_price_result['price']
            binance_amount = float(binance_record[0]['income']) / float(binance_price)
        print(binance_rate_result[0]['fundingRate'])
        date_time = datetime.fromtimestamp(float(binance_rate_result[0]['fundingTime']) / 1000)
        binance_rate = f"{float(binance_rate_result[0]['fundingRate']) * 100:.4f}%"
        binance_condition = self.evaluate_funding_rate(float(binance_rate_result[0]['fundingRate']))

        print(binance_price)
        return date_time, binance_rate, binance_condition, binance_amount, binance_price

    def ouput_excel(self, exchange, date_time, contract_code, rate, condition, record_amount, price):
        # 创建示例数据字典
        data = {
            '时间': [date_time],
            '交易所': [exchange],
            '币种': [contract_code],
            '资金费率': [rate],
            '资金费': [record_amount],
            'usdt': [float(price) * float(record_amount)],
            '备注': [condition]
        }

        # 将数据字典转换为DataFrame
        df_new = pd.DataFrame(data)

        # 指定Excel文件路径
        file_path = '资金费记录.xlsx'

        # 检查文件是否存在
        if not os.path.exists(file_path):
            # 如果文件不存在，直接将新DataFrame保存为Excel文件
            df_new.to_excel(file_path, index=False)
        else:
            # 如果文件存在，读取现有数据
            df_existing = pd.read_excel(file_path)

            # 检查是否有相同的'日期', '交易所', '币种'
            mask = (df_existing['时间'] == df_new['时间'][0]) & \
                   (df_existing['交易所'] == df_new['交易所'][0]) & \
                   (df_existing['币种'] == df_new['币种'][0])

            if mask.any():
                # 如果找到匹配的行，更新这些行
                index_to_update = df_existing[mask].index
                for col in df_new.columns:
                    df_existing.loc[index_to_update, col] = df_new[col][0]
            else:
                # 如果没有找到匹配的行，追加新数据
                df_existing = pd.concat([df_existing, df_new], ignore_index=True)

            # 将更新后的DataFrame写回Excel文件
            with pd.ExcelWriter(file_path, engine='openpyxl', mode='w') as writer:
                df_existing.to_excel(writer, index=False)

        print("数据已保存到Excel文件！")

    @staticmethod
    def evaluate_funding_rate(rate):
        if rate < 0:
            return "亏损"
        elif 0 <= rate < 0.0001:
            return "较低"
        elif rate == 0.0001:
            return "默认"
        elif 0.0001 < rate < 0.0005:
            return "较高"
        elif 0.0005 <= rate < 0.0012:
            return "高"
        elif rate >= 0.0013:
            return "极高"
        else:
            return "未知"  # 以防万一输入的数据不符合以上任何条件


if __name__ == '__main__':
    unittest.main(verbosity=2)
