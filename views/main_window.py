import sys

from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from viewmodels.main_viewmodel import main_viewmodel
from views.add_frame import AddFrame
from views.fav_frame import FavFrame
from views.search_frame import SearchFrame


class ChatSignal(QObject):
    updated = pyqtSignal()


chat_signal = ChatSignal()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("숲TV 채팅 검색기")
        self.setMinimumSize(700, 600)
        self.is_dark = True
        self.scroll_locked = True
        self.tab_streamers = []
        self.init_ui()
        self.search_frame.chat_list.itemClicked.connect(self.on_chat_clicked)
        self.apply_theme()
        self.load_favorites()

        chat_signal.updated.connect(self.auto_update_chat)
        main_viewmodel.on_chat_updated = lambda: chat_signal.updated.emit()
        main_viewmodel.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.load_streamers)
        self.timer.start(3000)

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

        # 프레임들
        self.add_frame = AddFrame()
        self.fav_frame = FavFrame()
        self.search_frame = SearchFrame()

        # 시그널 연결
        self.add_frame.add_btn.clicked.connect(self.add_streamer)
        self.add_frame.remove_btn.clicked.connect(self.remove_streamer)
        self.add_frame.fav_btn.clicked.connect(self.toggle_favorite)
        self.fav_frame.fav_list.itemDoubleClicked.connect(self.add_from_favorite)
        self.fav_frame.fav_list.customContextMenuRequested.connect(
            self.fav_context_menu
        )
        self.search_frame.nick_input.returnPressed.connect(self.search_chat)
        self.search_frame.search_btn.clicked.connect(self.search_chat)
        self.search_frame.scroll_lock_btn.clicked.connect(self.toggle_scroll_lock)
        self.search_frame.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.search_frame.tab_widget.customContextMenuRequested.connect(
            self.tab_context_menu
        )

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.add_frame)
        splitter.addWidget(self.fav_frame)
        splitter.addWidget(self.search_frame)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 3)
        splitter.setHandleWidth(6)
        layout.addWidget(splitter)

    def add_streamer(self):
        raw = self.add_frame.streamer_input.text().strip()
        if not raw:
            return
        streamer_id = main_viewmodel.extract_id(raw)
        if not main_viewmodel.is_live(streamer_id):
            QMessageBox.warning(self, "알림", f"{streamer_id} 방송 중이 아닙니다!")
            self.add_frame.streamer_input.clear()
            return
        message = main_viewmodel.add_streamer(raw)
        if streamer_id not in self.tab_streamers:
            self.tab_streamers.append(streamer_id)
        self.add_frame.streamer_input.clear()
        self.load_streamers()
        self.search_frame.chat_list.clear()
        self.search_frame.chat_list.addItem(message)

    def remove_streamer(self):
        raw = self.add_frame.streamer_input.text().strip()
        if not raw:
            return
        streamer_id = main_viewmodel.extract_id(raw)
        if streamer_id in self.tab_streamers:
            self.tab_streamers.remove(streamer_id)
        message = main_viewmodel.remove_streamer(streamer_id)
        self.add_frame.streamer_input.clear()
        self.load_streamers()
        self.search_frame.chat_list.clear()
        self.search_frame.chat_list.addItem(message)

    def load_streamers(self):
        tab = self.search_frame.tab_widget
        current_tab = tab.currentIndex()
        tab.blockSignals(True)
        tab.clear()
        for s in self.tab_streamers:
            tab.addTab(QWidget(), s)
        tab.blockSignals(False)
        if 0 <= current_tab < tab.count():
            tab.setCurrentIndex(current_tab)

    def on_tab_changed(self, index):
        self.search_frame.nick_input.clear()
        self.auto_update_chat()

    def tab_context_menu(self, pos):
        tab = self.search_frame.tab_widget
        idx = tab.tabBar().tabAt(pos)
        if idx < 0:
            return
        streamer_id = tab.tabText(idx)
        menu = QMenu(self)
        is_active = streamer_id in main_viewmodel.get_active_streamers()
        toggle_action = menu.addAction("수집 중단" if is_active else "재 시작")
        remove_action = menu.addAction("제거")
        action = menu.exec(tab.mapToGlobal(pos))
        if action == toggle_action:
            if is_active:
                message = main_viewmodel.stop_streamer(streamer_id)
            else:
                message = main_viewmodel.add_streamer(streamer_id)
            self.search_frame.chat_list.addItem(message)
        elif action == remove_action:
            if streamer_id in self.tab_streamers:
                self.tab_streamers.remove(streamer_id)
            message = main_viewmodel.remove_streamer(streamer_id)
            self.load_streamers()
            self.search_frame.chat_list.clear()
            self.search_frame.chat_list.addItem(message)

    def toggle_favorite(self):
        raw = self.add_frame.streamer_input.text().strip()
        if not raw:
            return
        streamer_id = main_viewmodel.extract_id(raw)
        main_viewmodel.toggle_favorite(streamer_id)
        self.load_favorites()

    def load_favorites(self):
        self.fav_frame.fav_list.clear()
        for fav in main_viewmodel.get_favorites():
            self.fav_frame.fav_list.addItem(fav)

    def fav_context_menu(self, pos):
        item = self.fav_frame.fav_list.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        delete_action = menu.addAction("삭제")
        action = menu.exec(self.fav_frame.fav_list.mapToGlobal(pos))
        if action == delete_action:
            main_viewmodel.remove_favorite(item.text())
            self.load_favorites()

    def add_from_favorite(self, item):
        streamer_id = main_viewmodel.get_favorite_id(item.text())
        if not main_viewmodel.is_live(streamer_id):
            QMessageBox.warning(self, "알림", f"{streamer_id} 방송 중이 아닙니다!")
            return
        message = main_viewmodel.add_streamer(streamer_id)
        if streamer_id not in self.tab_streamers:
            self.tab_streamers.append(streamer_id)
        self.load_streamers()
        self.search_frame.chat_list.addItem(message)

    def search_chat(self):
        tab = self.search_frame.tab_widget
        idx = tab.currentIndex()
        streamer_id = tab.tabText(idx) if idx >= 0 else ""
        nick = self.search_frame.nick_input.text().strip()
        if not streamer_id:
            self.search_frame.chat_list.clear()
            self.search_frame.chat_list.addItem("방송을 선택해주세요")
            return
        if not nick:
            self.search_frame.chat_list.clear()
            self.search_frame.chat_list.addItem("닉네임을 입력해주세요")
            return
        chats = main_viewmodel.search_by_nickname(streamer_id, nick)
        self.search_frame.chat_list.clear()
        if not chats:
            self.search_frame.chat_list.addItem("채팅 내역이 없습니다")
            return
        for c in chats:
            item = QListWidgetItem(f"[{c['time']}] {c['nickname']}: {c['message']}")
            self.search_frame.chat_list.addItem(item)

    def on_chat_clicked(self, item):
        text = item.text()
        try:
            nickname = text.split("] ")[1].split("(")[0]
            self.search_frame.nick_input.setText(nickname)
            self.search_chat()
        except Exception:
            pass

    def auto_update_chat(self):
        tab = self.search_frame.tab_widget
        idx = tab.currentIndex()
        if idx < 0:
            return
        streamer_id = tab.tabText(idx)
        if not streamer_id:
            return
        nick = self.search_frame.nick_input.text().strip()
        if nick:
            chats = main_viewmodel.search_by_nickname(streamer_id, nick)
        else:
            chats = main_viewmodel.get_all_chats(streamer_id)

        display_chats = chats[-1000:] if not nick else chats
        new_items = [
            f"[{c['time']}] {c['nickname']}({c['user_id']}): {c['message']}"
            for c in display_chats
        ]
        current_items = [
            self.search_frame.chat_list.item(i).text()
            for i in range(self.search_frame.chat_list.count())
        ]
        if new_items == current_items:
            return

        self.search_frame.chat_list.clear()
        for item in new_items:
            self.search_frame.chat_list.addItem(item)

        if self.scroll_locked:
            self.search_frame.chat_list.scrollToBottom()

    def toggle_scroll_lock(self):
        self.scroll_locked = self.search_frame.scroll_lock_btn.isChecked()
        self.search_frame.scroll_lock_btn.setText("🔒" if self.scroll_locked else "🔓")
        self.apply_theme()

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
                QTabWidget::pane { border: none; background: transparent; }
                QTabBar::tab { background: #2a2a2a; color: #888; padding: 6px 16px; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }
                QTabBar::tab:selected { background: #1a1a1a; color: #e0e0e0; border-bottom: 2px solid #4a9eff; }
                QTabBar::tab:hover { background: #333; color: #e0e0e0; }
                QPushButton { border-radius: 6px; padding: 4px 8px; }
            """
            )
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
                QTabWidget::pane { border: none; background: transparent; }
                QTabBar::tab { background: #eeeeee; color: #888; padding: 6px 16px; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }
                QTabBar::tab:selected { background: #ffffff; color: #1a1a1a; border-bottom: 2px solid #1a7fe8; }
                QTabBar::tab:hover { background: #ddd; color: #1a1a1a; }
                QPushButton { border-radius: 6px; padding: 4px 8px; }
            """
            )
            self.theme_btn.setStyleSheet(
                "background: #1a1a1a; color: #ffffff; border: 1px solid #ddd; border-radius: 6px;"
            )

        self.add_frame.apply_theme(self.is_dark)
        self.search_frame.apply_theme(self.is_dark, self.scroll_locked)
