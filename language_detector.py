# -*- coding: utf-8 -*-
"""
语种检测模块 - 自动检测输入文本语种并设置翻译方向
当前支持中英文检测，未来可扩展多语种
"""

import re
from config import TRANSLATION_CONFIG

# 支持的语种和对应的Unicode范围
LANGUAGE_PATTERNS = {
    'cn': r'[\u4e00-\u9fff]',                    # 中文 (CJK统一汉字)
    'en': r'[a-zA-Z]',                           # 英文 (基本拉丁字母)
    'ja': r'[\u3040-\u309f\u30a0-\u30ff]',      # 日文 (平假名+片假名，不包括汉字避免与中文混淆)
    'ko': r'[\uac00-\ud7af]',                    # 韩文 (韩文音节)
    'ru': r'[\u0400-\u04ff]',                    # 俄文 (西里尔字母)
    'ar': r'[\u0600-\u06ff]',                    # 阿拉伯文
    'th': r'[\u0e00-\u0e7f]',                    # 泰文
    'el': r'[\u0370-\u03ff]',                    # 希腊文
    'he': r'[\u0590-\u05ff]',                    # 希伯来文
    'hi': r'[\u0900-\u097f]',                    # 印地文 (天城文)
}

# 语种名称映射
LANGUAGE_NAMES = {
    'cn': '中文',
    'en': '英文', 
    'ja': '日文',
    'ko': '韩文',
    'ru': '俄文',
    'ar': '阿拉伯文',
    'th': '泰文',
    'el': '希腊文',
    'he': '希伯来文',
    'hi': '印地文'
}

def detect_language(text):
    """
    检测文本语种 - 支持多语种检测
    
    Args:
        text (str): 要检测的文本
        
    Returns:
        str: 语种代码，如 'cn', 'en', 'ja', 'ko', 'ru', 'ar', 'th', 'el', 'he', 'hi', 'unknown'
    """
    if not text or not text.strip():
        return 'unknown'
    
    # 移除空格和标点符号进行检测
    clean_text = re.sub(r'[^\w]', '', text)
    
    if not clean_text:
        return 'unknown'
    
    # 计算各语种字符的比例
    language_ratios = {}
    text_length = len(clean_text)
    
    for lang_code, pattern in LANGUAGE_PATTERNS.items():
        chars = re.findall(pattern, clean_text)
        ratio = len(chars) / text_length if text_length > 0 else 0
        language_ratios[lang_code] = ratio
    
    # 找出比例最高的语种
    max_ratio = 0
    detected_language = 'unknown'
    
    for lang_code, ratio in language_ratios.items():
        if ratio > max_ratio:
            # 设置最低阈值，避免误判
            min_threshold = 0.3 if lang_code == 'cn' else 0.5  # 中文阈值稍低，因为可能包含英文
            if ratio >= min_threshold:
                max_ratio = ratio
                detected_language = lang_code
    
    return detected_language

def get_translation_direction(text):
    """
    根据输入文本自动确定翻译方向
    
    Args:
        text (str): 输入文本
        
    Returns:
        tuple: (from_lang, to_lang, source_text_position, target_text_position)
               source_text_position: 'top' 或 'bottom' 表示源文本显示位置
               target_text_position: 'top' 或 'bottom' 表示译文显示位置
    """
    detected_lang = detect_language(text)
    
    if detected_lang == 'cn':
        # 中文翻译为英文：中文在上，英文在下
        return 'cn', 'en', 'top', 'bottom'
    elif detected_lang == 'en':
        # 英文翻译为中文：英文在上，中文在下
        return 'en', 'cn', 'top', 'bottom'
    else:
        # 未知语种，使用默认配置（中译英）
        return TRANSLATION_CONFIG['from_lang'], TRANSLATION_CONFIG['to_lang'], 'top', 'bottom'

def update_translation_config(text):
    """
    根据输入文本更新翻译配置
    
    Args:
        text (str): 输入文本
        
    Returns:
        dict: 更新后的翻译配置 {"from": "cn", "to": "en"}
    """
    from_lang, to_lang, _, _ = get_translation_direction(text)
    return {"from": from_lang, "to": to_lang}

def get_display_layout(text):
    """
    根据输入文本确定字幕显示布局
    
    Args:
        text (str): 输入文本
        
    Returns:
        dict: 显示布局信息
        {
            "source_text": text,
            "source_position": "top",  # 源文本位置
            "target_position": "bottom",  # 译文位置
            "from_lang": "cn",
            "to_lang": "en"
        }
    """
    from_lang, to_lang, source_pos, target_pos = get_translation_direction(text)
    
    return {
        "source_text": text,
        "source_position": source_pos,
        "target_position": target_pos,
        "from_lang": from_lang,
        "to_lang": to_lang
    }

# 未来扩展多语种的框架
"""
未来扩展多语种支持的方法：

1. 语种检测扩展：
   - 集成更专业的语种检测库，如 langdetect, polyglot 等
   - 支持更多语种的字符范围检测
   - 添加语种置信度评估

2. 翻译方向配置：
   - 在 TRANSLATION_CONFIG 中添加多语种映射
   - 支持多语种到中文的翻译
   - 添加语种优先级配置

3. 显示布局扩展：
   - 支持从右到左的文字显示（如阿拉伯语、希伯来语）
   - 支持不同语种的字体配置
   - 添加语种特定的显示样式

示例扩展代码：
```python
# 扩展语种检测
LANGUAGE_PATTERNS = {
    'cn': r'[\u4e00-\u9fff]',      # 中文
    'en': r'[a-zA-Z]',             # 英文
    'ja': r'[\u3040-\u309f\u30a0-\u30ff]',  # 日文
    'ko': r'[\uac00-\ud7af]',      # 韩文
    'ar': r'[\u0600-\u06ff]',      # 阿拉伯文
    'ru': r'[\u0400-\u04ff]',      # 俄文
}

# 扩展翻译方向配置
TRANSLATION_DIRECTIONS = {
    'cn': {'default_to': 'en', 'alternatives': ['ja', 'ko']},
    'en': {'default_to': 'cn', 'alternatives': ['ja', 'ko']},
    'ja': {'default_to': 'cn', 'alternatives': ['en']},
    'ko': {'default_to': 'cn', 'alternatives': ['en']},
}
```
"""

def get_language_name(lang_code):
    """获取语种的中文名称"""
    return LANGUAGE_NAMES.get(lang_code, f'未知语种({lang_code})')

def analyze_text_composition(text):
    """分析文本的语种组成"""
    if not text or not text.strip():
        return {}
    
    clean_text = re.sub(r'[^\w]', '', text)
    if not clean_text:
        return {}
    
    composition = {}
    text_length = len(clean_text)
    
    for lang_code, pattern in LANGUAGE_PATTERNS.items():
        chars = re.findall(pattern, clean_text)
        count = len(chars)
        ratio = count / text_length if text_length > 0 else 0
        if count > 0:
            composition[lang_code] = {
                'count': count,
                'ratio': ratio,
                'percentage': f"{ratio*100:.1f}%"
            }
    
    return composition

if __name__ == "__main__":
    # 基本测试
    test_texts = [
        "你好世界！这是中文测试。",
        "Hello world! This is English test.",
        "Hello 世界! Mixed text test.",
        "123456 数字测试",
        ""
    ]
    
    print("基本语种检测测试:")
    for text in test_texts:
        lang = detect_language(text)
        layout = get_display_layout(text)
        print(f"文本: '{text}' -> 语种: {get_language_name(lang)} ({lang})")
        print(f"  翻译方向: {layout['from_lang']} -> {layout['to_lang']}")
        print(f"  显示布局: 源文本({layout['source_position']}) -> 译文({layout['target_position']})")
        print() 