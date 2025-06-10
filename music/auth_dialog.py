# games/auth_dialog.py
import os
import sqlite3
import hashlib
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog, QTabWidget, QWidget, QFormLayout, QLineEdit,
    QPushButton, QVBoxLayout, QLabel, QDialogButtonBox,
    QMessageBox
)

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

class AuthDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("2025-1 영상처리프로그래밍 프로젝트")
        self.resize(470, 420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # --- 카드형 중앙 Wrapper ---
        wrapper = QWidget()
        wrapper.setObjectName("auth_card")

        # --- 타이틀 ---
        title = QLabel("Jyaenugu the Rapper")
        title.setObjectName("dialog_title")
        title.setAlignment(Qt.AlignCenter)

        # --- 탭 위젯 ---
        tabs = QTabWidget()
        tabs.setFont(QFont("Arial", 16, QFont.Bold))
        tabs.addTab(self._create_login_tab(),  "Login")
        tabs.addTab(self._create_signup_tab(), "Sign Up")

        vbox = QVBoxLayout(wrapper)
        vbox.addWidget(title)
        vbox.addSpacing(8)
        vbox.addWidget(tabs)

        main_lay = QVBoxLayout(self)
        main_lay.addStretch(2)
        main_lay.addWidget(wrapper, alignment=Qt.AlignCenter)
        main_lay.addStretch(1)

    def _create_login_tab(self):
        w = QWidget()
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self.login_user = QLineEdit()
        self.login_user.setPlaceholderText("Username")
        self.login_pwd  = QLineEdit()
        self.login_pwd.setEchoMode(QLineEdit.Password)
        self.login_pwd.setPlaceholderText("Password")
        form.addRow("Username:", self.login_user)
        form.addRow("Password:", self.login_pwd)

        btn_box = QDialogButtonBox()
        self.btn_login = QPushButton("Login")
        self.btn_login.setObjectName("btn_login")
        btn_box.addButton(self.btn_login, QDialogButtonBox.AcceptRole)
        self.btn_login.clicked.connect(self._do_login)

        lay = QVBoxLayout(w)
        lay.addSpacing(16)
        lay.addLayout(form)
        lay.addWidget(btn_box, alignment=Qt.AlignCenter)
        lay.addStretch(1)
        return w

    def _create_signup_tab(self):
        w = QWidget()
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self.sign_user = QLineEdit()
        self.sign_user.setPlaceholderText("Username")
        self.sign_pwd  = QLineEdit()
        self.sign_pwd.setEchoMode(QLineEdit.Password)
        self.sign_pwd.setPlaceholderText("Password")
        self.sign_pwd2 = QLineEdit()
        self.sign_pwd2.setEchoMode(QLineEdit.Password)
        self.sign_pwd2.setPlaceholderText("Confirm Password")
        form.addRow("User:",     self.sign_user)
        form.addRow("Password:", self.sign_pwd)
        form.addRow("Confirm:",  self.sign_pwd2)

        btn_box = QDialogButtonBox()
        self.btn_register = QPushButton("Register")
        self.btn_register.setObjectName("btn_register")
        btn_box.addButton(self.btn_register, QDialogButtonBox.AcceptRole)
        self.btn_register.clicked.connect(self._do_signup)

        lay = QVBoxLayout(w)
        lay.addSpacing(16)
        lay.addLayout(form)
        lay.addWidget(btn_box, alignment=Qt.AlignCenter)
        lay.addStretch(1)
        return w

    def _do_login(self):
        u = self.login_user.text().strip()
        p = self.login_pwd.text().strip()
        if not u or not p:
            QMessageBox.warning(self, "Error", "Both fields are required.")
            return

        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE username = ?", (u,))
        row = cur.fetchone()
        conn.close()

        if row and row[0] == hashlib.sha256(p.encode()).hexdigest():
            self.accept()
        else:
            QMessageBox.critical(self, "Failed", "Invalid username or password.")

    def _do_signup(self):
        u  = self.sign_user.text().strip()
        p  = self.sign_pwd.text().strip()
        p2 = self.sign_pwd2.text().strip()
        if not u or not p or not p2:
            QMessageBox.warning(self, "Error", "모든 필드를 채워주세요.")
            return
        if p != p2:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return

        h = hashlib.sha256(p.encode()).hexdigest()
        try:
            conn = get_db_connection()
            cur  = conn.cursor()
            cur.execute(
                "INSERT INTO users(username,password_hash) VALUES(?,?)",
                (u, h)
            )
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Error", "Username already exists.")
            return

        QMessageBox.information(
            self, "OK",
            "Registration successful.\nPlease switch to Login tab."
        )
        # 회원가입 후 로그인 탭으로 이동
        self.findChild(QTabWidget).setCurrentIndex(0)
