"""
Menedżer Konfiguracji
Centralne zarządzanie ustawieniami aplikacji
"""

import json
import os


class ConfigManager:
    """Singleton - Menedżer konfiguracji aplikacji"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.config_file = "audio_tool_config.json"
        self.config = {}
        self._initialized = True

        self.load_config()

    def load_config(self):
        """Ładuje konfigurację z pliku JSON"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                print(f"[ConfigManager] Konfiguracja załadowana pomyślnie")
                print(f"[ConfigManager] Konfiguracja załadowana z: {self.config_file}")
            except Exception as e:
                print(f"[ConfigManager] Błąd wczytywania konfiguracji: {e}")
                self.reset_to_defaults()
        else:
            print(f"[ConfigManager] Brak pliku konfiguracyjnego - tworzenie domyślnego")
            self.reset_to_defaults()

    def save_config(self):
        """Zapisuje konfigurację do pliku JSON"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print(f"[ConfigManager] Konfiguracja zapisana")
        except Exception as e:
            print(f"[ConfigManager] Błąd zapisu konfiguracji: {e}")

    def reload_config(self):
        """Przeładowuje konfigurację z pliku"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
        except:
            pass

    def get(self, key_path, default=None):
        """
        Pobiera wartość z konfiguracji używając ścieżki z kropkami
        Przykład: get('app.version', '1.0.0')
        """
        keys = key_path.split('.')
        value = self.config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key_path, value):
        """
        Ustawia wartość w konfiguracji używając ścieżki z kropkami
        Przykład: set('app.version', '1.1.0')
        """
        keys = key_path.split('.')
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def get_audio_config(self):
        """Zwraca konfigurację audio"""
        return self.config.get('audio', {})

    def reset_to_defaults(self):
        """Resetuje konfigurację do wartości domyślnych"""
        self.config = {
            "app": {
                "version": "1.0.0",
                "first_run": True,
                "window_geometry": {
                    "music_player": "650x580",
                    "tone_generator": "580x680"
                }
            },
            "security": {
                "engineering_password": "bose2024"
            },
            "operators": {
                "hrid_list": [
                    "OP001",
                    "OP002",
                    "OP003",
                    "ADMIN",
                    "TEST"
                ]
            },
            "audio": {
                "sample_rate": 44100,
                "channels": 2,
                "buffer_size": 512
            },
            "music_player": {
                "default_volume": 50,
                "max_volume": 82,
                "playlist": [],
                "equalizer": {
                    "60Hz": 0,
                    "250Hz": 0,
                    "1kHz": 0,
                    "4kHz": 0,
                    "16kHz": 0
                }
            },
            "tone_generator": {
                "default_frequency": 1000,
                "default_volume": 50,
                "default_wave": "sine"
            },
            "ui": {
                "theme": "white",
                "confirm_exit": True
            }
        }
        self.save_config()


# Singleton getter
_config_manager_instance = None

def get_config_manager():
    """Zwraca instancję ConfigManager (Singleton)"""
    global _config_manager_instance
    if _config_manager_instance is None:
        _config_manager_instance = ConfigManager()
    return _config_manager_instance
