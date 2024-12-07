#!/bin/bash

if [ ! -f "../config.py" ]; then
    echo "错误：config.py 文件不存在。"
    exit 1
fi

ADD_HOST=false

# 解析命令行参数
while [[ "$#" -gt 0 ]]; do
    case "\$1" in
        --addhost) ADD_HOST=true ;;
        *) echo "Unknown parameter passed: \$1"; exit 1 ;;
    esac
    shift
done

# 定义要检查的域名列表
declare -a urls=(
    "www.okx.com"
    "api.hbdm.com/swap-api/v1/swap_api_state"
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
docker build --build-arg ADD_HOST=$ADD_HOST -t get_coin_statistic .

# 根据 ADD_HOST 变量决定是否使用 --add-host
if $ADD_HOST; then
    docker run -it --add-host=www.okx.com:8.210.36.204 -v /usr/local/output:/output get_coin_statistic
else
    docker run -it -v /usr/local/output:/output get_coin_statistic
fi
