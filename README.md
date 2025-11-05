# 🎬 智能字幕软件

基于PyQt5和科大讯飞翻译API的智能实时字幕显示软件，支持中英文双向翻译和智能语言检测。

![软件图标](icon_simple.svg)

## ✨ 核心功能

- 🧠 **智能语言检测**: 自动识别中英文并选择翻译方向
- 🔄 **双向翻译**: 中文↔英文，支持混合文本
- 💾 **本地翻译缓存**: 自定义翻译映射，优先使用本地翻译
- 📺 **置顶显示**: 透明窗口，始终在最前方
- 🎨 **动态布局**: 根据语言自动调整上下布局
- 📡 **WebSocket通信**: 实时响应，低延迟
- 🎯 **系统托盘**: 后台运行，便捷控制
- 📋 **详细日志**: 按日生成，便于调试

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 启动程序
```bash
python main.py
```

程序启动后将：
- 在系统托盘显示图标
- 启动WebSocket服务器（端口4321）
- 准备接收字幕请求

## 📡 API接口

### WebSocket 消息格式
```python
import asyncio
import websockets
import json

async def send_subtitle():
    async with websockets.connect('ws://localhost:4321') as websocket:
        message = {
            "text": "Hello World 你好世界",      # 必需: 要显示的文本
            "y_position": 1000,                # 可选: 垂直位置 (默认 1000)
            "top_color": "cyan",              # 可选: 上方文本颜色
            "bottom_color": "yellow",         # 可选: 下方文本颜色
            "timeout": 8,                     # 可选: 显示时长(秒)
            "height": 200                     # 可选: 窗口高度
        }
        await websocket.send(json.dumps(message, ensure_ascii=False))

# 运行示例
asyncio.run(send_subtitle())
```

### 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `text` | string | ✅ | - | 要显示的文本（自动检测语言） |
| `y_position` | int | ❌ | 1000 | 垂直位置 (0-1080) |
| `top_color` | string | ❌ | "white" | 上方文本颜色 |
| `bottom_color` | string | ❌ | "yellow" | 下方文本颜色 |
| `timeout` | int | ❌ | 6 | 显示时长(秒) |
| `height` | int | ❌ | 200 | 窗口高度(像素) |

> 💡 **智能布局**: 中文输入时中文在上、英译在下；英文输入时英文在上、中译在下

## 🧪 测试程序

```bash
# 运行测试客户端（包含多种语言样本）
python test_client.py

# 语言检测测试
python language_detector.py
```

## 📦 打包发布

### 方法一：使用构建脚本（推荐）
```bash
pip install -r build_script/requirements_build.txt
python build_script/build.py
```

### 方法二：手动打包
```bash
pyinstaller --onefile --noconsole --name=subtitle_optimized main.py
```

构建完成后，可执行文件位于：`build/dist/subtitle_optimized.exe`

## 📁 项目结构

```
.
├── README.md
├── build_script/
│   ├── build.py              # 自动化构建脚本
│   └── requirements_build.txt # 构建依赖
├── config.py                 # 配置管理 - API密钥等
├── icon_simple.svg           # 程序图标
├── language_detector.py      # 语言检测
├── log/                      # 按日生成的详细日志
├── main.py                   # 主程序 - GUI + WebSocket服务
├── requirements.txt          # 开发环境依赖
├── test_client.py            # WebSocket测试客户端
├── trans.py                  # 翻译模块 - 科大讯飞API
└── translations.txt          # 本地翻译缓存
```

## 🔧 技术架构

```
┌─────────────┐    WebSocket     ┌─────────────┐    翻译API    ┌─────────────┐
│ 外部客户端  │ ───────────────> │ WebSocket   │ ───────────> │ 科大讯飞    │
│           │                 │ 服务器      │             │ 翻译服务    │
└─────────────┘                 └─────────────┘             └─────────────┘
                                       │
                                       ▼
                                ┌─────────────┐
                                │ 语言检测    │
                                │ + 智能布局  │
                                └─────────────┘
                                       │
                                       ▼
                                ┌─────────────┐
                                │ PyQt5       │
                                │ 字幕窗口    │
                                └─────────────┘
```

### 核心技术栈
- **GUI**: PyQt5 - 透明置顶窗口
- **网络**: WebSocket - 实时双向通信  
- **翻译**: 科大讯飞API - 机器翻译
- **语言检测**: Unicode范围检测 - 自动识别
- **多线程**: QThread - 异步处理
- **日志**: Python logging - 详细记录
- **打包**: PyInstaller - 单文件exe

## 🎯 使用场景

- 📺 **直播字幕**: 实时翻译弹幕和语音
- 🎥 **视频制作**: 为视频添加双语字幕
- 💼 **会议翻译**: 实时显示会议内容翻译
- 🎮 **游戏辅助**: 游戏文本实时翻译
- 🎓 **学习工具**: 语言学习辅助显示

## ⚙️ 配置说明

- **API密钥**: 科大讯飞配置已内置，开箱即用
- **显示设置**: 通过WebSocket消息参数动态调整
- **网络配置**: 默认监听 `0.0.0.0:4321`，接受所有连接
- **日志设置**: 自动按日轮转，保存在 `log/` 目录

## 💾 本地翻译缓存

### 🎯 功能概述
本地翻译缓存允许你为特定文本设置自定义翻译，系统会优先使用这些翻译而不是调用API。

**适用场景**：
- ⚡ **词语/短语替换**: 快速覆盖常用词、短语翻译
- 🎯 **专业术语**: 为特殊词汇设置标准翻译
- 💰 **降低成本**: 减少API调用次数
- 🚀 **提升速度**: 缓存命中时零延迟响应

### 📝 配置方法

#### 1. 编辑翻译映射文件
编辑根目录下的 `translations.txt` 文件（每行一个词语映射，使用中文逗号 `，` 分隔）：

```
# 注释行以 # 开头，会被忽略
引领者之星，Leader Star
小华，Xiao Hua
全方位，comprehensive
流转，transfer
Leader Star，引领者之星
Xiao Hua，小华
comprehensive，全方位
transfer，流转
```

#### 2. 文件放置位置（exe兼容）
系统会按以下优先级查找配置文件：
1. **当前工作目录** - `./translations.txt`
2. **exe同目录** - 与exe文件在同一文件夹
3. **程序内置** - 打包在exe中的默认配置

### ✨ 功能特点

#### 大小写不敏感匹配
```
"Leader Star" → "引领者之星"
"leader star" → "引领者之星"
"LEADER STAR" → "引领者之星"
```

#### 中英双向支持
```
"引领者之星" → "Leader Star"
"全方位" → "comprehensive"
"transfer" → "流转"
"Leader Star" → "引领者之星"
"Xiao Hua" → "小华"
"comprehensive" → "全方位"
```

#### 嵌入句子自动替换
```
"我们团队的引领者之星计划正在推进，请大家按时反馈。" 
  → "我们团队的 Leader Star 计划正在推进，请大家按时反馈。"
"The Leader Star roadmap ensures a comprehensive rollout for every team." 
  → "The 引领者之星 roadmap ensures a 全方位 rollout for every team."
"Xiao Hua will monitor the transfer milestones carefully." 
  → "小华 will monitor the 流转 milestones carefully."
```

#### 替换算法说明
- **匹配阶段**：根据自动检测的翻译方向筛选词条，对 `translations.txt` 中的短语逐条构建大小写不敏感的正则（`re.escape` 保留空格和特殊字符），收集所有命中区间。
- **排序策略**：命中结果按起始下标升序，在同一起点里优先选择更长的匹配，避免长词被短词截断。
- **占位符注入**：将命中短语替换成私有区字符占位符（运行时生成的独特符号），并记录占位符到目标译文的映射，同时保留一份兜底替换列表。
- **调用与回填**：携带占位符的整句交给科大讯飞接口翻译；得到结果后，再把占位符回填为指定译文。如接口无响应，则退化为直接对原句应用本地词典。
- **复杂度**：最多 200 条词条、句长有限时，整体复杂度近似 `O(词条数 × 句长)`，足够覆盖“带空格词组”等场景。若未来词条大幅增长，可考虑 Trie 或 Aho-Corasick 自动机降低扫描成本。

### 🧪 测试与验证

验证缓存是否生效的建议流程：
1. 在 `translations.txt` 中添加或修改需要缓存的词语映射。
2. 启动主程序：`python main.py`。
3. 使用测试客户端发送缓存中的文本，例如运行 `python test_client.py --mode interactive` 并输入缓存内容。
4. 观察字幕窗口或查看 `log/` 目录下的日志，确认是否命中本地缓存。
5. 每次执行 `test_client.py`，请求与响应摘要会追加写入根目录下的 `test_results.txt` 便于人工核对。

### 📋 配置示例

#### 商务对话
```
Good morning, how can I help you?，早上好，我能为您做什么？
Let me check that for you，让我为您检查一下
Thank you for your patience，感谢您的耐心
```

#### 技术术语
```
Machine Learning，机器学习
Deep Learning，深度学习
Neural Network，神经网络
API，应用程序接口
```

### 🔧 故障排除

| 问题 | 解决方案 |
|------|----------|
| 缓存不生效 | 检查TXT格式是否为“源文，目标文”，并确认日志无格式错误警告 |
| exe找不到文件 | 将translations.txt放在exe同目录 |
| 中文显示乱码 | 确保文件保存为UTF-8编码 |
| 修改未生效 | 重启程序或检查文件保存 |

### 📝 详细日志
```
INFO - 成功加载本地翻译映射: 10 条记录 (文件: ./translations.txt)
INFO - 本地翻译替换: '引领者之星' -> 'Leader Star' (匹配 1 次)
INFO - 本地翻译完成（局部替换 2 处）: 'Xiao Hua will monitor the transfer milestones carefully.' -> '小华 will monitor the 流转 milestones carefully.'
DEBUG - 本地缓存未找到 'New sentence'，调用API翻译
```

## 🆘 常见问题

| 问题 | 解决方案 |
|------|----------|
| 端口4321被占用 | 修改 `config.py` 中的 `WEBSOCKET_PORT` |
| 字幕不显示 | 检查防火墙设置，以管理员权限运行 |
| 翻译失败 | 检查网络连接，查看日志文件 |
| 程序闪退 | 查看 `log/` 目录下的错误日志 |

## 📄 开源协议

本项目基于 MIT 协议开源，欢迎贡献代码和建议！

---

🌟 **如果这个项目对您有帮助，请给个Star支持一下！**
