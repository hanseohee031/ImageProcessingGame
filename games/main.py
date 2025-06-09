import sys
import os
import random
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QFrame,
    QStackedWidget, QListWidget, QListWidgetItem,
    QTextBrowser, QSlider, QSplitter, QDialog
)
from qt_material import apply_stylesheet
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
        self.title_to_fn = {}
        self.current_index = -1
        self.shuffle = False
        self.repeat_mode = 0  # 0=off,1=all,2=one

        # HEADER
        header = QFrame(objectName="header")
        hdr_l = QHBoxLayout(header)
        hdr_l.setContentsMargins(20, 10, 20, 10)
        hdr_l.addStretch()
        self.name_label = QLabel(f"Hello, {username}", objectName="username")
        self.name_label.setFont(QFont("Arial", 24, QFont.Bold))
        hdr_l.addWidget(self.name_label)
        logout_btn = QPushButton("Logout", objectName="logout")
        logout_btn.setFont(QFont("Arial", 18))
        logout_btn.clicked.connect(self._on_logout)
        hdr_l.addWidget(logout_btn)
        hdr_l.addStretch()

        # SIDEBAR
        sidebar = QFrame(objectName="sidebar")
        sb_l = QVBoxLayout(sidebar)
        sb_l.setContentsMargins(0, 20, 0, 20)
        sb_l.setSpacing(20)
        self.btn_my = QPushButton("My Music", objectName="menu")
        self.btn_get = QPushButton("Get Music", objectName="menu")
        for btn in (self.btn_my, self.btn_get):
            btn.setFont(QFont("Arial", 20))
            btn.setFixedSize(200, 60)
            sb_l.addWidget(btn)
        sb_l.addStretch()

        # CONTENT STACK
        self.stack = QStackedWidget()

        # Page 0: My Music
        page_music = QWidget()
        splitter = QSplitter(Qt.Horizontal, page_music)

        # 좌측: 트랙 리스트 (드래그 & 드롭)
        self.list_widget = QListWidget()
        self.list_widget.setFont(QFont("Arial", 24))
        self.list_widget.setDragDropMode(QListWidget.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.MoveAction)
        self.list_widget.setAcceptDrops(True)
        self.list_widget.setDropIndicatorShown(True)
        self.list_widget.model().rowsMoved.connect(self._on_rows_moved)
        self._load_playlist()
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        splitter.addWidget(self.list_widget)

        # 우측: 가사 + 컨트롤
        content = QWidget()
        right = QVBoxLayout(content)
        self.lyrics = QTextBrowser()
        self.lyrics.setFont(QFont("Arial", 18))
        right.addWidget(self.lyrics, 5)

        # Controls row 1
        ctrl_top = QHBoxLayout()
        btns = {}
        for name, ico in [
            ('shuffle', '🔀'), ('prev', '⏮️'), ('play', '▶️'),
            ('pause', '⏸️'), ('next', '⏭️'), ('repeat', '🔁')
        ]:
            btn = QPushButton(ico)
            btn.setFixedSize(80, 80)
            btn.setFont(QFont("Arial", 28, QFont.Bold))
            btns[name] = btn
            ctrl_top.addWidget(btn)
        (self.btn_shuffle, self.btn_prev, self.btn_play,
         self.btn_pause, self.btn_next, self.btn_repeat) = (
            btns['shuffle'], btns['prev'], btns['play'],
            btns['pause'], btns['next'], btns['repeat']
        )
        self.btn_play.clicked.connect(self.player_play)
        self.btn_pause.clicked.connect(self.player_pause)
        self.btn_next.clicked.connect(self.next_track)
        self.btn_prev.clicked.connect(self.prev_track)
        self.btn_shuffle.clicked.connect(self.toggle_shuffle)
        self.btn_repeat.clicked.connect(self.toggle_repeat)

        # Controls row 2: slider + time
        ctrl_bot = QHBoxLayout()
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setStyleSheet(
            "QSlider::groove:horizontal{height:15px;} "
            "QSlider::handle:horizontal{width:25px;}"
        )
        self.time_lbl = QLabel("00:00 / 00:00")
        self.time_lbl.setFont(QFont("Arial", 18))
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(lambda p: self.player.setPosition(p))
        ctrl_bot.addWidget(self.slider, 1)
        ctrl_bot.addWidget(self.time_lbl)
        right.addLayout(ctrl_top, 1)
        right.addLayout(ctrl_bot, 1)

        splitter.addWidget(content)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        mus_lay = QHBoxLayout(page_music)
        mus_lay.setContentsMargins(20, 20, 20, 20)
        mus_lay.setSpacing(30)
        mus_lay.addWidget(splitter)
        self.stack.addWidget(page_music)

        # Page 1: Get Music
        page_game = QWidget()
        gl = QVBoxLayout(page_game)
        gl.setAlignment(Qt.AlignCenter)
        lbl = QLabel("🎮 Game Starting...")
        lbl.setFont(QFont("Arial", 26))
        gl.addWidget(lbl)
        self.stack.addWidget(page_game)

        # Sidebar 버튼 연결
        self.btn_my.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_get.clicked.connect(self._on_get_music)

        # ROOT LAYOUT
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

        # PLAYER SETUP
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

    def player_play(self):
        self.player.play()

    def player_pause(self):
        self.player.pause()

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
        # 반복 모드: off->all->one
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

    def _on_get_music(self):
        self.player.stop()
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
    # 고DPI 스케일링 활성화
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)

    # Light material theme
    apply_stylesheet(app, theme='light_blue.xml')

    # 전역 폰트: Arial
    base_font = QFont("Arial", 20)
    app.setFont(base_font)

    auth = AuthDialog()
    if auth.exec_() == QDialog.Accepted:
        w = MainWindow(auth.login_user.text().strip())
        w.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()
