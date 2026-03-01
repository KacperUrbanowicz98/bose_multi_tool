import subprocess
import sys
import os

def main():
    # Sprawdz czy PyInstaller jest zainstalowany
    try:
        import PyInstaller
    except ImportError:
        print("[!] PyInstaller nie znaleziony. Instaluję...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[+] PyInstaller zainstalowany.\n")

    # Sprawdz czy pliki istnieja
    required_files = ["main.py", "icon.ico", "audio_tool_config.json"]
    for f in required_files:
        if not os.path.exists(f):
            print(f"[!] BRAK PLIKU: {f}")
            input("\nNaciśnij Enter aby wyjść...")
            sys.exit(1)

    print("=" * 50)
    print("  Bose Audio Test - Builder EXE")
    print("=" * 50)
    print("[*] Buduję .exe, poczekaj...\n")

    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", "Bose - Audio Test 1.0.2",
        "--icon=icon.ico",
        "--add-data", "audio_tool_config.json;.",
        "--hidden-import=pygame",
        "--hidden-import=numpy",
        "main.py"
    ]

    result = subprocess.run(cmd, capture_output=False, text=True)

    print("\n" + "=" * 50)
    if result.returncode == 0:
        exe_path = os.path.join("dist", "Bose - Audio Test 1.0.2.exe")
        print(f"[+] SUKCES! Plik EXE gotowy:")
        print(f"    {os.path.abspath(exe_path)}")
    else:
        print(f"[!] BŁĄD podczas budowania (kod: {result.returncode})")
    print("=" * 50)

    input("\nNaciśnij Enter aby zamknąć...")

if __name__ == "__main__":
    main()