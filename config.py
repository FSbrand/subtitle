# -*- coding: utf-8 -*-
"""
简化配置模块 - 基本默认值和网络配置
"""

# 科大讯飞API配置 (硬编码)
XFYUN_CONFIG = {
    "host": "itrans.xfyun.cn",
    "app_id": "4eb9ed9f",
    "api_key": "81092656b8f469fbb60f1016247d03b1",
    "secret": "a2fae5fac1108c1327aac2444967ffb6"
}

# 翻译配置
TRANSLATION_CONFIG = {
    "from_lang": "cn",
    "to_lang": "en"
}

# 显示默认配置
DISPLAY_CONFIG = {
    "default_y_position": 1000,
    "default_height": 200,
    "default_top_color": "white",      # 上方字幕颜色
    "default_bottom_color": "yellow",  # 下方字幕颜色
    "default_timeout": 6,
    "font_family": "Microsoft YaHei UI",
    "font_size": 20
}

# 网络配置
NETWORK_CONFIG = {
    "websocket_port": 4321,
    "websocket_host": "0.0.0.0"
} 