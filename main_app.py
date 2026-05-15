import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QComboBox, QListWidgetItem, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
from chat_collector import add_streamer, remove_streamer, active_streamers, start
from storage import storage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('숲TV 채팅 검색기')
        self.setMinimumSize(700, 600)
        self.is_dark = True
        self.init_ui()
        self.apply_theme()

        # 채팅 수집기 시작
        start()

        # 3초마다 방송 목록 갱신
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_streamers)
        self.timer.start(3000)

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # 상단 헤더
        header = QHBoxLayout()
        title = QLabel('숲TV 채팅 검색기')
        title.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        self.theme_btn = QPushButton('☀️ 라이트모드')
        self.theme_btn.setFixedWidth(110)
        self.theme_btn.clicked.connect(self.toggle_theme)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.theme_btn)
        layout.addLayout(header)

        # 방송 추가 섹션
        add_frame = QFrame()
        add_frame.setFrameShape(QFrame.Shape.StyledPanel)
        add_layout = QVBoxLayout(add_frame)

        add_label = QLabel('방송 추가')
        add_label.setFont(QFont('Arial', 10))

        input_row = QHBoxLayout()
        self.streamer_input = QLineEdit()
        self.streamer_input.setPlaceholderText('스트리머 ID 또는 URL 입력')
        self.streamer_input.setFixedHeight(36)
        self.add_btn = QPushButton('추가')
        self.add_btn.setFixedSize(60, 36)
        self.add_btn.clicked.connect(self.add_streamer)
        self.remove_btn = QPushButton('제거')
        self.remove_btn.setFixedSize(60, 36)
        self.remove_btn.clicked.connect(self.remove_streamer)

        input_row.addWidget(self.streamer_input)
        input_row.addWidget(self.add_btn)
        input_row.addWidget(self.remove_btn)

        self.streamer_list_label = QLabel('수집 중인 방송: 없음')
        self.streamer_list_label.setFont(QFont('Arial', 9))

        add_layout.addWidget(add_label)
        add_layout.addLayout(input_row)
        add_layout.addWidget(self.streamer_list_label)
        layout.addWidget(add_frame)

        # 채팅 검색 섹션
        search_frame = QFrame()
        search_frame.setFrameShape(QFrame.Shape.StyledPanel)
        search_layout = QVBoxLayout(search_frame)

        search_label = QLabel('채팅 검색')
        search_label.setFont(QFont('Arial', 10))

        search_row = QHBoxLayout()
        self.streamer_combo = QComboBox()
        self.streamer_combo.setFixedHeight(36)
        self.streamer_combo.setMinimumWidth(160)
        self.nick_input = QLineEdit()
        self.nick_input.setPlaceholderText('닉네임 검색')
        self.nick_input.setFixedHeight(36)
        self.nick_input.returnPressed.connect(self.search_chat)
        self.search_btn = QPushButton('검색')
        self.search_btn.setFixedSize(60, 36)
        self.search_btn.clicked.connect(self.search_chat)

        search_row.addWidget(self.streamer_combo)
        search_row.addWidget(self.nick_input)
        search_row.addWidget(self.search_btn)

        self.chat_list = QListWidget()
        self.chat_list.setFont(QFont('Arial', 10))

        search_layout.addWidget(search_label)
        search_layout.addLayout(search_row)
        search_layout.addWidget(self.chat_list)
        layout.addWidget(search_frame)

    def extract_id(self, text):
        # URL에서 ID 추출
        text = text.strip()
        if 'sooplive.co.kr/' in text:
            return text.split('sooplive.co.kr/')[-1].split('/')[0]
        return text

    def add_streamer(self):
        raw = self.streamer_input.text().strip()
        if not raw:
            return
        streamer_id = self.extract_id(raw)
        message = add_streamer(streamer_id)
        self.streamer_input.clear()
        self.load_streamers()
        self.chat_list.clear()
        self.chat_list.addItem(message)

    def remove_streamer(self):
        raw = self.streamer_input.text().strip()
        if not raw:
            return
        streamer_id = self.extract_id(raw)
        message = remove_streamer(streamer_id)
        self.streamer_input.clear()
        self.load_streamers()
        self.chat_list.clear()
        self.chat_list.addItem(message)

    def load_streamers(self):
        streamers = list(active_streamers)
        if streamers:
            self.streamer_list_label.setText(f'수집 중인 방송: {", ".join(streamers)}')
        else:
            self.streamer_list_label.setText('수집 중인 방송: 없음')

        current = self.streamer_combo.currentText()
        self.streamer_combo.clear()
        self.streamer_combo.addItem('방송 선택')
        for s in streamers:
            self.streamer_combo.addItem(s)
        if current in streamers:
            self.streamer_combo.setCurrentText(current)

    def search_chat(self):
        streamer_id = self.streamer_combo.currentText()
        nick = self.nick_input.text().strip()
        if streamer_id == '방송 선택' or not streamer_id:
            self.chat_list.clear()
            self.chat_list.addItem('방송을 선택해주세요')
            return
        if not nick:
            self.chat_list.clear()
            self.chat_list.addItem('닉네임을 입력해주세요')
            return

        chats = storage.search_by_nickname(streamer_id, nick)
        self.chat_list.clear()
        if not chats:
            self.chat_list.addItem('채팅 내역이 없습니다')
            return
        for c in chats:
            item = QListWidgetItem(f"[{c['time']}] {c['nickname']}: {c['message']}")
            self.chat_list.addItem(item)
        self.chat_list.scrollToBottom()

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.apply_theme()
        self.theme_btn.setText('☀️ 라이트모드' if self.is_dark else '🌙 다크모드')

    def apply_theme(self):
        if self.is_dark:
            self.setStyleSheet('''
                QMainWindow, QWidget { background: #0e0e0e; color: #e0e0e0; }
                QFrame { background: #1a1a1a; border: 1px solid #333; border-radius: 8px; }
                QLineEdit, QComboBox { background: #2a2a2a; color: #e0e0e0; border: 1px solid #444; border-radius: 6px; padding: 4px 8px; }
                QListWidget { background: #1a1a1a; color: #e0e0e0; border: 1px solid #333; border-radius: 6px; }
                QPushButton { border-radius: 6px; padding: 4px 8px; }
            ''')
            self.add_btn.setStyleSheet('background: #4a9eff; color: white;')
            self.remove_btn.setStyleSheet('background: #ff4a4a; color: white;')
            self.search_btn.setStyleSheet('background: #4aff88; color: #0e0e0e;')
            self.theme_btn.setStyleSheet('background: #ffffff; color: #1a1a1a; border: 1px solid #444; border-radius: 6px;')
        else:
            self.setStyleSheet('''
                QMainWindow, QWidget { background: #f5f5f5; color: #1a1a1a; }
                QFrame { background: #ffffff; border: 1px solid #ddd; border-radius: 8px; }
                QLineEdit, QComboBox { background: #eeeeee; color: #1a1a1a; border: 1px solid #ddd; border-radius: 6px; padding: 4px 8px; }
                QListWidget { background: #ffffff; color: #1a1a1a; border: 1px solid #ddd; border-radius: 6px; }
                QPushButton { border-radius: 6px; padding: 4px 8px; }
            ''')
            self.add_btn.setStyleSheet('background: #1a7fe8; color: white;')
            self.remove_btn.setStyleSheet('background: #ff4a4a; color: white;')
            self.search_btn.setStyleSheet('background: #2ecc71; color: white;')
            self.theme_btn.setStyleSheet('background: #1a1a1a; color: #ffffff; border: 1px solid #ddd; border-radius: 6px;')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())