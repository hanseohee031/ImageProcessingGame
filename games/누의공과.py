import os
import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QSlider, QFrame, QListWidget, QListWidgetItem, QMessageBox
)
from PyQt5.QtGui import QPixmap, QImage, QFont
from PyQt5.QtCore import Qt, QUrl, QTime
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

class 누의공과(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("누의공과 - 틀린그림찾기")
        self.resize(1100, 680)
        self.setStyleSheet("""
            QWidget { background: #f7f9fa; font-family: 'Arial', 'Malgun Gothic', '맑은 고딕', sans-serif; font-size: 17px; color: #23272f; }
            QFrame#gamecard { background: #fff; border-radius: 32px; box-shadow: 0 8px 24px #eee; }
            QListWidget#musiclist { border: none; background: transparent; }
            QListWidget#musiclist::item:selected { background: #e6f0ff; color: #2563eb; border-radius: 12px; }
            QLabel#title { font-size: 22px; font-weight: bold; }
        """)

        # 이미지 스테이지 준비
        self.stage_index = 0
        self.image_pairs = self._load_image_pairs()
        self.game_started = False

        # 가사 로드
        self.lyrics_lines = self._load_lyrics()
        self.revealed_lyrics = []
        self.lyric_index = 0

        # 플레이어
        self.player = QMediaPlayer()
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)

        # 음악파일
        self.music_file = self._get_music_file()

        # 카드 프레임
        main_card = QFrame(objectName="gamecard")
        main_layout = QHBoxLayout(main_card)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(36)

        # --- 왼쪽: 이미지/게임영역 ---
        img_layout = QVBoxLayout()
        img_layout.setSpacing(10)
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignCenter)
        img_layout.addWidget(self.img_label, 9)

        self.score_label = QLabel("획득 점수: 0 / " + str(max(1, len(self.lyrics_lines)//2)))
        self.score_label.setStyleSheet("font-size: 17px; color: #31658c; margin: 0 0 14px 0;")
        img_layout.addWidget(self.score_label, 1)

        # --- 오른쪽: 음악/가사/조작 영역 ---
        right_layout = QVBoxLayout()
        right_layout.setSpacing(18)

        self.title_label = QLabel("누의공과 - 틀린그림찾기", objectName="title")
        self.title_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.title_label)

        # 음악 리스트 (누의공과만)
        self.music_list = QListWidget(objectName="musiclist")
        item = QListWidgetItem("누의공과", self.music_list)
        self.music_list.setFixedHeight(40)
        right_layout.addWidget(self.music_list)
        self.music_list.itemDoubleClicked.connect(self._on_music_selected)

        # 플레이어 슬라이더
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self._set_position)
        right_layout.addWidget(self.slider)

        # 시간표시
        self.time_label = QLabel("00:00 / 00:00")
        right_layout.addWidget(self.time_label)

        # 가사 표시
        self.lyrics_box = QTextEdit()
        self.lyrics_box.setReadOnly(True)
        self.lyrics_box.setStyleSheet("background: #f7f9fa; font-size: 17px; border: none; margin-top:10px;")
        right_layout.addWidget(QLabel("해금된 가사:", self))
        right_layout.addWidget(self.lyrics_box, 5)

        # 안내/상태 레이블
        self.status_label = QLabel("음악을 더블클릭해 시작하세요.")
        self.status_label.setStyleSheet("color: #2563eb; font-size: 16px;")
        right_layout.addWidget(self.status_label)

        # 잠금해제 버튼 (테스트용/전체해금)
        unlock_btn = QPushButton("전체 해금 (테스트)")
        unlock_btn.setStyleSheet("background: #31658c; color: #fff; border-radius: 14px; padding: 8px 20px; font-weight: bold;")
        unlock_btn.clicked.connect(self._unlock_all)
        right_layout.addWidget(unlock_btn)

        # 레이아웃 배치
        main_layout.addLayout(img_layout, 3)
        main_layout.addLayout(right_layout, 4)
        container = QVBoxLayout(self)
        container.addStretch()
        container.addWidget(main_card, 1)
        container.addStretch()

        # 초기 스테이지 로드
        self._load_stage(0)
        self.setFocusPolicy(Qt.StrongFocus)

    # --- 이미지 쌍 자동 로드 ---
    def _load_image_pairs(self):
        org_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'images', 'original')
        mod_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'images', 'modified')
        # 파일명 앞 번호만 추출
        orgs = sorted([f for f in os.listdir(org_dir) if f.endswith(('.jpg', '.png'))])
        pairs = []
        for org_name in orgs:
            num = org_name.split('.')[0]
            mod_name = f"{num}-Photoroom.png"
            mod_path = os.path.join(mod_dir, mod_name)
            org_path = os.path.join(org_dir, org_name)
            if os.path.exists(mod_path):
                pairs.append((org_path, mod_path))
        if not pairs:
            QMessageBox.warning(self, "이미지 없음", "원본/수정 이미지 쌍이 없습니다.")
        return pairs

    # --- 가사 로드 ---
    def _load_lyrics(self):
        lpath = os.path.join(os.path.dirname(__file__), '..', 'assets', 'lyrics', '누의공과_game.txt')
        if not os.path.exists(lpath):
            return []
        with open(lpath, encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    def _get_music_file(self):
        mp = os.path.join(os.path.dirname(__file__), '..', 'assets', 'music', '누의공과.wav')
        return mp if os.path.exists(mp) else None

    # --- 스테이지 및 게임 로직 ---
    def _load_stage(self, index):
        if not self.image_pairs:
            self.img_label.setText("이미지 쌍이 없습니다.")
            return
        org_path, mod_path = self.image_pairs[index]
        self.original_img = cv2.imread(org_path)
        self.modified_img = cv2.imread(mod_path)
        if self.original_img is None or self.modified_img is None:
            self.img_label.setText("이미지 로딩 오류")
            return
        # 크기 맞추기
        self.original_img = cv2.resize(self.original_img, (440, 350))
        self.modified_img = cv2.resize(self.modified_img, (440, 350))
        self.display_img = np.hstack([self.original_img, self.modified_img])
        # 정답박스 자동 감지
        self.answer_boxes = [self._detect_difference(self.original_img, self.modified_img)]
        self.found_boxes = []
        self.cursor_box = [0, 0, 50, 50]
        self.step = 10
        self.update_display()

    def _detect_difference(self, img1, img2):
        diff = cv2.absdiff(img1, img2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return (0, 0, 0, 0)
        x_min, y_min, x_max, y_max = 500, 400, 0, 0
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w * h > 100:
                x_min = min(x_min, x)
                y_min = min(y_min, y)
                x_max = max(x_max, x + w)
                y_max = max(y_max, y + h)
        return (x_min, y_min, x_max, y_max)

    def keyPressEvent(self, event):
        if not self.game_started:
            return
        key = event.key()
        if key == Qt.Key_Up:
            self._move_cursor(0, -self.step)
        elif key == Qt.Key_Down:
            self._move_cursor(0, self.step)
        elif key == Qt.Key_Left:
            self._move_cursor(-self.step, 0)
        elif key == Qt.Key_Right:
            self._move_cursor(self.step, 0)
        elif key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self._check_selection()

    def _move_cursor(self, dx, dy):
        x1, y1, x2, y2 = self.cursor_box
        x1 = max(0, min(self.display_img.shape[1] - 51, x1 + dx))
        y1 = max(0, min(self.display_img.shape[0] - 51, y1 + dy))
        self.cursor_box = [x1, y1, x1 + 50, y1 + 50]
        self.update_display()

    def _check_selection(self):
        x1, y1, x2, y2 = self.cursor_box
        for box in self.answer_boxes:
            bx1, by1, bx2, by2 = box
            if not (x2 < bx1 or x1 > bx2 or y2 < by1 or y1 > by2):
                if box not in self.found_boxes:
                    self.found_boxes.append(box)
                    self.status_label.setText("정답!")
                    self._reveal_lyrics()
                    self._update_score()
                    if self.lyric_index >= len(self.lyrics_lines):
                        self.status_label.setText("모든 가사를 획득했습니다!")
                        self._unlock_all()
                    else:
                        self.stage_index = (self.stage_index + 1) % len(self.image_pairs)
                        self._load_stage(self.stage_index)
                    return
        self.status_label.setText("오답!")

    def _reveal_lyrics(self):
        start = self.lyric_index
        end = min(start + 2, len(self.lyrics_lines))
        new_lyrics = self.lyrics_lines[start:end]
        self.revealed_lyrics.extend(new_lyrics)
        self.lyric_index = end
        # 색상 표시
        normal = "<br>".join(self.revealed_lyrics[:-2])
        highlight = "<br>".join(self.revealed_lyrics[-2:])
        formatted = f"<span style='color:#23272f'>{normal}</span><br><span style='color:#3ab54a'>{highlight}</span>"
        self.lyrics_box.setHtml(formatted)
        self.lyrics_box.verticalScrollBar().setValue(self.lyrics_box.verticalScrollBar().maximum())

    def _update_score(self):
        score = self.lyric_index // 2
        total = max(1, len(self.lyrics_lines) // 2)
        self.score_label.setText(f"획득 점수: {score} / {total}")

    def update_display(self):
        img = self.display_img.copy()
        for (x1, y1, x2, y2) in self.found_boxes:
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cx1, cy1, cx2, cy2 = self.cursor_box
        cv2.rectangle(img, (cx1, cy1), (cx2, cy2), (255, 60, 60), 2)
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, c = rgb.shape
        qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888)
        self.img_label.setPixmap(QPixmap.fromImage(qimg))

    # --- 음악/플레이어 ---
    def _on_music_selected(self, item):
        if self.music_file:
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.music_file)))
            self.player.play()
            self.status_label.setText("방향키로 커서를 옮기고 [Enter] 또는 [Space]로 정답을 맞혀보세요!")
            self.game_started = True
            self.setFocus()
        else:
            QMessageBox.warning(self, "음악 없음", "음악 파일이 존재하지 않습니다.")

    def _set_position(self, pos):
        self.player.setPosition(pos)

    def _on_position_changed(self, pos):
        self.slider.setValue(pos)
        self._update_time_label(pos, self.player.duration())

    def _on_duration_changed(self, dur):
        self.slider.setRange(0, dur)
        self._update_time_label(self.player.position(), dur)

    def _update_time_label(self, current, total):
        def ms_to_time(ms):
            return QTime(0, 0).addMSecs(ms).toString("mm:ss")
        self.time_label.setText(f"{ms_to_time(current)} / {ms_to_time(total)}")

    def _unlock_all(self):
        self.lyric_index = len(self.lyrics_lines)
        self.revealed_lyrics = self.lyrics_lines.copy()
        self._reveal_lyrics()
        self._update_score()
        self.status_label.setText("전체 가사 해금 완료!")

    def closeEvent(self, event):
        self.player.stop()
        event.accept()

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = 누의공과()
    w.show()
    sys.exit(app.exec_())
