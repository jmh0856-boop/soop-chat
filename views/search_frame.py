from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class SearchFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)

        self.tab_widget = QTabWidget()
        self.tab_widget.setMaximumHeight(36)
        self.tab_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        search_row = QHBoxLayout()
        self.nick_input = QLineEdit()
        self.nick_input.setPlaceholderText("닉네임 검색")
        self.nick_input.setFixedHeight(36)
        self.search_btn = QPushButton("검색")
        self.search_btn.setFixedSize(60, 36)
        self.scroll_lock_btn = QPushButton("🔒")
        self.scroll_lock_btn.setFixedSize(36, 36)
        self.scroll_lock_btn.setCheckable(True)
        self.scroll_lock_btn.setChecked(True)

        search_row.addWidget(self.nick_input)
        search_row.addWidget(self.search_btn)
        search_row.addWidget(self.scroll_lock_btn)

        self.chat_list = QListWidget()
        self.chat_list.setFont(QFont("Arial", 10))

        layout.addWidget(self.tab_widget)
        layout.addLayout(search_row)
        layout.addWidget(self.chat_list)

    def apply_theme(self, is_dark: bool, scroll_locked: bool):
        if is_dark:
            self.search_btn.setStyleSheet("background: #4aff88; color: #0e0e0e;")
            self.scroll_lock_btn.setStyleSheet(
                "background: #4a9eff; color: white;"
                if scroll_locked
                else "background: #444; color: white;"
            )
        else:
            self.search_btn.setStyleSheet("background: #2ecc71; color: white;")
            self.scroll_lock_btn.setStyleSheet(
                "background: #1a7fe8; color: white;"
                if scroll_locked
                else "background: #ccc; color: #1a1a1a;"
            )
