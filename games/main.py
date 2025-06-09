# games/main.py

import sys
import os
import random
from PyQt5.QtCore import Qt, QSize, QUrl
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QFrame,
    QStackedWidget, QListWidget, QListWidgetItem,
    QTextBrowser, QSlider, QDialog
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from games.auth_dialog import AuthDialog

def ms_to_mmss(ms: int) -> str:
    s = ms // 1000
    return f"{s//60:02d}:{s%60:02d}"

class MainWindow(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.setWindowTitle("🎵 Music Quest")
        self.resize(1000, 700)

        # 플레이리스트 상태
        self.playlist = []
        self.current_index = -1
        self.shuffle = False
        self.repeat_mode = 0  # 0=off,1=all,2=one

        # ── HEADER ──
        header = QFrame(objectName="header")
        hdr_l = QHBoxLayout(header)
        hdr_l.setContentsMargins(20, 10, 20, 10)
        hdr_l.addStretch()
        self.name_label = QLabel(f"Hello, {username}", objectName="username")
        header_font = QFont("", 20)
        self.name_label.setFont(header_font)
        hdr_l.addWidget(self.name_label)
        logout_btn = QPushButton("Logout", objectName="logout")
        logout_btn.setFont(QFont("", 16))
        logout_btn.clicked.connect(self._on_logout)
        hdr_l.addWidget(logout_btn)
        hdr_l.addStretch()

        # ── SIDEBAR ──
        sidebar = QFrame(objectName="sidebar")
        sb_l = QVBoxLayout(sidebar)
        sb_l.setContentsMargins(0, 20, 0, 20)
        sb_l.setSpacing(15)
        self.btn_my  = QPushButton("My Music", objectName="menu")
        self.btn_get = QPushButton("Get Music", objectName="menu")
        for btn in (self.btn_my, self.btn_get):
            btn.setFont(QFont("", 18))
            btn.setFixedSize(200, 60)
            sb_l.addWidget(btn)
        sb_l.addStretch()

        # ── CONTENT STACK ──
        self.stack = QStackedWidget()

        # ▶ Page 0: My Music
        page_music = QWidget()
        mus_lay = QHBoxLayout(page_music)
        mus_lay.setContentsMargins(20, 20, 20, 20)
        mus_lay.setSpacing(30)

        # Track list
        self.list_widget = QListWidget()
        self.list_widget.setFont(QFont("", 16))
        self._load_playlist()
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        mus_lay.addWidget(self.list_widget, 1)

        # Lyrics + controls
        right = QVBoxLayout()
        self.lyrics = QTextBrowser()
        self.lyrics.setFont(QFont("Monospace", 14))
        right.addWidget(self.lyrics, 5)

        # Controls row 1
        ctrl_top = QHBoxLayout()
        btns = {}
        for name, txt in [
            ('shuffle', '🔀'),
            ('prev',    '⏮️'),
            ('play',    '▶️'),
            ('pause',   '⏸️'),
            ('next',    '⏭️'),
            ('repeat',  '🔁'),
        ]:
            btn = QPushButton(txt)
            btn.setFixedSize(50, 50)
            btn.setFont(QFont("", 18))
            btns[name] = btn
            ctrl_top.addWidget(btn)
        self.btn_shuffle, self.btn_prev, self.btn_play, \
        self.btn_pause, self.btn_next, self.btn_repeat = (
            btns['shuffle'], btns['prev'], btns['play'],
            btns['pause'],   btns['next'], btns['repeat']
        )
        self.btn_play.clicked.connect(self.player_play)
        self.btn_pause.clicked.connect(self.player_pause)
        self.btn_next.clicked.connect(self.next_track)
        self.btn_prev.clicked.connect(self.prev_track)
        self.btn_shuffle.clicked.connect(self.toggle_shuffle)
        self.btn_repeat.clicked.connect(self.toggle_repeat)

        # Controls row 2: slider + time
        ctrl_bot = QHBoxLayout()
        self.slider   = QSlider(Qt.Horizontal)
        self.slider.setStyleSheet("QSlider::groove:horizontal{height:8px;} QSlider::handle:horizontal{width:16px;}")
        self.time_lbl = QLabel("00:00 / 00:00")
        self.time_lbl.setFont(QFont("", 16))
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(lambda p: self.player.setPosition(p))
        ctrl_bot.addWidget(self.slider, 1)
        ctrl_bot.addWidget(self.time_lbl)
        right.addLayout(ctrl_top, 1)
        right.addLayout(ctrl_bot, 1)

        mus_lay.addLayout(right, 3)
        self.stack.addWidget(page_music)

        # ▶ Page 1: Get Music
        page_game = QWidget()
        gl = QVBoxLayout(page_game)
        gl.setAlignment(Qt.AlignCenter)
        lbl = QLabel("🎮 Game Starting...")
        lbl.setFont(QFont("", 24))
        gl.addWidget(lbl)
        self.stack.addWidget(page_game)

        # Sidebar buttons
        self.btn_my.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_get.clicked.connect(self._on_get_music)

        # ── ROOT LAYOUT ──
        central = QWidget()
        root_l = QHBoxLayout(central)
        root_l.setContentsMargins(0, 0, 0, 0)
        root_l.addWidget(sidebar)
        root_l.addWidget(self.stack, 1)

        outer = QWidget()
        outer_l = QVBoxLayout(outer)
        outer_l.setContentsMargins(0, 0, 0, 0)
        outer_l.addWidget(header)
        outer_l.addWidget(central)
        self.setCentralWidget(outer)

        # ── PLAYER SETUP ──
        self.player = QMediaPlayer()
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status)

    def _load_playlist(self):
        music_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'music')
        for fn in sorted(os.listdir(music_dir)):
            if fn.lower().endswith(('.mp3', '.wav')):
                title = os.path.splitext(fn)[0]
                self.playlist.append(fn)
                item = QListWidgetItem(title)
                self.list_widget.addItem(item)

    def on_item_clicked(self, item):
        idx = self.list_widget.row(item)
        self.play_track(idx)

    def play_track(self, idx):
        if idx < 0 or idx >= len(self.playlist):
            return
        self.current_index = idx
        fn = self.playlist[idx]
        path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'music', fn)
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
        self.player.play()
        # load lyrics
        title = os.path.splitext(fn)[0]
        lyr = os.path.join(os.path.dirname(__file__), '..', 'assets', 'lyrics', f"{title}.txt")
        self.lyrics.setText(open(lyr, encoding='utf-8').read() if os.path.exists(lyr) else "(No lyrics)")

    def player_play(self):  self.player.play()
    def player_pause(self): self.player.pause()

    def next_track(self):
        if self.shuffle:
            nxt = random.randrange(len(self.playlist))
        else:
            nxt = (self.current_index + 1) % len(self.playlist)
        self.list_widget.setCurrentRow(nxt)
        self.play_track(nxt)

    def prev_track(self):
        if self.shuffle:
            prv = random.randrange(len(self.playlist))
        else:
            prv = (self.current_index - 1) % len(self.playlist)
        self.list_widget.setCurrentRow(prv)
        self.play_track(prv)

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        self.btn_shuffle.setStyleSheet("background:#edde73;" if self.shuffle else "")

    def toggle_repeat(self):
        self.repeat_mode = (self.repeat_mode + 1) % 3
        icons = {0: "🔁", 1: "🔁", 2: "🔂"}
        self.btn_repeat.setText(icons[self.repeat_mode])

    def _on_position_changed(self, pos):
        self.slider.setValue(pos)
        self._update_time_label()

    def _on_duration_changed(self, dur):
        self.slider.setRange(0, dur)
        self._update_time_label()

    def _on_media_status(self, status):
        from PyQt5.QtMultimedia import QMediaPlayer
        if status == QMediaPlayer.EndOfMedia:
            if self.repeat_mode == 2:
                self.play_track(self.current_index)
            elif self.repeat_mode == 1:
                self.next_track()
            else:
                if self.current_index < len(self.playlist) - 1:
                    self.next_track()

    def _update_time_label(self):
        p = self.player.position()
        d = self.player.duration()
        self.time_lbl.setText(f"{ms_to_mmss(p)} / {ms_to_mmss(d)}")

    def _on_get_music(self):
        # stop any playing music
        self.player.stop()
        # switch to get-music page
        self.stack.setCurrentIndex(1)

    def _on_logout(self):
        self.player.stop()
        self.hide()
        auth = AuthDialog()
        if auth.exec_() == QDialog.Accepted:
            new_user = auth.login_user.text().strip()
            self.name_label.setText(f"Hello, {new_user}")
            self.stack.setCurrentIndex(0)
            self.show()
        else:
            QApplication.quit()

def main():
    app = QApplication(sys.argv)
    font = app.font(); font.setPointSize(14); app.setFont(font)

    auth = AuthDialog()
    if auth.exec_() == QDialog.Accepted:
        w = MainWindow(auth.login_user.text().strip())
        w.show()
        sys.exit(app.exec_())
    else:
        sys.exit()

if __name__ == "__main__":
    main()
