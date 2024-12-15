import time
import yfinance as yf

from tests_huobi.config import config
from tests_huobi.strategy import strategy

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(subject, message, to_email):
    # 邮件发送者的邮箱和密码
    sender_email = config["sender_email"]
    sender_password = config["sender_password"]
    receiver_email = config["receiver_email"]

    # 创建邮件对象
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # 添加邮件正文
    msg.attach(MIMEText(message, 'plain'))

    # 连接到服务器
    with smtplib.SMTP_SSL("smtp.163.com", 465) as server:
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
    print("Email sent!")



def should_buy(current_price, fifty_two_week_high, conditions):
    if 'drop_percentage_from_52week_high' in conditions:
        drop_percentage = (fifty_two_week_high - current_price) / fifty_two_week_high * 100
        if drop_percentage >= conditions['drop_percentage_from_52week_high']:
            return True
    if 'price_below' in conditions and current_price <= conditions['price_below']:
        return True
    return False

def main():
    total_capital = strategy['total_capital']

    while not all(investment['purchased'] for investment in strategy['investments']):
        for investment in strategy['investments']:
            if not investment['purchased']:
                ticker = yf.Ticker(investment['asset'])
                info = ticker.info

                current_price = info['regularMarketPreviousClose']
                fifty_two_week_high = info.get('fiftyTwoWeekHigh', float('inf'))
                drop_percentage = (fifty_two_week_high - current_price) / fifty_two_week_high * 100

                print(f"{investment['name']} 当前价格: {current_price}, 相对于最高点跌幅: {drop_percentage:.2f}%")

                if should_buy(current_price, fifty_two_week_high, investment['conditions']):
                    investment_amount = total_capital * investment['position']
                    print(f"Buy {investment['asset']}: {investment_amount} USD at price {current_price}")
                    investment['purchased'] = True  # 标记为已购买

                    # 发送邮件通知
                    subject = f"Purchase Recommendation for {investment['asset']}"
                    message = (
                        f"现在{investment['asset']}的价格为{current_price}，已经相比最近高点下跌{fifty_two_week_high - current_price}，"
                        f"跌幅为{drop_percentage:.2f}%。根据您之前的配置，您应该用{investment_amount:.2f} USD购买它。"
                    )
                    send_email(subject, message, "receiver_email@example.com")

        time.sleep(60)


if __name__ == "__main__":
    main()
