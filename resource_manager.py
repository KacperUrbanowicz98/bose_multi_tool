"""
Resource Manager - Zarządzanie zasobami aplikacji
Singleton pattern - jedna instancja dla całej aplikacji
"""

import pygame
import gc

class ResourceManager:
    """Menedżer zasobów - singleton"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.pygame_initialized = False
        self.open_windows = []
        self.cached_files = {}
        self.active_sounds = []

        print("[ResourceManager] Inicjalizacja menedżera zasobów")

    def init_pygame(self, frequency=44100, size=-16, channels=2, buffer=512):
        """Inicjalizuje pygame mixer"""
        if not self.pygame_initialized:
            try:
                pygame.mixer.init(frequency=frequency, size=size, channels=channels, buffer=buffer)
                self.pygame_initialized = True
                print(f"[ResourceManager] Pygame mixer zainicjowany: {frequency}Hz, {channels} kanały")
                return True
            except Exception as e:
                print(f"[ResourceManager] Błąd inicjalizacji pygame: {e}")
                return False
        return True

    def register_window(self, window, name):
        """Rejestruje otwarte okno"""
        self.open_windows.append({'window': window, 'name': name})
        print(f"[ResourceManager] Zarejestrowano okno: {name}")

    def unregister_window(self, window):
        """Wyrejestrowuje okno"""
        self.open_windows = [w for w in self.open_windows if w['window'] != window]
        print(f"[ResourceManager] Wyrejestrowano okno")

    def stop_all_sounds(self):
        """Zatrzymuje wszystkie dźwięki"""
        try:
            pygame.mixer.stop()
            print("[ResourceManager] Zatrzymano wszystkie dźwięki")
        except Exception as e:
            print(f"[ResourceManager] Błąd zatrzymywania dźwięków: {e}")

    def force_garbage_collection(self):
        """Wymusza garbage collection"""
        collected = gc.collect()
        print(f"[ResourceManager] Garbage collection: {collected} obiektów")
        return collected

    def get_status(self):
        """Zwraca status menedżera"""
        return {
            'pygame_initialized': self.pygame_initialized,
            'open_windows': len(self.open_windows),
            'cached_files': len(self.cached_files),
            'active_sounds': len(self.active_sounds)
        }

    def shutdown(self):
        """Zamyka wszystkie zasoby"""
        print("[ResourceManager] Zamykanie zasobów...")

        self.stop_all_sounds()

        # Zamknij wszystkie okna
        for win_info in self.open_windows[:]:
            try:
                win_info['window'].destroy()
            except:
                pass

        # Zamknij pygame
        if self.pygame_initialized:
            try:
                pygame.mixer.quit()
                pygame.quit()
                print("[ResourceManager] Pygame zamknięty")
            except:
                pass

        print("[ResourceManager] Zasoby zamknięte")


# Funkcja pomocnicza - zwraca singleton
def get_resource_manager():
    """Zwraca instancję ResourceManager (singleton)"""
    return ResourceManager()
