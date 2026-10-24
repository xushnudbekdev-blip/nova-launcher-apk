import os
import sys
import subprocess
import shutil

def build_setup():
    print("Building NovaLauncherSetup.exe with PyInstaller...")

    icon_path = os.path.join("assets", "icon.ico")
    assets_data = "assets;assets"

    exe_src = "NovaLauncher.exe" if os.path.exists("NovaLauncher.exe") else os.path.join("dist", "NovaLauncher.exe")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name=NovaLauncherSetup",
        f"--icon={icon_path}",
        f"--add-data={assets_data}",
    ]

    if os.path.exists(exe_src):
        cmd.append(f"--add-data={exe_src};.")

    cmd.extend([
        "--version-file=version_info.txt",
        "--manifest=app.manifest",
        "--hidden-import=PyQt6",
        "--hidden-import=requests",
        "--clean",
        "installer_gui.py"
    ])

    print("Running command:", " ".join(cmd))
    res = subprocess.run(cmd)

    if res.returncode == 0:
        exe_path = os.path.join("dist", "NovaLauncherSetup.exe")
        target_path = os.path.join(os.getcwd(), "NovaLauncherSetup.exe")
        if os.path.exists(exe_path):
            try:
                shutil.copy(exe_path, target_path)
                print(f"\n[SUCCESS] Setup Installer created at: {target_path}")
            except Exception as e:
                print(f"\n[INFO] Built successfully at: {exe_path} ({e})")
        else:
            print("\n[ERROR] Build finished but NovaLauncherSetup.exe not found in dist/")
    else:
        print("\n[ERROR] Build failed with exit code:", res.returncode)

if __name__ == "__main__":
    build_setup()

