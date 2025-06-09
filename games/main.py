# games/main.py

import sys
import os
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFrame,
    QDialog          # ← 여기에 QDialog 추가
)
from games.auth_dialog import AuthDialog

class MainWindow(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.setWindowTitle("🎵 Music Quest")
        self.resize(1000, 700)

        # ── 전체 스타일시트 ──
        self.setStyleSheet("""
        QMainWindow {
            background-color: #f5f7fa;
        }
        QFrame#header {
            background-color: white;
            border-bottom: 1px solid #e0e0e0;
        }
        QLabel#username {
            font-size: 18px;
            color: #2f3e46;
        }
        QPushButton#logout {
            background-color: transparent;
            color: #e63946;
            border: 1px solid #e63946;
            border-radius: 4px;
            padding: 6px 12px;
            font-size: 14px;
        }
        QPushButton#logout:hover {
            background-color: #e63946;
            color: white;
        }
        QFrame#sidebar {
            background-color: #2a9d8f;
        }
        QPushButton#menu {
            background-color: transparent;
            color: #edf6f9;
            border: none;
            text-align: left;
            padding: 10px 20px;
            font-size: 16px;
        }
        QPushButton#menu:hover {
            background-color: #21867a;
        }
        QPushButton#menu:pressed {
            background-color: #1b665c;
        }
        """)

        # ── HEADER ──
        header = QFrame()
        header.setObjectName("header")
        hdr_lay = QHBoxLayout(header)
        hdr_lay.setContentsMargins(20, 10, 20, 10)
        hdr_lay.addStretch()

        self.name_label = QLabel(f"Hello, {username}")
        self.name_label.setObjectName("username")
        name_font = QFont()
        name_font.setPointSize(18)
        self.name_label.setFont(name_font)
        hdr_lay.addWidget(self.name_label)

        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("logout")
        logout_font = QFont()
        logout_font.setPointSize(14)
        logout_btn.setFont(logout_font)
        logout_btn.clicked.connect(self._on_logout)
        hdr_lay.addWidget(logout_btn)
        hdr_lay.addStretch()

        # ── SIDEBAR ──
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sb_lay = QVBoxLayout(sidebar)
        sb_lay.setContentsMargins(0, 20, 0, 20)
        sb_lay.setSpacing(15)

        for text in ("My Music", "Get Music"):
            btn = QPushButton(text)
            btn.setObjectName("menu")
            icon_path = os.path.join(
                os.path.dirname(__file__),
                "..", "assets", "icons",
                f"{text.lower().replace(' ', '_')}.png"
            )
            if os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(24, 24))
            sb_lay.addWidget(btn)

        sb_lay.addStretch()

        # ── CENTRAL LAYOUT ──
        central = QWidget()
        main_lay = QHBoxLayout(central)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.addWidget(sidebar, 1)

        content = QWidget()
        main_lay.addWidget(content, 4)

        # ── ROOT LAYOUT ──
        root = QWidget()
        root_lay = QVBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.addWidget(header)
        root_lay.addWidget(central)
        self.setCentralWidget(root)

    def _on_logout(self):
        # 1) 창 숨기기
        self.hide()
        # 2) 인증 다이얼로그 재실행
        auth = AuthDialog()
        if auth.exec_() == QDialog.Accepted:
            new_user = auth.login_user.text().strip()
            self.name_label.setText(f"Hello, {new_user}")
            self.show()
        else:
            QApplication.quit()

def main():
    app = QApplication(sys.argv)
    # 전역 기본 폰트 크기
    base_font = app.font()
    base_font.setPointSize(14)
    app.setFont(base_font)

    auth = AuthDialog()
    if auth.exec_() == QDialog.Accepted:
        user = auth.login_user.text().strip()
        win = MainWindow(user)
        win.show()
        sys.exit(app.exec_())
    else:
        sys.exit()

if __name__ == "__main__":
    main()
