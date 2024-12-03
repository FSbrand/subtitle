import sys
import asyncio
import ctypes
import threading
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QThread, QObject
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QFont
import websockets

from trans import get_result  # 请确保您有一个名为 trans.py 的翻译模块

current_y_position = 1000  # 初始垂直位置
default_height = 200  # 默认高度
PORT = 4321  # WebSocket 端口

class TranslatorThread(QThread):
    result_ready = pyqtSignal(str, int)  # 现在传递text_id
    finished_signal = pyqtSignal(QThread)

    def __init__(self, text, text_id):
        super().__init__()
        self.text = text
        self.text_id = text_id  # 保存text_id

    def run(self):
        # 在此线程中执行翻译
        host = "itrans.xfyun.cn"
        app_id = "43db53bc"  # 填入实际的AppID
        api_key = "401e2f30446a5e7e90671a72edea21af"  # 填入实际的APIKey
        secret = "NjE0NTIzNWI1M2JhMTg3OTM1MGI5MGU4"
        business_args = {"from": "cn", "to": "en"}
        translator = get_result(host, app_id, api_key, secret, self.text, business_args)
        response = translator.call_url()
        if response != '':
            english_text = response
        else:
            english_text = self.text  # 如果翻译失败，仍然显示原始文本
        self.result_ready.emit(english_text, self.text_id)
        # 线程完成，发出完成信号
        self.finished_signal.emit(self)

class SubtitleWindow(QWidget):
    update_signal = pyqtSignal(str, str, object, object, object, object, object)

    def __init__(self):
        super().__init__()
        self.chinese_color = ''  # 默认中文字幕颜色
        self.english_color = ''  # 默认英文字幕颜色
        self.timeout_interval = 6000  # 默认超时时间（毫秒）
        self.height = default_height  # 默认高度
        self.initUI()
        self.hide_timer = None
        self.translator_threads = []  # 用于保存翻译线程的引用
        self.current_text_id = 0  # 用于跟踪当前文本的ID

        # 连接更新信号到槽
        self.update_signal.connect(self.update_subtitle_slot)

    def initUI(self):
        # 设置窗口基本属性
        self.setWindowTitle('Subtitle Display')
        screen_width = QApplication.primaryScreen().size().width()
        self.setGeometry(0, current_y_position, screen_width, self.height)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)

        max_label_width = int(0.95 * screen_width)

        # 创建中文标签
        self.chinese_label = QLabel("", self)
        self.chinese_label.setAlignment(Qt.AlignCenter)
        font = QFont('Microsoft YaHei UI', 20, QFont.Bold)
        self.chinese_label.setFont(font)
        self.chinese_label.setStyleSheet(f"color: {self.chinese_color};")
        self.chinese_label.setMaximumWidth(max_label_width)

        # 创建英文标签
        self.english_label = QLabel("", self)
        self.english_label.setAlignment(Qt.AlignCenter)
        font = QFont('Microsoft YaHei UI', 20, QFont.Bold)
        self.english_label.setFont(font)
        self.english_label.setStyleSheet(f"color: {self.english_color};")
        self.english_label.setMaximumWidth(max_label_width)

        # 布局设置
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.chinese_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.english_label, alignment=Qt.AlignCenter)
        self.setLayout(layout)

        # 定时器，确保窗口始终在顶部
        self.topmost_timer = QTimer(self)
        self.topmost_timer.timeout.connect(self.set_always_on_top)
        self.topmost_timer.start(100)  # 每100毫秒检查一次

    def update_subtitle_slot(self, chinese_text, english_text, y_position=None, chinese_color=None, english_color=None, timeout=None, height=None):
        self.update_subtitle(chinese_text, english_text, y_position, chinese_color, english_color, timeout, height)
        if not english_text:
            self.start_translation(chinese_text)

    def update_subtitle(self, chinese_text, english_text, y_position=None, chinese_color=None, english_color=None, timeout=None, height=None):
        global current_y_position

        # 更新当前文本ID
        self.current_text_id += 1
        self.current_chinese_text_id = self.current_text_id

        if y_position is not None:
            current_y_position = y_position
            self.move(0, current_y_position)  # 动态更新垂直位置

        if chinese_color and chinese_color != self.chinese_color:
            self.chinese_color = chinese_color
            self.chinese_label.setStyleSheet(f"color: {self.chinese_color};")  # 更新中文字体颜色

        if english_color and english_color != self.english_color:
            self.english_color = english_color
            self.english_label.setStyleSheet(f"color: {self.english_color};")  # 更新英文字体颜色

        if timeout is not None:
            self.timeout_interval = int(timeout) * 1000  # 转换为毫秒

        if height is not None:
            self.height = int(height)
            screen_width = QApplication.primaryScreen().size().width()
            self.setGeometry(0, current_y_position, screen_width, self.height)  # 更新窗口高度

        # 更新字幕文本
        if chinese_text != self.chinese_label.text() or english_text != self.english_label.text():
            self.chinese_label.setText(chinese_text)
            if english_text:
                self.english_label.setText(english_text)
            else:
                self.english_label.setText('')  # 清空英文字幕，等待新的翻译

        # 显示字幕
        self.setWindowOpacity(1.0)
        # 重置计时器
        if self.hide_timer and self.hide_timer.isActive():
            self.hide_timer.stop()

        # 启动新的计时器，在超时时间后隐藏字幕
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_subtitle)
        self.hide_timer.start(self.timeout_interval)

    def start_translation(self, text):
        text_id = self.current_chinese_text_id  # 获取当前文本的ID
        translator_thread = TranslatorThread(text, text_id)
        translator_thread.result_ready.connect(self.update_english_subtitle)
        translator_thread.finished_signal.connect(self.on_thread_finished)
        translator_thread.start()
        self.translator_threads.append(translator_thread)

    def update_english_subtitle(self, english_text, text_id):
        # 只有当text_id匹配时才更新字幕
        if text_id == self.current_chinese_text_id:
            self.english_label.setText(english_text)

    def on_thread_finished(self, thread):
        if thread in self.translator_threads:
            self.translator_threads.remove(thread)
            thread.deleteLater()

    def hide_subtitle(self):
        self.setWindowOpacity(0.0)

    def set_always_on_top(self):
        hwnd = self.winId().__int__()
        HWND_TOPMOST = -1
        SWP_NOSIZE = 0x0001
        SWP_NOMOVE = 0x0002
        SWP_SHOWWINDOW = 0x0040
        GWL_EXSTYLE = -20
        WS_EX_TOPMOST = 0x00000008
        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_NOACTIVATE = 0x08000000
        user32 = ctypes.windll.user32
        SetWindowLong = user32.SetWindowLongW
        GetWindowLong = user32.GetWindowLongW
        # 移除冲突的扩展样式
        current_style = GetWindowLong(hwnd, GWL_EXSTYLE)
        new_style = (current_style | WS_EX_TOPMOST | WS_EX_TOOLWINDOW) & ~WS_EX_NOACTIVATE
        SetWindowLong(hwnd, GWL_EXSTYLE, new_style)
        # 设置窗口位置
        user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
        # 将窗口置于顶部
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)

async def websocket_handler(websocket):
    print("[INFO] WebSocket server started and waiting for client connection...")
    async for message in websocket:
        print(f"[DEBUG] Received message: {message}")
        try:
            import json
            data = json.loads(message)
            text = data.get('text', '')
            y_position = data.get('y_position')
            chinese_color = data.get('chinese_color', ex.chinese_color)
            english_color = data.get('english_color', ex.english_color)
            timeout = data.get('timeout')
            height = data.get('height', default_height)

            # 发送更新信号到 UI
            ex.update_signal.emit(text, '', y_position, chinese_color, english_color, timeout, height)
        except Exception as e:
            print(f"[ERROR] Failed to process message: {e}")

async def start_websocket_server():
    print(f"[INFO] Starting WebSocket server on ws://0.0.0.0:{PORT}")
    async with websockets.serve(websocket_handler, "0.0.0.0", PORT):
        print("[INFO] WebSocket server started and ready to accept connections")
        await asyncio.Future()  # Keep the server running

def start_websocket_server_in_thread():
    asyncio.run(start_websocket_server())

def start_qt_app():
    global ex
    qt_app = QApplication(sys.argv)
    ex = SubtitleWindow()
    ex.show()
    sys.exit(qt_app.exec_())

if __name__ == '__main__':
    # 启动 WebSocket 服务器线程
    websocket_thread = threading.Thread(target=start_websocket_server_in_thread)
    websocket_thread.start()

    # 启动 PyQt5 应用程序
    start_qt_app()
