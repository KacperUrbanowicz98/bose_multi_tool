"""
Test 1: Odtwarzacz Muzyki
Bose Style - White Theme (wersja polska z playlistą + progressbar + seek)
Fragment per-utwór pobierany z configu (Tryb Inżynieryjny)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pygame
import os
import json
import time
from mutagen import File
from datetime import datetime
from test_reporter import get_test_reporter


class MusicPlayerTest:
    def __init__(self, window, operator_hrid="UNKNOWN", device_serial=None, scan_callback=None):
        self.window = window
        self.operator_hrid = operator_hrid
        self.device_serial = device_serial
        self.scan_callback = scan_callback

        self.window.configure(bg='#FFFFFF')

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

        if not pygame.mixer.get_init():
            pygame.mixer.init()

        self.playlist = []
        self.current_index = -1
        self.current_file = None
        self.is_playing = False
        self.is_paused = False
        self.volume = 50
        self.song_length = 0
        self.update_job = None
        self.start_time = 0
        self.pause_pos = 0

        # Fragment per-utwór — pobierany z configu
        self.fragment_start = 0
        self.fragment_end = 0
        self.fragment_enabled = False
        self.fragments_config = {}

        # Auto test
        self.auto_test_running = False
        self.auto_test_job = None
        self.auto_test_step = 0
        self.auto_test_volumes = list(range(10, 83, 10))
        self.auto_test_duration = 5000
        self.auto_test_start_time = None

        self.config_file = "audio_tool_config.json"

        self.load_playlist_from_config()
        self.create_widgets()
        self.refresh_playlist_display()

        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

    # ─────────────────────────────────────────
    # CONFIG
    # ─────────────────────────────────────────

    def load_playlist_from_config(self):
        """Wczytuje playlistę i fragmenty z konfiguracji"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                mp = config.get('music_player', {})
                saved_playlist = mp.get('playlist', [])
                self.playlist = [f for f in saved_playlist if os.path.exists(f)]
                self.fragments_config = mp.get('fragments', {})
        except:
            pass

    def save_playlist_to_config(self):
        """Zapisuje playlistę do konfiguracji (fragmenty są zarządzane przez Tryb Inżynieryjny)"""
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

    def reload_fragments_config(self):
        """Przeładowuje fragmenty z pliku configu (bez nadpisywania playlisty)"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.fragments_config = config.get('music_player', {}).get('fragments', {})
        except:
            pass

    def get_fragment_for_file(self, filepath):
        """Zwraca (start_pct, end_pct) dla pliku, domyślnie (0, 100)"""
        frag = self.fragments_config.get(filepath, {})
        return frag.get('start_pct', 0), frag.get('end_pct', 100)

    # ─────────────────────────────────────────
    # UI
    # ─────────────────────────────────────────

    def create_widgets(self):
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
        self.progress_bar.bind('<Button-1>', self.seek_to_position)

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

        tk.Label(playlist_frame,
                 text="Wybierz utwór klikając na liście:",
                 font=('Arial', 8),
                 bg=self.colors['bg_main'],
                 fg=self.colors['text_secondary']).pack(anchor='w', padx=8, pady=(0, 6))

        # === INFO O FRAGMENCIE (tylko do odczytu — konfiguracja w Trybie Inżynieryjnym) ===
        self.fragment_info_frame = tk.Frame(
            main_frame,
            bg=self.colors['bg_card'],
            relief=tk.SOLID,
            bd=1
        )
        self.fragment_info_frame.pack(fill=tk.X, pady=(0, 12))

        self.fragment_info_label = tk.Label(
            self.fragment_info_frame,
            text="Fragment: cały utwór  |  Konfiguruj w Trybie Inżynieryjnym",
            font=('Arial', 8),
            bg=self.colors['bg_card'],
            fg=self.colors['text_secondary']
        )
        self.fragment_info_label.pack(padx=10, pady=6)

        # === AUTOMATYCZNY TEST ===
        auto_test_frame = tk.LabelFrame(
            main_frame,
            text="AUTOMATYCZNY TEST",
            font=('Arial', 8, 'bold'),
            bg=self.colors['bg_main'],
            fg=self.colors['text_primary'],
            bd=2,
            relief=tk.SOLID
        )
        auto_test_frame.pack(fill=tk.X, pady=(0, 12))

        auto_container = tk.Frame(auto_test_frame, bg=self.colors['bg_main'])
        auto_container.pack(fill=tk.X, padx=8, pady=8)

        self.auto_description_label = tk.Label(
            auto_container,
            text="Test głośności: 10% → 82% (5s na poziom)",
            font=('Arial', 8),
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary']
        )
        self.auto_description_label.pack(pady=(0, 5))

        auto_buttons = tk.Frame(auto_container, bg=self.colors['bg_main'])
        auto_buttons.pack()

        self.auto_start_btn = tk.Button(
            auto_buttons,
            text="▶ START AUTO TEST",
            font=('Arial', 8, 'bold'),
            bg=self.colors['button_bg'], fg=self.colors['button_fg'],
            activebackground=self.colors['button_active'],
            activeforeground=self.colors['button_active_fg'],
            bd=2, relief=tk.SOLID, width=18,
            state=tk.DISABLED,
            command=self.start_auto_test
        )
        self.auto_start_btn.pack(side=tk.LEFT, padx=3)

        self.auto_stop_btn = tk.Button(
            auto_buttons,
            text="⏹ STOP AUTO TEST",
            font=('Arial', 8, 'bold'),
            bg=self.colors['button_bg'], fg=self.colors['button_fg'],
            activebackground=self.colors['button_active'],
            activeforeground=self.colors['button_active_fg'],
            bd=2, relief=tk.SOLID, width=18,
            state=tk.DISABLED,
            command=self.stop_auto_test
        )
        self.auto_stop_btn.pack(side=tk.LEFT, padx=3)

        self.auto_status_label = tk.Label(
            auto_container,
            text="",
            font=('Arial', 8),
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary']
        )
        self.auto_status_label.pack(pady=(5, 0))

        # === STEROWANIE ===
        controls_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        controls_frame.pack(pady=10)

        seek_frame = tk.Frame(controls_frame, bg=self.colors['bg_main'])
        seek_frame.pack(pady=(0, 6))

        self.rewind_btn = tk.Button(
            seek_frame,
            text="⏪ -10s",
            font=('Arial', 8, 'bold'),
            bg=self.colors['bg_card'], fg=self.colors['text_secondary'],
            activebackground=self.colors['button_active'],
            activeforeground=self.colors['button_active_fg'],
            bd=2, relief=tk.SOLID, width=9,
            state=tk.DISABLED,
            command=self.rewind_10s
        )
        self.rewind_btn.pack(side=tk.LEFT, padx=3)

        self.forward_btn = tk.Button(
            seek_frame,
            text="⏩ +10s",
            font=('Arial', 8, 'bold'),
            bg=self.colors['bg_card'], fg=self.colors['text_secondary'],
            activebackground=self.colors['button_active'],
            activeforeground=self.colors['button_active_fg'],
            bd=2, relief=tk.SOLID, width=9,
            state=tk.DISABLED,
            command=self.forward_10s
        )
        self.forward_btn.pack(side=tk.LEFT, padx=3)

        playback_frame = tk.Frame(controls_frame, bg=self.colors['bg_main'])
        playback_frame.pack()

        self.play_btn = tk.Button(
            playback_frame,
            text="▶ PLAY",
            font=('Arial', 8, 'bold'),
            bg=self.colors['bg_card'], fg=self.colors['text_secondary'],
            activebackground=self.colors['button_active'],
            activeforeground=self.colors['button_active_fg'],
            bd=2, relief=tk.SOLID, width=9,
            state=tk.DISABLED,
            command=self.play_music
        )
        self.play_btn.pack(side=tk.LEFT, padx=3)

        self.pause_btn = tk.Button(
            playback_frame,
            text="⏸ PAUZA",
            font=('Arial', 8, 'bold'),
            bg=self.colors['bg_card'], fg=self.colors['text_secondary'],
            activebackground=self.colors['button_active'],
            activeforeground=self.colors['button_active_fg'],
            bd=2, relief=tk.SOLID, width=9,
            state=tk.DISABLED,
            command=self.pause_music
        )
        self.pause_btn.pack(side=tk.LEFT, padx=3)

        self.stop_btn = tk.Button(
            playback_frame,
            text="⏹ STOP",
            font=('Arial', 8, 'bold'),
            bg=self.colors['bg_card'], fg=self.colors['text_secondary'],
            activebackground=self.colors['button_active'],
            activeforeground=self.colors['button_active_fg'],
            bd=2, relief=tk.SOLID, width=9,
            state=tk.DISABLED,
            command=self.stop_music
        )
        self.stop_btn.pack(side=tk.LEFT, padx=3)

        # === GŁOŚNOŚĆ ===
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

        tk.Label(vol_container, text="0%",
                 bg=self.colors['bg_main'], fg=self.colors['text_secondary'],
                 font=('Arial', 7)).pack(side=tk.LEFT)

        self.volume_slider = tk.Scale(
            vol_container,
            from_=0, to=82,
            orient=tk.HORIZONTAL,
            bg=self.colors['bg_main'], fg=self.colors['text_primary'],
            troughcolor=self.colors['slider_bg'],
            highlightthickness=0,
            command=self.change_volume,
            showvalue=0, bd=0, relief=tk.FLAT
        )
        self.volume_slider.set(self.volume)
        self.volume_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

        tk.Label(vol_container, text="82%",
                 bg=self.colors['bg_main'], fg=self.colors['text_secondary'],
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
                  bd=2, relief=tk.SOLID, font=('Arial', 8),
                  width=20).pack(pady=(12, 0))

    # ─────────────────────────────────────────
    # PLAYLISTA
    # ─────────────────────────────────────────

    def add_files(self):
        file_paths = filedialog.askopenfilenames(
            title="Wybierz pliki audio",
            filetypes=[
                ("Pliki audio", "*.mp3 *.wav *.ogg *.flac"),
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
            self.window.lift()
            self.window.focus_force()

    def remove_selected(self):
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
        if messagebox.askyesno("Potwierdzenie", "Wyczyścić całą playlistę?"):
            self.stop_music()
            self.playlist = []
            self.current_index = -1
            self.refresh_playlist_display()
            self.save_playlist_to_config()

    def refresh_playlist_display(self):
        self.playlist_listbox.delete(0, tk.END)
        for i, filepath in enumerate(self.playlist):
            filename = os.path.basename(filepath)
            prefix = "▶ " if i == self.current_index else "  "
            self.playlist_listbox.insert(tk.END, f"{prefix}{filename}")

        if self.playlist:
            self.play_btn.config(state=tk.NORMAL,
                                 bg=self.colors['button_bg'],
                                 fg=self.colors['button_fg'])
            self.auto_start_btn.config(state=tk.NORMAL,
                                       bg=self.colors['button_bg'],
                                       fg=self.colors['button_fg'])
        else:
            self.play_btn.config(state=tk.DISABLED,
                                 bg=self.colors['bg_card'],
                                 fg=self.colors['text_secondary'])
            self.auto_start_btn.config(state=tk.DISABLED,
                                       bg=self.colors['bg_card'],
                                       fg=self.colors['text_secondary'])

    # ─────────────────────────────────────────
    # ODTWARZANIE
    # ─────────────────────────────────────────

    def load_and_play(self, filepath):
        """Ładuje i odtwarza plik — fragment pobierany z configu per-utwór"""
        try:
            self.song_length = self.get_song_length(filepath)

            # Przeładuj fragmenty z configu (żeby mieć aktualne dane)
            self.reload_fragments_config()

            # Pobierz fragment dla tego konkretnego pliku
            start_pct, end_pct = self.get_fragment_for_file(filepath)
            self.fragment_start = (start_pct / 100.0) * self.song_length
            self.fragment_end = (end_pct / 100.0) * self.song_length
            self.fragment_enabled = (start_pct != 0 or end_pct != 100)

            # Zaktualizuj info-bar
            if self.fragment_enabled:
                self.fragment_info_label.config(
                    text=f"✂ Fragment: {start_pct}% → {end_pct}%  "
                         f"({self.format_time(self.fragment_start)} → {self.format_time(self.fragment_end)})"
                         f"  |  Konfiguruj w Trybie Inżynieryjnym",
                    fg=self.colors['text_primary']
                )
            else:
                self.fragment_info_label.config(
                    text=f"Fragment: cały utwór ({self.format_time(self.song_length)})"
                         f"  |  Konfiguruj w Trybie Inżynieryjnym",
                    fg=self.colors['text_secondary']
                )

            pygame.mixer.music.load(filepath)
            self.current_file = filepath
            filename = os.path.basename(filepath)
            self.file_label.config(text=filename.upper(), fg=self.colors['text_primary'])

            if self.fragment_enabled and self.fragment_start > 0:
                pygame.mixer.music.play(start=self.fragment_start)
                self.start_time = time.time() - self.fragment_start
            else:
                pygame.mixer.music.play()
                self.start_time = time.time()

            pygame.mixer.music.set_volume(self.volume / 82.0)
            self.is_playing = True
            self.is_paused = False

            self.refresh_playlist_display()
            self.update_buttons_playing()

            if self.update_job:
                self.window.after_cancel(self.update_job)
            self.update_progress()

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można odtworzyć:\n{str(e)}")

    def play_music(self):
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
            self.start_time = time.time() - self.pause_pos
            if self.update_job:
                self.window.after_cancel(self.update_job)
            self.update_progress()
        else:
            self.load_and_play(self.playlist[self.current_index])

        self.update_buttons_playing()

    def pause_music(self):
        if self.is_playing and not self.is_paused:
            self.pause_pos = time.time() - self.start_time
            pygame.mixer.music.pause()
            self.is_paused = True
            if self.update_job:
                self.window.after_cancel(self.update_job)
                self.update_job = None
            self.update_buttons_paused()

    def stop_music(self):
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
        if self.is_playing and not self.is_paused and self.current_file:
            try:
                elapsed = time.time() - self.start_time
                new_pos = max(self.fragment_start if self.fragment_enabled else 0,
                              elapsed - 10)
                pygame.mixer.music.stop()
                pygame.mixer.music.load(self.current_file)
                pygame.mixer.music.play(start=new_pos)
                pygame.mixer.music.set_volume(self.volume / 82.0)
                self.start_time = time.time() - new_pos
            except Exception as e:
                print(f"Błąd przewijania: {e}")

    def forward_10s(self):
        if self.is_playing and not self.is_paused and self.current_file:
            try:
                elapsed = time.time() - self.start_time
                new_pos = elapsed + 10
                pygame.mixer.music.stop()
                pygame.mixer.music.load(self.current_file)
                pygame.mixer.music.play(start=new_pos)
                pygame.mixer.music.set_volume(self.volume / 82.0)
                self.start_time = time.time() - new_pos
            except Exception as e:
                print(f"Błąd przewijania: {e}")

    def seek_to_position(self, event):
        if self.is_playing and self.song_length > 0 and self.current_file:
            try:
                click_pos = event.x
                total_width = self.progress_bar.winfo_width()
                percent = (click_pos / total_width) * 100
                percent = max(0, min(100, percent))
                new_pos = (percent / 100) * self.song_length
                pygame.mixer.music.stop()
                pygame.mixer.music.load(self.current_file)
                pygame.mixer.music.play(start=new_pos)
                pygame.mixer.music.set_volume(self.volume / 82.0)
                self.start_time = time.time() - new_pos
            except Exception as e:
                print(f"Błąd przewijania: {e}")

    def change_volume(self, value):
        self.volume = int(float(value))
        pygame.mixer.music.set_volume(self.volume / 82.0)
        self.volume_label.config(text=f"POZIOM: {self.volume}%")

    def update_progress(self):
        if self.is_playing and not self.is_paused:
            try:
                pos_sec = time.time() - self.start_time

                # Pętlowanie fragmentu podczas auto testu
                if (self.fragment_enabled and
                        self.auto_test_running and
                        self.fragment_end > 0 and
                        pos_sec >= self.fragment_end):
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load(self.current_file)
                    pygame.mixer.music.play(start=self.fragment_start)
                    pygame.mixer.music.set_volume(self.volume / 82.0)
                    self.start_time = time.time() - self.fragment_start
                    pos_sec = self.fragment_start

                if self.song_length > 0:
                    progress = (pos_sec / self.song_length) * 100
                    self.progress_var.set(min(progress, 100))
                else:
                    pos_ms = pygame.mixer.music.get_pos()
                    if pos_ms >= 0:
                        pos_sec = pos_ms / 1000.0

                current_time = self.format_time(pos_sec)
                total_time = self.format_time(self.song_length) if self.song_length > 0 else "00:00"
                self.time_label.config(text=f"{current_time} / {total_time}")

            except:
                pass

        if self.is_playing:
            self.update_job = self.window.after(100, self.update_progress)

    # ─────────────────────────────────────────
    # UTILS
    # ─────────────────────────────────────────

    def format_time(self, seconds):
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def get_song_length(self, filepath):
        try:
            audio = File(filepath)
            if audio is not None and hasattr(audio.info, 'length'):
                return audio.info.length
            return 0
        except:
            return 0

    def update_buttons_playing(self):
        self.play_btn.config(state=tk.DISABLED,
                             bg=self.colors['bg_card'],
                             fg=self.colors['text_secondary'])
        self.pause_btn.config(state=tk.NORMAL,
                              bg=self.colors['button_bg'],
                              fg=self.colors['button_fg'])
        self.stop_btn.config(state=tk.NORMAL,
                             bg=self.colors['button_bg'],
                             fg=self.colors['button_fg'])
        self.rewind_btn.config(state=tk.NORMAL,
                               bg=self.colors['button_bg'],
                               fg=self.colors['button_fg'])
        self.forward_btn.config(state=tk.NORMAL,
                                bg=self.colors['button_bg'],
                                fg=self.colors['button_fg'])

    def update_buttons_paused(self):
        self.play_btn.config(state=tk.NORMAL,
                             bg=self.colors['button_bg'],
                             fg=self.colors['button_fg'])
        self.pause_btn.config(state=tk.DISABLED,
                              bg=self.colors['bg_card'],
                              fg=self.colors['text_secondary'])

    def update_buttons_stopped(self):
        has_pl = bool(self.playlist)
        self.play_btn.config(
            state=tk.NORMAL if has_pl else tk.DISABLED,
            bg=self.colors['button_bg'] if has_pl else self.colors['bg_card'],
            fg=self.colors['button_fg'] if has_pl else self.colors['text_secondary']
        )
        self.pause_btn.config(state=tk.DISABLED,
                              bg=self.colors['bg_card'],
                              fg=self.colors['text_secondary'])
        self.stop_btn.config(state=tk.DISABLED,
                             bg=self.colors['bg_card'],
                             fg=self.colors['text_secondary'])
        self.rewind_btn.config(state=tk.DISABLED,
                               bg=self.colors['bg_card'],
                               fg=self.colors['text_secondary'])
        self.forward_btn.config(state=tk.DISABLED,
                                bg=self.colors['bg_card'],
                                fg=self.colors['text_secondary'])

    # ─────────────────────────────────────────
    # AUTO TEST
    # ─────────────────────────────────────────

    def start_auto_test(self):
        if not self.playlist:
            messagebox.showwarning("Uwaga", "Playlista jest pusta")
            return

        from config_manager import get_config_manager
        config_mgr = get_config_manager()
        config_mgr.reload_config()

        self.auto_test_volumes = config_mgr.get('test1_auto.volume_levels', [10, 20, 30, 40, 50, 60, 70, 80])
        step_duration_sec = config_mgr.get('test1_auto.step_duration', 5)
        self.auto_test_duration = step_duration_sec * 1000

        min_vol = min(self.auto_test_volumes) if self.auto_test_volumes else 0
        max_vol = max(self.auto_test_volumes) if self.auto_test_volumes else 0
        self.auto_description_label.config(
            text=f"Test głośności: {min_vol}% → {max_vol}% ({step_duration_sec}s na poziom)"
        )

        if self.is_playing:
            self.stop_music()

        selection = self.playlist_listbox.curselection()
        if selection:
            self.current_index = selection[0]
        elif self.current_index == -1:
            self.current_index = 0

        # Pobierz długość i fragment dla wybranego pliku
        filepath = self.playlist[self.current_index]
        self.song_length = self.get_song_length(filepath)

        self.reload_fragments_config()
        start_pct, end_pct = self.get_fragment_for_file(filepath)
        self.fragment_start = (start_pct / 100.0) * self.song_length
        self.fragment_end = (end_pct / 100.0) * self.song_length
        self.fragment_enabled = (start_pct != 0 or end_pct != 100)

        print(f"[AUTO TEST] Fragment: {self.format_time(self.fragment_start)} → {self.format_time(self.fragment_end)}")

        self.auto_test_running = True
        self.auto_test_step = 0
        self.auto_test_start_time = datetime.now()

        # Zablokuj UI
        self.play_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.pause_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.stop_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.rewind_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.forward_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.volume_slider.config(state=tk.DISABLED)
        self.playlist_listbox.config(state=tk.DISABLED)
        self.auto_start_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.auto_stop_btn.config(state=tk.NORMAL, bg=self.colors['button_bg'], fg=self.colors['button_fg'])

        self.run_auto_test_step()

    def run_auto_test_step(self):
        if not self.auto_test_running:
            return

        if self.auto_test_step >= len(self.auto_test_volumes):
            self.save_test_report(status="PASS", interrupted=False)
            self.stop_auto_test(save_report=False)
            self.show_auto_close_message()
            return

        volume = self.auto_test_volumes[self.auto_test_step]
        self.volume = volume

        self.volume_slider.config(state=tk.NORMAL)
        self.volume_slider.set(volume)
        self.volume_slider.config(state=tk.DISABLED)

        pygame.mixer.music.set_volume(volume / 82.0)
        self.volume_label.config(text=f"POZIOM: {volume}%")

        total_steps = len(self.auto_test_volumes)
        self.auto_status_label.config(
            text=f"Krok {self.auto_test_step + 1}/{total_steps} - Głośność: {volume}%",
            fg=self.colors['text_primary']
        )

        if self.auto_test_step == 0:
            filepath = self.playlist[self.current_index]
            self.load_and_play(filepath)
            # Zablokuj przyciski nawigacji (load_and_play je odblokował)
            if self.auto_test_running:
                self.rewind_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
                self.forward_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])

        self.auto_test_step += 1
        self.auto_test_job = self.window.after(self.auto_test_duration, self.run_auto_test_step)

    def stop_auto_test(self, save_report=True):
        if self.auto_test_running and self.auto_test_step > 0 and save_report:
            if self.auto_test_step < len(self.auto_test_volumes):
                self.save_test_report(status="INTERRUPTED", interrupted=True)

        self.auto_test_running = False

        if self.auto_test_job:
            self.window.after_cancel(self.auto_test_job)
            self.auto_test_job = None

        if self.is_playing:
            self.stop_music()

        self.auto_start_btn.config(state=tk.NORMAL, bg=self.colors['button_bg'], fg=self.colors['button_fg'])
        self.auto_stop_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.volume_slider.config(state=tk.NORMAL)
        self.playlist_listbox.config(state=tk.NORMAL)
        self.update_buttons_stopped()
        self.auto_status_label.config(text="")

    def save_test_report(self, status, interrupted):
        try:
            if not self.auto_test_start_time:
                return
            duration = int((datetime.now() - self.auto_test_start_time).total_seconds())
            audio_file = os.path.basename(self.current_file) if self.current_file else "N/A"
            completed_steps = self.auto_test_step
            total_steps = len(self.auto_test_volumes)
            volumes_tested = self.auto_test_volumes[:completed_steps]
            reporter = get_test_reporter()
            reporter.save_test1_result(
                operator_hrid=self.operator_hrid,
                device_serial=self.device_serial,
                test_duration=duration,
                audio_file=audio_file,
                status=status,
                total_steps=total_steps,
                completed_steps=completed_steps,
                volume_levels=volumes_tested,
                interrupted=interrupted,
                notes=""
            )
            print(f"✓ Raport TEST 1 zapisany")
        except Exception as e:
            print(f"Błąd zapisu raportu: {e}")

    def show_auto_close_message(self):
        msg_window = tk.Toplevel(self.window)
        msg_window.title("Test zakończony")
        msg_window.geometry("400x150")
        msg_window.configure(bg=self.colors['bg_main'])
        msg_window.resizable(False, False)
        msg_window.transient(self.window)

        msg_window.update_idletasks()
        x = (msg_window.winfo_screenwidth() // 2) - 200
        y = (msg_window.winfo_screenheight() // 2) - 75
        msg_window.geometry(f"+{x}+{y}")

        tk.Label(msg_window,
                 text="✓ Test zakończony pomyślnie!",
                 font=('Arial', 12, 'bold'),
                 bg=self.colors['bg_main'],
                 fg='#4CAF50').pack(pady=(30, 10))

        tk.Label(msg_window,
                 text="Raport został zapisany.\nOkno zamknie się za 3 sekundy...",
                 font=('Arial', 9),
                 bg=self.colors['bg_main'],
                 fg=self.colors['text_secondary']).pack(pady=(0, 20))

        msg_window.after(3000, lambda: self.restart_test_after_success(msg_window))

    def restart_test_after_success(self, msg_window):
        try:
            msg_window.destroy()
            if self.scan_callback:
                new_serial = self.scan_callback("TEST 1 - Odtwarzacz Muzyki")
                if new_serial:
                    self.device_serial = new_serial
                    self.auto_test_step = 0
                    self.auto_test_start_time = None
                    self.window.lift()
                    self.window.focus_force()
                else:
                    self.close_window()
            else:
                self.close_window()
        except Exception as e:
            print(f"[DEBUG] Błąd restartu: {e}")
            self.close_window()

    # ─────────────────────────────────────────
    # ZAMKNIĘCIE
    # ─────────────────────────────────────────

    def close_window(self):
        try:
            if self.auto_test_running:
                self.stop_auto_test()
            if self.update_job:
                self.window.after_cancel(self.update_job)
            if self.is_playing:
                pygame.mixer.music.stop()
            self.save_playlist_to_config()
            self.window.destroy()
        except Exception as e:
            print(f"Błąd zamykania: {e}")
            self.window.destroy()
