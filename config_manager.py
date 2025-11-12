"""
Config Manager - Centralne zarządzanie konfiguracją aplikacji
Jeden plik JSON dla wszystkich ustawień
"""

import json
import os
from datetime import datetime


class ConfigManager:
    """
    Menedżer konfiguracji aplikacji.
    Singleton - tylko jedna instancja.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True

        # Ścieżka do pliku konfiguracji
        self.config_file = "audio_tool_config.json"

        # Domyślna konfiguracja
        self.default_config = {
            # === APLIKACJA ===
            'app': {
                'version': '1.0.0',
                'first_run': True,
                'last_used': None,
                'window_geometry': {
                    'main': '550x600',
                    'music_player': '700x600',
                    'tone_generator': '600x700'
                }
            },

            # === AUDIO ===
            'audio': {
                'sample_rate': 44100,
                'buffer_size': 512,
                'default_volume': 70,
                'max_volume': 100,
                'channels': 2
            },

            # === MUSIC PLAYER ===
            'music_player': {
                'last_files': [],
                'max_recent_files': 10,
                'last_volume': 70,
                'auto_save_state': True,
                'supported_formats': ['.mp3', '.wav', '.ogg', '.flac', '.m4a'],
                'max_file_size_mb': 500
            },

            # === TONE GENERATOR ===
            'tone_generator': {
                'last_frequency': 440.0,
                'last_wave_type': 'sine',
                'last_volume': 30,
                'frequency_range': [20, 20000]
            },

            # === ŚCIEŻKI ===
            'paths': {
                'last_open_directory': os.path.expanduser("~"),
                'default_music_folder': os.path.expanduser("~/Music"),
                'logs_directory': './logs'
            },

            # === UI ===
            'ui': {
                'theme': 'default',
                'font_size': 10,
                'show_tooltips': True,
                'confirm_exit': True
            },

            # === ZAAWANSOWANE ===
            'advanced': {
                'enable_logging': False,
                'debug_mode': False,
                'validate_file_integrity': True,
                'auto_garbage_collection': True
            }
        }

        # Aktualna konfiguracja (załadowana lub domyślna)
        self.config = {}

        # Załaduj konfigurację
        self.load_config()

        print(f"[ConfigManager] Konfiguracja załadowana z: {self.config_file}")

    # === ŁADOWANIE I ZAPISYWANIE ===

    def load_config(self):
        """Ładuje konfigurację z pliku JSON"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)

                # Merge z domyślną konfiguracją (dodaje brakujące klucze)
                self.config = self._merge_configs(self.default_config, loaded_config)

                print("[ConfigManager] Konfiguracja załadowana pomyślnie")
                return True

            except json.JSONDecodeError as e:
                print(f"[ConfigManager] Błąd parsowania JSON: {e}")
                self.config = self.default_config.copy()
                return False
            except Exception as e:
                print(f"[ConfigManager] Błąd ładowania konfiguracji: {e}")
                self.config = self.default_config.copy()
                return False
        else:
            # Pierwszy start - użyj domyślnej konfiguracji
            print("[ConfigManager] Pierwszy start - tworzenie domyślnej konfiguracji")
            self.config = self.default_config.copy()
            self.save_config()
            return True

    def save_config(self):
        """Zapisuje konfigurację do pliku JSON"""
        try:
            # Aktualizuj czas ostatniego użycia
            self.config['app']['last_used'] = datetime.now().isoformat()

            # Zapisz z ładnym formatowaniem
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)

            print("[ConfigManager] Konfiguracja zapisana")
            return True

        except IOError as e:
            print(f"[ConfigManager] Błąd zapisu: {e}")
            return False
        except Exception as e:
            print(f"[ConfigManager] Nieoczekiwany błąd zapisu: {e}")
            return False

    def _merge_configs(self, default, loaded):
        """
        Łączy domyślną konfigurację z załadowaną.
        Dodaje brakujące klucze z default do loaded.
        """
        merged = loaded.copy()

        for key, value in default.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(value, dict) and isinstance(merged[key], dict):
                merged[key] = self._merge_configs(value, merged[key])

        return merged

    # === GETTERY ===

    def get(self, key_path, default=None):
        """
        Pobiera wartość z konfiguracji.

        Args:
            key_path: Ścieżka do klucza, np. "audio.default_volume"
            default: Wartość domyślna jeśli klucz nie istnieje

        Returns:
            Wartość z konfiguracji lub default
        """
        keys = key_path.split('.')
        value = self.config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def get_audio_config(self):
        """Zwraca konfigurację audio"""
        return self.config.get('audio', {})

    def get_music_player_config(self):
        """Zwraca konfigurację music playera"""
        return self.config.get('music_player', {})

    def get_tone_generator_config(self):
        """Zwraca konfigurację generatora tonów"""
        return self.config.get('tone_generator', {})

    def get_ui_config(self):
        """Zwraca konfigurację UI"""
        return self.config.get('ui', {})

    # === SETTERY ===

    def set(self, key_path, value):
        """
        Ustawia wartość w konfiguracji.

        Args:
            key_path: Ścieżka do klucza, np. "audio.default_volume"
            value: Nowa wartość
        """
        keys = key_path.split('.')
        config = self.config

        # Przejdź do przedostatniego klucza
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # Ustaw wartość
        config[keys[-1]] = value

    def update_music_player_state(self, files=None, volume=None):
        """Aktualizuje stan music playera"""
        if files is not None:
            self.config['music_player']['last_files'] = files[:10]  # Max 10
        if volume is not None:
            self.config['music_player']['last_volume'] = volume

        self.save_config()

    def update_tone_generator_state(self, frequency=None, wave_type=None, volume=None):
        """Aktualizuje stan generatora tonów"""
        if frequency is not None:
            self.config['tone_generator']['last_frequency'] = frequency
        if wave_type is not None:
            self.config['tone_generator']['last_wave_type'] = wave_type
        if volume is not None:
            self.config['tone_generator']['last_volume'] = volume

        self.save_config()

    # === RESET ===

    def reset_to_defaults(self):
        """Resetuje konfigurację do wartości domyślnych"""
        self.config = self.default_config.copy()
        self.save_config()
        print("[ConfigManager] Konfiguracja zresetowana do domyślnej")

    def reset_section(self, section):
        """
        Resetuje jedną sekcję konfiguracji.

        Args:
            section: Nazwa sekcji (np. 'audio', 'music_player')
        """
        if section in self.default_config:
            self.config[section] = self.default_config[section].copy()
            self.save_config()
            print(f"[ConfigManager] Sekcja '{section}' zresetowana")

    # === INFO ===

    def print_config(self):
        """Wypisuje całą konfigurację do konsoli"""
        print("[ConfigManager] === KONFIGURACJA ===")
        print(json.dumps(self.config, indent=2, ensure_ascii=False))
        print("=" * 40)


# === SINGLETON - łatwy dostęp ===
def get_config_manager():
    """Zwraca globalną instancję ConfigManager"""
    return ConfigManager()
