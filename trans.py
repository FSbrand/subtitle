#!/usr/bin/env python 
# -*- coding:utf-8 -*-
"""
机器翻译 WebAPI 接口调用模块化
简化版本：直接使用配置参数
支持本地翻译缓存（基于txt词语映射），优先使用自定义翻译
"""

import requests
import datetime
import hashlib
import base64
import hmac
import json
import logging
import os
import sys
import re
from config import XFYUN_CONFIG, TRANSLATION_CONFIG
from language_detector import update_translation_config, detect_language

# 获取logger (不重复配置)
logger = logging.getLogger(__name__)

# 全局翻译缓存字典
local_translations = {}


def normalize_language_code(lang_code):
    """限制语言代码到已支持范围"""
    if not lang_code:
        return None
    lang_code = lang_code.lower()
    return lang_code if lang_code in ('cn', 'en') else None

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，兼容开发环境和打包后的exe"""
    try:
        # PyInstaller打包后的临时目录
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发环境，使用脚本所在目录
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)

def load_local_translations():
    """加载本地翻译映射文件（txt词语映射）"""
    global local_translations
    translations_file = "translations.txt"
    
    # 获取exe或脚本的实际目录
    if getattr(sys, 'frozen', False):
        # PyInstaller打包后的exe
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        # 开发环境
        exe_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 优先查找顺序：1) 当前工作目录 2) exe/脚本同目录 3) 资源目录
    search_paths = [
        translations_file,  # 当前工作目录
        os.path.join(exe_dir, translations_file),  # exe/脚本同目录
        get_resource_path(translations_file),  # PyInstaller资源目录
    ]
    
    try:
        loaded = False
        for file_path in search_paths:
            if os.path.exists(file_path):
                logger.info(f"尝试加载翻译文件: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    parsed_translations = {}
                    skipped_lines = 0
                    for line_number, line in enumerate(f, start=1):
                        stripped = line.strip()
                        if not stripped or stripped.startswith("#"):
                            continue
                        if "，" in stripped:
                            key, value = [part.strip() for part in stripped.split("，", 1)]
                        elif "," in stripped:
                            key, value = [part.strip() for part in stripped.split(",", 1)]
                        else:
                            skipped_lines += 1
                            logger.warning(f"翻译文件格式不正确（第{line_number}行）: {stripped}")
                            continue
                        if not key or not value:
                            skipped_lines += 1
                            logger.warning(f"翻译文件缺少键或值（第{line_number}行）: {stripped}")
                            continue
                        key_lower = key.lower()
                        source_lang = normalize_language_code(detect_language(key))
                        target_lang = normalize_language_code(detect_language(value))
                        compiled_regex = re.compile(re.escape(key), re.IGNORECASE)
                        parsed_translations[key_lower] = {
                            "pattern": key,
                            "replacement": value,
                            "source_lang": source_lang,
                            "target_lang": target_lang,
                            "regex": compiled_regex
                        }
                    
                    local_translations = parsed_translations
                    logger.info(
                        f"成功加载本地翻译映射: {len(local_translations)} 条记录 (文件: {file_path})"
                    )
                    if skipped_lines:
                        logger.warning(f"有 {skipped_lines} 行因格式问题被跳过")
                    loaded = True
                    break
        
        if not loaded:
            logger.warning(f"未找到翻译映射文件，搜索路径: {search_paths}")
            logger.warning("将只使用API翻译")
            local_translations = {}
            
    except Exception as e:
        logger.error(f"加载翻译映射文件失败: {e}")
        local_translations = {}

# 程序启动时自动加载翻译映射
load_local_translations()

def reload_local_translations():
    """重新加载本地翻译映射（运行时调用）"""
    logger.info("重新加载本地翻译映射...")
    load_local_translations()
    return len(local_translations)

def get_local_translations_count():
    """获取本地翻译映射数量"""
    return len(local_translations)

def check_local_translation(text):
    """检查文本是否在本地翻译缓存中"""
    return text.lower().strip() in local_translations

class get_result(object):
    def __init__(self, host, app_id, api_key, secret, text, business_args):
        # 应用ID（到控制台获取）
        self.APPID = app_id
        # 接口APISercet（到控制台机器翻译服务页面获取）
        self.Secret = secret
        # 接口APIKey（到控制台机器翻译服务页面获取）
        self.APIKey = api_key

        # 以下为POST请求
        self.Host = host
        self.RequestUri = "/v2/its"
        # 设置url
        self.url = "https://" + host + self.RequestUri
        self.HttpMethod = "POST"
        self.Algorithm = "hmac-sha256"
        self.HttpProto = "HTTP/1.1"

        # 设置当前时间
        curTime_utc = datetime.datetime.utcnow()
        self.Date = self.httpdate(curTime_utc)
        # 设置业务参数
        self.Text = text
        self.BusinessArgs = business_args

    def hashlib_256(self, res):
        m = hashlib.sha256(bytes(res.encode(encoding='utf-8'))).digest()
        result = "SHA-256=" + base64.b64encode(m).decode(encoding='utf-8')
        return result

    def httpdate(self, dt):
        weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()]
        month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
                 "Oct", "Nov", "Dec"][dt.month - 1]
        return "%s, %02d %s %04d %02d:%02d:%02d GMT" % (weekday, dt.day, month,
                                                        dt.year, dt.hour, dt.minute, dt.second)

    def generateSignature(self, digest):
        signatureStr = "host: " + self.Host + "\n"
        signatureStr += "date: " + self.Date + "\n"
        signatureStr += self.HttpMethod + " " + self.RequestUri + " " + self.HttpProto + "\n"
        signatureStr += "digest: " + digest
        signature = hmac.new(bytes(self.Secret.encode(encoding='utf-8')),
                             bytes(signatureStr.encode(encoding='utf-8')),
                             digestmod=hashlib.sha256).digest()
        result = base64.b64encode(signature)
        return result.decode(encoding='utf-8')

    def init_header(self, data):
        digest = self.hashlib_256(data)
        sign = self.generateSignature(digest)
        authHeader = 'api_key="%s", algorithm="%s", ' \
                     'headers="host date request-line digest", ' \
                     'signature="%s"' % (self.APIKey, self.Algorithm, sign)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Method": "POST",
            "Host": self.Host,
            "Date": self.Date,
            "Digest": digest,
            "Authorization": authHeader
        }
        return headers

    def get_body(self):
        content = str(base64.b64encode(self.Text.encode('utf-8')), 'utf-8')
        postdata = {
            "common": {"app_id": self.APPID},
            "business": self.BusinessArgs,
            "data": {
                "text": content,
            }
        }
        body = json.dumps(postdata)
        return body

    def call_url(self):
        """调用翻译API，增强错误处理"""
        if self.APPID == '' or self.APIKey == '' or self.Secret == '':
            logger.error('API配置信息不完整！请填写完整的APPID、APIKey和Secret。')
            return ''
        
        try:
            body = self.get_body()
            headers = self.init_header(body)
            
            logger.debug(f"发送翻译请求: {self.Text}")
            response = requests.post(self.url, data=body, headers=headers, timeout=10)
            status_code = response.status_code
            
            if status_code != 200:
                error_msg = f"HTTP请求失败，状态码：{status_code}，错误信息：{response.text}"
                logger.error(error_msg)
                return ''
            
            respData = json.loads(response.text)
            code = str(respData.get("code", "unknown"))

            if code != '0':
                error_msg = f"翻译API返回错误，错误码：{code}"
                logger.error(error_msg)
                if code == "10013":
                    logger.error("请检查APPID是否正确")
                elif code == "10014":
                    logger.error("请检查签名是否正确")
                elif code == "11200":
                    logger.error("请检查APIKey是否正确")
                else:
                    logger.error(f"请前往https://www.xfyun.cn/document/error-code?code={code} 查询解决办法")
                return ''
            
            result = respData.get('data', {}).get('result', {}).get('trans_result', {}).get('dst', '')
            if result:
                logger.debug(f"翻译成功: {self.Text} -> {result}")
            else:
                logger.warning("翻译结果为空")
            return result
            
        except requests.RequestException as e:
            logger.error(f"网络请求异常: {e}")
            return ''
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return ''
        except Exception as e:
            logger.error(f"翻译过程中发生未知错误: {str(e)}")
            return ''


def collect_glossary_matches(text, from_lang=None, to_lang=None):
    """收集与当前翻译方向匹配的词典命中"""
    if not local_translations or not text:
        return []
    
    matches = []
    for entry in local_translations.values():
        pattern_text = entry.get("pattern")
        replacement = entry.get("replacement")
        if not pattern_text or replacement is None:
            continue
        
        source_lang = entry.get("source_lang")
        target_lang = entry.get("target_lang")
        
        if from_lang and source_lang and source_lang != from_lang:
            continue
        if to_lang and target_lang and target_lang != to_lang:
            continue
        
        regex = entry.get("regex")
        if not regex:
            continue
        
        for match in regex.finditer(text):
            matches.append({
                "start": match.start(),
                "end": match.end(),
                "entry": entry
            })
    
    # 按起始位置排序，同起点时优先较长匹配
    matches.sort(key=lambda item: (item["start"], -(item["end"] - item["start"])))
    return matches


def apply_glossary_inline(text, matches):
    """将命中词条直接替换为目标语言"""
    if not matches:
        return text, []
    
    result_parts = []
    applied_entries = []
    last_index = 0
    
    for match in matches:
        start = match["start"]
        end = match["end"]
        entry = match["entry"]
        
        if start < last_index:
            # 已被前一个命中覆盖，跳过
            continue
        
        replacement = entry.get("replacement", "")
        result_parts.append(text[last_index:start])
        result_parts.append(replacement)
        last_index = end
        applied_entries.append(entry)
    
    result_parts.append(text[last_index:])
    return ''.join(result_parts), applied_entries


def enforce_glossary_in_result(text, applied_entries):
    """确保翻译结果中保留词典目标词条"""
    if not text or not applied_entries:
        return text
    
    result_text = text
    for entry in applied_entries:
        replacement = entry.get("replacement", "")
        if not replacement:
            continue
        regex = re.compile(re.escape(replacement), re.IGNORECASE)
        result_text = regex.sub(replacement, result_text)
    return result_text


def translate_text(text, from_lang=None, to_lang=None):
    """
    便捷的翻译函数，支持自动语种检测和翻译方向
    优先使用本地翻译缓存，未找到时调用API
    
    Args:
        text (str): 要翻译的文本
        from_lang (str, optional): 源语言，如果不指定则自动检测
        to_lang (str, optional): 目标语言，如果不指定则根据源语言自动选择
    
    Returns:
        str: 翻译结果，翻译失败返回原文
    """
    try:
        # 清理输入文本
        text_cleaned = text.strip()
        if not text_cleaned:
            return text
        
        # 首先检查本地翻译缓存（大小写不敏感）
        text_lower = text_cleaned.lower()
        entry = local_translations.get(text_lower)
        if entry:
            cached_result = entry.get("replacement", text_cleaned)
            logger.info(f"使用本地翻译缓存: '{text_cleaned}' -> '{cached_result}'")
            return cached_result
        
        # 根据文本内容自动检测翻译方向
        auto_config = update_translation_config(text_cleaned)
        from_lang = normalize_language_code(auto_config.get("from")) or TRANSLATION_CONFIG["from_lang"]
        to_lang = normalize_language_code(auto_config.get("to")) or TRANSLATION_CONFIG["to_lang"]
        
        matches = collect_glossary_matches(text_cleaned, from_lang, to_lang)
        inline_text, applied_entries = apply_glossary_inline(text_cleaned, matches)
        if applied_entries:
            match_terms = [
                entry.get("pattern", "")
                for entry in applied_entries
                if entry and entry.get("pattern")
            ]
            logger.info(
                f"使用本地词典短语替换: 匹配 {len(applied_entries)} 处"
                + (f" ({', '.join(match_terms)})" if match_terms else "")
            )
        
        request_text = inline_text
        
        # 获取API配置参数
        host = XFYUN_CONFIG["host"]
        app_id = XFYUN_CONFIG["app_id"]
        api_key = XFYUN_CONFIG["api_key"]
        secret = XFYUN_CONFIG["secret"]
        
        business_args = {"from": from_lang, "to": to_lang}
        
        # 执行翻译
        translator = get_result(host, app_id, api_key, secret, request_text, business_args)
        result = translator.call_url()
        
        if result:
            final_result = enforce_glossary_in_result(result, applied_entries)
            logger.info(f"API翻译完成: '{text_cleaned}' -> '{final_result}'")
            return final_result
        
        logger.warning(f"API翻译失败或无结果，返回兜底结果: '{text_cleaned}'")
        if applied_entries:
            logger.info(f"使用本地词典兜底: '{text_cleaned}' -> '{inline_text}'")
            return inline_text
        return text
        
    except Exception as e:
        logger.error(f"翻译函数发生错误: {str(e)}")
        return text
