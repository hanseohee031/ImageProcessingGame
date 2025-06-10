# games/get_games.py
import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QLabel, QFrame
from PyQt5.QtCore import Qt

class GetGamesWidget(QWidget):
    def __init__(self, music_dir, on_game_selected=None):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 28, 40, 28)

        card = QFrame()
        card.setObjectName("trackcard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 24, 20, 24)
        card_layout.setSpacing(12)

        label = QLabel("게임 목록")
        label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 18px;")
        card_layout.addWidget(label)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("tracklist")
        self.list_widget.setStyleSheet("""
            QListWidget { background: transparent; border: none; font-size: 17px; }
            QListWidget::item:selected { background: #e6f0ff; color: #2563eb; }
            QListWidget::item { padding: 10px; margin: 3px; border-radius: 12px; }
        """)
        self.load_music_titles(music_dir)
        card_layout.addWidget(self.list_widget)

        layout.addWidget(card, 1)
        self.on_game_selected = on_game_selected
        self.list_widget.itemDoubleClicked.connect(self._handle_double_click)

    def load_music_titles(self, music_dir):
        if not os.path.exists(music_dir):
            return
        for filename in sorted(os.listdir(music_dir)):
            if filename.endswith('.wav'):
                title = os.path.splitext(filename)[0]
                self.list_widget.addItem(title)

    def _handle_double_click(self, item):
        if self.on_game_selected:
            self.on_game_selected(item.text())
