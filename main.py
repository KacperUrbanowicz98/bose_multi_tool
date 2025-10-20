import tkinter as tk
from tkinter import ttk, filedialog
import pygame
import os
import json


class AudioTester:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Testing Multi-Tool")
        self.root.geometry("800x600")

        # Inicjalizacja pygame mixer
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        # Zmienne
        self.current_file = None
        self.is_playing = False
        self.volume = 0.7
        self.config_file = "audio_tester_config.json"

        # Słownik z częstotliwościami EQ (Hz)
        self.eq_bands = {
            '60 Hz': 60,
            '170 Hz': 170,
            '310 Hz': 310,
            '600 Hz': 600,
            '1 kHz': 1000,
            '3 kHz': 3000,
            '6 kHz': 6000,
            '12 kHz': 12000,
            '14 kHz': 14000,
            '16 kHz': 16000
        }

        self.eq_values = {band: 0 for band in self.eq_bands.keys()}
        self.eq_scales = {}

        # Ustawienie zamykania okna
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.create_widgets()
        self.load_state()  # Załaduj zapisany stan

    def create_widgets(self):
        # Główny kontener
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Sekcja wyboru pliku
        file_frame = ttk.LabelFrame(main_frame, text="Wybór utworu", padding="10")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.file_listbox = tk.Listbox(file_frame, height=6, width=70)
        self.file_listbox.grid(row=0, column=0, columnspan=2, pady=5)

        ttk.Button(file_frame, text="Dodaj pliki", command=self.add_files).grid(row=1, column=0, padx=5)
        ttk.Button(file_frame, text="Usuń zaznaczony", command=self.remove_file).grid(row=1, column=1, padx=5)

        # Sekcja odtwarzacza
        player_frame = ttk.LabelFrame(main_frame, text="Odtwarzacz", padding="10")
        player_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=(0, 5))

        self.play_button = ttk.Button(player_frame, text="▶ Play", command=self.play_pause)
        self.play_button.grid(row=0, column=0, padx=5, pady=5)

        ttk.Button(player_frame, text="⏹ Stop", command=self.stop).grid(row=0, column=1, padx=5, pady=5)

        self.status_label = ttk.Label(player_frame, text="Brak załadowanego utworu")
        self.status_label.grid(row=1, column=0, columnspan=2, pady=5)

        # Kontrola głośności
        volume_frame = ttk.LabelFrame(player_frame, text="Głośność", padding="5")
        volume_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))

        # POPRAWKA: Label PRZED scale
        self.volume_label = ttk.Label(volume_frame, text="70%", width=8)
        self.volume_label.grid(row=0, column=1, padx=5)

        self.volume_scale = ttk.Scale(volume_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                      command=self.change_volume, length=200)
        self.volume_scale.set(70)
        self.volume_scale.grid(row=0, column=0, padx=5)

        # Sekcja equalizera
        eq_frame = ttk.LabelFrame(main_frame, text="Equalizer (częstotliwości)", padding="10")
        eq_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Canvas z scrollbarem dla EQ
        eq_canvas = tk.Canvas(eq_frame, height=400, width=300)  # POPRAWKA: Stała szerokość
        scrollbar = ttk.Scrollbar(eq_frame, orient="vertical", command=eq_canvas.yview)
        scrollable_frame = ttk.Frame(eq_canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: eq_canvas.configure(scrollregion=eq_canvas.bbox("all"))
        )

        eq_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        eq_canvas.configure(yscrollcommand=scrollbar.set)

        eq_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Suwaki EQ
        row = 0
        for band_name in self.eq_bands.keys():
            frame = ttk.Frame(scrollable_frame)
            frame.grid(row=row, column=0, pady=5, padx=5, sticky=(tk.W, tk.E))

            label = ttk.Label(frame, text=band_name, width=10)
            label.grid(row=0, column=0, padx=5)

            value_label = ttk.Label(frame, text="0 dB", width=8)
            value_label.grid(row=0, column=2, padx=5)

            self.eq_scales[band_name] = (None, value_label)

            scale = ttk.Scale(frame, from_=-12, to=12, orient=tk.HORIZONTAL,
                              command=lambda val, b=band_name: self.update_eq(b, val), length=150)  # Stała długość
            scale.set(0)
            scale.grid(row=0, column=1, padx=5)

            self.eq_scales[band_name] = (scale, value_label)

            row += 1

        # Przycisk reset EQ
        ttk.Button(eq_frame, text="Reset EQ", command=self.reset_eq).grid(row=1, column=0, pady=10)

        # POPRAWKA: Konfiguracja grid - column 0 bez weight
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=0)  # Player - bez rozciągania
        main_frame.columnconfigure(1, weight=1)  # EQ - może się rozciągać
        main_frame.rowconfigure(1, weight=1)

    def add_files(self):
        files = filedialog.askopenfilenames(
            title="Wybierz pliki audio",
            filetypes=[("Pliki audio", "*.mp3 *.wav *.ogg *.flac"), ("Wszystkie pliki", "*.*")]
        )
        for file in files:
            self.file_listbox.insert(tk.END, file)

    def remove_file(self):
        try:
            selected = self.file_listbox.curselection()
            self.file_listbox.delete(selected)
        except:
            pass

    def play_pause(self):
        if not self.is_playing:
            selected = self.file_listbox.curselection()
            if selected:
                self.current_file = self.file_listbox.get(selected[0])
                try:
                    pygame.mixer.music.load(self.current_file)
                    pygame.mixer.music.set_volume(self.volume)
                    pygame.mixer.music.play()
                    self.is_playing = True
                    self.play_button.config(text="⏸ Pause")
                    filename = os.path.basename(self.current_file)
                    self.status_label.config(text=f"Odtwarzanie: {filename}")
                except Exception as e:
                    self.status_label.config(text=f"Błąd: {str(e)}")
        else:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
                self.play_button.config(text="▶ Play")
                self.is_playing = False
            else:
                pygame.mixer.music.unpause()
                self.play_button.config(text="⏸ Pause")
                self.is_playing = True

    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.play_button.config(text="▶ Play")
        self.status_label.config(text="Zatrzymano")

    def change_volume(self, value):
        self.volume = float(value) / 100
        pygame.mixer.music.set_volume(self.volume)
        self.volume_label.config(text=f"{int(float(value))}%")

    def update_eq(self, band, value):
        value = float(value)
        self.eq_values[band] = value
        scale, label = self.eq_scales[band]
        label.config(text=f"{value:.1f} dB")

    def reset_eq(self):
        for band_name, (scale, label) in self.eq_scales.items():
            scale.set(0)
            label.config(text="0 dB")
            self.eq_values[band_name] = 0

    def save_state(self):
        """Zapisuje stan aplikacji do pliku JSON"""
        state = {
            'files': list(self.file_listbox.get(0, tk.END)),
            'volume': self.volume_scale.get(),
            'eq_values': {band: scale.get() for band, (scale, _) in self.eq_scales.items()}
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Błąd zapisu: {e}")

    def load_state(self):
        """Ładuje zapisany stan aplikacji"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)

                # Przywróć listę plików
                for file_path in state.get('files', []):
                    if os.path.exists(file_path):  # Sprawdź czy plik nadal istnieje
                        self.file_listbox.insert(tk.END, file_path)

                # Przywróć głośność
                volume = state.get('volume', 70)
                self.volume_scale.set(volume)
                self.change_volume(volume)

                # Przywróć ustawienia EQ
                eq_vals = state.get('eq_values', {})
                for band, value in eq_vals.items():
                    if band in self.eq_scales:
                        scale, label = self.eq_scales[band]
                        scale.set(value)
                        label.config(text=f"{float(value):.1f} dB")

        except Exception as e:
            print(f"Błąd odczytu: {e}")

    def on_closing(self):
        """Obsługa zamykania aplikacji"""
        self.save_state()
        pygame.mixer.quit()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioTester(root)
    root.mainloop()
