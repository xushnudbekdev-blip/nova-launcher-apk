import os
import sys
import shutil
import time
import subprocess
import json
from datetime import datetime
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QProgressBar, QStackedWidget,
    QFileDialog, QMessageBox, QCheckBox
)


class InstallTaskWorker(QThread):
    progress_signal = pyqtSignal(int, str)
    # finished_signal emits (success: bool, payload: object)
    finished_signal = pyqtSignal(bool, object)

    def __init__(self, target_dir, create_desktop_sc=True, create_start_sc=True):
        super().__init__()
        self.target_dir = target_dir
        self.create_desktop_sc = create_desktop_sc
        self.create_start_sc = create_start_sc

    def run(self):
        try:
            self.progress_signal.emit(10, "O'rnatish papkasi yaratilmoqda...")
            os.makedirs(self.target_dir, exist_ok=True)

            self.progress_signal.emit(30, "Ilova fayllari nusxalanmoqda...")
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            curr_dir = os.getcwd()

            # Find NovaLauncher.exe only from bundled base_dir (avoid reading arbitrary working dir)
            exe_candidates = [
                os.path.join(base_dir, "NovaLauncher.exe"),
                os.path.join(base_dir, "dist", "NovaLauncher.exe"),
            ]

            target_exe = os.path.join(self.target_dir, "NovaLauncher.exe")
            copied_exe = False
            copied_files = []
            failed_files = []

            for cand in exe_candidates:
                if os.path.exists(cand):
                    ok, err = self.safe_copy(cand, target_exe)
                    if ok:
                        copied_exe = True
                        copied_files.append(target_exe)
                        break
                    else:
                        failed_files.append({'src': cand, 'dst': target_exe, 'error': err})

            if not copied_exe:
                # Fallback: Copy only launcher python files (from packaged source)
                launcher_files = [
                    "main.py", "skin_manager.py", "account_manager.py", "version_manager.py",
                    "config_manager.py", "downloader.py", "game_launcher.py", "modrinth_api.py",
                    "shortcut_installer.py", "server_manager.py"
                ]
                for fname in launcher_files:
                    # Only copy launcher files from the packaged base_dir to avoid touching user AppData
                    src = os.path.join(base_dir, fname)
                    if os.path.exists(src):
                        dstp = os.path.join(self.target_dir, fname)
                        ok, err = self.safe_copy(src, dstp)
                        if ok:
                            copied_files.append(dstp)
                        else:
                            failed_files.append({'src': src, 'dst': dstp, 'error': err})

            self.progress_signal.emit(60, "Aktiv assets va resurslar sozlanmoqda...")
            assets_src = os.path.join(base_dir, "assets")
            if not os.path.exists(assets_src):
                assets_src = os.path.join(curr_dir, "assets")
            assets_target = os.path.join(self.target_dir, "assets")
            if os.path.exists(assets_src):
                try:
                    self.safe_copytree(assets_src, assets_target)
                    for root, dirs, files in os.walk(assets_target):
                        for f in files:
                            copied_files.append(os.path.join(root, f))
                except Exception as asset_err:
                    failed_files.append({'src': assets_src, 'dst': assets_target, 'error': str(asset_err)})

            self.progress_signal.emit(85, "Windows yorliqlari yaratilmoqda...")
            icon_path = os.path.join(assets_target, "icon.ico")

            if self.create_desktop_sc:
                desktop_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
                sc_path = os.path.join(desktop_dir, 'NovaLauncher.lnk')
                self.create_shortcut(target_exe, sc_path, self.target_dir, icon_path)

            if self.create_start_sc:
                start_menu = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs')
                sc_path = os.path.join(start_menu, 'NovaLauncher.lnk')
                self.create_shortcut(target_exe, sc_path, self.target_dir, icon_path)

            self.progress_signal.emit(95, "Windows tizim ilovalari ro'yxatiga ro'yxatdan o'tkazilmoqda...")
            from shortcut_installer import ShortcutInstaller
            ShortcutInstaller.register_windows_app(self.target_dir, target_exe)

            self.progress_signal.emit(100, "O'rnatish yakunlandi!")

            if failed_files:
                result = {
                    'target_exe': target_exe,
                    'copied': copied_files,
                    'failed': failed_files,
                    'msg': "Qisman muvaffaqiyat: ba'zi fayllar nusxalanmadi"
                }
                self._write_log(result)
                self.finished_signal.emit(False, result)
            else:
                result = {'target_exe': target_exe, 'copied': copied_files}
                self._write_log(result)
                self.finished_signal.emit(True, result['target_exe'])

        except Exception as e:
            self._write_log({'error': str(e)})
            self.finished_signal.emit(False, {'error': str(e)})

    def safe_copy(self, src, dst, max_retries=5, delay=0.25):
        """Copy a single file with retries. Returns (True, None) on success or (False, error_str)."""
        last_err = None
        dst_dir = os.path.dirname(dst)
        try:
            os.makedirs(dst_dir, exist_ok=True)
        except Exception:
            pass
        for attempt in range(1, max_retries + 1):
            try:
                shutil.copy2(src, dst)
                return True, None
            except (PermissionError, OSError) as e:
                last_err = e
                time.sleep(delay)
            except Exception as e:
                return False, str(e)
        # After retries failed
        return False, str(last_err)

    def safe_copytree(self, src, dst):
        """Recursively copy a directory, skipping files that remain locked and reporting others."""
        if not os.path.exists(src):
            raise FileNotFoundError(src)
        os.makedirs(dst, exist_ok=True)
        for root, dirs, files in os.walk(src):
            rel = os.path.relpath(root, src)
            target_root = os.path.join(dst, rel) if rel != os.curdir else dst
            os.makedirs(target_root, exist_ok=True)
            for d in dirs:
                try:
                    os.makedirs(os.path.join(target_root, d), exist_ok=True)
                except Exception:
                    pass
            for f in files:
                s_path = os.path.join(root, f)
                d_path = os.path.join(target_root, f)
                ok, err = self.safe_copy(s_path, d_path)
                if not ok:
                    # skip locked files but log
                    print(f"Skipped locked file during copytree: {s_path} -> {err}")

    def _write_log(self, data):
        try:
            log_dir = os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser('~')), 'NovaLauncher')
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, 'installer.log')
            with open(log_path, 'a', encoding='utf-8') as lf:
                lf.write(f"[{datetime.utcnow().isoformat()}] {json.dumps(data, ensure_ascii=False)}\n")
        except Exception:
            pass

    def create_shortcut(self, target_exe, sc_path, work_dir, icon_path):
        try:
            ps_script = f"""
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut('{sc_path}')
            $Shortcut.TargetPath = '{target_exe}'
            $Shortcut.WorkingDirectory = '{work_dir}'
            if (Test-Path '{icon_path}') {{ $Shortcut.IconLocation = '{icon_path}' }}
            $Shortcut.Save()
            if (Test-Path '{target_exe}') {{ Unblock-File -Path '{target_exe}' -ErrorAction SilentlyContinue }}
            if (Test-Path '{sc_path}') {{ Unblock-File -Path '{sc_path}' -ErrorAction SilentlyContinue }}
            """
            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script]
            subprocess.run(cmd, capture_output=True, text=True)
        except Exception as e:
            print(f"Yorliq xatosi: {e}")


class SetupWizard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NovaLauncher Setup v2.0 — O'rnatish Dasturi")
        self.resize(650, 440)
        self.setFixedSize(650, 440)

        icon_path = os.path.join("assets", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.installed_exe_path = ""
        self.worker = None
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet("""
            QWidget {
                background-color: #0E0F17;
                color: #F8FAFC;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QLineEdit {
                background-color: #191B2B;
                border: 1px solid #2D314A;
                border-radius: 6px;
                padding: 8px 10px;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #7C3AED;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 10px 18px;
            }
            QPushButton:hover {
                background-color: #6D28D9;
            }
        """)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header Banner
        header = QHBoxLayout()
        logo_lbl = QLabel()
        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            logo_lbl.setPixmap(QPixmap(logo_path).scaled(42, 42, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        header.addWidget(logo_lbl)

        htitle = QLabel("NovaLauncher Setup v2.0")
        htitle.setStyleSheet("font-size: 20px; font-weight: 900; color: #C084FC;")
        header.addWidget(htitle)
        header.addStretch()
        layout.addLayout(header)

        # Pages
        self.pages = QStackedWidget()

        # Page 1: Welcome
        p1 = QWidget()
        p1_l = QVBoxLayout(p1)
        w_title = QLabel("O'rnatish Dasturiga Xush Kelibsiz!")
        w_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #F1F5F9; margin-top: 15px;")
        w_desc = QLabel("Ushbu dastur NovaLauncher (Minecraft 1.21.1 Fabric, Forge, OptiFine va Modrinth) ilovasini kompyuteringizga o'rnatib beradi.\n\nDavom etish uchun 'Keyingisi' tugmasini bosing.")
        w_desc.setWordWrap(True)
        w_desc.setStyleSheet("color: #94A3B8; font-size: 13px; line-height: 1.4;")
        p1_l.addWidget(w_title)
        p1_l.addWidget(w_desc)
        p1_l.addStretch()

        # Page 2: Path & Shortcuts
        p2 = QWidget()
        p2_l = QVBoxLayout(p2)
        p2_title = QLabel("O'rnatish Papkasi va Sozlamalar")
        p2_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #F1F5F9;")

        path_box = QHBoxLayout()
        default_install_dir = os.path.join(os.getenv('LOCALAPPDATA', os.path.expanduser('~')), 'Programs', 'NovaLauncher')
        self.txt_path = QLineEdit(default_install_dir)
        btn_browse = QPushButton("Tanlash...")
        btn_browse.clicked.connect(self.browse_folder)
        path_box.addWidget(self.txt_path)
        path_box.addWidget(btn_browse)

        self.chk_desktop = QCheckBox("Ishchi stolga yorliq yaratish (Desktop Shortcut)")
        self.chk_desktop.setChecked(True)
        self.chk_desktop.setStyleSheet("color: #CBD5E1;")

        self.chk_start = QCheckBox("Boshlash menyusiga qo'shish (Start Menu Shortcut)")
        self.chk_start.setChecked(True)
        self.chk_start.setStyleSheet("color: #CBD5E1;")

        p2_l.addWidget(p2_title)
        p2_l.addLayout(path_box)
        p2_l.addWidget(self.chk_desktop)
        p2_l.addWidget(self.chk_start)
        p2_l.addStretch()

        # Page 3: Installing Progress
        p3 = QWidget()
        p3_l = QVBoxLayout(p3)
        self.lbl_progress_status = QLabel("O'rnatish tayyorlanmoqda...")
        self.lbl_progress_status.setStyleSheet("font-size: 14px; color: #C084FC;")
        self.pbar = QProgressBar()
        self.pbar.setFixedHeight(12)
        self.pbar.setTextVisible(False)
        self.pbar.setStyleSheet("QProgressBar::chunk { background-color: #8B5CF6; border-radius: 4px; }")

        p3_l.addStretch()
        p3_l.addWidget(self.lbl_progress_status)
        p3_l.addWidget(self.pbar)
        p3_l.addStretch()

        # Page 4: Finish
        p4 = QWidget()
        p4_l = QVBoxLayout(p4)
        f_title = QLabel("🎉 O'rnatish Muvaffaqiyatli Yakunlandi!")
        f_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #10B981;")
        f_desc = QLabel("NovaLauncher kompyuteringizga to'liq o'rnatildi!")
        f_desc.setStyleSheet("color: #94A3B8; font-size: 13px;")

        self.chk_launch_now = QCheckBox("NovaLauncher-ni hozir ishga tushirish")
        self.chk_launch_now.setChecked(True)
        self.chk_launch_now.setStyleSheet("color: #F1F5F9; font-weight: bold;")

        p4_l.addWidget(f_title)
        p4_l.addWidget(f_desc)
        p4_l.addWidget(self.chk_launch_now)
        p4_l.addStretch()

        self.pages.addWidget(p1)
        self.pages.addWidget(p2)
        self.pages.addWidget(p3)
        self.pages.addWidget(p4)

        layout.addWidget(self.pages, 1)

        # Buttons Control Bar
        btn_bar = QHBoxLayout()
        self.btn_back = QPushButton("◀ Orqaga")
        self.btn_back.setStyleSheet("background-color: #374151;")
        self.btn_back.clicked.connect(self.go_back)

        self.btn_next = QPushButton("Keyingisi ▶")
        self.btn_next.clicked.connect(self.go_next)

        btn_bar.addWidget(self.btn_back)
        btn_bar.addStretch()
        btn_bar.addWidget(self.btn_next)

        layout.addLayout(btn_bar)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "O'rnatish papkasini tanlang", self.txt_path.text())
        if folder:
            self.txt_path.setText(folder)

    def go_back(self):
        idx = self.pages.currentIndex()
        if idx > 0 and idx != 2:
            self.pages.setCurrentIndex(idx - 1)
            self.update_nav_buttons()

    def go_next(self):
        idx = self.pages.currentIndex()
        if idx == 0:
            self.pages.setCurrentIndex(1)
            self.update_nav_buttons()
        elif idx == 1:
            # Start installation
            self.pages.setCurrentIndex(2)
            self.btn_back.setEnabled(False)
            self.btn_next.setEnabled(False)

            target_dir = self.txt_path.text().strip()
            self.worker = InstallTaskWorker(target_dir, self.chk_desktop.isChecked(), self.chk_start.isChecked())
            self.worker.progress_signal.connect(self.on_install_progress)
            self.worker.finished_signal.connect(self.on_install_finished)
            self.worker.start()
        elif idx == 3:
            # Finish
            if self.chk_launch_now.isChecked() and self.installed_exe_path and os.path.exists(self.installed_exe_path):
                subprocess.Popen(self.installed_exe_path, cwd=os.path.dirname(self.installed_exe_path))
            self.close()

    def update_nav_buttons(self):
        idx = self.pages.currentIndex()
        self.btn_back.setEnabled(idx > 0 and idx != 2 and idx != 3)
        if idx == 1:
            self.btn_next.setText("O'rnatish 🚀")
        elif idx == 3:
            self.btn_next.setText("Tugatish ✓")
        else:
            self.btn_next.setText("Keyingisi ▶")

    def on_install_progress(self, val, msg):
        self.pbar.setValue(val)
        self.lbl_progress_status.setText(msg)

    def on_install_finished(self, ok, msg_or_path):
        if ok:
            # success: msg_or_path is path to exe
            self.installed_exe_path = msg_or_path
            self.pages.setCurrentIndex(3)
            self.btn_next.setEnabled(True)
            self.update_nav_buttons()
        else:
            payload = msg_or_path
            # payload may be dict with 'failed' or 'error'
            if isinstance(payload, dict) and 'failed' in payload:
                failed = payload['failed']
                copied = payload.get('copied', [])
                dlg = QMessageBox(self)
                dlg.setWindowTitle("Xatolik: Fayl nusxalanmadi")
                dlg.setText("Ba'zi fayllar nusxalanmadi. Ilovani bloklayotgan ilovalarni yoping (masalan Telegram), so'ng qayta urin. Nima qilamiz?")
                retry_btn = dlg.addButton("Qayta urin", QMessageBox.ButtonRole.AcceptRole)
                skip_btn = dlg.addButton("O'tkazib yubor", QMessageBox.ButtonRole.DestructiveRole)
                abort_btn = dlg.addButton("Bekor qilish", QMessageBox.ButtonRole.RejectRole)
                dlg.exec()
                clicked = dlg.clickedButton()
                if clicked == retry_btn:
                    # retry full install
                    target_dir = self.txt_path.text().strip()
                    self.worker = InstallTaskWorker(target_dir, self.chk_desktop.isChecked(), self.chk_start.isChecked())
                    self.worker.progress_signal.connect(self.on_install_progress)
                    self.worker.finished_signal.connect(self.on_install_finished)
                    self.worker.start()
                    return
                elif clicked == skip_btn:
                    # continue finish with partial install
                    self.installed_exe_path = payload.get('target_exe', '')
                    self.pages.setCurrentIndex(3)
                    self.btn_next.setEnabled(True)
                    self.update_nav_buttons()
                    QMessageBox.information(self, "Ogohlantirish", "Ba'zi fayllar nusxalanmadi — ilova to'liq ishlamasligi mumkin.")
                    return
                else:
                    # Abort: rollback installation folder
                    try:
                        shutil.rmtree(self.txt_path.text().strip(), ignore_errors=True)
                    except Exception as e:
                        print("Rollback error:", e)
                    QMessageBox.warning(self, "Bekor qilindi", "O'rnatish bekor qilindi va nusxalar o'chirildi.")
                    self.pages.setCurrentIndex(1)
                    self.btn_back.setEnabled(True)
                    self.btn_next.setEnabled(True)
                    return
            else:
                # Generic error
                err_msg = payload.get('error') if isinstance(payload, dict) else str(payload)
                QMessageBox.critical(self, "Xatolik", f"O'rnatishda xatolik: {err_msg}")
                self.pages.setCurrentIndex(1)
                self.btn_back.setEnabled(True)
                self.btn_next.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    if "--uninstall" in sys.argv:
        from shortcut_installer import ShortcutInstaller
        reply = QMessageBox.question(
            None,
            "NovaLauncher-ni O'chirish (Uninstall)",
            "NovaLauncher ilovasi kompyuteringizdan to'liq o'chirilsinmi?\n\nBarcha yorliqlar va Windows registr yozuvlari o'chiriladi.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            ok, msg = ShortcutInstaller.uninstall_novalauncher(remove_game_data=False)
            if ok:
                QMessageBox.information(None, "Muvaffaqiyatli", msg)
            else:
                QMessageBox.warning(None, "Xatolik", msg)
        sys.exit(0)
    else:
        wiz = SetupWizard()
        wiz.show()
        sys.exit(app.exec())