import sys
import ctypes
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QFont
from flask import Flask, request
import threading
from trans import get_result  # 请确保您有一个名为 trans.py 的翻译模块

app = Flask(__name__)
current_y_position = 1000  # 初始垂直位置
default_height = 200  # 默认高度

class TranslatorThread(QThread):
    result_ready = pyqtSignal(str)
    finished_signal = pyqtSignal(QThread)  # 新增信号

    def __init__(self, text):
        super().__init__()
        self.text = text

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
        self.result_ready.emit(english_text)
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
        self.translator_threads = []  # 用于保存线程引用

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
        # 在主线程中更新字幕
        self.update_subtitle(chinese_text, english_text, y_position, chinese_color, english_color, timeout, height)

    def update_subtitle(self, chinese_text, english_text, y_position=None, chinese_color=None, english_color=None, timeout=None, height=None):
        global current_y_position

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
            self.english_label.setText(english_text)

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

    def hide_subtitle(self):
        self.setWindowOpacity(0.0)

    def update_english_subtitle(self, english_text):
        self.english_label.setText(english_text)

    def on_thread_finished(self, thread):
        # 从列表中移除线程引用
        if thread in self.translator_threads:
            self.translator_threads.remove(thread)
            thread.deleteLater()  # 删除线程对象

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

# 启动Qt应用程序
def start_qt_app():
    global ex
    qt_app = QApplication(sys.argv)
    ex = SubtitleWindow()
    ex.show()
    sys.exit(qt_app.exec_())

# 启动Flask服务器
@app.route('/update_subtitle', methods=['POST'])
def update_subtitle_route():
    global ex
    data = request.json
    text = data.get('text', '')
    y_position = data.get('y_position')
    chinese_color = data.get('chinese_color', ex.chinese_color)
    english_color = data.get('english_color', ex.english_color)
    timeout = data.get('timeout')
    height = data.get('height', default_height)

    # 立即使用中文文本更新UI
    ex.update_signal.emit(text, '', y_position, chinese_color, english_color, timeout, height)
    # 0.1秒后立即使用中文文本更新UI
    

    # 启动翻译线程
    translator_thread = TranslatorThread(text)
    translator_thread.result_ready.connect(ex.update_english_subtitle)
    translator_thread.finished_signal.connect(ex.on_thread_finished)  # 连接完成信号
    translator_thread.start()

    # 将线程添加到列表中，防止被垃圾回收
    ex.translator_threads.append(translator_thread)

    return "Subtitle updated!"

def start_flask():
    app.run(host='0.0.0.0', port=4321)

# 主执行部分
if __name__ == '__main__':
    # 在单独的线程中启动Flask服务器
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.start()

    # 在主线程中启动Qt应用程序
    start_qt_app()