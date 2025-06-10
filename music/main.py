import sys
import os
import random
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QFrame,
    QStackedWidget, QListWidget, QListWidgetItem,
    QTextBrowser, QSlider, QSplitter, QDialog, QStyle, QMessageBox
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from music.auth_dialog import AuthDialog  # 경로에 따라 조정
# games.get_games, importlib 등 삭제

def ms_to_mmss(ms: int) -> str:
    s = ms // 1000
    return f"{s//60:02d}:{s%60:02d}"

def apply_qss(app, qss_path):
    with open(qss_path, "r") as f:
        style = f.read()
    app.setStyleSheet(style)

class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            val = QStyle.sliderValueFromPosition(
                self.minimum(), self.maximum(),
                event.x() if self.orientation() == Qt.Horizontal else event.y(),
                self.width() if self.orientation() == Qt.Horizontal else self.height()
            )
            self.setValue(val)
            self.sliderMoved.emit(val)
        super().mousePressEvent(event)

class MainWindow(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.setWindowTitle("🎵 Music Quest")
        self.resize(1120, 720)

        self.playlist = []
        self.title_to_fn = {}
        self.current_index = -1
        self.shuffle = False
        self.repeat_mode = 0  # 0=off,1=all,2=one

        # ── HEADER ──
        header = QFrame(objectName="header")
        hdr_l = QHBoxLayout(header)
        hdr_l.setContentsMargins(32, 18, 32, 18)
        self.name_label = QLabel(f"Hello, {username}", objectName="username")
        self.name_label.setFont(QFont("Arial", 20, QFont.Bold))
        hdr_l.addWidget(self.name_label)
        hdr_l.addStretch()
        logout_btn = QPushButton("⎋ LOGOUT", objectName="logout")
        logout_btn.setFont(QFont("Arial", 14, QFont.Bold))
        logout_btn.clicked.connect(self._on_logout)
        hdr_l.addWidget(logout_btn)
        exit_btn = QPushButton("EXIT")
        exit_btn.setObjectName("exit")
        exit_btn.setFont(QFont("Arial", 18, QFont.Bold))
        exit_btn.setStyleSheet("""
            QPushButton {
                  border:2px solid #e53e3e; border-radius:8px;
                  padding:6px 20px; background:white; color:#e53e3e;
            }
            QPushButton:hover { background:#fef2f2; }
             """)
        exit_btn.clicked.connect(QApplication.quit)
        hdr_l.addWidget(exit_btn)

        # ── SIDEBAR ──
        sidebar = QFrame(objectName="sidebar")
        sb_l = QVBoxLayout(sidebar)
        sb_l.setContentsMargins(0, 30, 0, 30)
        sb_l.setSpacing(24)
        self.btn_my = QPushButton("MY MUSIC", objectName="menu")
        sb_l.addWidget(self.btn_my)
        sb_l.addStretch()

        # ── CONTENT STACK ──
        self.stack = QStackedWidget()

        # ▶ Page 0: My Music
        page_music = QWidget()
        page_music.setObjectName("musicpage")
        splitter = QSplitter(Qt.Horizontal, page_music)
        splitter.setChildrenCollapsible(False)

        # 좌측: 트랙 리스트 (카드형)
        track_card = QFrame(objectName="trackcard")
        card_l = QVBoxLayout(track_card)
        card_l.setContentsMargins(20, 24, 20, 24)
        self.list_widget = QListWidget(objectName="tracklist")
        self.list_widget.setDragDropMode(QListWidget.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.MoveAction)
        self.list_widget.setAcceptDrops(True)
        self.list_widget.setDropIndicatorShown(True)
        self.list_widget.model().rowsMoved.connect(self._on_rows_moved)
        self._load_playlist()
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.setMinimumWidth(100)
        card_l.addWidget(self.list_widget)
        splitter.addWidget(track_card)

        # 우측: 가사 + 플레이어 (카드형)
        right_card = QFrame(objectName="rightcard")
        rcard_l = QVBoxLayout(right_card)
        rcard_l.setContentsMargins(28, 28, 28, 28)
        self.lyrics = QTextBrowser(objectName="lyrics")
        rcard_l.addWidget(self.lyrics, 5)

        # --- Controls: 한 줄 배치 ---
        ctrl_row = QHBoxLayout()
        btns = {}

        # 컨트롤 버튼 딕셔너리 생성
        for name, ico in [
            ('shuffle', '🔀'), ('prev', '⏮️'), ('next', '⏭️'), ('repeat', '🔁')
        ]:
            btn = QPushButton(ico)
            btn.setObjectName(name)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedSize(54, 54)
            btn.setFont(QFont("Arial", 26, QFont.Bold))
            btns[name] = btn

        # ▶️⏸️ 토글 버튼 생성
        self.btn_playpause = QPushButton("▶️")
        self.btn_playpause.setObjectName("playpause")
        self.btn_playpause.setCursor(Qt.PointingHandCursor)
        self.btn_playpause.setFixedSize(54, 54)
        self.btn_playpause.setFont(QFont("Arial", 26, QFont.Bold))
        self.btn_playpause.clicked.connect(self.toggle_play_pause)

        ctrl_row.addWidget(btns['shuffle'])
        ctrl_row.addWidget(btns['prev'])
        ctrl_row.addWidget(self.btn_playpause)
        ctrl_row.addWidget(btns['next'])
        ctrl_row.addWidget(btns['repeat'])

        self.btn_prev = btns['prev']
        self.btn_next = btns['next']
        self.btn_shuffle = btns['shuffle']
        self.btn_repeat = btns['repeat']
        self.btn_prev.clicked.connect(self.prev_track)
        self.btn_next.clicked.connect(self.next_track)
        self.btn_shuffle.clicked.connect(self.toggle_shuffle)
        self.btn_repeat.clicked.connect(self.toggle_repeat)

        ctrl_row.addSpacing(20)

        self.slider = ClickableSlider(Qt.Horizontal)
        self.slider.setObjectName("slider")
        self.slider.setMinimumWidth(180)
        self.time_lbl = QLabel("00:00 / 00:00", objectName="time")
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(lambda p: self.player.setPosition(p))
        ctrl_row.addWidget(self.slider, 1)
        ctrl_row.addWidget(self.time_lbl)
        rcard_l.addLayout(ctrl_row, 1)

        splitter.addWidget(right_card)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 3)

        mus_lay = QHBoxLayout(page_music)
        mus_lay.setContentsMargins(18, 18, 18, 18)
        mus_lay.setSpacing(24)
        mus_lay.addWidget(splitter)
        page_music.setLayout(mus_lay)
        self.stack.addWidget(page_music)

        # ── 버튼 연결 ──
        self.btn_my.clicked.connect(lambda: self.stack.setCurrentIndex(0))

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
        self.player.stateChanged.connect(self._on_player_state_changed)

    def _load_playlist(self):
        music_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'music')
        for fn in sorted(os.listdir(music_dir)):
            if fn.lower().endswith(('.mp3', '.wav')):
                title = os.path.splitext(fn)[0]
                self.playlist.append(fn)
                self.title_to_fn[title] = fn
                self.list_widget.addItem(QListWidgetItem(title))

    def _on_rows_moved(self, parent, start, end, dest, row):
        new_list = []
        for i in range(self.list_widget.count()):
            t = self.list_widget.item(i).text()
            new_list.append(self.title_to_fn[t])
        self.playlist = new_list

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
        title = os.path.splitext(fn)[0]
        lyr_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'lyrics', f"{title}.txt")
        self.lyrics.setText(
            open(lyr_path, encoding='utf-8').read() if os.path.exists(lyr_path) else "(No lyrics)"
        )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            pos = self.player.position() - 10000
            self.player.setPosition(max(pos, 0))
        elif event.key() == Qt.Key_Right:
            dur = self.player.duration()
            pos = self.player.position() + 10000
            self.player.setPosition(min(pos, dur))
        elif event.key() == Qt.Key_Space:
            self.toggle_play_pause()
        elif event.key() == Qt.Key_Escape:
            QApplication.quit()
        else:
            super().keyPressEvent(event)

    def toggle_play_pause(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _on_player_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.btn_playpause.setText("⏸️")
        else:
            self.btn_playpause.setText("▶️")

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
        if self.shuffle:
            self.btn_shuffle.setStyleSheet("background: #ddebf7;")
        else:
            self.btn_shuffle.setStyleSheet("")

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
            elif self.current_index < len(self.playlist) - 1:
                self.next_track()

    def _update_time_label(self):
        p = self.player.position()
        d = self.player.duration()
        self.time_lbl.setText(f"{ms_to_mmss(p)} / {ms_to_mmss(d)}")

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
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 17))
    apply_qss(app, os.path.join(os.path.dirname(__file__), '..', 'assets', 'style', 'modern.qss'))
    auth = AuthDialog()
    if auth.exec_() == QDialog.Accepted:
        w = MainWindow(auth.login_user.text().strip())
        w.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()
