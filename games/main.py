# games/main.py

import sys
from PyQt5.QtCore import Qt                # 추가
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QVBoxLayout,
    QWidget,
    QDialog
)
from games.auth_dialog import AuthDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎵 Music Quest")
        self.resize(1000, 700)

        central = QWidget()
        layout = QVBoxLayout()
        layout.addStretch()

        welcome = QLabel("🎵 Welcome to Music Quest! 🎵")
        # 정수 대신 Qt.AlignCenter 사용
        welcome.setAlignment(Qt.AlignCenter)

        # 폰트 크게
        font = welcome.font()
        font.setPointSize(26)
        font.setBold(True)
        welcome.setFont(font)

        layout.addWidget(welcome)
        layout.addStretch()
        central.setLayout(layout)
        self.setCentralWidget(central)

def main():
    app = QApplication(sys.argv)

    # 앱 기본 폰트 키우기
    base_font = app.font()
    base_font.setPointSize(14)
    app.setFont(base_font)

    auth = AuthDialog()
    if auth.exec_() == QDialog.Accepted:
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit()

if __name__ == "__main__":
    main()
