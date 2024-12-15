FROM python:3.12.8-slim
ARG ADD_HOST
# 设置工作目录
WORKDIR /app

# 设置时区
ENV TZ=Asia/Shanghai
RUN apt-get update && apt-get install -y tzdata \
    && ln -fs /usr/share/zoneinfo/$TZ /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata
# 将项目压缩包复制到容器内
COPY huobi_python_contract-main.tar /app/

# 解压项目压缩包
RUN tar -xvf huobi_python_contract-main.tar
# 创建输出文件夹
RUN mkdir /output
# 安装Python依赖
# 假设解压后的目录名为huobi_python_contract-main，且requirements.txt在该目录下
RUN pip install --no-cache-dir -r requirements.txt

# 安装cron服务
RUN apt-get update && apt-get -y install cron
RUN if [ "$ADD_HOST" = "false" ]; then python -m examples.statistics_of_funding; fi
RUN if [ "$ADD_HOST" = "false" ]; then python -m examples.send_email2; fi

# 创建一个cron文件来添加任
# 注意切换到examples目录下执行Python脚本，并且send_email2.py比statistics_of_funding.py晚30秒执行
RUN echo "1 0,8,16 * * * cd /app && /usr/local/bin/python3 -m examples.statistics_of_funding >> /a.log 2>&1" > /etc/cron.d/my-cron-job
RUN echo "2 0,8,16 * * * cd /app && /usr/local/bin/python3 -m examples.send_email2 >> /a.log 2>&1" >> /etc/cron.d/my-cron-job

# 给cron文件设置权限
RUN chmod 0644 /etc/cron.d/my-cron-job

# 应用cron任务
RUN crontab /etc/cron.d/my-cron-job

# 定义容器启动时执行的命令
CMD cd /app && python3 -m examples.my_transaction_decision _script && cron -f
