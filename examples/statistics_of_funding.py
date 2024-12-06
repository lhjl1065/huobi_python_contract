import asyncio
import os
import sys
import unittest
import pandas as pd
from datetime import datetime

from okx import PublicData, Account

from alpha.platforms.huobi_coin_swap.restapi.rest_account_coin_swap import HuobiCoinSwapRestAccountAPI
from alpha.platforms.huobi_coin_swap.restapi.rest_market_coin_swap import HuobiCoinSwapRestMarketAPI
from alpha.platforms.huobi_coin_swap.restapi.rest_reference_coin_swap import HuobiCoinSwapRestReferenceAPI

from binance.cm_futures import CMFutures
from binance.um_futures import UMFutures

from tests_huobi.config import config

sys.path.append('..')


class TestRestAccountCoinSwap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.get_event_loop()
        cls.huobi_api = {
            'reference': HuobiCoinSwapRestReferenceAPI(config["huobi_host"], config["huobi_access_key"],
                                                       config["huobi_secret_key"]),
            'account': HuobiCoinSwapRestAccountAPI(config["huobi_host"], config["huobi_access_key"],
                                                   config["huobi_secret_key"]),
            'market': HuobiCoinSwapRestMarketAPI(config["huobi_host"], config["huobi_access_key"],
                                                 config["huobi_secret_key"]),
        }
        cls.binance_api = {
            'coin': CMFutures(key=config["binance_access_key"], secret=config["binance_secret_key"]),
            'usdt': UMFutures(key=config["binance_access_key"], secret=config["binance_secret_key"]),
        }
        cls.okx_api = {
            'public_data': PublicData.PublicAPI(config["okx_access_key"], config["okx_secret_key"], config["okx_passphrase"], flag = "0"),
            'account': Account.AccountAPI(config["okx_access_key"], config["okx_secret_key"], config["okx_passphrase"], flag = "0"),
        }


    @classmethod
    def tearDownClass(cls):
        cls.loop.close()

    def test_get_swap_historical_funding_rate(self):
        self.calculate_funding_rates('Huobi', ['DOGE-USD', 'ADA-USD', 'XRP-USD'])
        self.calculate_funding_rates('Binance', ['DOGEUSD_PERP', 'ETHUSDT'])
        self.calculate_funding_rates('Okx', ['DOGE-USD-SWAP'])

    def calculate_funding_rates(self, exchange, contracts):
        for contract in contracts:
            date_time, rate, condition, record_amount, price = self.get_funding_rate(exchange, contract)
            self.output_to_excel(exchange, date_time, contract, rate, condition, record_amount, price)

    def get_funding_rate(self, exchange, contract):
        global time
        if exchange == 'Huobi':
            rate_response = self.loop.run_until_complete(
                self.huobi_api['reference'].get_swap_historical_funding_rate(contract))
            time = datetime.fromtimestamp(float(rate_response[0]['data']['data'][0]['funding_time']) / 1000)
            rate = float(rate_response[0]['data']['data'][0]['funding_rate'])
            rate_show_str = f"{rate * 100:.4f}%"
            record_response = self.loop.run_until_complete(
                self.huobi_api['account'].get_swap_financial_record(contract=contract,
                                                                    type=30 if rate > 0 else 31, direct="prev"))
            amount = float(record_response[1]['data'][0]['amount'])
            price_response = self.loop.run_until_complete(
                self.huobi_api['market'].get_swap_mark_price_kline(contract, '1min', 1))
            price = float(price_response[0]['data'][0]['close'])
        elif exchange == 'Binance':
            api = self.binance_api['coin' if contract.endswith('PERP') else 'usdt']
            rate_response = api.funding_rate(symbol=contract, limit=1)
            time = datetime.fromtimestamp(float(rate_response[0]['fundingTime']) / 1000)
            rate = float(rate_response[0]['fundingRate'])
            rate_show_str = f"{rate * 100:.4f}%"
            record_response = api.get_income_history(symbol=contract, limit=1, incomeType="FUNDING_FEE")
            price_response = api.ticker_price(symbol=contract)
            price = float(price_response[0]['price']) if contract.endswith('PERP') else float(price_response['price'])
            amount = float(record_response[0]['income']) if contract.endswith('PERP') else float(record_response[0]['income']) / price
        elif exchange == 'Okx':
            rate_response = self.okx_api['public_data'].funding_rate_history(contract, limit=1)
            time = datetime.fromtimestamp(float(rate_response['data'][0]['fundingTime']) / 1000)
            rate = float(rate_response['data'][0]['fundingRate'])
            rate_show_str = f"{rate * 100:.4f}%"
            record_response = self.okx_api['account'].get_account_bills(instType='SWAP', ccy=contract.split('-')[0], type=8, limit=1,)
            price = float(record_response['data'][0]['px'])
            amount = float(record_response['data'][0]['balChg'])
        condition = self.evaluate_funding_rate(rate)

        return time, rate_show_str, condition, amount, price

    def output_to_excel(self, exchange, date_time, contract, rate, condition, record_amount, price):
        data = {
            '时间': [date_time],
            '交易所': [exchange],
            '币种': [contract],
            '资金费率': [rate],
            '资金费': [record_amount],
            'usdt': [price * record_amount],
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
            return "未知"


if __name__ == '__main__':
    unittest.main(verbosity=2)
