import os
import json
import shutil

DEFAULT_GAME_DIR = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), '.novalauncher')

class ConfigManager:
    def __init__(self):
        self.game_dir = DEFAULT_GAME_DIR
        os.makedirs(self.game_dir, exist_ok=True)
        self.config_path = os.path.join(self.game_dir, 'novalauncher_config.json')
        self.data = self.get_defaults()
        self.load()

    def get_defaults(self):
        java_path = shutil.which('javaw') or shutil.which('java') or ''
        return {
            "username": "O'yinchi",
            "ram_mb": 4096,
            "java_path": java_path,
            "game_dir": DEFAULT_GAME_DIR,
            "selected_version": "Fabric 1.21.1",
            "auto_close": False,
            "custom_resolution": False,
            "resolution_w": 854,
            "resolution_h": 480,
            "jvm_args": "-XX:+UseG1GC",
            "skin_path": ""
        }

    def load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
            except Exception as e:
                print(f"Konfiguratsiyani o'qishda xatolik: {e}")
                self.save()
        else:
            self.save()

    def save(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Konfiguratsiyani saqlashda xatolik: {e}")

    def reset_to_defaults(self):
        self.data = self.get_defaults()
        self.save()

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()

