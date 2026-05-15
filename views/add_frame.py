from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class AddFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        add_label = QLabel("방송 추가")
        add_label.setFont(QFont("Arial", 15))

        input_row = QHBoxLayout()
        self.streamer_input = QLineEdit()
        self.streamer_input.setPlaceholderText("스트리머 ID 또는 URL 입력")
        self.streamer_input.setFixedHeight(36)
        self.add_btn = QPushButton("추가")
        self.add_btn.setFixedSize(60, 36)
        self.remove_btn = QPushButton("제거")
        self.remove_btn.setFixedSize(60, 36)
        self.fav_btn = QPushButton("★")
        self.fav_btn.setFixedSize(36, 36)

        input_row.addWidget(self.streamer_input)
        input_row.addWidget(self.add_btn)
        input_row.addWidget(self.remove_btn)
        input_row.addWidget(self.fav_btn)

        layout.addWidget(add_label)
        layout.addLayout(input_row)

    def apply_theme(self, is_dark: bool):
        if is_dark:
            self.add_btn.setStyleSheet("background: #4a9eff; color: white;")
            self.remove_btn.setStyleSheet("background: #ff4a4a; color: white;")
            self.fav_btn.setStyleSheet("background: #f0a500; color: white;")
        else:
            self.add_btn.setStyleSheet("background: #1a7fe8; color: white;")
            self.remove_btn.setStyleSheet("background: #ff4a4a; color: white;")
            self.fav_btn.setStyleSheet("background: #e09400; color: white;")
