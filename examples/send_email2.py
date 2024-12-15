import smtplib
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

from tests_huobi.config import config


def find_closest_time_records():
    # 读取Excel文件
    df = pd.read_excel('../output/rate_records.xlsx')

    # 确保时间列是datetime类型
    df['时间'] = pd.to_datetime(df['时间'])

    # 计算当前时间
    now = datetime.now()

    # 计算当前日期的零点、8点和16点
    today = now.date()
    times_of_interest = [datetime(today.year, today.month, today.day, h) for h in (0, 8, 16)]

    # 如果当前时间小于今天的零点，则考虑昨天的零点、8点和16点
    if now < times_of_interest[0]:
        yesterday = today - timedelta(days=1)
        times_of_interest = [datetime(yesterday.year, yesterday.month, yesterday.day, h) for h in (0, 8, 16)]

    # 找到距离当前时间最近的过去时间点
    closest_time = max([t for t in times_of_interest if t <= now])

    # 找到与最接近的时间相匹配的所有记录
    closest_records = df[df['时间'].dt.floor('H') == closest_time]

    return closest_records

def send_email():
    sender_email = config["sender_email"]
    receiver_email = config["receiver_email"]
    password = config["sender_password"]

    message = MIMEMultipart("alternative")
    message["Subject"] = "Funding Rate Details"
    message["From"] = sender_email
    message["To"] = receiver_email

    # 获取最接近时间的记录
    records = find_closest_time_records()

    # 计算USDT总和
    total_usdt = records['usdt'].sum()

    # 构造HTML内容
    html = """\
    <html>
      <head>
        <style>
          body {{ font-family: Arial, sans-serif; }}
          table {{
            width: 100%;
            border-collapse: collapse;
            border: 1px solid #ccc;
            font-size: 14px;
          }}
          th, td {{
            border: 1px solid #ccc;
            padding: 10px;
            text-align: left;
          }}
          th {{
            background-color: #f2f2f2;
            font-weight: bold;
          }}
          tr:nth-child(even) {{
            background-color: #f9f9f9;
          }}
        </style>
      </head>
      <body>
        <h2>Funding Rate Table</h2>
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Exchange</th>
              <th>Currency</th>
              <th>Funding Rate</th>
              <th>Funding Fee</th>
              <th>USDT</th>
              <th>Remarks</th>
            </tr>
          </thead>
          <tbody>"""
    for _, row in records.iterrows():
        html += f"""\
            <tr>
              <td>{row['时间'].strftime('%Y-%m-%d %H:%M')}</td>
              <td>{row['交易所']}</td>
              <td>{row['币种']}</td>
              <td>{row['资金费率']}</td>
              <td>{row['资金费']:.4f}</td>
              <td>{row['usdt']:.2f}</td>
              <td>{row['备注']}</td>
            </tr>"""
    html += f"""\
          </tbody>
        </table>
        <p>Total USDT collected at {records.iloc[0]['时间'].strftime('%Y-%m-%d %H:%M:%S')}: {total_usdt:.2f} USDT</p>
      </body>
    </html>
    """

    # Turn this into an html MIMEText object
    part = MIMEText(html, "html")

    # Add HTML part to MIMEMultipart message
    message.attach(part)

    # Create secure connection with server and send email
    with smtplib.SMTP_SSL("smtp.163.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

    print("Email sent!")



send_email()