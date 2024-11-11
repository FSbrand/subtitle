import requests
import time
import random

url = "http://localhost:4321/update_subtitle"
texts = [
    "这是第一个例子。",
    "第二条消息发送中。",
    "Python请求示例。",
    "第四条消息在这里。",
    "这是一条测试消息。",
    "发送不同的内容。",
    "这是一个随机消息。",
    "请求已发送。",
    "这是第九条消息。",
    "这是第十条信息。",
    "另一条信息发送中。",
    "这是第十二条消息。",
    "看看这条信息。",
    "这是一个测试。",
    "发送更多内容。",
    "这是第十六条消息。",
    "更改文本内容。",
    "随机选择消息。",
    "倒数第二条信息。",
    "这是最后一条消息。",
    "重新发送消息请求。",
    "第一次发送成功。",
    "继续测试效果。",
    "这是一个新消息。",
    "测试是否正常。",
    "请注意信息内容。",
    "快速发送消息。",
    "请求处理完毕。",
    "等待下一条消息。",
    "这是第十七条。",
    "新内容已发送。",
    "这是第十九条。",
    "正在传输消息。",
    "测试不同情况。",
    "结果将在这里。",
    "请确认收到信息。",
    "确认发送成功。",
    "这是第十五条。",
    "测试内容更新。",
    "这是最后一个例子。"
]
headers = {"Content-Type": "application/json"}

# 定义发送POST请求的函数
def send_post_request(url, data, headers):
    response = requests.post(url, json=data, headers=headers)
    print(response.status_code, response.text)

# 发送第一条请求，3秒后发送
time.sleep(4)
send_post_request(url, {
    "text": texts[0],
    "y_position": 1300,
    "chinese_color": random.choice(["black", "black"]),
    "english_color": random.choice(["black", "black"]),
    "timeout": 8,
    "height": 0
}, headers)

# 发送第二条请求，5秒后发送
time.sleep(0.5)
send_post_request(url, {
    "text": texts[1],
    "y_position": 1300,
    "chinese_color": random.choice(["white", "white"]),
    "english_color": random.choice(["white", "white"]),
    "timeout": 8,
    "height": 0
}, headers)

# 发送第三条请求，1秒后发送
time.sleep(2)
send_post_request(url, {
    "text": texts[2],
    "y_position": 1300,
    "chinese_color": random.choice(["black", "black"]),
    "english_color": random.choice(["black", "black"]),
    "timeout": 8,
    "height": 0
}, headers)

# 发送剩余的请求，间隔随机1-6秒
for text in texts[3:]:
    color = random.choice(["black", "white"])
    # time.sleep(random.randint(1, 4))
    # 0.5秒 - 6秒 随机
    # time.sleep(random.uniform(0.5, 6))
    time.sleep(0.3)
    send_post_request(url, {
        "text": text,
        "y_position": 1300,
        "chinese_color": color,
        "english_color": color,
        "timeout": 8,
        "height": 0
    }, headers)