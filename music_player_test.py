"""
Test 1: Odtwarzacz Muzyki
Moduł testowy dla Audio Testing Multi-Tool
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pygame
import os
import json


class MusicPlayerTest:
    """
    Test odtwarzacza muzyki z kontrolą głośności i przewijaniem.
    Prosty odtwarzacz do testowania jakości dźwięku słuchawek/głośników.
    """

    def __init__(self, parent_window):
        """
        Inicjalizacja testu odtwarzacza.

        Args:
            parent_window: Okno rodzic (tk.Toplevel) w którym test jest wyświetlany
        """
        self.window = parent_window

        # Zmienne stanu odtwarzacza
        self.current_file = None      # Aktualnie załadowany plik
        self.is_playing = False       # Czy muzyka jest odtwarzana
        self.volume = 0.7            # Głośność (0.0 - 1.0)
        self.current_position = 0     # Aktualna pozycja w ms
        self.config_file = "music_player_config.json"  # Plik z konfiguracją

        # DOMYŚLNE WARTOŚCI
        self.default_volume = 70     # Domyślna głośność w procentach

        # Ustawienie zamykania okna
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Budowanie interfejsu
        self.create_widgets()

        # Załadowanie zapisanego stanu
        self.load_state()

    def create_widgets(self):
        """
        Tworzy wszystkie widgety (elementy interfejsu) testu.
        Wersja z przewijaniem ±10 sekund.
        """

        # === GŁÓWNY KONTENER ===
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # === SEKCJA WYBORU PLIKÓW ===
        file_frame = ttk.LabelFrame(main_frame, text="Wybór utworu", padding="10")
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)

        # Listbox z plikami audio
        self.file_listbox = tk.Listbox(file_frame, height=10, width=80)
        self.file_listbox.grid(row=0, column=0, columnspan=2, pady=5)

        # Przyciski zarządzania listą
        ttk.Button(file_frame, text="Dodaj pliki",
                  command=self.add_files).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(file_frame, text="Usuń zaznaczony",
                  command=self.remove_file).grid(row=1, column=1, padx=5, pady=5)

        # === SEKCJA ODTWARZACZA ===
        player_frame = ttk.LabelFrame(main_frame, text="Odtwarzacz", padding="15")
        player_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)

        # Przyciski sterowania - ROZSZERZONA WERSJA Z PRZEWIJANIEM
        control_frame = ttk.Frame(player_frame)
        control_frame.grid(row=0, column=0, pady=10)

        # Przycisk przewiń wstecz -10s
        ttk.Button(control_frame, text="⏪ -10s",
                  command=self.rewind_10s, width=12).pack(side=tk.LEFT, padx=3)

        # Przycisk Play/Pause
        self.play_button = ttk.Button(control_frame, text="▶ Play",
                                     command=self.play_pause, width=15)
        self.play_button.pack(side=tk.LEFT, padx=3)

        # Przycisk Stop
        ttk.Button(control_frame, text="⏹ Stop",
                  command=self.stop, width=15).pack(side=tk.LEFT, padx=3)

        # Przycisk przewiń do przodu +10s
        ttk.Button(control_frame, text="⏩ +10s",
                  command=self.forward_10s, width=12).pack(side=tk.LEFT, padx=3)

        # Status odtwarzacza
        self.status_label = ttk.Label(player_frame,
                                     text="Brak załadowanego utworu",
                                     font=('Arial', 10))
        self.status_label.grid(row=1, column=0, pady=10)

        # --- Kontrola głośności ---
        volume_frame = ttk.LabelFrame(player_frame, text="Głośność", padding="10")
        volume_frame.grid(row=2, column=0, pady=10, sticky=(tk.W, tk.E))

        # Kontener na suwak i etykietę
        vol_control = ttk.Frame(volume_frame)
        vol_control.pack(expand=True)

        # WAŻNE: Label przed Scale!
        self.volume_label = ttk.Label(vol_control, text="70%", width=8,
                                     font=('Arial', 11, 'bold'))
        self.volume_label.pack(side=tk.RIGHT, padx=10)

        # Suwak głośności
        self.volume_scale = ttk.Scale(vol_control, from_=0, to=100,
                                     orient=tk.HORIZONTAL,
                                     command=self.change_volume, length=400)
        self.volume_scale.set(70)
        self.volume_scale.pack(side=tk.LEFT, padx=10)

        # === SEPARATOR I PRZYCISKI ===
        ttk.Separator(main_frame, orient='horizontal').grid(row=2, column=0,
                                                            sticky=(tk.W, tk.E),
                                                            pady=15)

        button_frame = ttk.Frame(main_frame, padding="5")
        button_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))

        # Przycisk przywracania domyślnych
        ttk.Button(button_frame, text="⚙ Przywróć ustawienia domyślne",
                  command=self.restore_defaults, width=30).pack(side=tk.LEFT, padx=10)

        # Przycisk zamknięcia testu
        ttk.Button(button_frame, text="✖ Zamknij test",
                  command=self.close_test, width=25).pack(side=tk.RIGHT, padx=10)

        # === KONFIGURACJA GRID ===
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

    def add_files(self):
        """Otwiera dialog wyboru plików i dodaje je do listy"""
        files = filedialog.askopenfilenames(
            title="Wybierz pliki audio",
            filetypes=[
                ("Pliki audio", "*.mp3 *.wav *.ogg *.flac"),
                ("Wszystkie pliki", "*.*")
            ]
        )
        for file in files:
            self.file_listbox.insert(tk.END, file)

    def remove_file(self):
        """Usuwa zaznaczony plik z listy"""
        try:
            selected = self.file_listbox.curselection()
            self.file_listbox.delete(selected)
        except:
            pass

    def play_pause(self):
        """Odtwarza lub pauzuje muzykę"""
        if not self.is_playing:
            # Tryb PLAY
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
            # Tryb PAUSE/UNPAUSE
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
                self.play_button.config(text="▶ Play")
                self.is_playing = False
            else:
                pygame.mixer.music.unpause()
                self.play_button.config(text="⏸ Pause")
                self.is_playing = True

    def stop(self):
        """Zatrzymuje odtwarzanie"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.current_position = 0
        self.play_button.config(text="▶ Play")
        self.status_label.config(text="Zatrzymano")

    def rewind_10s(self):
        """
        Przewija utwór 10 sekund wstecz.

        UWAGA: pygame.mixer.music ma ograniczone możliwości przewijania.
        Dla MP3 może nie działać idealnie - najlepiej działa z OGG/WAV.
        """
        if self.current_file and pygame.mixer.music.get_busy():
            try:
                # Pobierz aktualną pozycję w milisekundach
                current_pos = pygame.mixer.music.get_pos()

                # Oblicz nową pozycję (10 sekund = 10000 ms)
                new_pos = max(0, current_pos - 10000)  # Nie mniej niż 0

                # Zatrzymaj i załaduj od nowa z nową pozycją
                pygame.mixer.music.stop()
                pygame.mixer.music.load(self.current_file)
                pygame.mixer.music.play(start=new_pos / 1000.0)  # start w sekundach
                pygame.mixer.music.set_volume(self.volume)

                self.status_label.config(text=f"Przewinięto -10s")

            except Exception as e:
                self.status_label.config(text=f"Błąd przewijania: {str(e)}")
        else:
            messagebox.showwarning("Uwaga", "Najpierw uruchom odtwarzanie!")

    def forward_10s(self):
        """
        Przewija utwór 10 sekund do przodu.

        UWAGA: pygame.mixer.music ma ograniczone możliwości przewijania.
        Dla MP3 może nie działać idealnie - najlepiej działa z OGG/WAV.
        """
        if self.current_file and pygame.mixer.music.get_busy():
            try:
                # Pobierz aktualną pozycję w milisekundach
                current_pos = pygame.mixer.music.get_pos()

                # Oblicz nową pozycję (10 sekund = 10000 ms)
                new_pos = current_pos + 10000

                # Zatrzymaj i załaduj od nowa z nową pozycją
                pygame.mixer.music.stop()
                pygame.mixer.music.load(self.current_file)
                pygame.mixer.music.play(start=new_pos / 1000.0)  # start w sekundach
                pygame.mixer.music.set_volume(self.volume)

                self.status_label.config(text=f"Przewinięto +10s")

            except Exception as e:
                self.status_label.config(text=f"Błąd przewijania: {str(e)}")
        else:
            messagebox.showwarning("Uwaga", "Najpierw uruchom odtwarzanie!")

    def change_volume(self, value):
        """Zmienia głośność"""
        self.volume = float(value) / 100
        pygame.mixer.music.set_volume(self.volume)
        self.volume_label.config(text=f"{int(float(value))}%")

    def restore_defaults(self):
        """Przywraca ustawienia domyślne z potwierdzeniem"""
        response = messagebox.askyesno(
            "Przywracanie ustawień",
            "Czy na pewno chcesz przywrócić głośność do 70%?"
        )

        if response:
            self.volume_scale.set(self.default_volume)
            self.change_volume(self.default_volume)
            messagebox.showinfo("Gotowe",
                              "Głośność została przywrócona do wartości domyślnej!")

    def close_test(self):
        """Zamyka okno testu z zapisem stanu"""
        self.on_closing()

    def save_state(self):
        """Zapisuje stan do JSON"""
        state = {
            'files': list(self.file_listbox.get(0, tk.END)),
            'volume': self.volume_scale.get()
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Błąd zapisu: {e}")

    def load_state(self):
        """Ładuje zapisany stan z JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)

                # Przywróć listę plików
                for file_path in state.get('files', []):
                    if os.path.exists(file_path):
                        self.file_listbox.insert(tk.END, file_path)

                # Przywróć głośność
                volume = state.get('volume', self.default_volume)
                self.volume_scale.set(volume)
                self.change_volume(volume)

        except Exception as e:
            print(f"Błąd odczytu: {e}")

    def on_closing(self):
        """Obsługa zamykania okna testu"""
        self.save_state()
        pygame.mixer.music.stop()
        self.window.destroy()
