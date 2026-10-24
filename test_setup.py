import os
import shutil
import sys
import minecraft_launcher_lib

def test_launcher_setup():
    appdata = os.getenv('APPDATA')
    game_dir = os.path.join(appdata, '.novalauncher_test')
    os.makedirs(game_dir, exist_ok=True)

    print("Checking Fabric loader versions...")
    loaders = minecraft_launcher_lib.fabric.get_all_loader_versions()
    print(f"Total loader versions found: {len(loaders)}")
    latest_loader = minecraft_launcher_lib.fabric.get_latest_loader_version()
    print(f"Latest loader: {latest_loader}")

    # Check installed versions
    installed = minecraft_launcher_lib.utils.get_installed_versions(game_dir)
    print(f"Installed versions in {game_dir}: {[v['id'] for v in installed]}")

    # Find java
    java = shutil.which('javaw') or shutil.which('java')
    print(f"Detected Java: {java}")

if __name__ == "__main__":
    test_launcher_setup()
