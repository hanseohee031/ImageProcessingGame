# games/signup.py
import os, sqlite3, hashlib
from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QMessageBox
)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'users.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT
        )
    """)
    return conn

class SignUpDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sign Up")
        self.resize(300, 160)

        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("Username")
        self.pwd_edit = QLineEdit()
        self.pwd_edit.setPlaceholderText("Password")
        self.pwd_edit.setEchoMode(QLineEdit.Password)
        self.pwd2_edit = QLineEdit()
        self.pwd2_edit.setPlaceholderText("Confirm Password")
        self.pwd2_edit.setEchoMode(QLineEdit.Password)

        self.btn_signup = QPushButton("Register")
        self.btn_signup.clicked.connect(self.attempt_signup)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Create a new account:"))
        layout.addWidget(self.user_edit)
        layout.addWidget(self.pwd_edit)
        layout.addWidget(self.pwd2_edit)
        layout.addWidget(self.btn_signup)
        self.setLayout(layout)

    def attempt_signup(self):
        username = self.user_edit.text().strip()
        pwd = self.pwd_edit.text().strip()
        pwd2 = self.pwd2_edit.text().strip()

        if not username or not pwd or not pwd2:
            QMessageBox.warning(self, "Error", "모든 필드를 채워주세요.")
            return
        if pwd != pwd2:
            QMessageBox.warning(self, "Error", "비밀번호가 일치하지 않습니다.")
            return

        hashed = hashlib.sha256(pwd.encode()).hexdigest()
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users(username, password_hash) VALUES (?, ?)",
                (username, hashed)
            )
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Error", "이미 존재하는 아이디입니다.")
            return

        QMessageBox.information(self, "Success", "회원가입이 완료되었습니다!")
        self.accept()
