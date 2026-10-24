import os
import sys
import shutil
import winreg
import subprocess

class ShortcutInstaller:
    @staticmethod
    def register_windows_app(install_dir, target_exe=None):
        """Registers NovaLauncher in Windows Add/Remove Programs (Control Panel & Settings)"""
        try:
            if not target_exe:
                target_exe = os.path.join(install_dir, "NovaLauncher.exe")

            icon_path = os.path.join(install_dir, "assets", "icon.ico")
            reg_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\NovaLauncher"

            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "NovaLauncher Minecraft Edition")
                winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "2.5.0")
                winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "NovaLauncher Team")
                winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, install_dir)
                winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, icon_path if os.path.exists(icon_path) else target_exe)
                winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{target_exe}" --uninstall')
                winreg.SetValueEx(key, "QuietUninstallString", 0, winreg.REG_SZ, f'"{target_exe}" --uninstall')
                winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
                total_size = 0
                for root, dirs, files in os.walk(install_dir):
                    for f in files:
                        fp = os.path.join(root, f)
                        if os.path.exists(fp):
                            total_size += os.path.getsize(fp)
                winreg.SetValueEx(key, "EstimatedSize", 0, winreg.REG_DWORD, int(total_size / 1024))
            return True, "Windows App registriga muvaffaqiyatli saqlandi"
        except Exception as e:
            return False, f"Registry registratsiya xatosi: {e}"

    @staticmethod
    def unregister_windows_app():
        try:
            reg_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\NovaLauncher"
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, reg_path)
            return True, "Registrydan o'chirildi"
        except Exception:
            return False, "Registry kaliti topilmadi"

    @staticmethod
    def create_desktop_shortcut(target_exe=None):
        if not target_exe:
            target_exe = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath("NovaLauncher.exe")

        if not os.path.exists(target_exe):
            return False, "NovaLauncher.exe fayli topilmadi."

        try:
            desktop_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
            shortcut_path = os.path.join(desktop_dir, 'NovaLauncher.lnk')
            icon_path = os.path.abspath(os.path.join("assets", "icon.ico"))
            work_dir = os.path.dirname(os.path.abspath(target_exe))

            # PowerShell command to create .lnk shortcut
            ps_script = f"""
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
            $Shortcut.TargetPath = '{target_exe}'
            $Shortcut.WorkingDirectory = '{work_dir}'
            if (Test-Path '{icon_path}') {{ $Shortcut.IconLocation = '{icon_path}' }}
            $Shortcut.Save()
            """

            cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                return True, f"Yorliq Ishchi stolga yaratildi: {shortcut_path}"
            return False, f"PowerShell xatoligi: {res.stderr}"
        except Exception as e:
            return False, f"Yorliq yaratishda xatolik: {e}"

    @staticmethod
    def uninstall_novalauncher(remove_game_data=False):
        try:
            # 1. Remove Desktop & Start Menu Shortcuts
            desktop_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
            shortcut_path = os.path.join(desktop_dir, 'NovaLauncher.lnk')
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)

            start_menu = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs')
            start_sc = os.path.join(start_menu, 'NovaLauncher.lnk')
            if os.path.exists(start_sc):
                os.remove(start_sc)

            # 2. Unregister Windows App
            ShortcutInstaller.unregister_windows_app()

            # 3. Remove game data if requested
            if remove_game_data:
                game_dir = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), '.novalauncher')
                if os.path.exists(game_dir):
                    shutil.rmtree(game_dir, ignore_errors=True)

            return True, "NovaLauncher va barcha yorliqlar kompyuteringizdan muvaffaqiyatli o'chirildi!"
        except Exception as e:
            return False, f"O'chirishda xatolik: {e}"

