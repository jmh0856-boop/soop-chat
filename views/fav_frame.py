from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QFrame, QLabel, QListWidget, QMenu, QVBoxLayout


class FavFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        fav_label = QLabel("즐겨 찾기")
        fav_label.setFont(QFont("Arial", 15))

        self.fav_list = QListWidget()
        self.fav_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        layout.addWidget(fav_label)
        layout.addWidget(self.fav_list)
