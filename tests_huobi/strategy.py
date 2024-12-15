# strategy.py

strategy = {
    "total_capital": 2000,
    "investments": [
        {
            "asset": "BTC-USD",
            "name": "比特币",
            "conditions": {
                "drop_percentage_from_52week_high": 30
            },
            "position": 0.1,
            "purchased": False  # 添加购买状态标志
        },
        {
            "asset": "BTC-USD",
            "name": "比特币",
            "conditions": {
                "drop_percentage_from_52week_high": 50
            },
            "position": 0.1,
            "purchased": False  # 添加购买状态标志
        },
        {
            "asset": "BTC-USD",
            "name": "比特币",
            "conditions": {
                "drop_percentage_from_52week_high": 70
            },
            "position": 0.1,
            "purchased": False  # 添加购买状态标志
        },
        {
            "asset": "^IXIC",
            "name": "纳斯达克指数",
            "conditions": {
                "drop_percentage_from_52week_high": 25
            },
            "position": 0.1,
            "purchased": False
        },
        {
            "asset": "^IXIC",
            "name": "纳斯达克指数",
            "conditions": {
                "drop_percentage_from_52week_high": 35
            },
            "position": 0.1,
            "purchased": False
        },
        {
            "asset": "^IXIC",
            "name": "纳斯达克指数",
            "conditions": {
                "drop_percentage_from_52week_high": 45
            },
            "position": 0.1,
            "purchased": False
        },
        {
            "asset": "000001.SS",
            "name": "上证指数",
            "conditions": {
                "price_below": 2700
            },
            "position": 0.1,
            "purchased": False
        },
        {
            "asset": "^GSPC",
            "name": "标普500",
            "conditions": {
                "drop_percentage_from_52week_high": 40
            },
            "position": 0.1,
            "purchased": False
        }
    ]
}
