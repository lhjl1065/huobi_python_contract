import sys
import time
import unittest

from alpha.platforms.huobi_coin_swap.websocket.ws_index_coin_swap import WsIndex
from alpha.utils import logger

sys.path.append('..')


class TestWsIndexCoinSwap(unittest.TestCase):
    def _callback_1(self, jdata):
        logger.info('_callback_1:{}'.format(jdata))

    def _callback_2(self, jdata):
        logger.info('_callback_2:{}'.format(jdata))

    def test_sub(self):
        ws1 = WsIndex()
        data = {"sub": "market.BTC-USDT.index.1min"}
        ws1.sub(data, self._callback_1)

        ws2 = WsIndex()
        data = {"sub": "market.ETH-USDT.basis.1min.open"}
        ws2.sub(data, self._callback_2)

        time.sleep(60)
        ws1.close()
        ws2.close()

    def test_req(self):
        ws1 = WsIndex()
        data = {"req": "market.BTC-USDT.index.1min",
                "from": 1614320780, "to": 1614321780}
        ws1.req(data, self._callback_1)

        ws2 = WsIndex()
        data = {"req": "market.ETH-USDT.basis.1min.open",
                "from": 1614321780, "to": 1614321780}
        ws2.req(data, self._callback_2)

        time.sleep(60)
        ws1.close()
        ws2.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)