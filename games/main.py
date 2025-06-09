# games/main.py

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QDialog
)
from PyQt5.QtGui import QFont
from games.auth_dialog import AuthDialog

class MainWindow(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.setWindowTitle("🎵 Music Quest")
        self.resize(1000, 700)

        # ── 상단 헤더 ──
        header = QWidget()
        hdr_lay = QHBoxLayout(header)
        hdr_lay.setContentsMargins(0, 10, 0, 10)
        hdr_lay.addStretch()

        # 사용자명 레이블 (이후 재로그인 시 업데이트)
        self.name_label = QLabel(f"Hello, {username}")
        name_font = QFont()
        name_font.setPointSize(18)
        self.name_label.setFont(name_font)
        hdr_lay.addWidget(self.name_label, alignment=Qt.AlignCenter)

        # 로그아웃 버튼
        logout_btn = QPushButton("Logout")
        logout_font = QFont()
        logout_font.setPointSize(14)
        logout_btn.setFont(logout_font)
        logout_btn.clicked.connect(self._on_logout)
        hdr_lay.addWidget(logout_btn, alignment=Qt.AlignCenter)

        hdr_lay.addStretch()

        # ── 사이드 메뉴 ──
        menu = QWidget()
        menu_lay = QVBoxLayout(menu)
        menu_lay.setContentsMargins(50, 20, 0, 0)
        menu_lay.setSpacing(20)

        btn_my  = QPushButton("My Music")
        btn_get = QPushButton("Get Music")
        for btn in (btn_my, btn_get):
            btn_font = QFont()
            btn_font.setPointSize(16)
            btn.setFont(btn_font)
            btn.setFixedSize(200, 50)
        menu_lay.addWidget(btn_my)
        menu_lay.addWidget(btn_get)
        menu_lay.addStretch()

        # ── 메인 레이아웃 ──
        central = QWidget()
        main_lay = QVBoxLayout(central)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.addWidget(header)
        main_lay.addWidget(menu, alignment=Qt.AlignLeft)
        self.setCentralWidget(central)

    def _on_logout(self):
        """로그아웃 시, 창을 숨기고 다시 로그인 → 성공하면 사용자명 업데이트 후 재표시"""
        # 1) 창 숨기기
        self.hide()

        # 2) 로그인 대화상자 재실행
        auth = AuthDialog()
        if auth.exec_() == QDialog.Accepted:
            # 3) 로그인 성공: 사용자명 갱신하고 창 다시 보이기
            new_user = auth.login_user.text().strip()
            self.name_label.setText(f"Hello, {new_user}")
            self.show()
        else:
            # 4) 로그인 취소: 애플리케이션 종료
            QApplication.quit()


def main():
    app = QApplication(sys.argv)

    # 전역 기본 폰트 크기 설정
    base_font = app.font()
    base_font.setPointSize(14)
    app.setFont(base_font)

    # 인증 대화상자
    auth = AuthDialog()
    if auth.exec_() == QDialog.Accepted:
        # 로그인 성공 시 메인 윈도우 띄우기
        username = auth.login_user.text().strip()
        window = MainWindow(username)
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit()


if __name__ == "__main__":
    main()
