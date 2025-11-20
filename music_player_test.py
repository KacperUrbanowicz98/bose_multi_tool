"""
Test 1: Odtwarzacz Muzyki
Bose Style - White Theme (wersja polska z playlistą + progressbar + seek)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pygame
import os
import json
import time
from mutagen import File

class MusicPlayerTest:
    def __init__(self, window):
        self.window = window
        self.window.configure(bg='#FFFFFF')

        # === KOLORY BOSE WHITE THEME ===
        self.colors = {
            'bg_main': '#FFFFFF',
            'bg_card': '#F5F5F5',
            'text_primary': '#000000',
            'text_secondary': '#666666',
            'border': '#000000',
            'button_bg': '#FFFFFF',
            'button_fg': '#000000',
            'button_active': '#000000',
            'button_active_fg': '#FFFFFF',
            'slider_bg': '#F5F5F5',
            'slider_fg': '#000000'
        }

        # Inicjalizacja pygame
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        # Zmienne stanu
        self.playlist = []
        self.current_index = -1
        self.current_file = None
        self.is_playing = False
        self.is_paused = False
        self.volume = 50
        self.song_length = 0
        self.update_job = None
        self.start_time = 0  # Czas startu utworu
        self.pause_pos = 0   # Pozycja przy pauzowaniu

        # Ścieżka do pliku konfiguracyjnego
        self.config_file = "audio_tool_config.json"

        # Wczytaj playlistę z poprzedniej sesji
        self.load_playlist_from_config()

        # Tworzenie interfejsu
        self.create_widgets()

        # Automatyczne załadowanie playlisty
        self.refresh_playlist_display()

        # Zatrzymaj muzykę przy zamykaniu okna
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

    def load_playlist_from_config(self):
        """Wczytuje playlistę z konfiguracji"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    saved_playlist = config.get('music_player', {}).get('playlist', [])
                    self.playlist = [f for f in saved_playlist if os.path.exists(f)]
        except:
            pass

    def save_playlist_to_config(self):
        """Zapisuje playlistę do konfiguracji"""
        try:
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            if 'music_player' not in config:
                config['music_player'] = {}

            config['music_player']['playlist'] = self.playlist

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Błąd zapisu playlisty: {e}")

    def create_widgets(self):
        """Tworzenie interfejsu"""
        main_frame = tk.Frame(self.window, bg=self.colors['bg_main'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # === NAGŁÓWEK ===
        header_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        header_frame.pack(fill=tk.X, pady=(0, 12))

        tk.Label(header_frame,
                text="ODTWARZACZ MUZYKI",
                font=('Arial', 16, 'bold'),
                bg=self.colors['bg_main'],
                fg=self.colors['text_primary']).pack()

        tk.Label(header_frame,
                text="Test 1",
                font=('Arial', 8),
                bg=self.colors['bg_main'],
                fg=self.colors['text_secondary']).pack(pady=(2, 0))

        # Separator
        tk.Frame(main_frame, bg=self.colors['border'], height=2).pack(fill=tk.X, pady=(0, 12))

        # === AKTUALNIE ODTWARZANY ===
        info_frame = tk.Frame(main_frame, bg=self.colors['bg_card'], bd=2, relief=tk.SOLID)
        info_frame.pack(fill=tk.X, pady=(0, 12), ipady=10)

        self.file_label = tk.Label(
            info_frame,
            text="BRAK PLIKU",
            font=('Arial', 9, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_secondary']
        )
        self.file_label.pack()

        # Pasek postępu
        progress_container = tk.Frame(info_frame, bg=self.colors['bg_card'])
        progress_container.pack(fill=tk.X, padx=10, pady=(5, 0))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_container,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(fill=tk.X)
        # Bind kliknięcia na pasek
        self.progress_bar.bind('<Button-1>', self.seek_to_position)

        # Etykieta czasu
        self.time_label = tk.Label(
            info_frame,
            text="00:00 / 00:00",
            font=('Arial', 8),
            bg=self.colors['bg_card'],
            fg=self.colors['text_secondary']
        )
        self.time_label.pack(pady=(2, 0))

        # === PLAYLISTA ===
        playlist_frame = tk.LabelFrame(
            main_frame,
            text="PLAYLISTA",
            font=('Arial', 8, 'bold'),
            bg=self.colors['bg_main'],
            fg=self.colors['text_primary'],
            bd=2,
            relief=tk.SOLID
        )
        playlist_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        # Listbox z utworami
        list_container = tk.Frame(playlist_frame, bg=self.colors['bg_main'])
        list_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.playlist_listbox = tk.Listbox(
            list_container,
            font=('Arial', 9),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary'],
            selectbackground=self.colors['text_primary'],
            selectforeground=self.colors['bg_main'],
            bd=0,
            highlightthickness=0,
            yscrollcommand=scrollbar.set,
            height=6
        )
        self.playlist_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.playlist_listbox.yview)

        # Przyciski playlisty
        playlist_btn_frame = tk.Frame(playlist_frame, bg=self.colors['bg_main'])
        playlist_btn_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        tk.Button(playlist_btn_frame,
                 text="+ DODAJ PLIKI",
                 command=self.add_files,
                 bg=self.colors['button_bg'],
                 fg=self.colors['button_fg'],
                 activebackground=self.colors['button_active'],
                 activeforeground=self.colors['button_active_fg'],
                 bd=2,
                 relief=tk.SOLID,
                 font=('Arial', 8),
                 width=14).pack(side=tk.LEFT, padx=2)

        tk.Button(playlist_btn_frame,
                 text="✖ USUŃ",
                 command=self.remove_selected,
                 bg=self.colors['button_bg'],
                 fg=self.colors['button_fg'],
                 activebackground=self.colors['button_active'],
                 activeforeground=self.colors['button_active_fg'],
                 bd=2,
                 relief=tk.SOLID,
                 font=('Arial', 8),
                 width=10).pack(side=tk.LEFT, padx=2)

        tk.Button(playlist_btn_frame,
                 text="🗑 WYCZYŚĆ",
                 command=self.clear_playlist,
                 bg=self.colors['button_bg'],
                 fg=self.colors['button_fg'],
                 activebackground=self.colors['button_active'],
                 activeforeground=self.colors['button_active_fg'],
                 bd=2,
                 relief=tk.SOLID,
                 font=('Arial', 8),
                 width=10).pack(side=tk.LEFT, padx=2)

        # === STEROWANIE ===
        controls_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        controls_frame.pack(pady=10)

        # Przewijanie
        seek_frame = tk.Frame(controls_frame, bg=self.colors['bg_main'])
        seek_frame.pack(pady=(0, 6))

        self.rewind_btn = tk.Button(
            seek_frame,
            text="⏪ -10s",
            font=('Arial', 8, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_secondary'],
            activebackground=self.colors['button_active'],
            activeforeground=self.colors['button_active_fg'],
            bd=2,
            relief=tk.SOLID,
            width=9,
            state=tk.DISABLED,
            command=self.rewind_10s
        )
        self.rewind_btn.pack(side=tk.LEFT, padx=3)

        self.forward_btn = tk.Button(
            seek_frame,
            text="⏩ +10s",
            font=('Arial', 8, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_secondary'],
            activebackground=self.colors['button_active'],
            activeforeground=self.colors['button_active_fg'],
            bd=2,
            relief=tk.SOLID,
            width=9,
            state=tk.DISABLED,
            command=self.forward_10s
        )
        self.forward_btn.pack(side=tk.LEFT, padx=3)

        # Play/Pause/Stop
        playback_frame = tk.Frame(controls_frame, bg=self.colors['bg_main'])
        playback_frame.pack()

        self.play_btn = tk.Button(
            playback_frame,
            text="▶ PLAY",
            font=('Arial', 8, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_secondary'],
            activebackground=self.colors['button_active'],
            activeforeground=self.colors['button_active_fg'],
            bd=2,
            relief=tk.SOLID,
            width=9,
            state=tk.DISABLED,
            command=self.play_music
        )
        self.play_btn.pack(side=tk.LEFT, padx=3)

        self.pause_btn = tk.Button(
            playback_frame,
            text="⏸ PAUZA",
            font=('Arial', 8, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_secondary'],
            activebackground=self.colors['button_active'],
            activeforeground=self.colors['button_active_fg'],
            bd=2,
            relief=tk.SOLID,
            width=9,
            state=tk.DISABLED,
            command=self.pause_music
        )
        self.pause_btn.pack(side=tk.LEFT, padx=3)

        self.stop_btn = tk.Button(
            playback_frame,
            text="⏹ STOP",
            font=('Arial', 8, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_secondary'],
            activebackground=self.colors['button_active'],
            activeforeground=self.colors['button_active_fg'],
            bd=2,
            relief=tk.SOLID,
            width=9,
            state=tk.DISABLED,
            command=self.stop_music
        )
        self.stop_btn.pack(side=tk.LEFT, padx=3)

        # === GŁOŚNOŚĆ (MAX 82%) ===
        volume_frame = tk.LabelFrame(
            main_frame,
            text="GŁOŚNOŚĆ",
            font=('Arial', 8, 'bold'),
            bg=self.colors['bg_main'],
            fg=self.colors['text_primary'],
            bd=2,
            relief=tk.SOLID
        )
        volume_frame.pack(fill=tk.X, pady=(10, 0))

        vol_container = tk.Frame(volume_frame, bg=self.colors['bg_main'])
        vol_container.pack(fill=tk.X, padx=8, pady=6)

        tk.Label(vol_container,
                text="0%",
                bg=self.colors['bg_main'],
                fg=self.colors['text_secondary'],
                font=('Arial', 7)).pack(side=tk.LEFT)

        self.volume_slider = tk.Scale(
            vol_container,
            from_=0,
            to=82,
            orient=tk.HORIZONTAL,
            bg=self.colors['bg_main'],
            fg=self.colors['text_primary'],
            troughcolor=self.colors['slider_bg'],
            highlightthickness=0,
            command=self.change_volume,
            showvalue=0,
            bd=0,
            relief=tk.FLAT
        )
        self.volume_slider.set(self.volume)
        self.volume_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

        tk.Label(vol_container,
                text="82%",
                bg=self.colors['bg_main'],
                fg=self.colors['text_secondary'],
                font=('Arial', 7)).pack(side=tk.RIGHT)

        self.volume_label = tk.Label(
            volume_frame,
            text=f"POZIOM: {self.volume}%",
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary'],
            font=('Arial', 8)
        )
        self.volume_label.pack(pady=(0, 6))

        # === POWRÓT ===
        tk.Button(main_frame,
                 text="← POWRÓT DO MENU",
                 command=self.close_window,
                 bg=self.colors['bg_main'],
                 fg=self.colors['text_secondary'],
                 activebackground=self.colors['button_active'],
                 activeforeground=self.colors['button_active_fg'],
                 bd=2,
                 relief=tk.SOLID,
                 font=('Arial', 8),
                 width=20).pack(pady=(12, 0))

    def add_files(self):
        """Dodaje pliki do playlisty"""
        file_paths = filedialog.askopenfilenames(
            title="Wybierz pliki audio",
            filetypes=[
                ("Pliki audio", "*.mp3 *.wav *.ogg"),
                ("Pliki MP3", "*.mp3"),
                ("Pliki WAV", "*.wav"),
                ("Pliki OGG", "*.ogg"),
                ("Wszystkie pliki", "*.*")
            ]
        )

        if file_paths:
            for path in file_paths:
                if path not in self.playlist:
                    self.playlist.append(path)

            self.refresh_playlist_display()
            self.save_playlist_to_config()

            # Przywróć focus na to okno
            self.window.lift()
            self.window.focus_force()

    def remove_selected(self):
        """Usuwa zaznaczony utwór"""
        selection = self.playlist_listbox.curselection()
        if selection:
            index = selection[0]
            del self.playlist[index]
            self.refresh_playlist_display()
            self.save_playlist_to_config()

            if index == self.current_index:
                self.stop_music()
                self.current_index = -1

    def clear_playlist(self):
        """Czyści całą playlistę"""
        if messagebox.askyesno("Potwierdzenie", "Wyczyścić całą playlistę?"):
            self.stop_music()
            self.playlist = []
            self.current_index = -1
            self.refresh_playlist_display()
            self.save_playlist_to_config()

    def refresh_playlist_display(self):
        """Odświeża wyświetlanie playlisty"""
        self.playlist_listbox.delete(0, tk.END)
        for i, filepath in enumerate(self.playlist):
            filename = os.path.basename(filepath)
            prefix = "▶ " if i == self.current_index else "  "
            self.playlist_listbox.insert(tk.END, f"{prefix}{filename}")

        if self.playlist:
            self.play_btn.config(state=tk.NORMAL, bg=self.colors['button_bg'], fg=self.colors['button_fg'])
        else:
            self.play_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])

    def load_and_play(self, filepath):
        """Ładuje i odtwarza plik"""
        try:
            # NAJPIERW pobierz długość utworu
            self.song_length = self.get_song_length(filepath)

            pygame.mixer.music.load(filepath)
            self.current_file = filepath
            filename = os.path.basename(filepath)

            self.file_label.config(
                text=filename.upper(),
                fg=self.colors['text_primary']
            )

            pygame.mixer.music.play()
            pygame.mixer.music.set_volume(self.volume / 82.0)
            self.is_playing = True
            self.is_paused = False

            # Zapisz czas startu
            self.start_time = time.time()

            self.refresh_playlist_display()
            self.update_buttons_playing()

            # Uruchom aktualizację paska postępu
            if self.update_job:
                self.window.after_cancel(self.update_job)
            self.update_progress()

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można odtworzyć:\n{str(e)}")

    def play_music(self):
        """Odtwarza muzykę"""
        if not self.playlist:
            messagebox.showwarning("Uwaga", "Playlista jest pusta")
            return

        selection = self.playlist_listbox.curselection()
        if selection:
            self.current_index = selection[0]
        elif self.current_index == -1:
            self.current_index = 0

        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.is_playing = True

            # Aktualizuj czas startu po wznowieniu
            self.start_time = time.time() - self.pause_pos

            if self.update_job:
                self.window.after_cancel(self.update_job)
            self.update_progress()
        else:
            self.load_and_play(self.playlist[self.current_index])

        self.update_buttons_playing()

    def pause_music(self):
        """Pauzuje"""
        if self.is_playing and not self.is_paused:
            # Zapisz pozycję przy pauzowaniu
            self.pause_pos = time.time() - self.start_time

            pygame.mixer.music.pause()
            self.is_paused = True

            if self.update_job:
                self.window.after_cancel(self.update_job)
                self.update_job = None

            self.update_buttons_paused()

    def stop_music(self):
        """Zatrzymuje"""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False

        if self.update_job:
            self.window.after_cancel(self.update_job)
            self.update_job = None

        self.progress_var.set(0)
        self.time_label.config(text="00:00 / 00:00")

        self.update_buttons_stopped()

    def rewind_10s(self):
        """Cofa o 10 sekund"""
        if self.is_playing and not self.is_paused and self.current_file:
            try:
                # Oblicz aktualną pozycję
                elapsed = time.time() - self.start_time
                new_pos = max(0, elapsed - 10)

                # Zatrzymaj i uruchom od nowej pozycji
                pygame.mixer.music.stop()
                pygame.mixer.music.load(self.current_file)
                pygame.mixer.music.play(start=new_pos)
                pygame.mixer.music.set_volume(self.volume / 82.0)

                # Aktualizuj czas startu
                self.start_time = time.time() - new_pos

            except Exception as e:
                print(f"Błąd przewijania: {e}")

    def forward_10s(self):
        """Przewija o 10 sekund"""
        if self.is_playing and not self.is_paused and self.current_file:
            try:
                # Oblicz aktualną pozycję
                elapsed = time.time() - self.start_time
                new_pos = elapsed + 10

                # Zatrzymaj i uruchom od nowej pozycji
                pygame.mixer.music.stop()
                pygame.mixer.music.load(self.current_file)
                pygame.mixer.music.play(start=new_pos)
                pygame.mixer.music.set_volume(self.volume / 82.0)

                # Aktualizuj czas startu
                self.start_time = time.time() - new_pos

            except Exception as e:
                print(f"Błąd przewijania: {e}")

    def seek_to_position(self, event):
        """Przewija do klikniętej pozycji na pasku"""
        if self.is_playing and self.song_length > 0 and self.current_file:
            try:
                # Oblicz procent kliknięcia
                click_pos = event.x
                total_width = self.progress_bar.winfo_width()
                percent = (click_pos / total_width) * 100
                percent = max(0, min(100, percent))

                # Oblicz nową pozycję w sekundach
                new_pos = (percent / 100) * self.song_length

                # Przewiń
                pygame.mixer.music.stop()
                pygame.mixer.music.load(self.current_file)
                pygame.mixer.music.play(start=new_pos)
                pygame.mixer.music.set_volume(self.volume / 82.0)

                # Aktualizuj czas startu
                self.start_time = time.time() - new_pos

            except Exception as e:
                print(f"Błąd przewijania: {e}")

    def change_volume(self, value):
        """Zmienia głośność"""
        self.volume = int(float(value))
        pygame.mixer.music.set_volume(self.volume / 82.0)
        self.volume_label.config(text=f"POZIOM: {self.volume}%")

    def update_progress(self):
        """Aktualizuje pasek postępu i czas"""
        if self.is_playing and not self.is_paused:
            try:
                # Oblicz aktualną pozycję od początku utworu
                pos_sec = time.time() - self.start_time

                # Aktualizuj pasek
                if self.song_length > 0:
                    progress = (pos_sec / self.song_length) * 100
                    self.progress_var.set(min(progress, 100))
                else:
                    # Jeśli nie znamy długości, użyj get_pos jako fallback
                    pos_ms = pygame.mixer.music.get_pos()
                    if pos_ms >= 0:
                        pos_sec = pos_ms / 1000.0

                # Formatuj czas
                current_time = self.format_time(pos_sec)
                total_time = self.format_time(self.song_length) if self.song_length > 0 else "00:00"
                self.time_label.config(text=f"{current_time} / {total_time}")
            except:
                pass

        # Zaplanuj następną aktualizację (co 100ms)
        if self.is_playing:
            self.update_job = self.window.after(100, self.update_progress)

    def format_time(self, seconds):
        """Formatuje sekundy na MM:SS"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def get_song_length(self, filepath):
        """Odczytuje długość utworu w sekundach"""
        try:
            audio = File(filepath)
            if audio is not None and hasattr(audio.info, 'length'):
                return audio.info.length
            return 0
        except:
            return 0

    def update_buttons_playing(self):
        """Aktualizuje przyciski - stan playing"""
        self.play_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.pause_btn.config(state=tk.NORMAL, bg=self.colors['button_bg'], fg=self.colors['button_fg'])
        self.stop_btn.config(state=tk.NORMAL, bg=self.colors['button_bg'], fg=self.colors['button_fg'])
        self.rewind_btn.config(state=tk.NORMAL, bg=self.colors['button_bg'], fg=self.colors['button_fg'])
        self.forward_btn.config(state=tk.NORMAL, bg=self.colors['button_bg'], fg=self.colors['button_fg'])

    def update_buttons_paused(self):
        """Aktualizuje przyciski - stan paused"""
        self.play_btn.config(state=tk.NORMAL, bg=self.colors['button_bg'], fg=self.colors['button_fg'])
        self.pause_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])

    def update_buttons_stopped(self):
        """Aktualizuje przyciski - stan stopped"""
        self.play_btn.config(state=tk.NORMAL if self.playlist else tk.DISABLED,
                             bg=self.colors['button_bg'] if self.playlist else self.colors['bg_card'],
                             fg=self.colors['button_fg'] if self.playlist else self.colors['text_secondary'])
        self.pause_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.stop_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.rewind_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.forward_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])

    def close_window(self):
        """Zamyka okno"""
        try:
            # Anuluj aktualizację
            if self.update_job:
                self.window.after_cancel(self.update_job)

            # Zatrzymaj muzykę
            if self.is_playing:
                pygame.mixer.music.stop()

            # Zapisz playlistę
            self.save_playlist_to_config()

            self.window.destroy()
        except Exception as e:
            print(f"Błąd zamykania: {e}")
            self.window.destroy()
