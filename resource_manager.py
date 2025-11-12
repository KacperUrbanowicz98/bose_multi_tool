"""
Resource Manager - Zarządzanie zasobami aplikacji
Odpowiada za prawidłowe zamykanie pygame, czyszczenie pamięci, kontrolę okien
"""

import pygame
import gc
import sys


class ResourceManager:
    """
    Menedżer zasobów aplikacji.
    Singleton - tylko jedna instancja w całej aplikacji.
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern - zawsze zwraca tę samą instancję"""
        if cls._instance is None:
            cls._instance = super(ResourceManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Inicjalizacja menedżera zasobów"""
        if self._initialized:
            return

        self._initialized = True

        # Śledzenie zasobów
        self.pygame_initialized = False
        self.open_windows = []  # Lista otwartych okien testów
        self.active_sounds = []  # Lista aktywnych dźwięków
        self.loaded_files = {}  # Cache załadowanych plików

        print("[ResourceManager] Inicjalizacja menedżera zasobów")

    # === PYGAME MIXER ===

    def init_pygame(self, frequency=44100, size=-16, channels=2, buffer=512):
        """
        Inicjalizuje pygame mixer z obsługą błędów.

        Args:
            frequency: Częstotliwość próbkowania
            size: Rozmiar próbki
            channels: Liczba kanałów (2 = stereo)
            buffer: Rozmiar bufora

        Returns:
            bool: True jeśli sukces, False jeśli błąd
        """
        if self.pygame_initialized:
            print("[ResourceManager] Pygame już zainicjowany")
            return True

        try:
            pygame.mixer.init(frequency=frequency, size=size,
                              channels=channels, buffer=buffer)
            self.pygame_initialized = True
            print(f"[ResourceManager] Pygame zainicjowany: {frequency}Hz, {channels}ch")
            return True

        except pygame.error as e:
            print(f"[ResourceManager] BŁĄD inicjalizacji pygame: {e}")
            return False
        except Exception as e:
            print(f"[ResourceManager] Nieoczekiwany błąd: {e}")
            return False

    def quit_pygame(self):
        """Zamyka pygame mixer i zwalnia zasoby"""
        if not self.pygame_initialized:
            return

        try:
            # Zatrzymaj wszystkie dźwięki
            pygame.mixer.stop()
            pygame.mixer.music.stop()

            # Wyczyść cache dźwięków
            self.active_sounds.clear()

            # Zamknij mixer
            pygame.mixer.quit()

            self.pygame_initialized = False
            print("[ResourceManager] Pygame zamknięty")

        except Exception as e:
            print(f"[ResourceManager] Błąd zamykania pygame: {e}")

    def stop_all_sounds(self):
        """Zatrzymuje wszystkie odtwarzane dźwięki"""
        try:
            if self.pygame_initialized:
                pygame.mixer.stop()
                pygame.mixer.music.stop()
                print("[ResourceManager] Zatrzymano wszystkie dźwięki")
        except Exception as e:
            print(f"[ResourceManager] Błąd zatrzymywania dźwięków: {e}")

    # === ZARZĄDZANIE OKNAMI ===

    def register_window(self, window, window_name):
        """
        Rejestruje nowe okno testu.

        Args:
            window: Obiekt okna (tk.Toplevel)
            window_name: Nazwa okna (np. "music_player", "tone_generator")
        """
        window_info = {
            'window': window,
            'name': window_name
        }
        self.open_windows.append(window_info)
        print(f"[ResourceManager] Zarejestrowano okno: {window_name}")

    def unregister_window(self, window):
        """
        Wyrejestrowuje okno testu.

        Args:
            window: Obiekt okna do usunięcia
        """
        self.open_windows = [w for w in self.open_windows if w['window'] != window]
        print(f"[ResourceManager] Wyrejestrowano okno")

    def close_all_windows(self):
        """Zamyka wszystkie otwarte okna testów"""
        print(f"[ResourceManager] Zamykanie {len(self.open_windows)} okien...")

        for window_info in self.open_windows[:]:  # Kopia listy
            try:
                window_info['window'].destroy()
                print(f"[ResourceManager] Zamknięto: {window_info['name']}")
            except Exception as e:
                print(f"[ResourceManager] Błąd zamykania {window_info['name']}: {e}")

        self.open_windows.clear()

    def get_open_windows_count(self):
        """Zwraca liczbę otwartych okien"""
        return len(self.open_windows)

    # === CACHE PLIKÓW ===

    def cache_file(self, file_path, data):
        """
        Cachuje dane pliku w pamięci.

        Args:
            file_path: Ścieżka do pliku
            data: Dane do zachowania
        """
        self.loaded_files[file_path] = data
        print(f"[ResourceManager] Cachowano: {file_path}")

    def get_cached_file(self, file_path):
        """
        Pobiera dane z cache.

        Args:
            file_path: Ścieżka do pliku

        Returns:
            Dane z cache lub None
        """
        return self.loaded_files.get(file_path)

    def clear_cache(self):
        """Czyści cache plików"""
        cache_size = len(self.loaded_files)
        self.loaded_files.clear()
        gc.collect()  # Wymuś garbage collection
        print(f"[ResourceManager] Wyczyszczono cache ({cache_size} plików)")

    # === CZYSZCZENIE PAMIĘCI ===

    def force_garbage_collection(self):
        """Wymusza garbage collection (czyszczenie nieużywanej pamięci)"""
        collected = gc.collect()
        print(f"[ResourceManager] Garbage collection: {collected} obiektów")
        return collected

    # === SHUTDOWN ===

    def shutdown(self):
        """
        Całkowite zamknięcie aplikacji - zwalnia WSZYSTKIE zasoby.
        Wywołaj to przed zamknięciem głównego okna.
        """
        print("[ResourceManager] === SHUTDOWN ROZPOCZĘTY ===")

        # 1. Zatrzymaj wszystkie dźwięki
        self.stop_all_sounds()

        # 2. Zamknij wszystkie okna testów
        self.close_all_windows()

        # 3. Zamknij pygame
        self.quit_pygame()

        # 4. Wyczyść cache
        self.clear_cache()

        # 5. Wymuś garbage collection
        self.force_garbage_collection()

        print("[ResourceManager] === SHUTDOWN ZAKOŃCZONY ===")

    # === INFO ===

    def get_status(self):
        """Zwraca status menedżera zasobów"""
        return {
            'pygame_initialized': self.pygame_initialized,
            'open_windows': len(self.open_windows),
            'cached_files': len(self.loaded_files),
            'active_sounds': len(self.active_sounds)
        }

    def print_status(self):
        """Wypisuje status do konsoli"""
        status = self.get_status()
        print("[ResourceManager] === STATUS ===")
        print(f"  Pygame: {'✓' if status['pygame_initialized'] else '✗'}")
        print(f"  Otwarte okna: {status['open_windows']}")
        print(f"  Cache plików: {status['cached_files']}")
        print(f"  Aktywne dźwięki: {status['active_sounds']}")
        print("=" * 30)


# === SINGLETON - łatwy dostęp ===
def get_resource_manager():
    """Zwraca globalną instancję ResourceManager"""
    return ResourceManager()
