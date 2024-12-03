import asyncio
import websockets
import random
import json
import time

# 定义WebSocket服务器地址
WEBSOCKET_SERVER_URL = 'ws://localhost:4321'

# 用于测试的中文句子列表（您可以添加更多长文本）
SAMPLE_TEXTS = [
    "你好，世界！这是一个测试。",
    "在很久很久以前，有一个美丽的公主，她住在一座高高的城堡里，等待着她的骑士。",
    "生活就像一盒巧克力，你永远不知道你会得到什么。",
    "天空中最亮的星，能否听清，那仰望的人，心底的孤独和叹息。",
    "当你凝视深渊时，深渊也在凝视着你。这是人生的哲理。",
    "道路是曲折的，前途是光明的，坚持就是胜利。",
    "知识就是力量，这是永恒的真理，我们应该不断学习。",
    "春眠不觉晓，处处闻啼鸟。夜来风雨声，花落知多少。",
    "山不在高，有仙则名；水不在深，有龙则灵。斯是陋室，惟吾德馨。",
    "明月几时有，把酒问青天。不知天上宫阙，今夕是何年。",
    "天生我材必有用，千金散尽还复来。烹羊宰牛且为乐，会须一饮三百杯。",
    "苟利国家生死以，岂因祸福避趋之。我的信仰坚定不移。",
    "曾经沧海难为水，除却巫山不是云。取次花丛懒回顾，半缘修道半缘君。",
    "路漫漫其修远兮，吾将上下而求索。坚持不懈，终会成功。",
    "长风破浪会有时，直挂云帆济沧海。我们要有远大的志向。",
    "君不见黄河之水天上来，奔流到海不复回。人生短暂，当及时行乐。",
    "人生自古谁无死，留取丹心照汗青。忠诚是最宝贵的品质。",
    "海内存知己，天涯若比邻。朋友，无论多远都在心中。",
    "会当凌绝顶，一览众山小。站得高，才能看得远。",
    "大江东去，浪淘尽，千古风流人物。历史的洪流滚滚向前。",
    "红酥手，黄藤酒，满城春色宫墙柳。东风恶，欢情薄，一怀愁绪，几年离索。",
    "黑夜给了我黑色的眼睛，我却用它寻找光明。",
    "如果你不能忍受我最差的一面，那么你也不值得拥有我最好的一面。",
    "世界上只有一种真正的英雄主义，那就是认清生活的真相后依然热爱生活。",
    "所有的光鲜亮丽，都抵不过时间，并且时间会证明一切。",
    "每一个不曾起舞的日子，都是对生命的辜负。",
    "人生就像一场旅行，不必在乎目的地，在乎的是沿途的风景以及看风景的心情。"
]

# 生成随机十六进制颜色
def random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

async def send_messages():
    async with websockets.connect(WEBSOCKET_SERVER_URL) as websocket:
        for _ in range(100):  # 您可以根据需要调整消息数量
            text = random.choice(SAMPLE_TEXTS)
            y_position = random.randint(500, 1000)
            chinese_color = random_color()
            english_color = random_color()
            timeout = random.uniform(3, 10)  # 超时时间在3到10秒之间
            height = random.randint(100, 300)
            message = {
                'text': text,
                'y_position': y_position,
                'chinese_color': chinese_color,
                'english_color': english_color,
                'timeout': timeout,
                'height': height
            }
            # 将消息作为JSON发送
            await websocket.send(json.dumps(message))
            print(f"发送消息: {message}")
            # 等待0.5到5秒的随机间隔
            wait_time = random.uniform(0.5, 5)
            await asyncio.sleep(wait_time)

if __name__ == "__main__":
    asyncio.run(send_messages())
