import subprocess
import sys
import os
import shutil

def main():
    # Sprawdz czy PyInstaller jest zainstalowany
    try:
        import PyInstaller
    except ImportError:
        print("[!] PyInstaller nie znaleziony. Instaluję...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[+] PyInstaller zainstalowany.\n")

    # Sprawdz czy pliki istnieja
    required_files = ["main.py", "icon.ico"]
    for f in required_files:
        if not os.path.exists(f):
            print(f"[!] BRAK PLIKU: {f}")
            input("\nNaciśnij Enter aby wyjść...")
            sys.exit(1)

    # Szukaj audio_tool_config.json – najpierw lokalnie, potem w %APPDATA%
    config_path = None
    local_config = "audio_tool_config.json"
    appdata_config = os.path.join(os.environ.get("APPDATA", ""), "AudioMultiTool", "audio_tool_config.json")

    if os.path.exists(local_config):
        config_path = os.path.abspath(local_config)
        print(f"[+] Znaleziono config lokalnie:\n    {config_path}")
    elif os.path.exists(appdata_config):
        config_path = os.path.abspath(appdata_config)
        # Skopiuj do folderu lokalnego żeby PyInstaller mógł go spakować
        shutil.copy2(config_path, local_config)
        config_path = os.path.abspath(local_config)
        print(f"[+] Znaleziono config w AppData, skopiowano lokalnie:\n    {config_path}")
    else:
        print("[!] Nie znaleziono audio_tool_config.json!")
        print("    Szukałem w:")
        print(f"      - {os.path.abspath(local_config)}")
        print(f"      - {appdata_config}")
        input("\nNaciśnij Enter aby wyjść...")
        sys.exit(1)

    print("\n" + "=" * 55)
    print("  Bose Audio Test - Builder EXE")
    print("=" * 55)
    print("[*] Buduję .exe, poczekaj...\n")

    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", "Bose - Audio Test 1.0.2",
        "--icon=icon.ico",
        "--add-data", f"{config_path};.",
        "--hidden-import=pygame",
        "--hidden-import=numpy",
        "main.py"
    ]

    result = subprocess.run(cmd, capture_output=False, text=True)

    print("\n" + "=" * 55)
    if result.returncode == 0:
        exe_path = os.path.join("dist", "Bose - Audio Test 1.0.2.exe")
        print(f"[+] SUKCES! Plik EXE gotowy:")
        print(f"    {os.path.abspath(exe_path)}")
    else:
        print(f"[!] BŁĄD podczas budowania (kod: {result.returncode})")
    print("=" * 55)

    input("\nNaciśnij Enter aby zamknąć...")

if __name__ == "__main__":
    main()