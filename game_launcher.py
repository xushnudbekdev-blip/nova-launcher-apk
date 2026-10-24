import os
import shutil
import subprocess
import minecraft_launcher_lib
from PyQt6.QtCore import QThread, pyqtSignal
from server_manager import ServerManager

def get_version_profile_dir(game_dir, version_str):
    clean_ver = version_str.replace("⚡", "").replace("🔥", "").replace("🧊", "").replace("🛡️", "").replace("🪶", "").replace("🟩", "").replace("🧪", "").replace("📜", "").strip()
    safe_name = clean_ver.replace(" ", "_").replace(":", "_").replace("/", "_")
    profile_dir = os.path.join(game_dir, "profiles", safe_name)
    os.makedirs(profile_dir, exist_ok=True)
    for sub in ["mods", "resourcepacks", "shaderpacks", "datapacks", "saves", "modpacks"]:
        os.makedirs(os.path.join(profile_dir, sub), exist_ok=True)
    ServerManager.ensure_novamc_server(profile_dir)
    ServerManager.ensure_novamc_server(game_dir)
    return profile_dir

class LaunchWorker(QThread):
    log_signal = pyqtSignal(str)
    started_signal = pyqtSignal()
    finished_signal = pyqtSignal(int, str)

    def __init__(self, config_manager, version_str=None):
        super().__init__()
        self.cfg = config_manager
        self.version_str = version_str or config_manager.get("selected_version", "Fabric 1.21.1")
        self.process = None

    def find_java(self, custom_path):
        if custom_path and os.path.exists(custom_path):
            return custom_path
        java_bin = shutil.which('javaw') or shutil.which('java')
        if java_bin:
            return java_bin

        program_files = os.getenv('ProgramFiles', r'C:\Program Files')
        common_files = os.getenv('CommonProgramFiles', r'C:\Program Files\Common Files')
        possible_paths = [
            os.path.join(common_files, r'Oracle\Java\javapath\javaw.exe'),
            os.path.join(program_files, r'Java\jdk-23\bin\javaw.exe'),
            os.path.join(program_files, r'Java\jdk-21\bin\javaw.exe'),
            os.path.join(program_files, r'Eclipse Adoptium\jdk-21.0.0.35-hotspot\bin\javaw.exe')
        ]
        for p in possible_paths:
            if os.path.exists(p):
                return p
        return 'java'

    def resolve_installed_version_id(self, game_dir, version_str):
        v_lower = version_str.lower()
        clean_ver = version_str.replace("⚡", "").replace("🔥", "").replace("🧊", "").replace("🛡️", "").replace("🪶", "").replace("🟩", "").replace("🧪", "").replace("📜", "").replace("Fabric", "").replace("Forge", "").replace("OptiFine", "").replace("NeoForge", "").replace("Quilt", "").replace("Vanilla", "").replace("Old", "").strip()

        installed = minecraft_launcher_lib.utils.get_installed_versions(game_dir)
        installed_ids = [v['id'] for v in installed]

        if "fabric" in v_lower:
            for vid in installed_ids:
                if 'fabric' in vid.lower() and clean_ver in vid:
                    return vid
            for vid in installed_ids:
                if 'fabric' in vid.lower():
                    return vid

        if "forge" in v_lower:
            for vid in installed_ids:
                if 'forge' in vid.lower() and clean_ver in vid:
                    return vid
            for vid in installed_ids:
                if 'forge' in vid.lower():
                    return vid

        if clean_ver in installed_ids:
            return clean_ver

        if len(installed_ids) > 0:
            return installed_ids[0]

        return clean_ver

    def run(self):
        try:
            game_dir = self.cfg.get("game_dir")
            username = self.cfg.get("username", "O'yinchi").strip() or "O'yinchi"
            ram_mb = self.cfg.get("ram_mb", 4096)
            custom_java = self.cfg.get("java_path", "")
            java_exec = self.find_java(custom_java)

            version_id = self.resolve_installed_version_id(game_dir, self.version_str)
            profile_dir = get_version_profile_dir(game_dir, self.version_str)

            self.log_signal.emit(f"[NovaLauncher] Tanlangan versiya: {self.version_str} -> {version_id}")
            self.log_signal.emit(f"[NovaLauncher] Profil (Modlar/Resurslar) papkasi: {profile_dir}")
            self.log_signal.emit(f"[NovaLauncher] Java executables: {java_exec}")
            self.log_signal.emit(f"[NovaLauncher] O'yin papkasi: {game_dir}")
            self.log_signal.emit(f"[NovaLauncher] Foydalanuvchi: {username} | RAM: {ram_mb} MB")

            test_options = minecraft_launcher_lib.utils.generate_test_options()
            uuid_str = test_options["uuid"]

            jvm_args_str = self.cfg.get("jvm_args", "-XX:+UseG1GC")
            jvm_list = jvm_args_str.split()
            jvm_list.extend([f"-Xmx{ram_mb}M", f"-Xms{min(1024, ram_mb)}M"])

            options = {
                "username": username,
                "uuid": uuid_str,
                "token": "",
                "executablePath": java_exec,
                "jvmArguments": jvm_list,
                "gameDirectory": profile_dir,
            }

            if self.cfg.get("custom_resolution"):
                options["customResolution"] = True
                options["resolutionWidth"] = str(self.cfg.get("resolution_w", 854))
                options["resolutionHeight"] = str(self.cfg.get("resolution_h", 480))

            self.log_signal.emit("[NovaLauncher] Ishga tushirish buyrug'i tayyorlanmoqda...")
            cmd = minecraft_launcher_lib.command.get_minecraft_command(version_id, game_dir, options)

            self.log_signal.emit(f"[NovaLauncher] Jarayon boshlandi: {cmd[0]} ...")
            self.started_signal.emit()

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                startupinfo=startupinfo
            )

            for line in self.process.stdout:
                line_str = line.strip()
                if line_str:
                    self.log_signal.emit(line_str)

            self.process.wait()
            exit_code = self.process.returncode
            self.log_signal.emit(f"[NovaLauncher] O'yin yakunlandi (Exit code: {exit_code})")
            self.finished_signal.emit(exit_code, f"O'yin tugadi (Kodi: {exit_code})")

        except Exception as e:
            err_msg = f"[NovaLauncher Error] Ishga tushirishda xatolik: {str(e)}"
            self.log_signal.emit(err_msg)
            self.finished_signal.emit(-1, err_msg)
