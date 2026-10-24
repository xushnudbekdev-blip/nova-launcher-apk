import os
import zipfile
import requests
from PyQt6.QtCore import QThread, pyqtSignal

class ModrinthAPI:
    BASE_URL = "https://api.modrinth.com/v2"

    @staticmethod
    def search_projects(query="", game_version=None, loader="fabric", project_type="mod", limit=24):
        try:
            params = {
                "query": query,
                "limit": limit
            }
            facets = []
            if project_type:
                facets.append(f'["project_type:{project_type}"]')
            if loader and project_type in ["mod", "modpack"]:
                facets.append(f'["categories:{loader.lower()}"]')
            if game_version:
                facets.append(f'["versions:{game_version}"]')

            if facets:
                params["facets"] = "[" + ",".join(facets) + "]"

            url = f"{ModrinthAPI.BASE_URL}/search"
            headers = {"User-Agent": "NovaLauncher/2.5.0 (minecraft-launcher)"}
            res = requests.get(url, params=params, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return data.get("hits", [])
            return []
        except Exception as e:
            print(f"Modrinth qidiruvida xatolik: {e}")
            return []

    # Backward compatibility alias
    search_mods = search_projects

    @staticmethod
    def get_latest_version_download(project_id_or_slug, game_version=None, loader="fabric", project_type="mod"):
        try:
            url = f"{ModrinthAPI.BASE_URL}/project/{project_id_or_slug}/version"
            params = {}
            if game_version:
                params["game_versions"] = f'["{game_version}"]'
            if loader and project_type in ["mod", "modpack"]:
                params["loaders"] = f'["{loader.lower()}"]'

            headers = {"User-Agent": "NovaLauncher/2.5.0 (minecraft-launcher)"}
            res = requests.get(url, params=params, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if data and len(data) > 0:
                    primary_file = data[0]['files'][0]
                    return {
                        "url": primary_file["url"],
                        "filename": primary_file["filename"],
                        "version_number": data[0].get("version_number", "")
                    }
            return None
        except Exception as e:
            print(f"Modrinth fayl versiyasini olishda xatolik: {e}")
            return None

class ModrinthSearchWorker(QThread):
    results_signal = pyqtSignal(list)

    def __init__(self, query="", game_version=None, loader="fabric", project_type="mod"):
        super().__init__()
        self.query = query
        self.game_version = game_version
        self.loader = loader
        self.project_type = project_type

    def run(self):
        hits = ModrinthAPI.search_projects(
            query=self.query,
            game_version=self.game_version,
            loader=self.loader,
            project_type=self.project_type
        )
        self.results_signal.emit(hits)

class ModrinthDownloadWorker(QThread):
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, project_id, target_dir, game_version=None, loader="fabric", project_type="mod"):
        super().__init__()
        self.project_id = project_id
        self.target_dir = target_dir
        self.game_version = game_version
        self.loader = loader
        self.project_type = project_type

    def run(self):
        try:
            os.makedirs(self.target_dir, exist_ok=True)
            self.status_signal.emit(f"'{self.project_id}' uchun fayl qidirilmoqda...")

            v_info = ModrinthAPI.get_latest_version_download(
                self.project_id, self.game_version, self.loader, self.project_type
            )
            if not v_info:
                # Retry without game_version constraint if missing
                v_info = ModrinthAPI.get_latest_version_download(
                    self.project_id, None, self.loader, self.project_type
                )

            if v_info:
                url = v_info["url"]
                filename = v_info["filename"]
                save_path = os.path.join(self.target_dir, filename)

                self.status_signal.emit(f"{filename} yuklab olinmoqda...")
                headers = {"User-Agent": "NovaLauncher/2.5.0 (minecraft-launcher)"}
                res = requests.get(url, headers=headers, stream=True, timeout=90)
                if res.status_code == 200:
                    with open(save_path, 'wb') as f:
                        for chunk in res.iter_content(chunk_size=8192):
                            f.write(chunk)

                    # Extract map zip into saves folder automatically
                    if self.project_type == "map" and save_path.endswith(".zip"):
                        try:
                            self.status_signal.emit(f"Xarita unzip qilinmoqda ({filename})...")
                            extract_dir = os.path.join(self.target_dir, os.path.splitext(filename)[0])
                            with zipfile.ZipFile(save_path, 'r') as zip_ref:
                                zip_ref.extractall(extract_dir)
                        except Exception as ze:
                            print(f"Map unzip warning: {ze}")

                    type_names = {
                        "mod": "Mod",
                        "resourcepack": "Resurs-paket",
                        "shader": "Sheyder",
                        "datapack": "Datapack",
                        "modpack": "Modpack",
                        "map": "Xarita (World Map)"
                    }
                    type_str = type_names.get(self.project_type, "Fayl")
                    self.finished_signal.emit(True, f"{type_str} ({filename}) muvaffaqiyatli o'rnatildi!")
                    return
            self.finished_signal.emit(False, f"'{self.project_id}' uchun mos fayl topilmadi.")
        except Exception as e:
            self.finished_signal.emit(False, f"Yuklab olishda xatolik: {str(e)}")
