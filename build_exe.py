import os
import sys
import subprocess
import shutil

def build():
    print("Building NovaLauncher.exe with PyInstaller...")

    icon_path = os.path.join("assets", "icon.ico")
    assets_data = "assets;assets"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name=NovaLauncher",
        f"--icon={icon_path}",
        f"--add-data={assets_data}",
        "--version-file=version_info.txt",
        "--manifest=app.manifest",
        "--hidden-import=PyQt6",
        "--hidden-import=minecraft_launcher_lib",
        "--hidden-import=requests",
        "--hidden-import=PIL",
        "--hidden-import=psutil",
        "--hidden-import=account_manager",
        "--hidden-import=skin_manager",
        "--hidden-import=version_manager",
        "--hidden-import=server_manager",
        "--hidden-import=downloader",
        "--hidden-import=game_launcher",
        "--hidden-import=modrinth_api",
        "--hidden-import=shortcut_installer",
        "--clean",
        "main.py"
    ]

    print("Running command:", " ".join(cmd))
    res = subprocess.run(cmd)

    if res.returncode == 0:
        exe_path = os.path.join("dist", "NovaLauncher.exe")
        target_path = os.path.join(os.getcwd(), "NovaLauncher.exe")
        if os.path.exists(exe_path):
            try:
                shutil.copy(exe_path, target_path)
                print(f"\n[SUCCESS] Executable created and updated at: {target_path}")
            except Exception as e:
                print(f"\n[INFO] Built successfully at: {exe_path} (Notice: Could not copy to root due to: {e})")
        else:
            print("\n❌ Build finished but NovaLauncher.exe not found in dist/")
    else:
        print("\n❌ Build failed with exit code:", res.returncode)

if __name__ == "__main__":
    build()

