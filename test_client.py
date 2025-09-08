# -*- coding: utf-8 -*-
"""
WebSocket测试客户端
用于测试字幕软件的WebSocket接口
"""

import asyncio
import websockets
import json
import random
import argparse
import sys
from config import NETWORK_CONFIG

# 测试文本样本
SAMPLE_TEXTS = [
    "Please send me the updated documents",
    "你好，世界！",
    "Hello, world!",
    "这是一个字幕测试。",
    "Please send me the updated documents",
    "This is a subtitle test.",
    "生活就像一盒巧克力，你永远不知道你会得到什么。",
    "Life is like a box of chocolates, you never know what you're gonna get.",
    "知识就是力量，这是永恒的真理。",
    "Knowledge is power, this is an eternal truth.",
    "道路是曲折的，前途是光明的。",
    "The road is winding, but the future is bright.",
    "春眠不觉晓，处处闻啼鸟。",
    "Spring sleep and dawn, everywhere birds singing.",
    "明月几时有，把酒问青天。",
    "When will the bright moon appear? I raise my cup to ask the blue sky.",
    "长风破浪会有时，直挂云帆济沧海。",
    "There will be times when the wind and waves break, and the clouds and sails will sail across the sea.",
    "海内存知己，天涯若比邻。",
    "A bosom friend afar brings a distant land near."
]

def random_color():
    """生成随机十六进制颜色"""
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

async def send_test_message(websocket, text, custom_params=None):
    """发送测试消息"""
    message = {
        'text': text,
        'y_position': random.randint(500, 1200),
        'top_color': random.choice(['yellow', 'cyan', 'lime', 'orange', 'pink', random_color()]),
        'bottom_color': random.choice(['yellow', 'cyan', 'lime', 'orange', 'pink', random_color()]),
        'timeout': random.uniform(3, 8),
        'height': random.randint(150, 300)
    }
    
    # 应用自定义参数
    if custom_params:
        message.update(custom_params)
    
    try:
        await websocket.send(json.dumps(message, ensure_ascii=False))
        print(f"✓ 发送: {text[:20]}{'...' if len(text) > 20 else ''}")
        return True
    except Exception as e:
        print(f"✗ 发送失败: {e}")
        return False

async def test_basic_functionality(host="localhost", port=None):
    """基本功能测试"""
    print("\n=== 基本功能测试 ===")
    
    if port is None:
        port = NETWORK_CONFIG["websocket_port"]
    
    try:
        async with websockets.connect(f'ws://{host}:{port}') as websocket:
            print(f"连接到 ws://{host}:{port}")
            
            # 发送单条测试消息
            await send_test_message(websocket, "基本功能测试 - 你好世界")
            await asyncio.sleep(2)
            
            print("✓ 基本功能测试完成")
            
    except Exception as e:
        print(f"✗ 基本功能测试失败: {e}")

async def test_batch_messages(host="localhost", port=None):
    """批量消息测试"""
    print("\n=== 批量消息测试 ===")
    
    if port is None:
        port = NETWORK_CONFIG["websocket_port"]
    
    try:
        async with websockets.connect(f'ws://{host}:{port}') as websocket:
            print(f"连接到 ws://{host}:{port}")
            
            success_count = 0
            total_count = len(SAMPLE_TEXTS)
            
            for i, text in enumerate(SAMPLE_TEXTS):
                # if await send_test_message(websocket, f"[{i+1}/{total_count}] {text}"):
                if await send_test_message(websocket,text):
                    success_count += 1
                
                # 随机间隔
                await asyncio.sleep(random.uniform(0.5, 2.0))
            
            print(f"✓ 批量测试完成: {success_count}/{total_count} 成功")
            
    except Exception as e:
        print(f"✗ 批量消息测试失败: {e}")

async def test_rapid_messages(host="localhost", port=None):
    """快速消息测试"""
    print("\n=== 快速消息测试 ===")
    
    if port is None:
        port = NETWORK_CONFIG["websocket_port"]
    
    try:
        async with websockets.connect(f'ws://{host}:{port}') as websocket:
            print(f"连接到 ws://{host}:{port}")
            
            success_count = 0
            rapid_tests = SAMPLE_TEXTS[:5]  # 取前5条进行快速测试
            
            for i, text in enumerate(rapid_tests):
                # if await send_test_message(websocket, f"快速测试{i+1}: {text}"):
                if await send_test_message(websocket,text):
                    success_count += 1
                
                # 短间隔
                await asyncio.sleep(0.1)
            
            print(f"✓ 快速测试完成: {success_count}/{len(rapid_tests)} 成功")
            
    except Exception as e:
        print(f"✗ 快速消息测试失败: {e}")

async def test_custom_params(host="localhost", port=None):
    """自定义参数测试"""
    print("\n=== 自定义参数测试 ===")
    
    if port is None:
        port = NETWORK_CONFIG["websocket_port"]
    
    test_cases = [
        {
            'text': 'Red top text, blue bottom text',
            'params': {'top_color': 'red', 'bottom_color': 'blue'}
        },
        {
            'text': '顶部位置显示测试',
            'params': {'y_position': 100, 'height': 150, 'top_color': 'cyan'}
        },
        {
            'text': 'Long display time test',
            'params': {'timeout': 10, 'top_color': 'yellow', 'bottom_color': 'lime'}
        },
        {
            'text': '底部大窗口测试',
            'params': {'y_position': 900, 'height': 250, 'top_color': 'orange'}
        },
        {
            'text': 'Mixed 中英文 language test',
            'params': {'top_color': 'green', 'bottom_color': 'orange'}
        }
    ]
    
    try:
        async with websockets.connect(f'ws://{host}:{port}') as websocket:
            print(f"连接到 ws://{host}:{port}")
            
            for test_case in test_cases:
                await send_test_message(websocket, test_case['text'], test_case['params'])
                await asyncio.sleep(3)
            
            print("✓ 自定义参数测试完成")
            
    except Exception as e:
        print(f"✗ 自定义参数测试失败: {e}")

async def interactive_test(host="localhost", port=None):
    """交互式测试"""
    print("\n=== 交互式测试模式 ===")
    print("输入要测试的文本，按回车发送。输入 'quit' 退出。")
    
    if port is None:
        port = NETWORK_CONFIG["websocket_port"]
    
    try:
        async with websockets.connect(f'ws://{host}:{port}') as websocket:
            print(f"连接到 ws://{host}:{port}")
            
            while True:
                try:
                    text = input("请输入文本: ").strip()
                    if text.lower() == 'quit':
                        break
                    
                    if text:
                        await send_test_message(websocket, text)
                    else:
                        print("请输入有效文本")
                        
                except KeyboardInterrupt:
                    print("\n用户中断")
                    break
                except EOFError:
                    print("\n输入结束")
                    break
            
            print("✓ 交互式测试结束")
            
    except Exception as e:
        print(f"✗ 交互式测试失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='字幕软件WebSocket测试客户端')
    parser.add_argument('--mode', '-m', choices=['basic', 'batch', 'rapid', 'custom', 'interactive', 'all'],
                       default='basic', help='测试模式')
    parser.add_argument('--host', default='localhost', help='WebSocket服务器地址')
    parser.add_argument('--port', type=int, default=NETWORK_CONFIG["websocket_port"], help='WebSocket服务器端口')
    
    args = parser.parse_args()
    
    print("字幕软件 WebSocket 测试客户端")
    print(f"目标服务器: ws://{args.host}:{args.port}")
    
    async def run_tests():
        if args.mode == 'basic':
            await test_basic_functionality(args.host, args.port)
        elif args.mode == 'batch':
            await test_batch_messages(args.host, args.port)
        elif args.mode == 'rapid':
            await test_rapid_messages(args.host, args.port)
        elif args.mode == 'custom':
            await test_custom_params(args.host, args.port)
        elif args.mode == 'interactive':
            await interactive_test(args.host, args.port)
        elif args.mode == 'all':
            await test_basic_functionality(args.host, args.port)
            await asyncio.sleep(1)
            await test_batch_messages(args.host, args.port)
            await asyncio.sleep(1)
            await test_rapid_messages(args.host, args.port)
            await asyncio.sleep(1)
            await test_custom_params(args.host, args.port)
    
    try:
        asyncio.run(run_tests())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试执行失败: {e}")

if __name__ == "__main__":
    main() 