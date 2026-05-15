import sys

from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from viewmodels.main_viewmodel import main_viewmodel


class ChatSignal(QObject):
    updated = pyqtSignal()


chat_signal = ChatSignal()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("숲TV 채팅 검색기")
        self.setMinimumSize(700, 600)
        self.is_dark = True
        self.init_ui()
        self.apply_theme()
        self.load_favorites()

        chat_signal.updated.connect(self.auto_update_chat)
        main_viewmodel.on_chat_updated = lambda: chat_signal.updated.emit()
        main_viewmodel.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.load_streamers)
        self.timer.start(3000)

        self.chat_timer = QTimer()
        self.chat_timer.timeout.connect(self.auto_update_chat)
        self.chat_timer.start(1000)

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # 헤더
        header = QHBoxLayout()
        title = QLabel("숲TV 채팅 검색기")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.theme_btn = QPushButton("☀️ 라이트모드")
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

        add_label = QLabel("방송 추가")
        add_label.setFont(QFont("Arial", 10))

        input_row = QHBoxLayout()
        self.streamer_input = QLineEdit()
        self.streamer_input.setPlaceholderText("스트리머 ID 또는 URL 입력")
        self.streamer_input.setFixedHeight(36)
        self.add_btn = QPushButton("추가")
        self.add_btn.setFixedSize(60, 36)
        self.add_btn.clicked.connect(self.add_streamer)
        self.remove_btn = QPushButton("제거")
        self.remove_btn.setFixedSize(60, 36)
        self.remove_btn.clicked.connect(self.remove_streamer)
        self.fav_btn = QPushButton("★")
        self.fav_btn.setFixedSize(36, 36)
        self.fav_btn.clicked.connect(self.toggle_favorite)
        input_row.addWidget(self.streamer_input)
        input_row.addWidget(self.add_btn)
        input_row.addWidget(self.remove_btn)
        input_row.addWidget(self.fav_btn)

        fav_label = QLabel("즐겨찾기 (더블클릭으로 추가)")
        fav_label.setFont(QFont("Arial", 9))
        self.fav_list = QListWidget()
        self.fav_list.setFixedHeight(70)
        self.fav_list.itemDoubleClicked.connect(self.add_from_favorite)
        self.fav_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.fav_list.customContextMenuRequested.connect(self.fav_context_menu)

        add_layout.addWidget(add_label)
        add_layout.addLayout(input_row)
        add_layout.addWidget(fav_label)
        add_layout.addWidget(self.fav_list)
        layout.addWidget(add_frame)

        # 채팅 검색 섹션
        search_frame = QFrame()
        search_frame.setFrameShape(QFrame.Shape.StyledPanel)
        search_layout = QVBoxLayout(search_frame)

        search_label = QLabel("채팅 검색")
        search_label.setFont(QFont("Arial", 10))

        search_row = QHBoxLayout()
        self.nick_input = QLineEdit()
        self.nick_input.setPlaceholderText("닉네임 검색")
        self.nick_input.setFixedHeight(36)
        self.nick_input.returnPressed.connect(self.search_chat)
        self.search_btn = QPushButton("검색")
        self.search_btn.setFixedSize(60, 36)
        self.search_btn.clicked.connect(self.search_chat)
        search_row.addWidget(self.nick_input)
        search_row.addWidget(self.search_btn)

        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        self.chat_list = QListWidget()
        self.chat_list.setFont(QFont("Arial", 10))

        search_layout.addWidget(search_label)
        search_layout.addLayout(search_row)
        search_layout.addWidget(self.tab_widget)
        search_layout.addWidget(self.chat_list)
        layout.addWidget(search_frame)

    def add_streamer(self):
        raw = self.streamer_input.text().strip()
        if not raw:
            return
        message = main_viewmodel.add_streamer(raw)
        self.streamer_input.clear()
        self.load_streamers()
        self.chat_list.clear()
        self.chat_list.addItem(message)

    def remove_streamer(self):
        raw = self.streamer_input.text().strip()
        if not raw:
            return
        message = main_viewmodel.remove_streamer(raw)
        self.streamer_input.clear()
        self.load_streamers()
        self.chat_list.clear()
        self.chat_list.addItem(message)

    def load_streamers(self):
        streamers = main_viewmodel.get_active_streamers()

        current_tab = self.tab_widget.currentIndex()
        self.tab_widget.blockSignals(True)
        self.tab_widget.clear()
        for s in streamers:
            self.tab_widget.addTab(QWidget(), s)
        self.tab_widget.blockSignals(False)
        if 0 <= current_tab < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(current_tab)

    def on_tab_changed(self, index):
        self.chat_list.clear()

    def toggle_favorite(self):
        raw = self.streamer_input.text().strip()
        if not raw:
            return
        streamer_id = main_viewmodel.extract_id(raw)
        main_viewmodel.toggle_favorite(streamer_id)
        self.load_favorites()

    def load_favorites(self):
        self.fav_list.clear()
        for fav in main_viewmodel.get_favorites():
            self.fav_list.addItem(fav)

    def fav_context_menu(self, pos):
        item = self.fav_list.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        delete_action = menu.addAction("삭제")
        action = menu.exec(self.fav_list.mapToGlobal(pos))
        if action == delete_action:
            main_viewmodel.remove_favorite(item.text())
            self.load_favorites()

    def add_from_favorite(self, item):
        streamer_id = main_viewmodel.get_favorite_id(item.text())
        message = main_viewmodel.add_streamer(streamer_id)
        self.load_streamers()
        self.chat_list.addItem(message)

    def search_chat(self):
        idx = self.tab_widget.currentIndex()
        streamer_id = self.tab_widget.tabText(idx) if idx >= 0 else ""
        nick = self.nick_input.text().strip()
        if not streamer_id:
            self.chat_list.clear()
            self.chat_list.addItem("방송을 선택해주세요")
            return
        if not nick:
            self.chat_list.clear()
            self.chat_list.addItem("닉네임을 입력해주세요")
            return
        chats = main_viewmodel.search_by_nickname(streamer_id, nick)
        self.chat_list.clear()
        if not chats:
            self.chat_list.addItem("채팅 내역이 없습니다")
            return
        for c in chats:
            item = QListWidgetItem(f"[{c['time']}] {c['nickname']}: {c['message']}")
            self.chat_list.addItem(item)
        self.chat_list.scrollToBottom()

    def auto_update_chat(self):
        idx = self.tab_widget.currentIndex()
        streamer_id = self.tab_widget.tabText(idx) if idx >= 0 else ""
        if not streamer_id:
            return
        nick = self.nick_input.text().strip()
        if nick:
            chats = main_viewmodel.search_by_nickname(streamer_id, nick)
        else:
            chats = main_viewmodel.get_all_chats(streamer_id)
        self.chat_list.clear()
        for c in chats[-100:]:
            self.chat_list.addItem(
                f"[{c['time']}] {c['nickname']}({c['user_id']}): {c['message']}"
            )
        self.chat_list.scrollToBottom()

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.apply_theme()
        self.theme_btn.setText("☀️ 라이트모드" if self.is_dark else "🌙 다크모드")

    def apply_theme(self):
        if self.is_dark:
            self.setStyleSheet(
                """
                QMainWindow, QWidget { background: #0e0e0e; color: #e0e0e0; }
                QFrame { background: #1a1a1a; border: 1px solid #333; border-radius: 8px; }
                QLineEdit, QComboBox { background: #2a2a2a; color: #e0e0e0; border: 1px solid #444; border-radius: 6px; padding: 4px 8px; }
                QListWidget { background: #1a1a1a; color: #e0e0e0; border: 1px solid #333; border-radius: 6px; }
                QTabWidget::pane { border: 1px solid #333; }
                QTabBar::tab { background: #2a2a2a; color: #e0e0e0; padding: 6px 16px; border-radius: 4px; }
                QTabBar::tab:selected { background: #4a9eff; color: white; }
                QPushButton { border-radius: 6px; padding: 4px 8px; }
            """
            )
            self.add_btn.setStyleSheet("background: #4a9eff; color: white;")
            self.remove_btn.setStyleSheet("background: #ff4a4a; color: white;")
            self.search_btn.setStyleSheet("background: #4aff88; color: #0e0e0e;")
            self.fav_btn.setStyleSheet("background: #f0a500; color: white;")
            self.theme_btn.setStyleSheet(
                "background: #ffffff; color: #1a1a1a; border: 1px solid #444; border-radius: 6px;"
            )

        else:
            self.setStyleSheet(
                """
                QMainWindow, QWidget { background: #f5f5f5; color: #1a1a1a; }
                QFrame { background: #ffffff; border: 1px solid #ddd; border-radius: 8px; }
                QLineEdit, QComboBox { background: #eeeeee; color: #1a1a1a; border: 1px solid #ddd; border-radius: 6px; padding: 4px 8px; }
                QListWidget { background: #ffffff; color: #1a1a1a; border: 1px solid #ddd; border-radius: 6px; }
                QTabWidget::pane { border: 1px solid #ddd; }
                QTabBar::tab { background: #eeeeee; color: #1a1a1a; padding: 6px 16px; border-radius: 4px; }
                QTabBar::tab:selected { background: #1a7fe8; color: white; }
                QPushButton { border-radius: 6px; padding: 4px 8px; }
            """
            )
            self.add_btn.setStyleSheet("background: #1a7fe8; color: white;")
            self.remove_btn.setStyleSheet("background: #ff4a4a; color: white;")
            self.search_btn.setStyleSheet("background: #2ecc71; color: white;")
            self.fav_btn.setStyleSheet("background: #e09400; color: white;")
            self.theme_btn.setStyleSheet(
                "background: #1a1a1a; color: #ffffff; border: 1px solid #ddd; border-radius: 6px;"
            )
