# games/login.py
import os, sqlite3, hashlib
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton,
    QFormLayout, QVBoxLayout, QDialogButtonBox, QMessageBox
)
from games.signup import SignUpDialog

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'users.db')

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT
        )
    """)
    return conn

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎵 Music Quest Login")
        self.resize(360, 220)

        # --- 헤더 ---
        header = QLabel("Welcome back!")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font: bold 18px; margin-bottom: 15px;")

        # --- 폼 레이아웃 (라벨 + 입력) ---
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("Enter your username")
        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.Password)
        self.pass_edit.setPlaceholderText("Enter your password")
        form.addRow("Username:", self.user_edit)
        form.addRow("Password:", self.pass_edit)

        # --- 버튼박스 ---
        buttons = QDialogButtonBox()
        self.btn_login  = QPushButton("Login")
        self.btn_signup = QPushButton("Sign Up")
        buttons.addButton(self.btn_login,  QDialogButtonBox.AcceptRole)
        buttons.addButton(self.btn_signup, QDialogButtonBox.ActionRole)
        buttons.setCenterButtons(True)
        self.btn_login.clicked.connect(self.attempt_login)
        self.btn_signup.clicked.connect(self.open_signup)

        # --- 메인 레이아웃 ---
        main_lay = QVBoxLayout(self)
        main_lay.addWidget(header)
        main_lay.addLayout(form)
        main_lay.addSpacing(10)
        main_lay.addWidget(buttons)

        # --- 스타일 ---
        self.setStyleSheet("""
        QDialog {
            background-color: #fafafa;
        }
        QLabel {
            color: #333;
        }
        QLineEdit {
            padding: 6px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 14px;
        }
        QPushButton {
            min-width: 80px;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 14px;
            background-color: #5cb85c;
            color: white;
        }
        QPushButton:hover {
            background-color: #4cae4c;
        }
        QPushButton#signup {
            background-color: #0275d8;
        }
        QPushButton#signup:hover {
            background-color: #025aa5;
        }
        """)
        self.btn_signup.setObjectName("signup")

    def open_signup(self):
        dlg = SignUpDialog()
        if dlg.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "회원가입이 완료되었습니다! 방금 만든 계정으로 로그인하세요.")

    def attempt_login(self):
        username = self.user_edit.text().strip()
        pwd      = self.pass_edit.text().strip()
        if not username or not pwd:
            QMessageBox.warning(self, "Error", "모든 필드를 채워주세요.")
            return

        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        conn.close()

        if row and row[0] == hashlib.sha256(pwd.encode()).hexdigest():
            self.accept()
        else:
            QMessageBox.critical(self, "Failed", "아이디 또는 비밀번호가 잘못되었습니다.")
