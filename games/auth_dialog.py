# games/auth_dialog.py
import os, sqlite3, hashlib
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QTabWidget, QWidget, QFormLayout, QLineEdit,
    QPushButton, QVBoxLayout, QLabel, QDialogButtonBox,
    QMessageBox, QGraphicsDropShadowEffect
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
        self.setWindowTitle("🎶 Music Quest")
        self.resize(500, 420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # 그림자
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setOffset(0, 0)
        shadow.setColor(Qt.black)
        self.setGraphicsEffect(shadow)

        # 탭
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabBar::tab { font-size: 20px; padding: 12px 30px; }")
        tabs.addTab(self._create_login_tab(),   "Login")
        tabs.addTab(self._create_signup_tab(),  "Sign Up")
        tabs.setTabPosition(QTabWidget.North)

        # 전체 레이아웃
        title = QLabel("Welcome to Music Quest!")
        title.setAlignment(Qt.AlignCenter)
        title_font = title.font()
        title_font.setPointSize(28)
        title_font.setBold(True)
        title.setFont(title_font)

        main_lay = QVBoxLayout(self)
        main_lay.addWidget(title)
        main_lay.addWidget(tabs)

        # 스타일시트: 입력창·버튼 크기 키우기
        self.setStyleSheet("""
        QDialog {
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #ffffff, stop:1 #f0f0f0
            );
            border-radius: 10px;
        }
        QLabel {
            font-size: 20px;
        }
        QLineEdit {
            padding: 12px;
            border: 1px solid #bbb;
            border-radius: 5px;
            font-size: 20px;
        }
        QPushButton {
            min-width: 120px;
            padding: 10px;
            border: none;
            border-radius: 5px;
            font-size: 20px;
            color: white;
        }
        QPushButton#btn_login {
            background-color: #28a745;
        }
        QPushButton#btn_login:hover {
            background-color: #218838;
        }
        QPushButton#btn_register {
            background-color: #dc3545;
        }
        QPushButton#btn_register:hover {
            background-color: #c82333;
        }
        """)

    def _create_login_tab(self):
        w = QWidget()
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self.login_user = QLineEdit()
        self.login_user.setPlaceholderText("👤 Username")
        self.login_pwd  = QLineEdit()
        self.login_pwd.setEchoMode(QLineEdit.Password)
        self.login_pwd.setPlaceholderText("🔒 Password")
        form.addRow("User:", self.login_user)
        form.addRow("Pass:", self.login_pwd)

        btn_box = QDialogButtonBox()
        self.btn_login = QPushButton("Login")
        self.btn_login.setObjectName("btn_login")
        btn_box.addButton(self.btn_login, QDialogButtonBox.AcceptRole)
        self.btn_login.clicked.connect(self._do_login)

        lay = QVBoxLayout(w)
        lay.addLayout(form)
        lay.addWidget(btn_box, alignment=Qt.AlignCenter)
        return w

    def _create_signup_tab(self):
        w = QWidget()
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        self.sign_user = QLineEdit()
        self.sign_user.setPlaceholderText("👤 Username")
        self.sign_pwd  = QLineEdit()
        self.sign_pwd.setEchoMode(QLineEdit.Password)
        self.sign_pwd.setPlaceholderText("🔒 Password")
        self.sign_pwd2 = QLineEdit()
        self.sign_pwd2.setEchoMode(QLineEdit.Password)
        self.sign_pwd2.setPlaceholderText("🔒 Confirm")
        form.addRow("User:",    self.sign_user)
        form.addRow("Password:", self.sign_pwd)
        form.addRow("Confirm:",  self.sign_pwd2)

        btn_box = QDialogButtonBox()
        self.btn_register = QPushButton("Register")
        self.btn_register.setObjectName("btn_register")
        btn_box.addButton(self.btn_register, QDialogButtonBox.AcceptRole)
        self.btn_register.clicked.connect(self._do_signup)

        lay = QVBoxLayout(w)
        lay.addLayout(form)
        lay.addWidget(btn_box, alignment=Qt.AlignCenter)
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
            QMessageBox.critical(self, "Failed", "Invalid credentials.")

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
            cur.execute("INSERT INTO users(username,password_hash) VALUES(?,?)", (u, h))
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Error", "Username already exists.")
            return
        QMessageBox.information(self, "OK", "Registration successful.\nPlease switch to Login tab.")
        self.findChild(QTabWidget).setCurrentIndex(0)
