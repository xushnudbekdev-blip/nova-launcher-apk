import sys
import os
import math
import time
import random
import shutil
import psutil
import requests
import subprocess
from PyQt6.QtCore import Qt, QPoint, QSize, pyqtSignal, pyqtSlot, QThread, QPropertyAnimation, QEasingCurve, QTimer, QRect
from PyQt6.QtGui import QIcon, QPixmap, QFont, QColor, QPalette, QCursor, QPainter, QRadialGradient, QBrush, QLinearGradient, QPen, QFontDatabase
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSlider, QProgressBar,
    QStackedWidget, QFileDialog, QMessageBox, QTextEdit, QFrame,
    QCheckBox, QGroupBox, QScrollArea, QSplitter, QDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QRadioButton, QButtonGroup,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QSpacerItem, QSizePolicy
)

APP_NAME    = "Nova Launcher"
APP_BRAND   = "NOVA LAUNCHER"
APP_VERSION = "2.5.0"
APP_ICON_PATH       = os.path.join("assets", "logo.png")
APP_BACKGROUND_PATH = os.path.join("assets", "background.png")

from config_manager   import ConfigManager
from account_manager  import AccountManager
from downloader       import InstallWorker
from game_launcher    import LaunchWorker
from skin_manager     import SkinManager
from version_manager  import VersionManager
from modrinth_api     import ModrinthAPI, ModrinthSearchWorker, ModrinthDownloadWorker
from shortcut_installer import ShortcutInstaller


# ─────────────────────────────────────────────────────────────
#  ANIMATED BACKGROUND  –  subtle dark nebula particles
# ─────────────────────────────────────────────────────────────
class DarkNebulaBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        random.seed(42)
        self.particles = []
        for _ in range(60):
            self.particles.append({
                'x': random.random(), 'y': random.random(),
                'size': random.uniform(1, 3),
                'speed': random.uniform(0.003, 0.012),
                'drift': random.uniform(-0.003, 0.003),
                'alpha': random.randint(20, 80),
                'phase': random.uniform(0, math.tau),
                'color': random.choice(['cyan','purple','blue','teal']),
            })
        self._t = QTimer(self)
        self._t.setInterval(40)
        self._t.timeout.connect(self._tick)
        self._t.start()
        self._start = time.time()

    def _tick(self):
        for p in self.particles:
            p['y'] -= p['speed']
            p['x'] += p['drift'] * 0.3
            if p['y'] < -0.02: p['y'] = 1.02; p['x'] = random.random()
            if p['x'] < 0: p['x'] = 1.0
            if p['x'] > 1: p['x'] = 0.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        if os.path.exists(APP_BACKGROUND_PATH):
            bg = QPixmap(APP_BACKGROUND_PATH)
            if not bg.isNull():
                painter.drawPixmap(0, 0, w, h, bg)

        t = time.time() - self._start

        # Base gradient – deep dark navy/charcoal
        base = QLinearGradient(0, 0, 0, h)
        base.setColorAt(0.0,  QColor(10, 10, 18))
        base.setColorAt(0.5,  QColor( 8,  8, 15))
        base.setColorAt(1.0,  QColor( 6,  6, 12))
        painter.fillRect(0, 0, w, h, QBrush(base))

        # Nebula glow top-right (purple)
        g1 = QRadialGradient(w * 0.85, h * 0.15, w * 0.45)
        g1.setColorAt(0.0, QColor(100, 60, 180, int(25 + 10*math.sin(t*0.3))))
        g1.setColorAt(1.0, QColor(0,0,0,0))
        painter.fillRect(0, 0, w, h, QBrush(g1))

        # Nebula glow bottom-left (cyan/teal)
        g2 = QRadialGradient(w * 0.1, h * 0.8, w * 0.4)
        g2.setColorAt(0.0, QColor(0, 180, 180, int(18 + 8*math.sin(t*0.4+1))))
        g2.setColorAt(1.0, QColor(0,0,0,0))
        painter.fillRect(0, 0, w, h, QBrush(g2))

        # Subtle particles
        now = time.time()
        for p in self.particles:
            sx, sy = int(p['x']*w), int(p['y']*h)
            tw = math.sin(now*1.5 + p['phase'])
            alpha = int(max(5, min(100, p['alpha'] + tw*25)))
            sz = p['size'] * (0.7 + 0.4*abs(tw))

            if p['color'] == 'cyan':   c = QColor(0, 210, 220, alpha)
            elif p['color'] == 'purple': c = QColor(140, 80, 255, alpha)
            elif p['color'] == 'teal':   c = QColor(0, 180, 160, alpha)
            else:                        c = QColor(80, 120, 255, alpha)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(c))
            r = max(1, int(sz))
            painter.drawEllipse(sx-r, sy-r, r*2, r*2)


# ─────────────────────────────────────────────────────────────
#  BADGE LABEL  (e.g. "3D", "MODRINTH", "ONLINE")
# ─────────────────────────────────────────────────────────────
def make_badge(text, bg="#1DB954", fg="#FFFFFF", radius=4):
    lbl = QLabel(f" {text} ")
    lbl.setStyleSheet(f"""
        background: {bg}; color: {fg};
        font-size: 9px; font-weight: 900;
        border-radius: {radius}px;
        padding: 1px 5px;
        letter-spacing: 0.5px;
    """)
    lbl.setFixedHeight(16)
    return lbl

def make_tag_chip(text, bg="rgba(0,210,220,0.15)", border="rgba(0,210,220,0.5)", fg="#00D2DC"):
    lbl = QLabel(f"  {text}  ")
    lbl.setStyleSheet(f"""
        background: {bg};
        color: {fg};
        border: 1px solid {border};
        border-radius: 10px;
        font-size: 10px;
        font-weight: 700;
        padding: 2px 4px;
    """)
    return lbl


# ─────────────────────────────────────────────────────────────
#  CUSTOM TITLE BAR
# ─────────────────────────────────────────────────────────────
class CustomTitleBar(QWidget):
    def __init__(self, parent=None, title=""):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(38)
        self.setStyleSheet("""
            QWidget { background: rgba(8,8,14,0.98); border-bottom: 1px solid rgba(255,255,255,0.06); }
            QLabel  { color: #9CA3AF; font-size: 12px; background: transparent; border: none; }
            QPushButton {
                background: transparent; border: none; color: #6B7280;
                font-size: 13px; font-family: 'Segoe UI Emoji','Segoe UI Symbol'; font-weight: bold;
                border-radius: 4px; padding: 2px 8px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.08); color: #E5E7EB; }
            QPushButton#close_btn:hover { background: #EF4444; color: #fff; }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 6, 0)
        layout.setSpacing(4)

        icon_lbl = QLabel()
        if os.path.exists(APP_ICON_PATH):
            px = QPixmap(APP_ICON_PATH).scaled(18, 18,
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_lbl.setPixmap(px)
        layout.addWidget(icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color:#6B7280; font-size:11px; background:transparent; border:none;")
        layout.addWidget(title_lbl)
        layout.addStretch()

        for symbol, tip, slot in [
            ("─", "Minimize", self.parent.showMinimized),
            ("❐", "Maximize", self.toggle_max),
            ("✕", "Close",    self.parent.close),
        ]:
            btn = QPushButton(symbol)
            btn.setFixedSize(32, 26)
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            if symbol == "✕": btn.setObjectName("close_btn")
            layout.addWidget(btn)

        self.drag_pos = QPoint()

    def toggle_max(self):
        self.parent.showNormal() if self.parent.isMaximized() else self.parent.showMaximized()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = e.globalPosition().toPoint() - self.parent.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton:
            self.parent.move(e.globalPosition().toPoint() - self.drag_pos)


class ImageLoaderThread(QThread):
    loaded_signal = pyqtSignal(QLabel, QPixmap)
    def __init__(self, lbl, url):
        super().__init__(); self.lbl = lbl; self.url = url
    def run(self):
        try:
            res = requests.get(self.url, timeout=5)
            if res.status_code == 200:
                px = QPixmap(); px.loadFromData(res.content)
                if not px.isNull():
                    w = self.lbl.width() or 56; h = self.lbl.height() or 56
                    self.loaded_signal.emit(self.lbl, px.scaled(w, h,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation))
        except: pass


# ─────────────────────────────────────────────────────────────
#  TOAST
# ─────────────────────────────────────────────────────────────
class ToastNotification(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.SubWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.container = QFrame(self)
        layout = QHBoxLayout(self); layout.setContentsMargins(0,0,0,0)
        c_layout = QHBoxLayout(self.container); c_layout.setContentsMargins(14,8,14,8)
        self.icon_lbl = QLabel("✓"); self.msg_lbl = QLabel("")
        c_layout.addWidget(self.icon_lbl); c_layout.addWidget(self.msg_lbl)
        layout.addWidget(self.container)
        self.hide()
        self.timer = QTimer(self); self.timer.setSingleShot(True); self.timer.timeout.connect(self.hide)

    def show_toast(self, message, is_error=False, duration_ms=3200):
        if is_error:
            self.container.setStyleSheet("QFrame{background:#1A0505;border:1px solid #EF4444;border-radius:8px;} QLabel{color:#FCA5A5;font-size:12px;font-weight:bold;background:transparent;border:none;}")
            self.icon_lbl.setText("⚠")
        else:
            self.container.setStyleSheet("QFrame{background:#051A0F;border:1px solid #10B981;border-radius:8px;} QLabel{color:#6EE7B7;font-size:12px;font-weight:bold;background:transparent;border:none;}")
            self.icon_lbl.setText("✓")
        self.msg_lbl.setText(message); self.adjustSize()
        if self.parent():
            w = max(260, self.sizeHint().width()); self.setFixedWidth(w)
            self.move(self.parent().width()-w-20, 48)
        self.show(); self.raise_(); self.timer.start(duration_ms)


# ─────────────────────────────────────────────────────────────
#  LOGIN MODAL
# ─────────────────────────────────────────────────────────────
class LoginRegisterModal(QDialog):
    def __init__(self, account_manager, parent=None):
        super().__init__(parent)
        self.acc_mgr = account_manager
        self.setWindowTitle("Nova Launcher — Kirish")
        self.setFixedSize(400, 460)
        self.setStyleSheet("""
            QDialog{background:#0D0D18;color:#E5E7EB;font-family:'Segoe UI',sans-serif;}
            QLabel{color:#9CA3AF;background:transparent;border:none;}
            QLineEdit{
                background:#161625;border:1px solid rgba(255,255,255,0.1);
                border-radius:8px;padding:10px 14px;color:#F9FAFB;font-size:13px;
            }
            QLineEdit:focus{border:1px solid #00D2DC;}
            QCheckBox{color:#9CA3AF;}
        """)
        layout = QVBoxLayout(self); layout.setContentsMargins(28,28,28,28)

        title = QLabel("Nova Launcher")
        title.setStyleSheet("font-size:22px;font-weight:900;color:#FFFFFF;background:transparent;border:none;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        self.stacked = QStackedWidget()

        # Page 1: Login
        p1 = QWidget(); p1_l = QVBoxLayout(p1); p1_l.setSpacing(10)
        p1_lbl = QLabel("Tizimga Kirish")
        p1_lbl.setStyleSheet("font-size:15px;font-weight:700;color:#E5E7EB;background:transparent;border:none;")
        self.txt_login_user = QLineEdit(); self.txt_login_user.setPlaceholderText("Nikneym")
        self.txt_login_pass = QLineEdit(); self.txt_login_pass.setPlaceholderText("Parol")
        self.txt_login_pass.setEchoMode(QLineEdit.EchoMode.Password)
        btn_login = QPushButton("Kirish"); btn_login.clicked.connect(self.handle_login)
        btn_login.setStyleSheet("background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00B4D8,stop:1 #0096C7);color:#fff;font-weight:900;font-size:14px;border-radius:8px;padding:11px;border:none;")
        btn_to_reg = QPushButton("Ro'yxatdan o'tish"); btn_to_reg.clicked.connect(lambda: self.stacked.setCurrentIndex(1))
        btn_to_reg.setStyleSheet("background:rgba(255,255,255,0.06);color:#9CA3AF;border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:9px;")
        for w in [p1_lbl,QLabel("Nikneym:"),self.txt_login_user,QLabel("Parol:"),self.txt_login_pass,btn_login,btn_to_reg]:
            p1_l.addWidget(w)
        p1_l.addStretch()

        # Page 2: Register
        p2 = QWidget(); p2_l = QVBoxLayout(p2); p2_l.setSpacing(10)
        p2_lbl = QLabel("Ro'yxatdan O'tish")
        p2_lbl.setStyleSheet("font-size:15px;font-weight:700;color:#E5E7EB;background:transparent;border:none;")
        self.txt_reg_user = QLineEdit(); self.txt_reg_user.setPlaceholderText("Yangi nikneym")
        self.txt_reg_pass = QLineEdit(); self.txt_reg_pass.setPlaceholderText("Yangi parol")
        self.txt_reg_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.chk_reg_alex = QCheckBox("Slim (Alex) modeli")
        btn_reg = QPushButton("Ro'yxatdan o'tish"); btn_reg.clicked.connect(self.handle_register)
        btn_reg.setStyleSheet("background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00B4D8,stop:1 #0096C7);color:#fff;font-weight:900;font-size:14px;border-radius:8px;padding:11px;border:none;")
        btn_to_login = QPushButton("◀ Orqaga"); btn_to_login.clicked.connect(lambda: self.stacked.setCurrentIndex(0))
        btn_to_login.setStyleSheet("background:rgba(255,255,255,0.06);color:#9CA3AF;border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:9px;")
        for w in [p2_lbl,QLabel("Nikneym:"),self.txt_reg_user,QLabel("Parol:"),self.txt_reg_pass,self.chk_reg_alex,btn_reg,btn_to_login]:
            p2_l.addWidget(w)
        p2_l.addStretch()

        self.stacked.addWidget(p1); self.stacked.addWidget(p2)
        layout.addWidget(self.stacked)

    def handle_login(self):
        ok, msg = self.acc_mgr.authenticate(self.txt_login_user.text().strip(), self.txt_login_pass.text().strip())
        if self.parent() and hasattr(self.parent(),'show_toast'): self.parent().show_toast(msg, is_error=not ok)
        if ok: self.accept()

    def handle_register(self):
        ok, msg = self.acc_mgr.register(self.txt_reg_user.text().strip(), self.txt_reg_pass.text().strip(), is_alex=self.chk_reg_alex.isChecked())
        if self.parent() and hasattr(self.parent(),'show_toast'): self.parent().show_toast(msg, is_error=not ok)
        if ok: self.accept()


# ─────────────────────────────────────────────────────────────
#  MAIN WINDOW
# ─────────────────────────────────────────────────────────────
class NovaLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg      = ConfigManager()
        self.acc_mgr  = AccountManager(self.cfg.get("game_dir"))
        self.install_worker = self.launch_worker = None
        self.mod_search_worker = self.mod_dl_worker = None
        self.img_threads = []; self.skin_view_back = False

        self.toast = ToastNotification(self)
        self.init_ui()
        self.load_settings_to_ui()
        self.populate_versions()
        # Restore saved account state after UI is fully built
        self.refresh_account_dropdown()
        self.update_admin_visibility()
        self.switch_page(0)

    def show_toast(self, message, is_error=False, duration_ms=3200):
        """Show a toast notification only — does NOT alter account state."""
        if hasattr(self, 'toast'):
            self.toast.show_toast(message, is_error=is_error, duration_ms=duration_ms)

    # ── INIT ────────────────────────────────────────────────
    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowMinimizeButtonHint)
        self.resize(1050, 660)
        self.setMinimumSize(900, 580)
        self.setWindowTitle(APP_NAME)
        if os.path.exists(APP_ICON_PATH): self.setWindowIcon(QIcon(APP_ICON_PATH))

        self.bg = DarkNebulaBackground(self)
        self.bg.setObjectName("BG")
        self.setCentralWidget(self.bg)

        root = QVBoxLayout(self.bg)
        root.setContentsMargins(0,0,0,0)
        root.setSpacing(0)

        # Title bar
        self.title_bar = CustomTitleBar(self, APP_NAME)
        root.addWidget(self.title_bar)

        # Body: sidebar + pages
        body = QHBoxLayout()
        body.setContentsMargins(0,0,0,0)
        body.setSpacing(0)

        body.addWidget(self._build_sidebar())

        pages_wrap = QVBoxLayout()
        pages_wrap.setContentsMargins(0,0,0,0)
        pages_wrap.setSpacing(0)

        self.pages_stacked = QStackedWidget()
        self.pages_stacked.setStyleSheet("background:transparent;")

        for page in [self.create_page_home(), self.create_page_auth(),
                     self.create_page_skin(), self.create_page_mods(),
                     self.create_page_settings(), self.create_page_admin(),
                     self.create_page_logs()]:
            self.pages_stacked.addWidget(page)

        pages_wrap.addWidget(self.pages_stacked, 1)

        body_w = QWidget(); body_w.setStyleSheet("background:transparent;")
        body_w.setLayout(pages_wrap)
        body.addWidget(body_w, 1)
        body_widget = QWidget(); body_widget.setStyleSheet("background:transparent;")
        body_widget.setLayout(body)
        root.addWidget(body_widget, 1)

        # Bottom dock
        root.addWidget(self._build_bottom_dock())

    # ── SIDEBAR ─────────────────────────────────────────────
    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(200)
        sidebar.setObjectName("Sidebar")
        sidebar.setStyleSheet("""
            QWidget#Sidebar {
                background: rgba(8,8,14,0.95);
                border-right: 1px solid rgba(255,255,255,0.07);
            }
        """)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12,16,12,16)
        layout.setSpacing(4)

        # Logo
        logo_row = QHBoxLayout()
        logo_icon = QLabel()
        if os.path.exists(APP_ICON_PATH):
            logo_icon.setPixmap(QPixmap(APP_ICON_PATH).scaled(34,34,
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_row.addWidget(logo_icon)
        logo_text = QVBoxLayout(); logo_text.setSpacing(1)
        lbl_name = QLabel("NOVA"); lbl_name.setStyleSheet("color:#FFFFFF;font-weight:900;font-size:14px;background:transparent;border:none;")
        version_badge = make_badge(f"v{APP_VERSION}", "#1DB954")
        logo_text.addWidget(lbl_name); logo_text.addWidget(version_badge)
        logo_row.addLayout(logo_text); logo_row.addStretch()
        layout.addLayout(logo_row)
        layout.addSpacing(14)

        # Nav buttons definition: (icon, label, page_idx, badge_text, badge_color)
        nav_items = [
            ("🏠", "Asosiy",         0, None, None),
            ("👤", "Profil",         1, None, None),
            ("👕", "Skin & Plashch", 2, "3D", "#7C3AED"),
            ("🌐", "Modlar",         3, "MODRINTH", "#1DB954"),
            ("⚙", "Sozlamalar",     4, None, None),
            ("👑", "Admin Paneli",   5, None, None),
            ("📜", "Konsol",         6, None, None),
        ]

        self.nav_buttons = []
        for icon, label, idx, badge, badge_color in nav_items:
            btn = self._make_nav_btn(icon, label, idx, badge, badge_color)
            layout.addWidget(btn)
            self.nav_buttons.append((btn, idx))

        # Hide admin by default
        self.nav_buttons[5][0].setVisible(False)

        layout.addStretch()

        # Bottom: current user info
        self.sidebar_user_card = QFrame()
        self.sidebar_user_card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 10px;
            }
        """)
        uc_layout = QHBoxLayout(self.sidebar_user_card)
        uc_layout.setContentsMargins(10,8,10,8)

        self.sidebar_avatar = QLabel("🎮")
        self.sidebar_avatar.setStyleSheet("font-size:22px;background:transparent;border:none;")
        self.sidebar_avatar.setFixedSize(32,32)
        self.sidebar_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        uc_info = QVBoxLayout(); uc_info.setSpacing(1)
        self.sidebar_username = QLabel("O'yinchi")
        self.sidebar_username.setStyleSheet("color:#F9FAFB;font-weight:700;font-size:12px;background:transparent;border:none;")
        self.sidebar_status = QLabel("O'ynashga tayyor")
        self.sidebar_status.setStyleSheet("color:#1DB954;font-size:10px;font-weight:600;background:transparent;border:none;")
        uc_info.addWidget(self.sidebar_username); uc_info.addWidget(self.sidebar_status)

        uc_layout.addWidget(self.sidebar_avatar)
        uc_layout.addLayout(uc_info)
        layout.addWidget(self.sidebar_user_card)
        return sidebar

    def _make_nav_btn(self, icon, label, idx, badge=None, badge_color=None):
        btn = QWidget()
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setFixedHeight(40)
        btn.setObjectName(f"nav_{idx}")
        btn.setProperty("nav_idx", idx)
        btn.setProperty("nav_active", False)
        btn.setStyleSheet("""
            QWidget { background:transparent; border-radius:8px; }
            QWidget:hover { background:rgba(255,255,255,0.06); }
        """)

        row = QHBoxLayout(btn); row.setContentsMargins(10,0,10,0); row.setSpacing(8)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("color:#6B7280;font-size:15px;background:transparent;border:none;")
        icon_lbl.setFixedWidth(20)

        text_lbl = QLabel(label)
        text_lbl.setObjectName(f"nav_text_{idx}")
        text_lbl.setStyleSheet("color:#9CA3AF;font-size:13px;font-weight:600;background:transparent;border:none;")

        row.addWidget(icon_lbl)
        row.addWidget(text_lbl)
        row.addStretch()

        if badge and badge_color:
            b = make_badge(badge, badge_color)
            row.addWidget(b)

        # Clickable via mousePressEvent override
        btn.mousePressEvent = lambda e, i=idx: self.switch_page(i)
        btn._icon_lbl = icon_lbl
        btn._text_lbl = text_lbl
        return btn

    def _set_nav_active(self, active_idx):
        for btn, idx in self.nav_buttons:
            is_active = (idx == active_idx)
            if is_active:
                btn.setStyleSheet("""
                    QWidget { background:rgba(0,210,220,0.1); border-radius:8px;
                              border-left:3px solid #00D2DC; }
                """)
                btn._text_lbl.setStyleSheet(
                    "color:#00D2DC;font-size:13px;font-weight:700;background:transparent;border:none;")
                btn._icon_lbl.setStyleSheet(
                    "color:#00D2DC;font-size:15px;background:transparent;border:none;")
            else:
                btn.setStyleSheet("QWidget{background:transparent;border-radius:8px;} QWidget:hover{background:rgba(255,255,255,0.06);}")
                btn._text_lbl.setStyleSheet(
                    "color:#9CA3AF;font-size:13px;font-weight:600;background:transparent;border:none;")
                btn._icon_lbl.setStyleSheet(
                    "color:#6B7280;font-size:15px;background:transparent;border:none;")

    # ── BOTTOM DOCK ─────────────────────────────────────────
    def _build_bottom_dock(self):
        dock = QFrame()
        dock.setFixedHeight(68)
        dock.setStyleSheet("""
            QFrame {
                background: rgba(6,6,11,0.98);
                border-top: 1px solid rgba(255,255,255,0.07);
            }
        """)
        layout = QHBoxLayout(dock)
        layout.setContentsMargins(16,0,16,0)
        layout.setSpacing(10)

        # User info
        user_section = QHBoxLayout(); user_section.setSpacing(10)
        self.bottom_avatar = QLabel("🎮")
        self.bottom_avatar.setStyleSheet("""
            background: rgba(0,210,220,0.15);
            border: 1px solid rgba(0,210,220,0.3);
            border-radius: 20px;
            font-size: 20px;
            padding: 4px;
        """)
        self.bottom_avatar.setFixedSize(40,40)
        self.bottom_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        user_info_v = QVBoxLayout(); user_info_v.setSpacing(1)
        self.bottom_username = QLabel("O'yinchi")
        self.bottom_username.setStyleSheet("color:#F9FAFB;font-weight:700;font-size:13px;background:transparent;border:none;")
        self.bottom_status_lbl = QLabel("O'ynashga tayyor")
        self.bottom_status_lbl.setStyleSheet("color:#1DB954;font-size:10px;font-weight:600;background:transparent;border:none;")
        user_info_v.addWidget(self.bottom_username)
        user_info_v.addWidget(self.bottom_status_lbl)
        user_section.addWidget(self.bottom_avatar)
        user_section.addLayout(user_info_v)

        layout.addLayout(user_section)
        layout.addSpacing(8)

        # Version combo
        self.combo_version = QComboBox()
        self.combo_version.setMinimumWidth(240)
        self.combo_version.setFixedHeight(38)
        self.combo_version.setStyleSheet("""
            QComboBox {
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 8px;
                color: #E5E7EB;
                font-size: 13px;
                font-weight: 600;
                padding: 0 12px;
            }
            QComboBox::drop-down { border:none; width:20px; }
            QComboBox QAbstractItemView {
                background: #0D0D18; border: 1px solid rgba(255,255,255,0.1);
                color: #E5E7EB; selection-background-color: rgba(0,210,220,0.2);
            }
        """)
        self.combo_version.currentIndexChanged.connect(self.on_version_changed)
        layout.addWidget(self.combo_version)

        # Progress bar (thin, above play btn)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedSize(2, 2); self.progress_bar.hide()
        self.progress_bar.setValue(0)

        # Account combo (hidden, compact)
        self.chk_accounts_enable = QCheckBox()
        self.chk_accounts_enable.setChecked(True)
        self.chk_accounts_enable.hide()
        self.chk_accounts_enable.stateChanged.connect(self.on_accounts_chk_changed)

        self.combo_accounts = QComboBox()
        self.combo_accounts.setFixedHeight(38)
        self.combo_accounts.setFixedWidth(160)
        self.combo_accounts.setStyleSheet("""
            QComboBox {
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 8px;
                color: #E5E7EB; font-size: 12px; padding: 0 10px;
            }
            QComboBox::drop-down{border:none;width:16px;}
            QComboBox QAbstractItemView{background:#0D0D18;border:1px solid rgba(255,255,255,0.1);color:#E5E7EB;}
        """)
        self.combo_accounts.currentIndexChanged.connect(self.on_account_selected)
        layout.addWidget(self.combo_accounts)

        # Icon buttons
        for icon, tip, slot in [
            ("🔄", "Versiyalarni yangilash", self.populate_versions),
            ("📁", "O'yin papkasini ochish",  self.open_mods_folder),
            ("⚙️", "Sozlamalar",              lambda: self.switch_page(4)),
        ]:
            b = QPushButton(icon)
            b.setFixedSize(38,38)
            b.setToolTip(tip)
            b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            b.setStyleSheet("""
                QPushButton {
                    background:rgba(255,255,255,0.06);
                    border:1px solid rgba(255,255,255,0.1);
                    border-radius:8px; font-size:16px; color:#9CA3AF;
                }
                QPushButton:hover { background:rgba(255,255,255,0.12); color:#E5E7EB; }
                QPushButton:pressed { background:rgba(255,255,255,0.04); }
            """)
            b.clicked.connect(slot)
            layout.addWidget(b)

        # Status label
        self.lbl_status = QLabel("O'yinga kirishga tayyor")
        self.lbl_status.setStyleSheet("color:#6B7280;font-size:11px;background:transparent;border:none;")
        layout.addWidget(self.lbl_status, 1)

        # MODS button
        btn_mods = QPushButton("📁  MODS")
        btn_mods.setFixedHeight(44)
        btn_mods.setFixedWidth(110)
        btn_mods.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_mods.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.07);
                border: 1px solid rgba(255,255,255,0.14);
                border-radius: 10px;
                color: #D1D5DB; font-size: 13px; font-weight: 700;
            }
            QPushButton:hover { background:rgba(255,255,255,0.13); color:#fff; }
            QPushButton:pressed { background:rgba(255,255,255,0.04); }
        """)
        btn_mods.clicked.connect(self.open_mods_folder)
        layout.addWidget(btn_mods)

        # PLAY button
        self.btn_launch = QPushButton("▶  O'YINGA KIRISH")
        self.btn_launch.setFixedHeight(44)
        self.btn_launch.setMinimumWidth(200)
        self.btn_launch.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_launch.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #0096C7, stop:1 #0077B6);
                border: none;
                border-radius: 10px;
                color: #FFFFFF;
                font-size: 15px;
                font-weight: 900;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #00B4D8, stop:1 #0096C7);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #005F73, stop:1 #0077B6);
            }
            QPushButton:disabled {
                background: rgba(255,255,255,0.08); color:#4B5563;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self.btn_launch)
        shadow.setBlurRadius(22); shadow.setColor(QColor(0,180,216,130)); shadow.setOffset(0,4)
        self.btn_launch.setGraphicsEffect(shadow)
        self.btn_launch.clicked.connect(self.on_launch_clicked)
        layout.addWidget(self.btn_launch)

        return dock

    # ── GLOBAL STYLESHEET ───────────────────────────────────
    def apply_global_theme(self):
        pass  # All styling done inline for DEX-style precision

    def _card(self, bg="rgba(255,255,255,0.04)", border="rgba(255,255,255,0.08)"):
        f = QFrame()
        f.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 12px;
            }}
        """)
        return f

    def _section_head(self, title, subtitle=""):
        w = QWidget(); w.setStyleSheet("background:transparent;")
        v = QVBoxLayout(w); v.setContentsMargins(0,0,0,0); v.setSpacing(2)
        t = QLabel(title)
        t.setStyleSheet("color:#F9FAFB;font-size:17px;font-weight:800;background:transparent;border:none;")
        v.addWidget(t)
        if subtitle:
            s = QLabel(subtitle)
            s.setStyleSheet("color:#6B7280;font-size:11px;background:transparent;border:none;")
            v.addWidget(s)
        return w

    def _input(self, placeholder=""):
        e = QLineEdit(); e.setPlaceholderText(placeholder)
        e.setFixedHeight(38)
        e.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px; padding: 0 12px;
                color: #F9FAFB; font-size: 13px;
            }
            QLineEdit:focus { border: 1px solid #00D2DC; }
        """)
        return e

    def _combo(self):
        c = QComboBox(); c.setFixedHeight(38)
        c.setStyleSheet("""
            QComboBox {
                background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);
                border-radius:8px;padding:0 12px;color:#F9FAFB;font-size:13px;
            }
            QComboBox::drop-down{border:none;width:20px;}
            QComboBox QAbstractItemView{background:#0D0D18;border:1px solid rgba(255,255,255,0.1);
                color:#F9FAFB;selection-background-color:rgba(0,210,220,0.2);}
        """)
        return c

    def _btn_primary(self, text, color_start="#0096C7", color_end="#0077B6"):
        b = QPushButton(text); b.setFixedHeight(38)
        b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        b.setStyleSheet(f"""
            QPushButton {{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {color_start},stop:1 {color_end});
                color:#fff;font-weight:700;font-size:13px;border:none;border-radius:8px;
            }}
            QPushButton:hover {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00B4D8,stop:1 #0096C7); }}
            QPushButton:pressed {{ background:rgba(0,150,199,0.6); }}
            QPushButton:disabled {{ background:rgba(255,255,255,0.07); color:#4B5563; }}
        """)
        return b

    def _btn_ghost(self, text):
        b = QPushButton(text); b.setFixedHeight(38)
        b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        b.setStyleSheet("""
            QPushButton{background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);
                border-radius:8px;color:#9CA3AF;font-size:13px;font-weight:600;}
            QPushButton:hover{background:rgba(255,255,255,0.1);color:#E5E7EB;}
            QPushButton:pressed{background:rgba(255,255,255,0.04);}
        """)
        return b

    def _btn_danger(self, text):
        b = QPushButton(text); b.setFixedHeight(38)
        b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        b.setStyleSheet("""
            QPushButton{background:rgba(239,68,68,0.15);border:1px solid rgba(239,68,68,0.3);
                border-radius:8px;color:#FCA5A5;font-size:13px;font-weight:600;}
            QPushButton:hover{background:rgba(239,68,68,0.3);color:#fff;}
        """)
        return b

    def _btn_success(self, text):
        b = QPushButton(text); b.setFixedHeight(38)
        b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        b.setStyleSheet("""
            QPushButton{background:rgba(29,185,84,0.15);border:1px solid rgba(29,185,84,0.3);
                border-radius:8px;color:#6EE7B7;font-size:13px;font-weight:600;}
            QPushButton:hover{background:rgba(29,185,84,0.3);color:#fff;}
        """)
        return b

    def _groupbox(self, title):
        g = QGroupBox(title)
        g.setStyleSheet("""
            QGroupBox{
                background:rgba(255,255,255,0.02);
                border:1px solid rgba(255,255,255,0.08);
                border-radius:10px;margin-top:14px;padding:14px;
                color:#9CA3AF;font-size:12px;font-weight:700;
            }
            QGroupBox::title{
                subcontrol-origin:margin;left:12px;padding:0 6px;
                background:rgba(8,8,14,0.9);color:#9CA3AF;
            }
        """)
        return g

    # ═══════════════════════════════════════════════════════
    #  PAGES
    # ═══════════════════════════════════════════════════════

    # ── HOME PAGE ──────────────────────────────────────────
    def create_page_home(self):
        page = QWidget(); page.setStyleSheet("background:transparent;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24,20,24,20)
        layout.setSpacing(16)

        # Section header
        header_row = QHBoxLayout()
        section_lbl = QLabel("ASOSIY")
        section_lbl.setStyleSheet("color:#6B7280;font-size:11px;font-weight:700;letter-spacing:1.5px;background:transparent;border:none;")
        header_row.addWidget(section_lbl)
        header_row.addStretch()
        layout.addLayout(header_row)

        # Hero card
        hero = self._card("rgba(255,255,255,0.04)", "rgba(255,255,255,0.09)")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(24,22,24,22)
        hero_layout.setSpacing(20)

        # Left: info
        left_v = QVBoxLayout(); left_v.setSpacing(10)

        # Tags row
        tags = QHBoxLayout(); tags.setSpacing(6)
        for txt, bg, fg in [
            (f"⚡ {APP_VERSION} FABRIC", "rgba(0,210,220,0.15)", "#00D2DC"),
            ("🚀 MAX FPS 240+",         "rgba(139,92,246,0.15)", "#A78BFA"),
            ("✨ 3D SKINLAR",            "rgba(236,72,153,0.15)", "#F472B6"),
            ("⭐ PREMIUM",               "rgba(251,191,36,0.15)", "#FCD34D"),
        ]:
            border = "1px solid " + fg
            tags.addWidget(make_tag_chip(txt, bg, border, fg))
        tags.addStretch()
        left_v.addLayout(tags)

        # Big title
        title_row = QHBoxLayout(); title_row.setSpacing(8)
        t1 = QLabel("NOVA"); t1.setStyleSheet("color:#FFFFFF;font-size:32px;font-weight:900;background:transparent;border:none;")
        t2 = QLabel("LAUNCHER"); t2.setStyleSheet("color:#00D2DC;font-size:32px;font-weight:900;background:transparent;border:none;")
        title_row.addWidget(t1); title_row.addWidget(t2); title_row.addStretch()
        left_v.addLayout(title_row)

        desc = QLabel("Minecraft uchun eng ilg'or, tezkor va bepul launcher.\nFabric, Forge, OptiFine — 1-bosishda o'rnating.")
        desc.setStyleSheet("color:#9CA3AF;font-size:12px;line-height:1.6;background:transparent;border:none;")
        desc.setWordWrap(True)
        left_v.addWidget(desc)

        # Stats row
        stats = QHBoxLayout(); stats.setSpacing(24)
        for val, label in [
            (APP_VERSION, "VERSIYA"),
            ("4 GB",      "AJRATILGAN RAM"),
            ("ONLINE",    "TARMOQ HOLATI"),
            ("FABRIC",    "LOADER DVIGATELI"),
        ]:
            sv = QVBoxLayout(); sv.setSpacing(1)
            color = "#1DB954" if val in ("ONLINE",) else "#F9FAFB"
            v_lbl = QLabel(val)
            v_lbl.setStyleSheet(f"color:{color};font-size:16px;font-weight:900;background:transparent;border:none;")
            k_lbl = QLabel(label)
            k_lbl.setStyleSheet("color:#4B5563;font-size:9px;font-weight:700;letter-spacing:0.5px;background:transparent;border:none;")
            sv.addWidget(v_lbl); sv.addWidget(k_lbl)
            stats.addLayout(sv)
        stats.addStretch()
        left_v.addLayout(stats)

        hero_layout.addLayout(left_v, 1)

        layout.addWidget(hero)

        # Feature cards section
        layout.addWidget(self._section_head("Asosiy Bo'limlar & Imkoniyatlar",
                                             "Mijozning eng muhim funksiyalariga tezkor o'tish"))

        cards_row = QHBoxLayout(); cards_row.setSpacing(12)

        feat_data = [
            ("🎨", "#7C3AED", "rgba(124,58,237,0.15)", "3D STUDIO",
             "3D Skin & Plashch", "Skinlar, qanot va plashchlarni 3D studiyada ko'ring va sozlang.",
             "Skin sahifasi", 2),
            ("📦", "#1DB954", "rgba(29,185,84,0.15)", "MODRINTH HUB",
             "Modlar Markazi", "Sodium, Iris Shaders, AppleSkin va yuzlab modlar. Avtomatik o'rnatiladi.",
             "Modlarni tanlash", 3),
            ("⚡", "#F59E0B", "rgba(245,158,11,0.15)", "240+ FPS ENGINE",
             "FPS Boost & Sozlamalar", "RAM xotirasi, ZGC parametrlarini sozlang va maksimal FPS oling.",
             "Sozlamalarni ochish", 4),
        ]

        for icon, icon_color, icon_bg, badge_txt, title, desc_txt, link_txt, page_idx in feat_data:
            card = self._card("rgba(255,255,255,0.04)", "rgba(255,255,255,0.08)")
            cl = QVBoxLayout(card); cl.setContentsMargins(18,18,18,18); cl.setSpacing(10)

            top_row = QHBoxLayout()
            icon_box = QLabel(icon)
            icon_box.setFixedSize(40,40)
            icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_box.setStyleSheet(f"background:{icon_bg};border-radius:10px;font-size:20px;")
            badge = make_badge(badge_txt, icon_bg.replace("0.15","0.4"), icon_color)
            top_row.addWidget(icon_box); top_row.addStretch(); top_row.addWidget(badge)
            cl.addLayout(top_row)

            ct = QLabel(title)
            ct.setStyleSheet("color:#F9FAFB;font-size:14px;font-weight:700;background:transparent;border:none;")
            cd = QLabel(desc_txt); cd.setWordWrap(True)
            cd.setStyleSheet("color:#6B7280;font-size:11px;background:transparent;border:none;")
            cl.addWidget(ct); cl.addWidget(cd); cl.addStretch()

            link_btn = QPushButton(f"{link_txt}  ›")
            link_btn.setStyleSheet(f"background:transparent;border:none;color:{icon_color};font-size:11px;font-weight:700;text-align:left;padding:0;")
            link_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            link_btn.clicked.connect(lambda _, i=page_idx: self.switch_page(i))
            cl.addWidget(link_btn)

            cards_row.addWidget(card)

        layout.addLayout(cards_row)
        layout.addStretch()
        return page

    # ── AUTH PAGE ──────────────────────────────────────────
    def create_page_auth(self):
        page = QWidget(); page.setStyleSheet("background:transparent;")
        layout = QVBoxLayout(page); layout.setContentsMargins(24,20,24,20); layout.setSpacing(14)
        layout.addWidget(self._section_head("Profil & Akkaunt Boshqaruvi"))

        card = self._card()
        cl = QVBoxLayout(card); cl.setContentsMargins(20,20,20,20); cl.setSpacing(12)

        info_row = QHBoxLayout(); info_row.setSpacing(14)
        avatar = QLabel("🎮")
        avatar.setFixedSize(52,52); avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("background:rgba(0,210,220,0.12);border:1px solid rgba(0,210,220,0.3);border-radius:26px;font-size:24px;")
        info_row.addWidget(avatar)

        info_v = QVBoxLayout(); info_v.setSpacing(2)
        self.lbl_auth_username = QLabel("Foydalanuvchi: Kirilmagan")
        self.lbl_auth_username.setStyleSheet("color:#F9FAFB;font-size:16px;font-weight:700;background:transparent;border:none;")
        self.lbl_auth_role = QLabel("Maqomi: Oddiy Foydalanuvchi")
        self.lbl_auth_role.setStyleSheet("color:#9CA3AF;font-size:12px;background:transparent;border:none;")
        info_v.addWidget(self.lbl_auth_username); info_v.addWidget(self.lbl_auth_role)
        info_row.addLayout(info_v); info_row.addStretch()
        cl.addLayout(info_row)

        btn = self._btn_primary("🔑  Kirish / Ro'yxatdan O'tish")
        btn.clicked.connect(self.open_login_modal)
        cl.addWidget(btn)
        layout.addWidget(card)

        self.admin_info_box = self._groupbox("👑 Admin Akkaunti (Maxsus)")
        ai = QVBoxLayout(self.admin_info_box)
        ai_d = QLabel("NovaLauncher Admin boshqaruv paneli va tizim akkaunti sozlamalari.")
        ai_d.setStyleSheet("color:#9CA3AF;font-size:12px;background:transparent;border:none;")
        ai.addWidget(ai_d)
        layout.addWidget(self.admin_info_box)
        layout.addStretch()
        return page

    # ── SKIN PAGE ──────────────────────────────────────────
    def create_page_skin(self):
        page = QWidget(); page.setStyleSheet("background:transparent;")
        layout = QVBoxLayout(page); layout.setContentsMargins(24,20,24,20); layout.setSpacing(14)
        layout.addWidget(self._section_head("Skin & Plashch (Cape)", "3D Isometric ko'rinishda boshqaring"))

        card = self._card()
        cl = QHBoxLayout(card); cl.setContentsMargins(20,20,20,20); cl.setSpacing(20)

        # Left preview
        prev_v = QVBoxLayout(); prev_v.setSpacing(8)
        self.lbl_avatar_preview = QLabel()
        self.lbl_avatar_preview.setFixedSize(140,280)
        self.lbl_avatar_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_avatar_preview.setStyleSheet("background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-radius:10px;")
        prev_v.addWidget(self.lbl_avatar_preview)

        vf = self._btn_primary("👤  Front"); vf.clicked.connect(lambda: self.toggle_skin_view(False))
        vb = self._btn_ghost("🧥  Back"); vb.clicked.connect(lambda: self.toggle_skin_view(True))
        prev_v.addWidget(vf); prev_v.addWidget(vb)
        cl.addLayout(prev_v)

        # Right controls
        ctrl = QVBoxLayout(); ctrl.setSpacing(10)

        # Model
        ml = QLabel("Skin Modeli"); ml.setStyleSheet("color:#9CA3AF;font-size:11px;font-weight:700;letter-spacing:0.5px;background:transparent;border:none;")
        self.radio_steve = QRadioButton("Classic (Steve)")
        self.radio_alex  = QRadioButton("Slim (Alex)")
        for r in [self.radio_steve, self.radio_alex]:
            r.setStyleSheet("color:#D1D5DB;font-size:12px;")
        self.radio_steve.setChecked(True)
        self.radio_steve.toggled.connect(self.on_skin_model_changed)
        model_row = QHBoxLayout(); model_row.addWidget(self.radio_steve); model_row.addWidget(self.radio_alex)

        skin_btn = self._btn_primary("🖼  Skin Yuklash (.png)"); skin_btn.clicked.connect(self.choose_skin_file)

        cape_lbl = QLabel("Plashch (Cape)"); cape_lbl.setStyleSheet("color:#9CA3AF;font-size:11px;font-weight:700;letter-spacing:0.5px;background:transparent;border:none;")
        self.combo_preset_cape = self._combo()
        self.combo_preset_cape.addItem("⭐ Nova Launcher Gold Cape", "preset_nova")
        self.combo_preset_cape.addItem("👑 Royal Crown Cape",       "preset_admin")
        self.combo_preset_cape.addItem("🧊 OptiFine Red Cape",      "preset_optifine")
        self.combo_preset_cape.addItem("🔥 Minecon Creeper Cape",   "preset_minecon")
        self.combo_preset_cape.currentIndexChanged.connect(self.on_preset_cape_changed)

        cape_btn = self._btn_success("🧥  Shaxsiy Plashch Yuklash"); cape_btn.clicked.connect(self.choose_cape_file)
        reset_btn = self._btn_danger("🔄  Standartga Qaytarish"); reset_btn.clicked.connect(self.reset_skin_and_cape)

        for w in [ml, model_row if False else self.radio_steve, self.radio_alex,
                  skin_btn, cape_lbl, self.combo_preset_cape, cape_btn, reset_btn]:
            if isinstance(w, QWidget): ctrl.addWidget(w)
        ctrl.addLayout(model_row)
        ctrl.addWidget(skin_btn); ctrl.addWidget(cape_lbl)
        ctrl.addWidget(self.combo_preset_cape); ctrl.addWidget(cape_btn); ctrl.addWidget(reset_btn)
        ctrl.addStretch()
        cl.addLayout(ctrl, 1)
        layout.addWidget(card); layout.addStretch()
        return page

    def toggle_skin_view(self, is_back): self.skin_view_back=is_back; self.update_skin_and_cape_preview()

    def update_skin_and_cape_preview(self):
        acc=self.acc_mgr.get_active_account()
        pix=SkinManager.render_avatar(acc.get("skin_path",""),acc.get("cape_path","preset_nova"),
                                       is_alex=acc.get("is_alex",False),view_back=self.skin_view_back)
        self.lbl_avatar_preview.setPixmap(pix)

    def choose_skin_file(self):
        path,_=QFileDialog.getOpenFileName(self,"Skin faylini tanlang","","Images (*.png)")
        if path:
            acc=self.acc_mgr.get_active_account(); user=acc.get("username","O'yinchi")
            self.acc_mgr.update_skin(user,path,is_alex=self.radio_alex.isChecked())
            self.update_skin_and_cape_preview(); self.show_toast("Skin saqlandi!")

    def choose_cape_file(self):
        path,_=QFileDialog.getOpenFileName(self,"Plashch faylini tanlang","","Images (*.png)")
        if path:
            acc=self.acc_mgr.get_active_account(); user=acc.get("username","O'yinchi")
            self.acc_mgr.update_cape(user,path); self.update_skin_and_cape_preview(); self.show_toast("Plashch saqlandi!")

    def on_preset_cape_changed(self):
        d=self.combo_preset_cape.currentData()
        if d:
            acc=self.acc_mgr.get_active_account(); self.acc_mgr.update_cape(acc.get("username","admin"),d)
            self.update_skin_and_cape_preview()

    def on_skin_model_changed(self):
        acc=self.acc_mgr.get_active_account(); user=acc.get("username","admin")
        self.acc_mgr.update_skin(user,acc.get("skin_path",""),is_alex=self.radio_alex.isChecked())
        self.update_skin_and_cape_preview()

    def reset_skin_and_cape(self):
        acc=self.acc_mgr.get_active_account(); user=acc.get("username","admin")
        self.acc_mgr.update_skin(user,"",is_alex=False); self.acc_mgr.update_cape(user,"preset_nova")
        self.update_skin_and_cape_preview()

    # ── MODS PAGE ──────────────────────────────────────────
    def create_page_mods(self):
        page = QWidget(); page.setStyleSheet("background:transparent;")
        layout = QVBoxLayout(page); layout.setContentsMargins(24,20,24,20); layout.setSpacing(12)
        layout.addWidget(self._section_head("Modrinth Kontent Markazi", "Mod, sheyder, resurs paket va xaritalarni qidiring"))

        # Search bar
        search_card = self._card()
        sc = QHBoxLayout(search_card); sc.setContentsMargins(12,10,12,10); sc.setSpacing(8)

        self.combo_content_type = self._combo()
        self.combo_content_type.setFixedWidth(160)
        for txt, val in [("🧩 Modlar","mod"),("🎨 Resurs Paketlar","resourcepack"),
                          ("✨ Sheyderlar","shader"),("📜 Datapacklar","datapack"),
                          ("📦 Modpacklar","modpack"),("🗺️ Xaritalar","map")]:
            self.combo_content_type.addItem(txt,val)
        self.combo_content_type.currentIndexChanged.connect(self.on_content_type_changed)

        self.txt_mod_search = self._input("Mod nomini kiriting (Sodium, WorldEdit, Iris...)...")
        self.txt_mod_search.returnPressed.connect(self.perform_mod_search)

        self.combo_loader_filter = self._combo()
        self.combo_loader_filter.setFixedWidth(120)
        self.combo_loader_filter.addItem("⚡ Fabric","fabric"); self.combo_loader_filter.addItem("🔥 Forge","forge"); self.combo_loader_filter.addItem("🌐 Barchasi","")

        btn_search = self._btn_primary("🔍  Qidirish"); btn_search.setFixedWidth(110); btn_search.clicked.connect(self.perform_mod_search)
        btn_inst   = self._btn_ghost("📋  O'rnatilganlar"); btn_inst.setFixedWidth(140); btn_inst.clicked.connect(self.show_installed_content_dialog)

        sc.addWidget(self.combo_content_type); sc.addWidget(self.txt_mod_search,1)
        sc.addWidget(self.combo_loader_filter); sc.addWidget(btn_search); sc.addWidget(btn_inst)
        layout.addWidget(search_card)

        self.mod_results_scroll = QScrollArea(); self.mod_results_scroll.setWidgetResizable(True)
        self.mod_results_scroll.setStyleSheet("background:transparent;border:none;")
        self.mod_results_container = QWidget(); self.mod_results_container.setStyleSheet("background:transparent;")
        self.mod_results_layout = QVBoxLayout(self.mod_results_container); self.mod_results_layout.setSpacing(8)
        self.mod_results_scroll.setWidget(self.mod_results_container)
        layout.addWidget(self.mod_results_scroll)
        return page

    def on_content_type_changed(self):
        ptype = self.combo_content_type.currentData() if hasattr(self,'combo_content_type') else "mod"
        ph = {"mod":"Mod nomini kiriting...","resourcepack":"Resurs paket nomini kiriting...","shader":"Sheyder nomini kiriting...","datapack":"Datapack nomini kiriting...","modpack":"Modpack nomini kiriting...","map":"Xarita nomini kiriting..."}
        self.txt_mod_search.setPlaceholderText(ph.get(ptype,"Qidiruv...")); self.perform_mod_search()

    def perform_mod_search(self):
        query = self.txt_mod_search.text().strip()
        for i in reversed(range(self.mod_results_layout.count())):
            item=self.mod_results_layout.itemAt(i)
            if item.widget(): item.widget().deleteLater()
        ptype = self.combo_content_type.currentData() if hasattr(self,'combo_content_type') else "mod"
        lbl = QLabel("🔍  Modrinth-dan qidirilmoqda...")
        lbl.setStyleSheet("color:#6B7280;font-size:13px;margin:20px;background:transparent;border:none;")
        self.mod_results_layout.addWidget(lbl)
        clean_ver = self.get_selected_clean_version()
        loader_val = self.combo_loader_filter.currentData() if hasattr(self,'combo_loader_filter') else "fabric"
        self.mod_search_worker = ModrinthSearchWorker(query=query,game_version=clean_ver,loader=loader_val,project_type=ptype)
        self.mod_search_worker.results_signal.connect(self.display_mod_results)
        self.mod_search_worker.start()

    def display_mod_results(self, hits):
        for i in reversed(range(self.mod_results_layout.count())):
            item=self.mod_results_layout.itemAt(i)
            if item.widget(): item.widget().deleteLater()
        if not hits:
            lbl=QLabel("Hech qanday kontent topilmadi.")
            lbl.setStyleSheet("color:#4B5563;font-size:13px;margin:20px;background:transparent;border:none;")
            self.mod_results_layout.addWidget(lbl); return
        for hit in hits: self.mod_results_layout.addWidget(self.create_modrinth_hit_card(hit))
        self.mod_results_layout.addStretch()

    def create_modrinth_hit_card(self, hit):
        frame = self._card()
        layout = QHBoxLayout(frame); layout.setContentsMargins(14,12,14,12); layout.setSpacing(14)

        icon_label=QLabel(); icon_label.setFixedSize(52,52); icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:10px;font-size:24px;color:#9CA3AF;")

        ptype=hit.get("project_type","mod")
        type_emojis={"mod":"🧩","resourcepack":"🎨","shader":"✨","datapack":"📜","modpack":"📦","map":"🗺️"}
        icon_url=hit.get("icon_url")
        if icon_url:
            t=ImageLoaderThread(icon_label,icon_url); t.loaded_signal.connect(lambda lbl,px:lbl.setPixmap(px)); t.start(); self.img_threads.append(t)
        else: icon_label.setText(type_emojis.get(ptype,"🧩"))
        layout.addWidget(icon_label)

        vbox=QVBoxLayout(); vbox.setSpacing(4)
        t_row=QHBoxLayout(); t_row.setSpacing(8)
        title_lbl=QLabel(hit.get("title","Nomsiz")); title_lbl.setStyleSheet("color:#F9FAFB;font-weight:700;font-size:14px;background:transparent;border:none;")
        type_badge=make_badge(ptype.upper(),"rgba(255,255,255,0.1)","#9CA3AF")
        dl=hit.get("downloads",0); dl_badge=make_badge(f"📥 {dl:,}","rgba(0,210,220,0.1)","#00D2DC")
        t_row.addWidget(title_lbl); t_row.addWidget(type_badge); t_row.addWidget(dl_badge); t_row.addStretch()
        desc_lbl=QLabel(hit.get("description","")[:120]); desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color:#6B7280;font-size:11px;background:transparent;border:none;")
        vbox.addLayout(t_row); vbox.addWidget(desc_lbl)
        layout.addLayout(vbox,1)

        slug=hit.get("slug") or hit.get("project_id")
        btn=self._btn_primary("⬇  O'rnatish"); btn.setFixedWidth(110)
        btn.clicked.connect(lambda: self.download_modrinth_content(slug,ptype,btn))
        layout.addWidget(btn)
        return frame

    def get_active_profile_dir(self):
        gdir=self.cfg.get("game_dir")
        sel_ver=self.combo_version.currentText() if hasattr(self,'combo_version') and self.combo_version else self.cfg.get("selected_version","Fabric 1.21.1")
        clean_ver=sel_ver.replace("⚡","").replace("🔥","").replace("🧊","").replace("🛡️","").replace("🪶","").replace("🟩","").replace("🧪","").replace("📜","").strip()
        safe_name=clean_ver.replace(" ","_").replace(":","_").replace("/","_")
        pdir=os.path.join(gdir,"profiles",safe_name); os.makedirs(pdir,exist_ok=True)
        for sub in ["mods","resourcepacks","shaderpacks","datapacks","saves","modpacks"]: os.makedirs(os.path.join(pdir,sub),exist_ok=True)
        return pdir

    def download_modrinth_content(self, slug_or_id, project_type, btn_widget):
        pdir=self.get_active_profile_dir()
        tf={"mod":os.path.join(pdir,'mods'),"resourcepack":os.path.join(pdir,'resourcepacks'),"shader":os.path.join(pdir,'shaderpacks'),"datapack":os.path.join(pdir,'datapacks'),"modpack":os.path.join(pdir,'modpacks'),"map":os.path.join(pdir,'saves')}
        target_dir=tf.get(project_type,os.path.join(pdir,'mods'))
        clean_ver=self.get_selected_clean_version()
        loader_val=self.combo_loader_filter.currentData() if hasattr(self,'combo_loader_filter') else "fabric"
        btn_widget.setEnabled(False); btn_widget.setText("Yuklanmoqda...")
        self.mod_dl_worker=ModrinthDownloadWorker(project_id=slug_or_id,target_dir=target_dir,game_version=clean_ver,loader=loader_val,project_type=project_type)
        self.mod_dl_worker.status_signal.connect(self.lbl_status.setText)
        self.mod_dl_worker.finished_signal.connect(lambda ok,msg: self.on_modrinth_dl_finished(ok,msg,btn_widget))
        self.mod_dl_worker.start()

    def on_modrinth_dl_finished(self, ok, msg, btn_widget):
        if btn_widget: btn_widget.setEnabled(True); btn_widget.setText("✓ O'rnatildi" if ok else "⬇ Qayta")
        self.lbl_status.setText(msg); self.log(f"[Modrinth] {msg}"); self.show_toast(msg,is_error=not ok)

    def show_installed_content_dialog(self):
        pdir=self.get_active_profile_dir()
        folders={"🧩 Modlar":os.path.join(pdir,'mods'),"🎨 Resurs":os.path.join(pdir,'resourcepacks'),"✨ Sheyderlar":os.path.join(pdir,'shaderpacks'),"📜 Datapacks":os.path.join(pdir,'datapacks'),"📦 Modpacks":os.path.join(pdir,'modpacks'),"🗺️ Xaritalar":os.path.join(pdir,'saves')}
        lines=[]
        for label,path in folders.items():
            os.makedirs(path,exist_ok=True); lines.append(f"• {label}: {len(os.listdir(path))} ta fayl")
        msg=QMessageBox(self); msg.setWindowTitle("O'rnatilgan Kontentlar"); msg.setText("Joriy profil:\n\n"+"\n".join(lines)); msg.exec()

    # ── SETTINGS PAGE ──────────────────────────────────────
    def create_page_settings(self):
        page = QWidget(); page.setStyleSheet("background:transparent;")
        layout = QVBoxLayout(page); layout.setContentsMargins(24,20,24,20); layout.setSpacing(12)
        layout.addWidget(self._section_head("Sozlamalar", "Launcher konfiguratsiyasini boshqaring"))

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background:transparent;border:none;QScrollBar:vertical{background:rgba(255,255,255,0.04);width:5px;border-radius:3px;}QScrollBar::handle:vertical{background:rgba(255,255,255,0.15);border-radius:3px;}")
        container = QWidget(); container.setStyleSheet("background:transparent;")
        cl = QVBoxLayout(container); cl.setSpacing(12)

        # RAM
        ram_card = self._card()
        rl = QVBoxLayout(ram_card); rl.setContentsMargins(18,16,18,16); rl.setSpacing(8)
        ram_head = QHBoxLayout()
        ram_title = QLabel("🖥  Operativ Xotira (RAM)"); ram_title.setStyleSheet("color:#F9FAFB;font-size:13px;font-weight:700;background:transparent;border:none;")
        self.lbl_ram_val = QLabel("4096 MB"); self.lbl_ram_val.setStyleSheet("color:#00D2DC;font-size:13px;font-weight:700;background:transparent;border:none;")
        ram_head.addWidget(ram_title); ram_head.addStretch(); ram_head.addWidget(self.lbl_ram_val)
        total_ram_gb=int(psutil.virtual_memory().total/(1024**3)); max_ram_mb=max(8192,total_ram_gb*1024)
        self.slider_ram = QSlider(Qt.Orientation.Horizontal)
        self.slider_ram.setRange(1024,max_ram_mb); self.slider_ram.setSingleStep(512); self.slider_ram.setPageStep(1024)
        self.slider_ram.setStyleSheet("QSlider::groove:horizontal{background:rgba(255,255,255,0.1);height:4px;border-radius:2px;}QSlider::handle:horizontal{background:#00D2DC;width:16px;height:16px;margin:-6px 0;border-radius:8px;}QSlider::sub-page:horizontal{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00D2DC,stop:1 #0096C7);border-radius:2px;}")
        self.slider_ram.valueChanged.connect(self.on_ram_slider_change)
        rl.addLayout(ram_head); rl.addWidget(self.slider_ram); cl.addWidget(ram_card)

        # Java
        java_card = self._card()
        jl = QVBoxLayout(java_card); jl.setContentsMargins(18,16,18,16); jl.setSpacing(8)
        jl.addWidget(QLabel("☕  Java Joylashuvi").__setattr__('styleSheet',"") or self._lbl("☕  Java Joylashuvi"))
        self.txt_java_path = self._input("C:\\Program Files\\Java\\jdk-23\\bin\\javaw.exe")
        btn_java = self._btn_ghost("Tanlash..."); btn_java.setFixedWidth(100); btn_java.clicked.connect(self.browse_java_path)
        jr = QHBoxLayout(); jr.addWidget(self.txt_java_path,1); jr.addWidget(btn_java)
        jl.addLayout(jr); cl.addWidget(java_card)

        # Game dir
        dir_card = self._card()
        dl = QVBoxLayout(dir_card); dl.setContentsMargins(18,16,18,16); dl.setSpacing(8)
        dl.addWidget(self._lbl("📁  O'yin Papkasi (.novalauncher)"))
        self.txt_game_dir = self._input("O'yin papkasi manzili")
        btn_dir = self._btn_ghost("Tanlash..."); btn_dir.setFixedWidth(100); btn_dir.clicked.connect(self.browse_game_dir)
        dr = QHBoxLayout(); dr.addWidget(self.txt_game_dir,1); dr.addWidget(btn_dir)
        dl.addLayout(dr); cl.addWidget(dir_card)

        # Advanced
        adv_card = self._card()
        al = QVBoxLayout(adv_card); al.setContentsMargins(18,16,18,16); al.setSpacing(10)
        al.addWidget(self._lbl("🔧  Qo'shimcha Parametrlar"))
        self.chk_auto_close = QCheckBox("O'yin boshlanganda launcher yopilsin")
        self.chk_auto_close.setStyleSheet("color:#9CA3AF;font-size:12px;")
        self.chk_show_snapshots = QCheckBox("Snapshot va eski versiyalarni ko'rsatish")
        self.chk_show_snapshots.setStyleSheet("color:#9CA3AF;font-size:12px;")
        self.chk_show_snapshots.stateChanged.connect(self.populate_versions)
        al.addWidget(self._lbl("JVM Argumentlari:"))
        self.txt_jvm_args = self._input("JVM Arguments (-XX:+UseG1GC)")
        al.addWidget(self.chk_auto_close); al.addWidget(self.chk_show_snapshots); al.addWidget(self.txt_jvm_args)
        cl.addWidget(adv_card)

        # Windows buttons
        win_card = self._card()
        wl = QVBoxLayout(win_card); wl.setContentsMargins(18,16,18,16); wl.setSpacing(8)
        wl.addWidget(self._lbl("🪟  Windows Boshqaruvi"))
        b1=self._btn_primary("📌  Desktop Yorliq Yaratish"); b1.clicked.connect(self.create_desktop_shortcut)
        b2=self._btn_primary("📥  Setup O'rnatgichni Ishga Tushirish","#7C3AED","#6D28D9"); b2.clicked.connect(self.launch_setup_wizard)
        b3=self._btn_danger("🗑  NovaLauncher-ni O'chirish"); b3.clicked.connect(self.uninstall_launcher)
        b4=self._btn_danger("🧹  Sozlamalarni Standartga Qaytarish"); b4.clicked.connect(self.reset_settings_to_defaults)
        for b in [b1,b2,b3,b4]: wl.addWidget(b)
        cl.addWidget(win_card); cl.addStretch()

        scroll.setWidget(container); layout.addWidget(scroll,1)

        save_btn=self._btn_primary("💾  Sozlamalarni Saqlash"); save_btn.clicked.connect(self.save_settings_from_ui)
        layout.addWidget(save_btn)
        return page

    def _lbl(self, text, color="#9CA3AF", size=12):
        l=QLabel(text); l.setStyleSheet(f"color:{color};font-size:{size}px;font-weight:700;background:transparent;border:none;"); return l

    def reset_settings_to_defaults(self):
        r=QMessageBox.question(self,"Sozlamalarni o'chirish","Barcha sozlamalar standartga qaytarilsinmi?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if r==QMessageBox.StandardButton.Yes:
            self.cfg.reset_to_defaults(); self.load_settings_to_ui(); self.populate_versions()
            QMessageBox.information(self,"Qayta tiklandi","Muvaffaqiyatli!")

    def uninstall_launcher(self):
        mb=QMessageBox(self); mb.setWindowTitle("NovaLauncher-ni O'chirish"); mb.setText("NovaLauncher-ni o'chirishni tasdiqlaysizmi?")
        mb.setStandardButtons(QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        chk=QCheckBox("O'yin fayllari va dunyolarini ham o'chirish"); mb.setCheckBox(chk)
        if mb.exec()==QMessageBox.StandardButton.Yes:
            ok,msg=ShortcutInstaller.uninstall_novalauncher(remove_game_data=chk.isChecked())
            if ok: QMessageBox.information(self,"O'chirildi",msg); self.close()
            else: QMessageBox.warning(self,"Xatolik",msg)

    # ── ADMIN PAGE ──────────────────────────────────────────
    def create_page_admin(self):
        page = QWidget(); page.setStyleSheet("background:transparent;")
        layout = QVBoxLayout(page); layout.setContentsMargins(24,20,24,20); layout.setSpacing(12)
        layout.addWidget(self._section_head("👑 Admin Boshqaruv Paneli"))
        self.lbl_admin_status = QLabel("Holat tekshirilmoqda...")
        self.lbl_admin_status.setStyleSheet("color:#6B7280;font-size:12px;background:transparent;border:none;")
        layout.addWidget(self.lbl_admin_status)
        self.table_users = QTableWidget()
        self.table_users.setColumnCount(4)
        self.table_users.setHorizontalHeaderLabels(["Nikneym","Maqomi","Skin","Plashch"])
        self.table_users.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_users.setStyleSheet("QTableWidget{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);color:#E5E7EB;gridline-color:rgba(255,255,255,0.06);border-radius:8px;}QHeaderView::section{background:rgba(255,255,255,0.06);color:#9CA3AF;font-weight:700;border:none;padding:8px;}QTableWidget::item:selected{background:rgba(0,210,220,0.15);}")
        layout.addWidget(self.table_users)
        btn_row=QHBoxLayout()
        bd=self._btn_danger("🗑  O'chirish"); bd.clicked.connect(self.delete_selected_user)
        br=self._btn_ghost("🔄  Yangilash"); br.clicked.connect(self.refresh_admin_panel)
        btn_row.addWidget(bd); btn_row.addWidget(br); layout.addLayout(btn_row)
        return page

    def refresh_admin_panel(self):
        acc=self.acc_mgr.get_active_account(); is_admin=acc.get("role")=="Admin" or acc.get("username")=="admin"
        if not is_admin: self.lbl_admin_status.setText("Admin akkauntida emassiz."); self.table_users.setRowCount(0); return
        self.lbl_admin_status.setText("✅ Admin. Barcha foydalanuvchilar:")
        users=self.acc_mgr.get_all_accounts(); self.table_users.setRowCount(len(users))
        for row,(u,d) in enumerate(users.items()):
            self.table_users.setItem(row,0,QTableWidgetItem(u)); self.table_users.setItem(row,1,QTableWidgetItem(d.get("display_role","User")))
            self.table_users.setItem(row,2,QTableWidgetItem("Slim (Alex)" if d.get("is_alex") else "Classic (Steve)"))
            self.table_users.setItem(row,3,QTableWidgetItem(d.get("cape_path","—")))

    def delete_selected_user(self):
        acc=self.acc_mgr.get_active_account()
        if acc.get("username")!="admin": QMessageBox.warning(self,"Ruxsat yo'q","Admin akkounti talab qilinadi!"); return
        r=self.table_users.currentRow()
        if r<0: QMessageBox.warning(self,"Tanlanmagan","Foydalanuvchini tanlang!"); return
        u=self.table_users.item(r,0).text()
        if QMessageBox.question(self,"Tasdiqlash",f"'{u}'ni o'chirishni tasdiqlaysizmi?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes:
            ok,msg=self.acc_mgr.delete_account(u)
            if ok: self.refresh_admin_panel(); self.refresh_account_dropdown()
            else: QMessageBox.warning(self,"Xatolik",msg)

    # ── LOGS PAGE ──────────────────────────────────────────
    def create_page_logs(self):
        page = QWidget(); page.setStyleSheet("background:transparent;")
        layout = QVBoxLayout(page); layout.setContentsMargins(24,20,24,20); layout.setSpacing(12)
        layout.addWidget(self._section_head("Konsol Loglar", "O'yin jarayoni va xatolar"))
        self.txt_log = QTextEdit(); self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("background:rgba(0,0,0,0.6);color:#00D2DC;font-family:'Consolas','Courier New',monospace;font-size:12px;border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:12px;")
        layout.addWidget(self.txt_log)
        cb=self._btn_ghost("🧹  Loglarni Tozalash"); cb.clicked.connect(self.txt_log.clear); layout.addWidget(cb)
        return page

    # ── PAGE NAVIGATION ─────────────────────────────────────
    def update_admin_visibility(self):
        acc=self.acc_mgr.get_active_account(); is_admin=acc.get("role")=="Admin"
        self.nav_buttons[5][0].setVisible(is_admin or acc.get("username")=="admin")
        if hasattr(self,'admin_info_box'): self.admin_info_box.setVisible(is_admin)

    def switch_page(self, index):
        acc=self.acc_mgr.get_active_account(); is_admin=acc.get("role")=="Admin" or acc.get("username")=="admin"
        if index==5 and not is_admin: QMessageBox.warning(self,"Ruxsat etilmadi","Admin paneli faqat Admin uchun!"); return
        target=self.pages_stacked.widget(index)
        if target:
            eff=QGraphicsOpacityEffect(target); target.setGraphicsEffect(eff)
            anim=QPropertyAnimation(eff,b"opacity"); anim.setDuration(200); anim.setStartValue(0.1); anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic); anim.start(); self.anim_holder=anim
        self.pages_stacked.setCurrentIndex(index)
        self._set_nav_active(index)
        if index==2: self.update_skin_and_cape_preview()
        elif index==3: QTimer.singleShot(100, self.perform_mod_search)
        elif index==5: self.refresh_admin_panel()

    # ── ACCOUNT MANAGEMENT ──────────────────────────────────
    def refresh_account_dropdown(self):
        self.combo_accounts.blockSignals(True); self.combo_accounts.clear()
        users=self.acc_mgr.get_all_accounts(); active_acc=self.acc_mgr.get_active_account(); active_name=active_acc.get("username","O'yinchi")
        for u,d in users.items(): self.combo_accounts.addItem(f"{'👑' if d.get('role')=='Admin' else '🎮'} {u}",u)
        self.combo_accounts.addItem("➕ Akkaunt Qo'shish...","__add_new__")
        idx=self.combo_accounts.findData(active_name)
        if idx>=0: self.combo_accounts.setCurrentIndex(idx)
        self.combo_accounts.blockSignals(False)
        self.lbl_auth_username.setText(f"Foydalanuvchi: {active_name}")
        self.lbl_auth_role.setText(f"Maqomi: {active_acc.get('display_role','Offlayn')}")
        self.sidebar_username.setText(active_name)
        self.bottom_username.setText(active_name)
        self.update_admin_visibility()

    def on_account_selected(self):
        d=self.combo_accounts.currentData()
        if d=="__add_new__": self.open_login_modal()
        elif d:
            self.acc_mgr.set_active_username(d); acc=self.acc_mgr.get_active_account()
            self.lbl_auth_username.setText(f"Foydalanuvchi: {d}")
            self.lbl_auth_role.setText(f"Maqomi: {acc.get('display_role','Offlayn')}")
            self.sidebar_username.setText(d); self.bottom_username.setText(d)
            self.update_skin_and_cape_preview(); self.update_admin_visibility()

    def on_accounts_chk_changed(self): self.combo_accounts.setEnabled(self.chk_accounts_enable.isChecked())

    def open_login_modal(self):
        modal=LoginRegisterModal(self.acc_mgr,self); modal.exec()
        self.refresh_account_dropdown(); self.update_skin_and_cape_preview(); self.update_admin_visibility()

    # ── VERSION MANAGEMENT ──────────────────────────────────
    def populate_versions(self):
        show_snaps=hasattr(self,'chk_show_snapshots') and self.chk_show_snapshots.isChecked()
        self.combo_version.blockSignals(True); self.combo_version.clear()
        for fv in VersionManager.get_fabric_mc_versions(): self.combo_version.addItem(f"⚡ Fabric {fv}",f"Fabric {fv}")
        for mc_v,f_v in VersionManager.get_popular_forge_versions(): self.combo_version.addItem(f"🔥 Forge {mc_v}",f"Forge {mc_v}")
        for ov in VersionManager.get_popular_optifine_versions(): self.combo_version.addItem(f"🧊 OptiFine {ov}",f"OptiFine {ov}")
        for nv in VersionManager.get_neoforge_versions(): self.combo_version.addItem(f"🛡️ NeoForge {nv}",f"NeoForge {nv}")
        for qv in VersionManager.get_quilt_versions(): self.combo_version.addItem(f"🪶 Quilt {qv}",f"Quilt {qv}")
        releases,snapshots,old_vers=VersionManager.get_all_minecraft_versions(show_snaps,True)
        for r in releases: self.combo_version.addItem(f"🟩 Vanilla {r}",f"Vanilla {r}")
        for o in old_vers: self.combo_version.addItem(f"📜 Old {o}",f"Vanilla {o}")
        if show_snaps:
            for s in snapshots: self.combo_version.addItem(f"🧪 Snapshot {s}",f"Vanilla {s}")
        self.combo_version.blockSignals(False)
        saved=self.cfg.get("selected_version","Fabric 1.21.1"); idx=self.combo_version.findData(saved)
        if idx>=0: self.combo_version.setCurrentIndex(idx)

    def on_version_changed(self):
        sel=self.combo_version.currentData()
        if sel: self.cfg.set("selected_version",sel)

    def get_selected_clean_version(self):
        sel=(self.combo_version.currentData() if hasattr(self,'combo_version') and self.combo_version else None) or self.cfg.get("selected_version","Fabric 1.21.1")
        for t in ["⚡","🔥","🧊","🛡️","🪶","🟩","🧪","📜","Fabric","Forge","OptiFine","NeoForge","Quilt","Vanilla","Old"]: sel=sel.replace(t,"")
        return sel.strip()

    # ── SETTINGS LOGIC ──────────────────────────────────────
    def load_settings_to_ui(self):
        ram=self.cfg.get("ram_mb",4096); self.slider_ram.setValue(ram); self.lbl_ram_val.setText(f"{ram} MB ({round(ram/1024,1)} GB)")
        self.txt_java_path.setText(self.cfg.get("java_path","")); self.txt_game_dir.setText(self.cfg.get("game_dir",""))
        self.chk_auto_close.setChecked(self.cfg.get("auto_close",False)); self.chk_show_snapshots.setChecked(self.cfg.get("show_snapshots",False))
        self.txt_jvm_args.setText(self.cfg.get("jvm_args","-XX:+UseG1GC"))

    def save_settings_from_ui(self):
        self.cfg.set("ram_mb",self.slider_ram.value()); self.cfg.set("java_path",self.txt_java_path.text().strip())
        self.cfg.set("game_dir",self.txt_game_dir.text().strip()); self.cfg.set("auto_close",self.chk_auto_close.isChecked())
        self.cfg.set("show_snapshots",self.chk_show_snapshots.isChecked()); self.cfg.set("jvm_args",self.txt_jvm_args.text().strip())
        self.show_toast("Sozlamalar saqlandi!")

    def create_desktop_shortcut(self): ok,msg=ShortcutInstaller.create_desktop_shortcut(); self.show_toast(msg,is_error=not ok)
    def launch_setup_wizard(self):
        exe=os.path.abspath("NovaLauncherSetup.exe")
        subprocess.Popen(exe) if os.path.exists(exe) else subprocess.Popen([sys.executable,"installer_gui.py"])
    def on_ram_slider_change(self,val): self.lbl_ram_val.setText(f"{val} MB ({round(val/1024,1)} GB)")
    def browse_java_path(self):
        f,_=QFileDialog.getOpenFileName(self,"javaw.exe tanlang","","Executables (*.exe);;All Files (*)")
        if f: self.txt_java_path.setText(f)
    def browse_game_dir(self):
        d=QFileDialog.getExistingDirectory(self,"O'yin papkasini tanlang",self.txt_game_dir.text())
        if d: self.txt_game_dir.setText(d)
    def open_mods_folder(self): pdir=self.get_active_profile_dir(); os.makedirs(pdir,exist_ok=True); os.startfile(pdir)
    def log(self,text): self.txt_log.append(text)

    # ── LAUNCH ──────────────────────────────────────────────
    def on_launch_clicked(self):
        acc=self.acc_mgr.get_active_account(); username=acc.get("username","O'yinchi")
        selected_version=self.combo_version.currentData() or "Fabric 1.21.1"
        self.cfg.set("selected_version",selected_version); self.cfg.set("username",username)
        self.btn_launch.setEnabled(False); self.btn_launch.setText("⏳  Yuklanmoqda...")
        self.lbl_status.setText("O'rnatish tekshirilmoqda...")
        self.log(f"[Nova] Foydalanuvchi: {username} | Versiya: {selected_version}")
        self.install_worker=InstallWorker(version_str=selected_version,game_dir=self.cfg.get("game_dir"))
        self.install_worker.status_signal.connect(self.on_install_status)
        self.install_worker.progress_signal.connect(self.on_install_progress)
        self.install_worker.finished_signal.connect(self.on_install_finished)
        self.install_worker.start()

    def on_install_status(self,text): self.lbl_status.setText(text); self.log(f"[O'rnatish] {text}")
    def on_install_progress(self,curr,max_v,text):
        pct=int((curr/max_v)*100) if max_v>0 else 0
        self.progress_bar.setValue(pct)

    def on_install_finished(self,success,msg):
        if not success:
            QMessageBox.critical(self,"Xatolik",msg); self.btn_launch.setEnabled(True)
            self.btn_launch.setText("▶  O'YINGA KIRISH"); self.lbl_status.setText("Xatolik yuz berdi"); return
        self.lbl_status.setText("O'yin ishga tushirilmoqda...")
        self.log("[Nova] Minecraft boshlanmoqda...")
        selected_version=self.combo_version.currentData() or "Fabric 1.21.1"
        self.launch_worker=LaunchWorker(self.cfg,version_str=selected_version)
        self.launch_worker.log_signal.connect(self.log)
        self.launch_worker.started_signal.connect(self.on_game_started)
        self.launch_worker.finished_signal.connect(self.on_game_finished)
        self.launch_worker.start()

    def on_game_started(self):
        self.lbl_status.setText("O'yin ishlamoqda! 🎮"); self.progress_bar.setValue(100)
        self.log("[Nova] Minecraft muvaffaqiyatli ishga tushirildi!")
        self.bottom_status_lbl.setText("🎮 O'yin ishlamoqda")
        self.sidebar_status.setText("🎮 O'yin ishlamoqda")
        if self.cfg.get("auto_close"): self.close()

    def on_game_finished(self,code,msg):
        self.btn_launch.setEnabled(True); self.btn_launch.setText("▶  O'YINGA KIRISH")
        self.lbl_status.setText("O'yin yakunlandi"); self.log(f"[Nova] {msg}")
        self.bottom_status_lbl.setText("O'ynashga tayyor"); self.sidebar_status.setText("O'ynashga tayyor")

    def closeEvent(self,event):
        try:
            if hasattr(self,'combo_version') and self.combo_version:
                sel=self.combo_version.currentData()
                if sel: self.cfg.set("selected_version",sel)
            if hasattr(self,'acc_mgr') and self.acc_mgr:
                acc=self.acc_mgr.get_active_account(); u=acc.get("username","")
                if u and u!="O'yinchi": self.acc_mgr.set_active_username(u); self.cfg.set("username",u)
                self.acc_mgr.save()
            self.cfg.save()
        except Exception as e: print(f"Close save error: {e}")
        event.accept()


# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)

    if "--uninstall" in sys.argv or "-uninstall" in sys.argv:
        from shortcut_installer import ShortcutInstaller
        reply=QMessageBox.question(None,"NovaLauncher — O'chirish","NovaLauncher-ni o'chirishni xohlaysizmi?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
        if reply==QMessageBox.StandardButton.Yes:
            del_d=QMessageBox.question(None,"O'yin Ma'lumotlari","O'yin ma'lumotlarini ham o'chirasizmi?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
            ok,msg=ShortcutInstaller.uninstall_novalauncher(remove_game_data=(del_d==QMessageBox.StandardButton.Yes))
            install_dir=os.path.dirname(os.path.abspath(sys.executable if getattr(sys,'frozen',False) else __file__))
            subprocess.Popen(f'cmd.exe /c timeout /t 2 /nobreak & rmdir /s /q "{install_dir}"',shell=True)
            if ok: QMessageBox.information(None,"Muvaffaqiyatli","NovaLauncher o'chirib tashlandi!")
            else: QMessageBox.warning(None,"Xatolik",f"Xatolik: {msg}")
        sys.exit(0)

    launcher = NovaLauncher()
    launcher.show()
    sys.exit(app.exec())
