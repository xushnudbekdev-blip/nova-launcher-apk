import os
import requests
import minecraft_launcher_lib

class VersionManager:
    _cached_version_list = None
    _cached_fabric_versions = None

    @staticmethod
    def get_installed_versions(game_dir):
        if not os.path.exists(game_dir):
            return []
        try:
            installed = minecraft_launcher_lib.utils.get_installed_versions(game_dir)
            return [v['id'] for v in installed]
        except Exception as e:
            print(f"O'rnatilgan versiyalarni olishda xatolik: {e}")
            return []

    @staticmethod
    def get_all_minecraft_versions(show_snapshots=True, show_old=True):
        if VersionManager._cached_version_list is None:
            try:
                VersionManager._cached_version_list = minecraft_launcher_lib.utils.get_version_list()
            except Exception as e:
                print(f"Mojang versiya manifestini olishda xatolik: {e}")
                # Fallback comprehensive releases and old versions list
                VersionManager._cached_version_list = [
                    {"id": "1.21.4", "type": "release"},
                    {"id": "1.21.3", "type": "release"},
                    {"id": "1.21.2", "type": "release"},
                    {"id": "1.21.1", "type": "release"},
                    {"id": "1.21", "type": "release"},
                    {"id": "1.20.6", "type": "release"},
                    {"id": "1.20.4", "type": "release"},
                    {"id": "1.20.2", "type": "release"},
                    {"id": "1.20.1", "type": "release"},
                    {"id": "1.19.4", "type": "release"},
                    {"id": "1.19.2", "type": "release"},
                    {"id": "1.18.2", "type": "release"},
                    {"id": "1.17.1", "type": "release"},
                    {"id": "1.16.5", "type": "release"},
                    {"id": "1.15.2", "type": "release"},
                    {"id": "1.14.4", "type": "release"},
                    {"id": "1.13.2", "type": "release"},
                    {"id": "1.12.2", "type": "release"},
                    {"id": "1.11.2", "type": "release"},
                    {"id": "1.10.2", "type": "release"},
                    {"id": "1.9.4", "type": "release"},
                    {"id": "1.8.9", "type": "release"},
                    {"id": "1.7.10", "type": "release"},
                    {"id": "1.6.4", "type": "release"},
                    {"id": "1.5.2", "type": "release"},
                    {"id": "1.4.7", "type": "release"},
                    {"id": "1.3.2", "type": "release"},
                    {"id": "1.2.5", "type": "release"},
                    {"id": "1.1", "type": "release"},
                    {"id": "1.0", "type": "release"},
                    # Classic Old Beta & Alpha
                    {"id": "b1.8.1", "type": "old_beta"},
                    {"id": "b1.7.3", "type": "old_beta"},
                    {"id": "b1.5_01", "type": "old_beta"},
                    {"id": "b1.3_01", "type": "old_beta"},
                    {"id": "b1.1_02", "type": "old_beta"},
                    {"id": "a1.2.6", "type": "old_alpha"},
                    {"id": "a1.1.2_01", "type": "old_alpha"},
                    {"id": "c0.30_01c", "type": "old_alpha"},
                    {"id": "rd-132211", "type": "old_alpha"}
                ]

        releases = []
        snapshots = []
        old_vers = []

        for v in VersionManager._cached_version_list:
            v_type = v.get('type')
            v_id = v.get('id')
            if v_type == 'release':
                releases.append(v_id)
            elif v_type == 'snapshot':
                snapshots.append(v_id)
            elif v_type in ['old_beta', 'old_alpha']:
                old_vers.append(v_id)

        # Fallback if old_vers is empty from Mojang manifest
        if not old_vers:
            old_vers = ["b1.8.1", "b1.7.3", "b1.5_01", "b1.3_01", "a1.2.6", "a1.1.2_01", "c0.30_01c"]

        return releases, snapshots, old_vers

    @staticmethod
    def get_fabric_mc_versions():
        if VersionManager._cached_fabric_versions is None:
            try:
                mc_versions = minecraft_launcher_lib.fabric.get_all_minecraft_versions()
                VersionManager._cached_fabric_versions = [v['version'] for v in mc_versions if v.get('stable', True)]
            except Exception as e:
                print(f"Fabric versiyalarini olishda xatolik: {e}")
                VersionManager._cached_fabric_versions = [
                    "1.21.4", "1.21.3", "1.21.2", "1.21.1", "1.21", "1.20.6", "1.20.4", "1.20.2", "1.20.1",
                    "1.19.4", "1.19.2", "1.18.2", "1.17.1", "1.16.5", "1.15.2", "1.14.4"
                ]
        return VersionManager._cached_fabric_versions

    @staticmethod
    def get_popular_forge_versions():
        return [
            ("1.21.4", "1.21.4-54.0.1"),
            ("1.21.3", "1.21.3-53.0.1"),
            ("1.21.2", "1.21.2-52.1.0"),
            ("1.21.1", "1.21.1-52.0.2"),
            ("1.21", "1.21-51.0.33"),
            ("1.20.6", "1.20.6-50.0.35"),
            ("1.20.4", "1.20.4-49.0.38"),
            ("1.20.2", "1.20.2-48.1.0"),
            ("1.20.1", "1.20.1-47.3.0"),
            ("1.19.4", "1.19.4-45.2.0"),
            ("1.19.2", "1.19.2-43.3.0"),
            ("1.18.2", "1.18.2-40.2.21"),
            ("1.17.1", "1.17.1-37.1.1"),
            ("1.16.5", "1.16.5-36.2.39"),
            ("1.15.2", "1.15.2-31.2.57"),
            ("1.14.4", "1.14.4-28.2.26"),
            ("1.12.2", "1.12.2-14.23.5.2860"),
            ("1.10.2", "1.10.2-12.18.3.2511"),
            ("1.8.9", "1.8.9-11.15.1.2318"),
            ("1.7.10", "1.7.10-10.13.4.1614"),
            ("1.6.4", "1.6.4-9.11.1.965"),
            ("1.5.2", "1.5.2-7.8.1.737")
        ]

    @staticmethod
    def get_popular_optifine_versions():
        return [
            "1.21.4", "1.21.3", "1.21.2", "1.21.1", "1.21", "1.20.6", "1.20.4", "1.20.2", "1.20.1",
            "1.19.4", "1.19.2", "1.18.2", "1.17.1", "1.16.5", "1.15.2",
            "1.14.4", "1.12.2", "1.8.9", "1.7.10", "1.6.4", "1.5.2"
        ]

    @staticmethod
    def get_neoforge_versions():
        return [
            "1.21.4", "1.21.3", "1.21.2", "1.21.1", "1.21", "1.20.6", "1.20.4"
        ]

    @staticmethod
    def get_quilt_versions():
        return [
            "1.21.4", "1.21.3", "1.21.2", "1.21.1", "1.21", "1.20.4", "1.20.1", "1.19.4", "1.19.2", "1.18.2"
        ]


