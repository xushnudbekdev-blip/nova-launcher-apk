import os
import requests
import minecraft_launcher_lib
from PyQt6.QtCore import QThread, pyqtSignal

class InstallWorker(QThread):
    progress_signal = pyqtSignal(int, int, str)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, version_str="Fabric 1.21.1", game_dir=None):
        super().__init__()
        self.version_str = version_str
        self.game_dir = game_dir
        self._current_progress = 0
        self._max_progress = 100

    def set_status(self, status):
        self.status_signal.emit(str(status))
        self.progress_signal.emit(self._current_progress, self._max_progress, str(status))

    def set_progress(self, progress):
        self._current_progress = int(progress)
        self.progress_signal.emit(self._current_progress, self._max_progress, f"Yuklanmoqda: {self._current_progress}%")

    def set_max(self, max_val):
        self._max_progress = max(1, int(max_val))

    def run(self):
        try:
            callback = {
                "setStatus": self.set_status,
                "setProgress": self.set_progress,
                "setMax": self.set_max
            }

            v_lower = self.version_str.lower()
            clean_mc_ver = self.version_str.replace("⚡", "").replace("🔥", "").replace("🧊", "").replace("🛡️", "").replace("🪶", "").replace("🟩", "").replace("🧪", "").replace("📜", "").replace("Fabric", "").replace("Forge", "").replace("OptiFine", "").replace("NeoForge", "").replace("Quilt", "").replace("Vanilla", "").replace("Old", "").strip()


            self.set_status(f"Minecraft {clean_mc_ver} fayllari tekshirilmoqda...")

            # 1. Base Minecraft installation
            minecraft_launcher_lib.install.install_minecraft_version(
                clean_mc_ver,
                self.game_dir,
                callback=callback
            )

            # 2. Fabric Loader Installation
            if "fabric" in v_lower:
                self.set_status(f"Fabric Loader ({clean_mc_ver}) o'rnatilmoqda...")
                latest_loader = minecraft_launcher_lib.fabric.get_latest_loader_version()
                minecraft_launcher_lib.fabric.install_fabric(
                    clean_mc_ver,
                    self.game_dir,
                    loader_version=latest_loader,
                    callback=callback
                )
                mods_dir = os.path.join(self.game_dir, 'mods')
                os.makedirs(mods_dir, exist_ok=True)
                self.auto_install_fabric_api(mods_dir, clean_mc_ver)

            # 3. Forge Loader Installation
            elif "forge" in v_lower:
                self.set_status(f"Forge Loader ({clean_mc_ver}) izlanmoqda va o'rnatilmoqda...")
                forge_ver = minecraft_launcher_lib.forge.find_forge_version(clean_mc_ver)
                if forge_ver:
                    minecraft_launcher_lib.forge.install_forge_version(
                        forge_ver,
                        self.game_dir,
                        callback=callback
                    )
                else:
                    self.set_status(f"Forge {clean_mc_ver} uchun topilmadi, standart versiya o'rnatildi.")

            # 4. OptiFine Installation
            elif "optifine" in v_lower:
                self.set_status(f"OptiFine ({clean_mc_ver}) qo'shilmoqda...")
                mods_dir = os.path.join(self.game_dir, 'mods')
                os.makedirs(mods_dir, exist_ok=True)
                # Auto install OptiFabric or Sodium/Iris if fabric is present
                self.auto_install_optifine_mod(mods_dir, clean_mc_ver)

            self.set_status("O'rnatish muvaffaqiyatli yakunlandi!")
            self.finished_signal.emit(True, f"Minecraft {self.version_str} muvaffaqiyatli o'rnatildi!")

        except Exception as e:
            err_msg = f"O'rnatishda xatolik yuz berdi: {str(e)}"
            self.status_signal.emit(err_msg)
            self.finished_signal.emit(False, err_msg)

    def auto_install_fabric_api(self, mods_dir, mc_ver):
        try:
            existing = [f for f in os.listdir(mods_dir) if 'fabric-api' in f.lower() and f.endswith('.jar')]
            if existing:
                return

            self.set_status(f"Fabric API ({mc_ver}) yuklab olinmoqda...")
            url = f'https://api.modrinth.com/v2/project/fabric-api/version?game_versions=["{mc_ver}"]&loaders=["fabric"]'
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    jar_url = data[0]['files'][0]['url']
                    filename = data[0]['files'][0]['filename']
                    save_path = os.path.join(mods_dir, filename)

                    jar_resp = requests.get(jar_url, stream=True, timeout=30)
                    if jar_resp.status_code == 200:
                        with open(save_path, 'wb') as f:
                            for chunk in jar_resp.iter_content(chunk_size=8192):
                                f.write(chunk)
                        self.set_status(f"Fabric API ({filename}) o'rnatildi!")
        except Exception as e:
            print(f"Fabric API auto install warning: {e}")

    def auto_install_optifine_mod(self, mods_dir, mc_ver):
        try:
            url = f'https://api.modrinth.com/v2/project/optifabric/version?game_versions=["{mc_ver}"]'
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    jar_url = data[0]['files'][0]['url']
                    filename = data[0]['files'][0]['filename']
                    save_path = os.path.join(mods_dir, filename)
                    jar_resp = requests.get(jar_url, stream=True, timeout=30)
                    if jar_resp.status_code == 200:
                        with open(save_path, 'wb') as f:
                            for chunk in jar_resp.iter_content(chunk_size=8192):
                                f.write(chunk)
        except Exception as e:
            print(f"OptiFine mod warning: {e}")
