# -*- coding: utf-8 -*-
"""
字幕软件主程序
基于PyQt5和WebSocket的实时字幕显示系统
支持科大讯飞翻译API，配置界面和增强错误处理
"""

import sys
import asyncio
import ctypes
import threading
import logging
import traceback
import os
from datetime import datetime
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QThread, QObject
from PyQt5.QtWidgets import (QApplication, QLabel, QWidget, QVBoxLayout, 
                           QSystemTrayIcon, QMenu, QAction, QMessageBox)
from PyQt5.QtGui import QFont, QIcon
import websockets
import json

from config import DISPLAY_CONFIG, NETWORK_CONFIG
from trans import translate_text
from language_detector import get_display_layout

# 配置日志 - 按天生成日志文件
os.makedirs('log', exist_ok=True)
log_filename = f"log/subtitle_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TranslatorThread(QThread):
    """翻译线程，异步处理翻译任务"""
    result_ready = pyqtSignal(str, int)  # 翻译结果和文本ID
    finished_signal = pyqtSignal(QThread)  # 线程完成信号
    error_signal = pyqtSignal(str)  # 错误信号

    def __init__(self, text, text_id):
        super().__init__()
        self.text = text
        self.text_id = text_id

    def run(self):
        """执行翻译"""
        try:
            logger.info(f"开始翻译文本[{self.text_id}]: {self.text}")
            english_text = translate_text(self.text)
            self.result_ready.emit(english_text, self.text_id)
            logger.info(f"翻译完成[{self.text_id}]: {self.text} -> {english_text}")
        except Exception as e:
            error_msg = f"翻译线程错误[{self.text_id}]: {str(e)}"
            logger.error(error_msg)
            self.error_signal.emit(error_msg)
            # 翻译失败时发送原文
            self.result_ready.emit(self.text, self.text_id)
        finally:
            self.finished_signal.emit(self)

class SubtitleWindow(QWidget):
    """字幕显示窗口"""
    update_signal = pyqtSignal(str, str, object, object, object, object, object)

    def __init__(self):
        super().__init__()
        self.load_config()
        self.initUI()
        self.hide_timer = None
        self.translator_threads = []  # 翻译线程列表
        self.current_text_id = 0  # 当前文本ID

        # 连接信号
        self.update_signal.connect(self.update_subtitle_slot)
        
        logger.info("字幕窗口初始化完成")

    def load_config(self):
        """加载配置"""
        try:
            self.top_color = DISPLAY_CONFIG["default_top_color"]
            self.bottom_color = DISPLAY_CONFIG["default_bottom_color"]
            self.timeout_interval = DISPLAY_CONFIG["default_timeout"] * 1000
            self.height = DISPLAY_CONFIG["default_height"]
            self.font_family = DISPLAY_CONFIG["font_family"]
            self.font_size = DISPLAY_CONFIG["font_size"]
            self.y_position = DISPLAY_CONFIG["default_y_position"]
            logger.info("配置加载成功")
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            # 设置默认值
            self.top_color = "yellow"
            self.bottom_color = "white"
            self.timeout_interval = 6000
            self.height = 200
            self.font_family = "Microsoft YaHei UI"
            self.font_size = 20
            self.y_position = 1000

    def initUI(self):
        """初始化用户界面"""
        try:
            # 设置窗口基本属性
            self.setWindowTitle('Subtitle Display')
            screen_width = QApplication.primaryScreen().size().width()
            self.setGeometry(0, self.y_position, screen_width, self.height)
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint | Qt.SubWindow)
            self.setAttribute(Qt.WA_TranslucentBackground)

            # 创建上方标签 - 使用全屏宽度，不自动换行
            self.top_label = QLabel("", self)
            self.top_label.setAlignment(Qt.AlignCenter)
            font = QFont(self.font_family, self.font_size, QFont.Bold)
            self.top_label.setFont(font)
            self.top_label.setStyleSheet(f"color: {self.top_color};")
            self.top_label.setWordWrap(False)  # 禁用自动换行

            # 创建下方标签 - 使用全屏宽度，不自动换行
            self.bottom_label = QLabel("", self)
            self.bottom_label.setAlignment(Qt.AlignCenter)
            font = QFont(self.font_family, self.font_size, QFont.Bold)
            self.bottom_label.setFont(font)
            self.bottom_label.setStyleSheet(f"color: {self.bottom_color};")
            self.bottom_label.setWordWrap(False)  # 禁用自动换行

            # 布局设置 - 最小边距，最大化可用宽度
            layout = QVBoxLayout()
            layout.setSpacing(2)
            layout.setContentsMargins(0, 5, 0, 5)  # 仅保留上下边距
            layout.addWidget(self.top_label, alignment=Qt.AlignCenter)
            layout.addWidget(self.bottom_label, alignment=Qt.AlignCenter)
            self.setLayout(layout)

            # 定时器，确保窗口始终在顶部
            self.topmost_timer = QTimer(self)
            self.topmost_timer.timeout.connect(self.set_always_on_top)
            self.topmost_timer.start(100)  # 每100毫秒检查一次

            logger.info("字幕窗口UI初始化完成")
            
        except Exception as e:
            logger.error(f"UI初始化失败: {e}")
            raise

    def update_subtitle_slot(self, source_text, target_text, y_position=None, 
                           top_color=None, bottom_color=None, timeout=None, height=None):
        """字幕更新槽函数"""
        try:
            logger.info(f"接收到字幕更新请求 - 原文: {source_text}, 译文: {target_text}, 位置: {y_position}, 上方颜色: {top_color}, 下方颜色: {bottom_color}, 超时: {timeout}, 高度: {height}")
            self.update_subtitle(source_text, target_text, y_position, 
                               top_color, bottom_color, timeout, height)
        except Exception as e:
            logger.error(f"字幕更新失败: {e}")

    def update_subtitle(self, source_text, target_text, y_position=None, 
                       top_color=None, bottom_color=None, timeout=None, height=None):
        """更新字幕显示"""
        try:
            # 更新当前文本ID
            self.current_text_id += 1
            self.current_source_text_id = self.current_text_id

            # 获取显示布局信息
            layout_info = get_display_layout(source_text)
            logger.info(f"检测到语言布局: {layout_info}")
            
            # 更新位置
            if y_position is not None:
                self.y_position = y_position
                self.move(0, self.y_position)
                logger.info(f"更新字幕位置: {y_position}")

            # 更新颜色
            if top_color and top_color != self.top_color:
                self.top_color = top_color
                self.top_label.setStyleSheet(f"color: {self.top_color};")
                logger.info(f"更新上方颜色: {top_color}")

            if bottom_color and bottom_color != self.bottom_color:
                self.bottom_color = bottom_color
                self.bottom_label.setStyleSheet(f"color: {self.bottom_color};")
                logger.info(f"更新下方颜色: {bottom_color}")

            # 更新高度
            if height is not None:
                self.height = height
                self.resize(self.width(), self.height)
                logger.info(f'更新窗口高度: {height}')

            # 根据语言检测结果设置文本显示
            if layout_info['from_lang'] == 'cn':
                # 中文在上，翻译在下
                self.top_label.setText(source_text)
                if target_text:
                    self.bottom_label.setText(target_text)
                else:
                    # 启动翻译线程，翻译前底部标签保持空白
                    self.bottom_label.setText("")
                    self.start_translation(source_text, self.current_source_text_id)
            else:
                # 外文在上，中文翻译在下
                self.top_label.setText(source_text)
                if target_text:
                    self.bottom_label.setText(target_text)
                else:
                    # 启动翻译线程，翻译前底部标签保持空白
                    self.bottom_label.setText("")
                    self.start_translation(source_text, self.current_source_text_id)

            # 显示窗口
            self.show()
            self.set_always_on_top()

            # 设置自动隐藏计时器
            timeout_ms = int(timeout * 1000) if timeout else self.timeout_interval
            if self.hide_timer:
                self.hide_timer.stop()

            self.hide_timer = QTimer(self)
            self.hide_timer.setSingleShot(True)
            self.hide_timer.timeout.connect(self.hide_subtitle)
            self.hide_timer.start(timeout_ms)
            
            logger.info(f"字幕显示成功，{timeout_ms/1000}秒后自动隐藏")

        except Exception as e:
            logger.error(f"更新字幕时发生错误: {e}")
            logger.error(traceback.format_exc())

    def start_translation(self, text, text_id):
        """启动翻译线程"""
        try:
            translator = TranslatorThread(text, text_id)
            translator.result_ready.connect(self.on_translation_ready)
            translator.error_signal.connect(self.on_translation_error)
            translator.finished_signal.connect(self.on_translation_finished)
            
            self.translator_threads.append(translator)
            translator.start()
            
            logger.info(f"启动翻译线程[{text_id}]: {text}")
        except Exception as e:
            logger.error(f"启动翻译线程失败: {e}")

    def on_translation_ready(self, translated_text, text_id):
        """翻译结果准备就绪"""
        try:
            # 只更新当前显示的文本
            if hasattr(self, 'current_source_text_id') and text_id == self.current_source_text_id:
                self.bottom_label.setText(translated_text)
                logger.info(f"翻译结果已更新[{text_id}]: {translated_text}")
            else:
                logger.info(f"忽略过期翻译结果[{text_id}]: {translated_text}")
        except Exception as e:
            logger.error(f"处理翻译结果时发生错误: {e}")

    def on_translation_error(self, error_msg):
        """翻译错误处理"""
        self.bottom_label.setText("翻译失败")
        logger.error(f"翻译错误: {error_msg}")

    def on_translation_finished(self, thread):
        """翻译线程完成"""
        try:
            if thread in self.translator_threads:
                self.translator_threads.remove(thread)
                thread.deleteLater()
        except Exception as e:
            logger.error(f"清理翻译线程时发生错误: {e}")

    def hide_subtitle(self):
        """隐藏字幕"""
        try:
            self.hide()
            self.top_label.setText("")
            self.bottom_label.setText("")
            logger.info("字幕已隐藏")
        except Exception as e:
            logger.error(f"隐藏字幕时发生错误: {e}")

    def set_always_on_top(self):
        """设置窗口始终在最上层"""
        try:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint | Qt.SubWindow)
            self.show()
        except Exception as e:
            logger.error(f"设置窗口置顶时发生错误: {e}")

class SystemTrayIcon(QSystemTrayIcon):
    """系统托盘图标"""
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        self.setToolTip('字幕软件')
        self.setup_menu()

    def setup_menu(self):
        """设置托盘菜单"""
        try:
            menu = QMenu()
            
            show_action = QAction("显示", self)
            show_action.triggered.connect(self.show_window)
            menu.addAction(show_action)
            
            hide_action = QAction("隐藏", self)
            hide_action.triggered.connect(self.hide_window)
            menu.addAction(hide_action)
            
            menu.addSeparator()
            
            quit_action = QAction("退出", self)
            quit_action.triggered.connect(self.quit_application)
            menu.addAction(quit_action)
            
            self.setContextMenu(menu)
            logger.info("系统托盘菜单设置完成")
        except Exception as e:
            logger.error(f"设置系统托盘菜单失败: {e}")

    def show_window(self):
        """显示窗口"""
        if hasattr(self.parent(), 'show'):
            self.parent().show()

    def hide_window(self):
        """隐藏窗口"""
        if hasattr(self.parent(), 'hide'):
            self.parent().hide()

    def quit_application(self):
        """退出应用程序"""
        QApplication.quit()

class WebSocketHandler:
    """WebSocket消息处理器"""
    def __init__(self, subtitle_window):
        self.subtitle_window = subtitle_window

    async def handle_message(self, websocket):
        """处理WebSocket消息"""
        try:
            logger.info(f"WebSocket客户端连接: {websocket.remote_address}")
            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.info(f"接收到WebSocket消息: {data}")
                    
                    # 解析消息
                    source_text = data.get('text', '')
                    target_text = data.get('target_text', '')
                    y_position = data.get('y_position')
                    top_color = data.get('top_color')
                    bottom_color = data.get('bottom_color')
                    timeout = data.get('timeout')
                    height = data.get('height')
                    
                    logger.info(f"解析参数 - 原文: {source_text}, 译文: {target_text}, 位置: {y_position}, 上方颜色: {top_color}, 下方颜色: {bottom_color}, 超时: {timeout}, 高度: {height}")

                    # 发送更新信号
                    self.subtitle_window.update_signal.emit(
                        source_text, target_text, y_position, 
                        top_color, bottom_color, timeout, height
                    )
                    
                    # 发送确认响应
                    response = {"status": "success", "message": "字幕已更新"}
                    await websocket.send(json.dumps(response))
                    logger.info(f"发送响应: {response}")
                    
                except json.JSONDecodeError as e:
                    error_msg = f"JSON解析错误: {e}"
                    logger.error(error_msg)
                    await websocket.send(json.dumps({"status": "error", "message": error_msg}))
                except Exception as e:
                    error_msg = f"处理消息时发生错误: {e}"
                    logger.error(error_msg)
                    logger.error(traceback.format_exc())
                    await websocket.send(json.dumps({"status": "error", "message": error_msg}))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket客户端断开连接")
        except Exception as e:
            logger.error(f"WebSocket连接错误: {e}")
            logger.error(traceback.format_exc())

async def start_websocket_server(subtitle_window):
    """启动WebSocket服务器"""
    try:
        handler = WebSocketHandler(subtitle_window)
        host = NETWORK_CONFIG["websocket_host"]
        port = NETWORK_CONFIG["websocket_port"]
        
        logger.info(f"正在启动WebSocket服务器: ws://{host}:{port}")
        
        server = await websockets.serve(handler.handle_message, host, port)
        logger.info("WebSocket服务器启动成功，等待客户端连接...")
        
        await server.wait_closed()
    except Exception as e:
        logger.error(f"WebSocket服务器启动失败: {e}")
        logger.error(traceback.format_exc())

def main():
    """主函数"""
    try:
        # 设置高DPI支持
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)  # 防止窗口关闭时退出程序
        
        # 创建字幕窗口
        subtitle_window = SubtitleWindow()
        
        # 创建系统托盘图标
        if QSystemTrayIcon.isSystemTrayAvailable():
            # 尝试使用自定义SVG图标
            try:
                icon_path = "icon_simple.svg"
                if os.path.exists(icon_path):
                    icon = QIcon(icon_path)
                    logger.info(f"使用自定义图标: {icon_path}")
                else:
                    # 回退到默认图标
                    icon = app.style().standardIcon(app.style().SP_ComputerIcon)
                    logger.warning(f"未找到图标文件 {icon_path}，使用默认图标")
            except Exception as e:
                # 如果加载自定义图标失败，使用默认图标
                icon = app.style().standardIcon(app.style().SP_ComputerIcon)
                logger.warning(f"加载自定义图标失败: {e}，使用默认图标")
            
            tray_icon = SystemTrayIcon(icon, subtitle_window)
            tray_icon.show()
        else:
            logger.warning("系统托盘不可用")
        
        logger.info("字幕软件启动完成")
        
        # 在新线程中启动WebSocket服务器
        def start_server():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(start_websocket_server(subtitle_window))
            except Exception as e:
                logger.error(f"WebSocket服务器线程错误: {e}")
        
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()

        # 运行应用程序
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"程序启动失败: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()
