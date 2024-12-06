cp ../config.py ./tests_huobi/
tar -cvf huobi_python_contract-main.tar .
docker build -t get_coin_statistic .