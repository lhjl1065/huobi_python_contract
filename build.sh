if [ ! -f "../config.py" ]; then
    echo "错误：config.py 文件不存在。"
    exit 1
fi

# 定义要检查的域名列表
declare -a urls=(
    "www.okx.com"
    "api.hbdm.com/v2/market-status"
    "fapi.binance.com/fapi/v1/ping"
    "dapi.binance.com/dapi/v1/ping"
)

# 检查每个域名是否可访问
for url in "${urls[@]}"; do
    if ! curl -L --output /dev/null --silent --head --fail "https://$url"; then
        echo "错误：无法访问 $url"
        exit 1
    else
        echo "访问测试通过：$url"
    fi
done

cp ../config.py ./tests_huobi/ &&
tar -cvf huobi_python_contract-main.tar . &&
docker build -t get_coin_statistic . &&
docker run -it -v /usr/local/output:/output get_coin_statistic