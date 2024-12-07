FROM python:3.12.8-slim

# 设置工作目录
WORKDIR /app

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

RUN cd /app && python -m examples.statistics_of_funding
RUN cd /app && python -m examples.send_email2

# 创建一个cron文件来添加任
# 注意切换到examples目录下执行Python脚本，并且send_email2.py比statistics_of_funding.py晚30秒执行
RUN echo "1 0,8,16 * * * cd /app && /usr/local/bin/python3 -m examples.statistics_of_funding >> /a.log 2>&1" > /etc/cron.d/my-cron-job
RUN echo "2 0,8,16 * * * cd /app && /usr/local/bin/python3 -m examples.send_email2 >> /a.log 2>&1" >> /etc/cron.d/my-cron-job

# 给cron文件设置权限
RUN chmod 0644 /etc/cron.d/my-cron-job

# 应用cron任务
RUN crontab /etc/cron.d/my-cron-job

# 运行cron
CMD ["cron", "-f"]