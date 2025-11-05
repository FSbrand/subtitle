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
from datetime import datetime
from config import NETWORK_CONFIG

# 测试文本样本
EXECUTION_LOGS = []


def log_output(message):
    """打印并记录日志到内存，便于写入文件"""
    text = str(message)
    print(text)
    EXECUTION_LOGS.append(text)


def write_execution_log(args, status):
    """将本次测试结果追加写入本地文件"""
    if not EXECUTION_LOGS:
        return
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"=== Test run {timestamp} mode={args.mode} host={args.host}:{args.port} status={status} ==="
    lines = [header, *EXECUTION_LOGS, ""]
    
    try:
        with open("test_results.txt", "a", encoding="utf-8") as log_file:
            log_file.write("\n".join(lines))
    except Exception as exc:
        # 仅记录写入失败，不抛出
        print(f"⚠️ 无法写入test_results.txt: {exc}")
    finally:
        EXECUTION_LOGS.clear()


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
        log_output(f"✓ 发送: {text[:20]}{'...' if len(text) > 20 else ''}")
        
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=8)
            if isinstance(response, bytes):
                response = response.decode('utf-8', errors='replace')
            try:
                response_json = json.loads(response)
                translated = response_json.get("translated_text", "")
                source_preview = response_json.get("source_text", "")[:40]
                translated_preview = translated[:80]
                log_output(f"← 翻译: {source_preview}{'...' if len(source_preview) >= 40 else ''} -> {translated_preview}{'...' if len(translated) > 80 else ''}")
            except json.JSONDecodeError:
                log_output(f"← 响应: {response[:120]}{'...' if len(response) > 120 else ''}")
        except asyncio.TimeoutError:
            log_output("⚠️ 未收到响应（8s 超时）")
        except Exception as recv_exc:
            log_output(f"⚠️ 接收响应失败: {recv_exc}")
        
        return True
    except Exception as e:
        log_output(f"✗ 发送失败: {e}")
        return False

async def test_basic_functionality(host="localhost", port=None):
    """基本功能测试"""
    log_output("\n=== 基本功能测试 ===")
    
    if port is None:
        port = NETWORK_CONFIG["websocket_port"]
    
    try:
        async with websockets.connect(f'ws://{host}:{port}') as websocket:
            log_output(f"连接到 ws://{host}:{port}")
            
            # 发送单条测试消息
            await send_test_message(websocket, "基本功能测试 - 你好世界")
            await asyncio.sleep(2)
            
            log_output("✓ 基本功能测试完成")
            
    except Exception as e:
        log_output(f"✗ 基本功能测试失败: {e}")

async def test_batch_messages(host="localhost", port=None):
    """批量消息测试"""
    log_output("\n=== 批量消息测试 ===")
    
    if port is None:
        port = NETWORK_CONFIG["websocket_port"]
    
    try:
        async with websockets.connect(f'ws://{host}:{port}') as websocket:
            log_output(f"连接到 ws://{host}:{port}")
            
            success_count = 0
            total_count = len(SAMPLE_TEXTS)
            
            for i, text in enumerate(SAMPLE_TEXTS):
                # if await send_test_message(websocket, f"[{i+1}/{total_count}] {text}"):
                if await send_test_message(websocket,text):
                    success_count += 1
                
                # 随机间隔
                await asyncio.sleep(random.uniform(0.5, 2.0))
            
            log_output(f"✓ 批量测试完成: {success_count}/{total_count} 成功")
            
    except Exception as e:
        log_output(f"✗ 批量消息测试失败: {e}")

async def test_rapid_messages(host="localhost", port=None):
    """快速消息测试"""
    log_output("\n=== 快速消息测试 ===")
    
    if port is None:
        port = NETWORK_CONFIG["websocket_port"]
    
    try:
        async with websockets.connect(f'ws://{host}:{port}') as websocket:
            log_output(f"连接到 ws://{host}:{port}")
            
            success_count = 0
            rapid_tests = SAMPLE_TEXTS[:5]  # 取前5条进行快速测试
            
            for i, text in enumerate(rapid_tests):
                # if await send_test_message(websocket, f"快速测试{i+1}: {text}"):
                if await send_test_message(websocket,text):
                    success_count += 1
                
                # 短间隔
                await asyncio.sleep(0.1)
            
            log_output(f"✓ 快速测试完成: {success_count}/{len(rapid_tests)} 成功")
            
    except Exception as e:
        log_output(f"✗ 快速消息测试失败: {e}")

async def test_custom_params(host="localhost", port=None):
    """自定义参数测试"""
    log_output("\n=== 自定义参数测试 ===")
    
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
        },
        {
            'text': '我们团队的引领者之星计划正在推进，请大家按时反馈进展。',
            'params': {'top_color': 'cyan', 'bottom_color': 'yellow'}
        },
        {
            'text': '小华提出全方位的改进建议，确保流程可以迅速流转。',
            'params': {'top_color': 'magenta', 'bottom_color': 'lime'}
        },
        {
            'text': 'The Leader Star roadmap ensures a comprehensive rollout for every team this quarter.',
            'params': {'top_color': 'orange', 'bottom_color': 'white'}
        },
        {
            'text': 'Xiao Hua will monitor the transfer milestones carefully to avoid last-minute surprises.',
            'params': {'top_color': 'pink', 'bottom_color': 'cyan'}
        }
    ]
    
    try:
        async with websockets.connect(f'ws://{host}:{port}') as websocket:
            log_output(f"连接到 ws://{host}:{port}")
            
            for test_case in test_cases:
                await send_test_message(websocket, test_case['text'], test_case['params'])
                await asyncio.sleep(3)
            
            log_output("✓ 自定义参数测试完成")
            
    except Exception as e:
        log_output(f"✗ 自定义参数测试失败: {e}")

async def interactive_test(host="localhost", port=None):
    """交互式测试"""
    log_output("\n=== 交互式测试模式 ===")
    log_output("输入要测试的文本，按回车发送。输入 'quit' 退出。")
    
    if port is None:
        port = NETWORK_CONFIG["websocket_port"]
    
    try:
        async with websockets.connect(f'ws://{host}:{port}') as websocket:
            log_output(f"连接到 ws://{host}:{port}")
            
            while True:
                try:
                    text = input("请输入文本: ").strip()
                    if text.lower() == 'quit':
                        break
                    
                    if text:
                        await send_test_message(websocket, text)
                    else:
                        log_output("请输入有效文本")
                        
                except KeyboardInterrupt:
                    log_output("\n用户中断")
                    break
                except EOFError:
                    log_output("\n输入结束")
                    break
            
            log_output("✓ 交互式测试结束")
            
    except Exception as e:
        log_output(f"✗ 交互式测试失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='字幕软件WebSocket测试客户端')
    parser.add_argument('--mode', '-m', choices=['basic', 'batch', 'rapid', 'custom', 'interactive', 'all'],
                       default='basic', help='测试模式')
    parser.add_argument('--host', default='localhost', help='WebSocket服务器地址')
    parser.add_argument('--port', type=int, default=NETWORK_CONFIG["websocket_port"], help='WebSocket服务器端口')
    
    args = parser.parse_args()
    
    log_output("字幕软件 WebSocket 测试客户端")
    log_output(f"目标服务器: ws://{args.host}:{args.port}")
    
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
    
    status = "success"
    try:
        asyncio.run(run_tests())
    except KeyboardInterrupt:
        log_output("\n测试被用户中断")
        status = "interrupt"
    except Exception as e:
        log_output(f"测试执行失败: {e}")
        status = f"error: {e}"
    finally:
        write_execution_log(args, status)

if __name__ == "__main__":
    main() 
