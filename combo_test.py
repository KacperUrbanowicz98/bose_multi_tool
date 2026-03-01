"""
Test 4: COMBO Test (TEST 1 + TEST 2 + TEST 3)
Bose Audio Multi-Tool
"""

import tkinter as tk
from tkinter import messagebox
import pygame
import numpy as np
import threading
import time
import os
from datetime import datetime
from test_reporter import get_test_reporter
from config_manager import get_config_manager


class ComboTest:
    def __init__(self, window, operator_hrid="UNKNOWN",
                 device_serial=None, scan_callback=None, close_callback=None):
        self.window = window
        self.window.configure(bg='#FFFFFF')
        self.operator_hrid = operator_hrid
        self.device_serial = device_serial
        self.scan_callback = scan_callback
        self.close_callback = close_callback

        # === KOLORY ===
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
            'green': '#4CAF50',
            'orange': '#FF9800',
            'red': '#F44336',
            'blue': '#2196F3'
        }

        # === KONFIGURACJA ===
        config_mgr = get_config_manager()
        config_mgr.reload_config()

        # TEST 1 config
        self.t1_step_duration = config_mgr.get('test1_auto.step_duration', 2)
        self.t1_volume_levels = config_mgr.get('test1_auto.volume_levels',
                                                [10, 20, 30, 40, 50, 60, 70, 80])
        # TEST 2 config
        self.t2_freq_min = config_mgr.get('test2_auto.freq_min', 20)
        self.t2_freq_max = config_mgr.get('test2_auto.freq_max', 20000)
        self.t2_duration = config_mgr.get('test2_auto.duration', 11)
        self.t2_volume = config_mgr.get('test2_auto.volume', 50)
        self.t2_wave_type = config_mgr.get('test2_auto.wave_type', 'sine')

        # TEST 3 config
        self.t3_duration_per_channel = config_mgr.get('test3_auto.duration_per_channel', 5)
        self.t3_frequency = config_mgr.get('test3_auto.frequency', 1000)
        self.t3_volume = config_mgr.get('test3_auto.volume', 50)

        # === STAN ===
        self.combo_running = False
        self.combo_start_time = None
        self.current_phase = None  # 'test1', 'test2', 'test3', 'break'
        self.combo_job = None
        self.interrupted = False

        # Playlist / fragment
        self.playlist = []
        self.current_index = 0
        self.song_length = 0
        self.fragment_start = 0
        self.fragment_end = 0
        self.fragment_enabled = False

        # Audio
        self.is_playing = False
        self.sound = None
        self.stop_sound = False
        self.sound_thread = None
        self.current_file = None
        self.start_time_offset = 0

        # Wyniki testów
        self.test1_data = {}
        self.test2_data = {}
        self.test3_data = {}
        self.test1_start_time = None
        self.test2_start_time = None
        self.test3_start_time = None

        # TEST 2 sweep
        self.sweep_job = None
        self.t2_sound = None

        # TEST 3
        self.t3_sound_thread = None
        self.t3_stop_sound = False
        self.t3_channel_index = 0
        self.t3_job = None

        # Inicjalizacja pygame
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        self.create_widgets()

    # =====================
    # === TWORZENIE GUI ===
    # =====================

    def create_widgets(self):
        """Tworzy interfejs COMBO testu"""

        # === NAGŁÓWEK ===
        header = tk.Frame(self.window, bg=self.colors['bg_main'])
        header.pack(fill='x', padx=20, pady=(15, 5))

        tk.Label(header,
                 text="COMBO TEST",
                 font=('Arial', 18, 'bold'),
                 bg=self.colors['bg_main'],
                 fg=self.colors['text_primary']).pack()

        tk.Label(header,
                 text="TEST 1 + TEST 2 + TEST 3 automatycznie",
                 font=('Arial', 9),
                 bg=self.colors['bg_main'],
                 fg=self.colors['text_secondary']).pack(pady=(3, 0))

        self.sn_label = tk.Label(
            header,
            text=f"Operator: {self.operator_hrid}  |  S/N: {self.device_serial or 'N/A'}",
            font=('Arial', 8),
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary']
        )
        self.sn_label.pack(pady=(2, 0))

        tk.Frame(self.window, height=2,
                 bg=self.colors['border']).pack(fill='x', padx=20, pady=(8, 10))

        # === GŁÓWNY KONTENER ===
        main = tk.Frame(self.window, bg=self.colors['bg_main'])
        main.pack(fill='both', expand=True, padx=20)

        # === STATUS TESTÓW ===
        status_frame = tk.LabelFrame(main,
                                     text="STATUS TESTOW",
                                     font=('Arial', 9, 'bold'),
                                     bg=self.colors['bg_main'],
                                     fg=self.colors['text_primary'],
                                     bd=2, relief=tk.SOLID)
        status_frame.pack(fill='x', pady=(0, 10))

        status_grid = tk.Frame(status_frame, bg=self.colors['bg_main'])
        status_grid.pack(pady=10, padx=10)

        # TEST 1 status
        self.t1_status_frame = tk.Frame(status_grid,
                                        bg=self.colors['bg_card'],
                                        relief=tk.SOLID, bd=1)
        self.t1_status_frame.grid(row=0, column=0, padx=5, pady=3, ipadx=10, ipady=5)

        tk.Label(self.t1_status_frame, text="TEST 1",
                 font=('Arial', 8, 'bold'),
                 bg=self.colors['bg_card'],
                 fg=self.colors['text_primary']).pack()

        tk.Label(self.t1_status_frame, text="Music Player",
                 font=('Arial', 7),
                 bg=self.colors['bg_card'],
                 fg=self.colors['text_secondary']).pack()

        self.t1_status_label = tk.Label(self.t1_status_frame,
                                        text="OCZEKUJE",
                                        font=('Arial', 8, 'bold'),
                                        bg=self.colors['bg_card'],
                                        fg=self.colors['text_secondary'])
        self.t1_status_label.pack()

        # Strzałka
        tk.Label(status_grid, text="→",
                 font=('Arial', 14, 'bold'),
                 bg=self.colors['bg_main'],
                 fg=self.colors['text_secondary']).grid(row=0, column=1, padx=3)

        # TEST 2 status
        self.t2_status_frame = tk.Frame(status_grid,
                                        bg=self.colors['bg_card'],
                                        relief=tk.SOLID, bd=1)
        self.t2_status_frame.grid(row=0, column=2, padx=5, pady=3, ipadx=10, ipady=5)

        tk.Label(self.t2_status_frame, text="TEST 2",
                 font=('Arial', 8, 'bold'),
                 bg=self.colors['bg_card'],
                 fg=self.colors['text_primary']).pack()

        tk.Label(self.t2_status_frame, text="Tone Generator",
                 font=('Arial', 7),
                 bg=self.colors['bg_card'],
                 fg=self.colors['text_secondary']).pack()

        self.t2_status_label = tk.Label(self.t2_status_frame,
                                        text="OCZEKUJE",
                                        font=('Arial', 8, 'bold'),
                                        bg=self.colors['bg_card'],
                                        fg=self.colors['text_secondary'])
        self.t2_status_label.pack()

        # Strzałka
        tk.Label(status_grid, text="→",
                 font=('Arial', 14, 'bold'),
                 bg=self.colors['bg_main'],
                 fg=self.colors['text_secondary']).grid(row=0, column=3, padx=3)

        # TEST 3 status
        self.t3_status_frame = tk.Frame(status_grid,
                                        bg=self.colors['bg_card'],
                                        relief=tk.SOLID, bd=1)
        self.t3_status_frame.grid(row=0, column=4, padx=5, pady=3, ipadx=10, ipady=5)

        tk.Label(self.t3_status_frame, text="TEST 3",
                 font=('Arial', 8, 'bold'),
                 bg=self.colors['bg_card'],
                 fg=self.colors['text_primary']).pack()

        tk.Label(self.t3_status_frame, text="Stereo L/R",
                 font=('Arial', 7),
                 bg=self.colors['bg_card'],
                 fg=self.colors['text_secondary']).pack()

        self.t3_status_label = tk.Label(self.t3_status_frame,
                                        text="OCZEKUJE",
                                        font=('Arial', 8, 'bold'),
                                        bg=self.colors['bg_card'],
                                        fg=self.colors['text_secondary'])
        self.t3_status_label.pack()

        # === WYBÓR FRAGMENTU ===
        fragment_frame = tk.LabelFrame(main,
                                       text="WYBOR FRAGMENTU UTWORU (TEST 1)",
                                       font=('Arial', 9, 'bold'),
                                       bg=self.colors['bg_main'],
                                       fg=self.colors['text_primary'],
                                       bd=2, relief=tk.SOLID)
        fragment_frame.pack(fill='x', pady=(0, 10))

        frag_container = tk.Frame(fragment_frame, bg=self.colors['bg_main'])
        frag_container.pack(fill='x', padx=8, pady=8)

        # Playlist
        playlist_row = tk.Frame(frag_container, bg=self.colors['bg_main'])
        playlist_row.pack(fill='x', pady=(0, 5))

        tk.Label(playlist_row, text="Utwór:",
                 font=('Arial', 8, 'bold'),
                 bg=self.colors['bg_main'],
                 fg=self.colors['text_primary'],
                 width=8, anchor='w').pack(side='left')

        self.track_label = tk.Label(playlist_row,
                                    text="Brak wybranego utworu",
                                    font=('Arial', 8),
                                    bg=self.colors['bg_main'],
                                    fg=self.colors['text_secondary'],
                                    anchor='w')
        self.track_label.pack(side='left', fill='x', expand=True)

        self.load_track_btn = tk.Button(playlist_row,
                                        text="WYBIERZ UTWOR",
                                        font=('Arial', 7, 'bold'),
                                        bg=self.colors['button_bg'],
                                        fg=self.colors['button_fg'],
                                        activebackground=self.colors['button_active'],
                                        activeforeground=self.colors['button_active_fg'],
                                        bd=1, relief=tk.SOLID,
                                        command=self.load_track)
        self.load_track_btn.pack(side='right', padx=(5, 0))

        # Checkbox fragment
        self.fragment_var = tk.BooleanVar(value=False)
        self.fragment_check = tk.Checkbutton(frag_container,
                                             text="Uzyj wybranego fragmentu",
                                             variable=self.fragment_var,
                                             command=self.toggle_fragment,
                                             font=('Arial', 8),
                                             bg=self.colors['bg_main'],
                                             fg=self.colors['text_primary'],
                                             selectcolor=self.colors['bg_card'],
                                             activebackground=self.colors['bg_main'],
                                             state=tk.DISABLED)
        self.fragment_check.pack(anchor='w', pady=(0, 3))

        # START suwak
        start_row = tk.Frame(frag_container, bg=self.colors['bg_main'])
        start_row.pack(fill='x', pady=1)

        tk.Label(start_row, text="START:",
                 font=('Arial', 8, 'bold'),
                 bg=self.colors['bg_main'],
                 fg=self.colors['text_primary'],
                 width=8, anchor='w').pack(side='left')

        self.start_slider = tk.Scale(start_row,
                                     from_=0, to=100,
                                     orient=tk.HORIZONTAL,
                                     bg=self.colors['bg_main'],
                                     fg=self.colors['text_primary'],
                                     troughcolor=self.colors['bg_card'],
                                     highlightthickness=0,
                                     showvalue=0,
                                     command=self.update_fragment_start,
                                     bd=0, relief=tk.FLAT,
                                     state=tk.DISABLED)
        self.start_slider.pack(side='left', fill='x', expand=True, padx=5)

        self.start_time_label = tk.Label(start_row, text="0:00",
                                         font=('Arial', 8),
                                         bg=self.colors['bg_main'],
                                         fg=self.colors['text_secondary'],
                                         width=5)
        self.start_time_label.pack(side='left')

        # END suwak
        end_row = tk.Frame(frag_container, bg=self.colors['bg_main'])
        end_row.pack(fill='x', pady=1)

        tk.Label(end_row, text="KONIEC:",
                 font=('Arial', 8, 'bold'),
                 bg=self.colors['bg_main'],
                 fg=self.colors['text_primary'],
                 width=8, anchor='w').pack(side='left')

        self.end_slider = tk.Scale(end_row,
                                   from_=0, to=100,
                                   orient=tk.HORIZONTAL,
                                   bg=self.colors['bg_main'],
                                   fg=self.colors['text_primary'],
                                   troughcolor=self.colors['bg_card'],
                                   highlightthickness=0,
                                   showvalue=0,
                                   command=self.update_fragment_end,
                                   bd=0, relief=tk.FLAT,
                                   state=tk.DISABLED)
        self.end_slider.set(100)
        self.end_slider.pack(side='left', fill='x', expand=True, padx=5)

        self.end_time_label = tk.Label(end_row, text="0:00",
                                       font=('Arial', 8),
                                       bg=self.colors['bg_main'],
                                       fg=self.colors['text_secondary'],
                                       width=5)
        self.end_time_label.pack(side='left')

        # Info fragment
        self.fragment_info_label = tk.Label(frag_container,
                                            text="Zaladuj utwor aby wybrac fragment",
                                            font=('Arial', 8),
                                            bg=self.colors['bg_main'],
                                            fg=self.colors['text_secondary'])
        self.fragment_info_label.pack(pady=(4, 0))

        # === STATUS / PROGRESS ===
        progress_frame = tk.LabelFrame(main,
                                       text="POSTEP",
                                       font=('Arial', 9, 'bold'),
                                       bg=self.colors['bg_main'],
                                       fg=self.colors['text_primary'],
                                       bd=2, relief=tk.SOLID)
        progress_frame.pack(fill='x', pady=(0, 10))

        self.phase_label = tk.Label(progress_frame,
                                    text="Gotowy do uruchomienia",
                                    font=('Arial', 10, 'bold'),
                                    bg=self.colors['bg_main'],
                                    fg=self.colors['text_primary'])
        self.phase_label.pack(pady=(8, 3))

        self.progress_label = tk.Label(progress_frame,
                                       text="",
                                       font=('Arial', 8),
                                       bg=self.colors['bg_main'],
                                       fg=self.colors['text_secondary'])
        self.progress_label.pack(pady=(0, 8))

        # === PRZYCISKI ===
        btn_frame = tk.Frame(main, bg=self.colors['bg_main'])
        btn_frame.pack(pady=(0, 10))

        self.start_btn = tk.Button(btn_frame,
                                   text="▶ START COMBO TEST",
                                   font=('Arial', 10, 'bold'),
                                   bg=self.colors['button_bg'],
                                   fg=self.colors['button_fg'],
                                   activebackground=self.colors['button_active'],
                                   activeforeground=self.colors['button_active_fg'],
                                   bd=2, relief=tk.SOLID,
                                   width=20,
                                   command=self.start_combo_test)
        self.start_btn.pack(side='left', padx=5)

        self.stop_btn = tk.Button(btn_frame,
                                  text="⏹ STOP",
                                  font=('Arial', 10, 'bold'),
                                  bg=self.colors['button_bg'],
                                  fg=self.colors['button_fg'],
                                  activebackground=self.colors['button_active'],
                                  activeforeground=self.colors['button_active_fg'],
                                  bd=2, relief=tk.SOLID,
                                  width=10,
                                  state=tk.DISABLED,
                                  command=self.stop_combo_test)
        self.stop_btn.pack(side='left', padx=5)

        # Powrót
        tk.Button(main,
                  text="← POWROT DO MENU",
                  font=('Arial', 8),
                  bg=self.colors['bg_main'],
                  fg=self.colors['text_secondary'],
                  activebackground=self.colors['button_active'],
                  activeforeground=self.colors['button_active_fg'],
                  bd=1, relief=tk.SOLID,
                  command=self.back_to_menu).pack(pady=(0, 10))

    # ========================
    # === WYBOR FRAGMENTU ===
    # ========================

    def load_track(self):
        """Otwiera dialog wyboru pliku audio"""
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            title="Wybierz utwór do testu",
            filetypes=[
                ("Pliki audio", "*.mp3 *.wav *.ogg *.flac"),
                ("Wszystkie pliki", "*.*")
            ]
        )
        if filepath:
            self.playlist = [filepath]
            self.current_index = 0
            filename = os.path.basename(filepath)
            self.track_label.config(text=filename,
                                    fg=self.colors['text_primary'])

            # Pobierz długość utworu
            self.song_length = self.get_song_length(filepath)

            if self.song_length > 0:
                self.fragment_end = self.song_length
                self.fragment_start = 0
                self.start_slider.set(0)
                self.end_slider.set(100)
                self.start_time_label.config(text="0:00")
                self.end_time_label.config(
                    text=self.format_time(self.song_length)
                )
                self.fragment_check.config(state=tk.NORMAL)
                self.fragment_info_label.config(
                    text=f"Dlugosc utworu: {self.format_time(self.song_length)}"
                )

            print(f"[COMBO] Zaladowano utwor: {filename} ({self.format_time(self.song_length)})")

    def get_song_length(self, filepath):
        """Pobiera długość pliku audio w sekundach"""
        try:
            pygame.mixer.music.load(filepath)
            # Spróbuj uzyskać długość przez mutagen jeśli dostępny
            try:
                from mutagen import File as MutagenFile
                audio = MutagenFile(filepath)
                if audio and audio.info:
                    return audio.info.length
            except ImportError:
                pass

            # Fallback: odtwórz i zmierz
            temp_sound = pygame.mixer.Sound(filepath)
            return temp_sound.get_length()
        except Exception as e:
            print(f"[COMBO] Blad pobierania dlugosci: {e}")
            return 0

    def format_time(self, seconds):
        """Formatuje sekundy do MM:SS"""
        seconds = int(seconds)
        m = seconds // 60
        s = seconds % 60
        return f"{m}:{s:02d}"

    def toggle_fragment(self):
        """Włącza/wyłącza wybór fragmentu"""
        if self.fragment_var.get():
            self.start_slider.config(state=tk.NORMAL)
            self.end_slider.config(state=tk.NORMAL)
            self.fragment_enabled = True
        else:
            self.start_slider.config(state=tk.DISABLED)
            self.end_slider.config(state=tk.DISABLED)
            self.fragment_enabled = False
            self.fragment_start = 0
            self.fragment_end = self.song_length
            self.start_slider.set(0)
            self.end_slider.set(100)
        self.update_fragment_info()

    def update_fragment_start(self, value):
        """Aktualizuje czas startu fragmentu"""
        if self.song_length > 0:
            self.fragment_start = self.song_length * (float(value) / 100)
            if self.fragment_start >= self.fragment_end:
                self.fragment_start = max(0, self.fragment_end - 1)
                self.start_slider.set(
                    int((self.fragment_start / self.song_length) * 100)
                )
            self.start_time_label.config(text=self.format_time(self.fragment_start))
            self.update_fragment_info()

    def update_fragment_end(self, value):
        """Aktualizuje czas końca fragmentu"""
        if self.song_length > 0:
            self.fragment_end = self.song_length * (float(value) / 100)
            if self.fragment_end <= self.fragment_start:
                self.fragment_end = min(self.song_length, self.fragment_start + 1)
                self.end_slider.set(
                    int((self.fragment_end / self.song_length) * 100)
                )
            self.end_time_label.config(text=self.format_time(self.fragment_end))
            self.update_fragment_info()

    def update_fragment_info(self):
        """Aktualizuje info o fragmencie"""
        if self.song_length > 0:
            if self.fragment_enabled:
                length = self.fragment_end - self.fragment_start
                self.fragment_info_label.config(
                    text=f"Fragment: {self.format_time(self.fragment_start)} → {self.format_time(self.fragment_end)} (dlugosc: {self.format_time(length)})",
                    fg=self.colors['text_primary']
                )
            else:
                self.fragment_info_label.config(
                    text=f"Dlugosc utworu: {self.format_time(self.song_length)}",
                    fg=self.colors['text_secondary']
                )

    # ======================
    # === COMBO TEST FLOW ===
    # ======================

    def start_combo_test(self):
        """Startuje cały COMBO test"""
        # Sprawdź czy utwór jest załadowany
        if not self.playlist:
            messagebox.showwarning("Brak utworu",
                                   "Wybierz utwor do testu przed uruchomieniem!")
            return

        # Resetuj wyniki
        self.test1_data = {}
        self.test2_data = {}
        self.test3_data = {}
        self.interrupted = False
        self.combo_start_time = datetime.now()
        self.combo_running = True

        # Resetuj statusy w GUI
        self.set_test_status(1, 'waiting')
        self.set_test_status(2, 'waiting')
        self.set_test_status(3, 'waiting')

        # Zablokuj przyciski
        self.start_btn.config(state=tk.DISABLED,
                              bg=self.colors['bg_card'],
                              fg=self.colors['text_secondary'])
        self.stop_btn.config(state=tk.NORMAL)
        self.load_track_btn.config(state=tk.DISABLED)
        self.fragment_check.config(state=tk.DISABLED)
        self.start_slider.config(state=tk.DISABLED)
        self.end_slider.config(state=tk.DISABLED)

        print(f"[COMBO] START - S/N: {self.device_serial}")

        # Oblicz pozycje fragmentu z suwaków
        if self.fragment_enabled and self.song_length > 0:
            self.fragment_start = (self.start_slider.get() / 100) * self.song_length
            self.fragment_end = (self.end_slider.get() / 100) * self.song_length

        # Start TEST 1
        self.run_test1()

    def set_test_status(self, test_num, status):
        """Aktualizuje wizualny status testu"""
        labels = {1: self.t1_status_label, 2: self.t2_status_label, 3: self.t3_status_label}
        frames = {1: self.t1_status_frame, 2: self.t2_status_frame, 3: self.t3_status_frame}

        label = labels[test_num]
        frame = frames[test_num]

        if status == 'waiting':
            label.config(text="OCZEKUJE", fg=self.colors['text_secondary'])
            frame.config(bg=self.colors['bg_card'])
        elif status == 'running':
            label.config(text="W TOKU...", fg=self.colors['blue'])
            frame.config(bg='#E3F2FD')
        elif status == 'pass':
            label.config(text="PASS ✓", fg=self.colors['green'])
            frame.config(bg='#E8F5E9')
        elif status == 'fail':
            label.config(text="FAIL ✗", fg=self.colors['red'])
            frame.config(bg='#FFEBEE')
        elif status == 'interrupted':
            label.config(text="PRZERWANY", fg=self.colors['orange'])
            frame.config(bg='#FFF3E0')

        # Zaktualizuj kolory labelek wewnątrz frame
        for widget in frame.winfo_children():
            if widget != label:
                widget.config(bg=frame.cget('bg'))
        label.config(bg=frame.cget('bg'))

    # ==============
    # === TEST 1 ===
    # ==============

    def run_test1(self):
        """Uruchamia TEST 1 - Music Player"""
        self.current_phase = 'test1'
        self.test1_start_time = datetime.now()
        self.set_test_status(1, 'running')
        self.phase_label.config(text="TEST 1: Music Player", fg=self.colors['blue'])

        # Pobierz parametry
        volume_levels = self.t1_volume_levels
        step_duration = self.t1_step_duration
        total_steps = len(volume_levels)

        self.t1_current_step = 0
        self.t1_volume_levels_copy = volume_levels[:]

        # Załaduj utwór
        filepath = self.playlist[self.current_index]
        try:
            pygame.mixer.music.load(filepath)
            if self.fragment_enabled and self.fragment_start > 0:
                pygame.mixer.music.play(start=self.fragment_start)
            else:
                pygame.mixer.music.play()
            self.is_playing = True
            self.current_file = filepath
        except Exception as e:
            print(f"[COMBO] Blad ladowania utworu: {e}")
            self.test1_data = {
                'status': 'FAIL', 'duration': 0,
                'audio_file': 'ERROR', 'volume_levels': []
            }
            self.set_test_status(1, 'fail')
            self.finish_combo(interrupted=False)
            return

        audio_file = os.path.basename(filepath)

        def t1_step():
            """Jeden krok TEST 1"""
            if not self.combo_running:
                return

            if self.t1_current_step >= total_steps:
                # TEST 1 zakończony
                pygame.mixer.music.stop()
                self.is_playing = False
                duration = int((datetime.now() - self.test1_start_time).total_seconds())
                self.test1_data = {
                    'status': 'PASS',
                    'duration': duration,
                    'audio_file': audio_file,
                    'volume_levels': self.t1_volume_levels_copy
                }
                self.set_test_status(1, 'pass')
                print(f"[COMBO] TEST 1 PASS ({duration}s)")

                # Przerwa 2 sekundy przed TEST 2
                self.start_break(2, self.run_test2)
                return

            # Ustaw głośność
            vol = self.t1_volume_levels_copy[self.t1_current_step]
            pygame.mixer.music.set_volume(vol / 82.0)

            self.progress_label.config(
                text=f"Krok {self.t1_current_step + 1}/{total_steps} | Glosnosc: {vol}% | Czas: {step_duration}s"
            )

            # Jeśli fragment włączony - sprawdź czy nie wyszliśmy poza fragment
            if self.fragment_enabled:
                current_pos = pygame.mixer.music.get_pos() / 1000.0 + self.fragment_start
                if current_pos >= self.fragment_end:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load(filepath)
                    pygame.mixer.music.play(start=self.fragment_start)
                    pygame.mixer.music.set_volume(vol / 82.0)

            self.t1_current_step += 1
            self.combo_job = self.window.after(step_duration * 1000, t1_step)

        # Start pierwszego kroku
        t1_step()

    # ==============
    # === TEST 2 ===
    # ==============

    def run_test2(self):
        """Uruchamia TEST 2 - Tone Generator Sweep"""
        self.current_phase = 'test2'
        self.test2_start_time = datetime.now()
        self.set_test_status(2, 'running')
        self.phase_label.config(text="TEST 2: Tone Generator", fg=self.colors['blue'])
        self.progress_label.config(text="Przejazd czestotliwosci...")

        start_time = time.time()
        end_time = start_time + self.t2_duration

        self.t2_sound = None

        def sweep_step():
            if not self.combo_running:
                return

            current_time = time.time()
            elapsed = current_time - start_time
            total_duration = end_time - start_time

            if current_time >= end_time:
                # TEST 2 zakończony
                if self.t2_sound:
                    self.t2_sound.stop()
                duration = int((datetime.now() - self.test2_start_time).total_seconds())
                self.test2_data = {
                    'status': 'PASS',
                    'duration': duration,
                    'wave_type': self.t2_wave_type,
                    'freq_range': f"{self.t2_freq_min}-{self.t2_freq_max}"
                }
                self.set_test_status(2, 'pass')
                print(f"[COMBO] TEST 2 PASS ({duration}s)")

                # Przerwa 2 sekundy przed TEST 3
                self.start_break(2, self.run_test3)
                return

            # Oblicz częstotliwość
            progress = elapsed / total_duration
            log_min = np.log10(self.t2_freq_min)
            log_max = np.log10(self.t2_freq_max)

            if progress <= 0.5:
                sweep_progress = progress * 2
                current_freq = int(10 ** (log_min + sweep_progress * (log_max - log_min)))
            else:
                sweep_progress = (progress - 0.5) * 2
                current_freq = int(10 ** (log_max - sweep_progress * (log_max - log_min)))

            remaining = int(total_duration - elapsed)
            self.progress_label.config(
                text=f"Czestotliwosc: {current_freq} Hz | Pozostalo: {remaining}s"
            )

            # Generuj i odtwórz dźwięk
            if self.t2_sound:
                self.t2_sound.stop()

            wave = self.generate_tone_wave(current_freq, self.t2_volume, self.t2_wave_type)
            self.t2_sound = pygame.sndarray.make_sound(wave)
            self.t2_sound.play(loops=-1)

            self.sweep_job = self.window.after(50, sweep_step)

        sweep_step()

    def generate_tone_wave(self, frequency, volume, wave_type, duration=1.0, sample_rate=44100):
        """Generuje falę dźwiękową dla TEST 2"""
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples, False)

        if wave_type == "sine":
            wave = np.sin(2 * np.pi * frequency * t)
        elif wave_type == "square":
            wave = np.sign(np.sin(2 * np.pi * frequency * t))
        elif wave_type == "sawtooth":
            wave = 2 * (t * frequency - np.floor(t * frequency + 0.5))
        elif wave_type == "triangle":
            wave = 2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1
        else:
            wave = np.sin(2 * np.pi * frequency * t)

        wave = wave * (volume / 100.0)
        wave = np.int16(wave * 32767)
        wave = np.repeat(wave.reshape(-1, 1), 2, axis=1)
        return wave

    # ==============
    # === TEST 3 ===
    # ==============

    def run_test3(self):
        """Uruchamia TEST 3 - Stereo L/R"""
        self.current_phase = 'test3'
        self.test3_start_time = datetime.now()
        self.set_test_status(3, 'running')
        self.phase_label.config(text="TEST 3: Stereo L/R", fg=self.colors['blue'])

        channels = ['left', 'right', 'both']
        self.t3_channel_index = 0
        self.t3_stop_sound = False

        def play_next_channel():
            if not self.combo_running or self.t3_channel_index >= len(channels):
                # TEST 3 zakończony
                self.t3_stop_sound = True
                pygame.mixer.stop()
                duration = int((datetime.now() - self.test3_start_time).total_seconds())
                self.test3_data = {
                    'status': 'PASS',
                    'duration': duration,
                    'duration_per_channel': self.t3_duration_per_channel
                }
                self.set_test_status(3, 'pass')
                print(f"[COMBO] TEST 3 PASS ({duration}s)")

                # Zakończ cały COMBO test
                self.finish_combo(interrupted=False)
                return

            channel = channels[self.t3_channel_index]
            channel_names = {'left': 'Lewy', 'right': 'Prawy', 'both': 'Oba'}

            self.progress_label.config(
                text=f"Kanalal: {channel_names[channel]} ({self.t3_channel_index + 1}/3)"
            )

            # Zatrzymaj poprzedni dźwięk
            self.t3_stop_sound = True
            pygame.mixer.stop()
            time.sleep(0.05)

            # Uruchom nowy wątek dźwięku
            self.t3_stop_sound = False
            self.t3_sound_thread = threading.Thread(
                target=self.play_stereo_channel,
                args=(channel,)
            )
            self.t3_sound_thread.daemon = True
            self.t3_sound_thread.start()

            self.t3_channel_index += 1
            self.t3_job = self.window.after(
                self.t3_duration_per_channel * 1000,
                play_next_channel
            )

        play_next_channel()

    def play_stereo_channel(self, channel):
        """Wątek odtwarzający dźwięk na kanale stereo"""
        try:
            sample_rate = 44100
            while not self.t3_stop_sound:
                t = np.linspace(0, 0.5, int(sample_rate * 0.5), False)
                tone = np.sin(self.t3_frequency * 2 * np.pi * t)
                tone = (tone * 32767).astype(np.int16)

                if channel == 'left':
                    stereo = np.zeros((len(tone), 2), dtype=np.int16)
                    stereo[:, 0] = tone
                elif channel == 'right':
                    stereo = np.zeros((len(tone), 2), dtype=np.int16)
                    stereo[:, 1] = tone
                else:
                    stereo = np.column_stack((tone, tone))

                volume_factor = self.t3_volume / 100.0
                stereo = (stereo * volume_factor).astype(np.int16)

                sound = pygame.sndarray.make_sound(stereo)
                sound.play()

                while pygame.mixer.get_busy() and not self.t3_stop_sound:
                    time.sleep(0.05)
        except Exception as e:
            print(f"[COMBO] Blad watku T3: {e}")

    # ==================
    # === PRZERWA ===
    # ==================

    def start_break(self, seconds, next_func):
        """Wyświetla odliczanie między testami"""
        self.current_phase = 'break'

        def countdown(remaining):
            if not self.combo_running:
                return
            if remaining <= 0:
                next_func()
                return
            self.phase_label.config(
                text=f"Przerwa - nastepny test za: {remaining}s",
                fg=self.colors['orange']
            )
            self.combo_job = self.window.after(1000, lambda: countdown(remaining - 1))

        countdown(seconds)

    # =====================
    # === ZAKOŃCZENIE ===
    # =====================

    def finish_combo(self, interrupted=False):
        """Kończy COMBO test i zapisuje raport"""
        self.combo_running = False
        self.interrupted = interrupted

        # Zatrzymaj wszystkie dźwięki
        pygame.mixer.stop()
        pygame.mixer.music.stop()
        self.t3_stop_sound = True

        # Oblicz łączny czas
        total_duration = 0
        if self.combo_start_time:
            total_duration = int((datetime.now() - self.combo_start_time).total_seconds())

        # Uzupełnij brakujące dane jeśli przerwano
        if not self.test1_data:
            self.test1_data = {
                'status': 'INTERRUPTED', 'duration': 0,
                'audio_file': 'N/A', 'volume_levels': []
            }
        if not self.test2_data:
            self.test2_data = {
                'status': 'INTERRUPTED', 'duration': 0,
                'wave_type': self.t2_wave_type,
                'freq_range': f"{self.t2_freq_min}-{self.t2_freq_max}"
            }
        if not self.test3_data:
            self.test3_data = {
                'status': 'INTERRUPTED', 'duration': 0,
                'duration_per_channel': self.t3_duration_per_channel
            }

        # Zapisz raport
        reporter = get_test_reporter()
        test_id, overall_status = reporter.save_combo_result(
            operator_hrid=self.operator_hrid,
            device_serial=self.device_serial,
            test1_data=self.test1_data,
            test2_data=self.test2_data,
            test3_data=self.test3_data,
            total_duration=total_duration,
            interrupted=interrupted
        )

        # Zaktualizuj GUI
        if overall_status == "PASS":
            self.phase_label.config(text="✓ COMBO TEST ZAKONCZONY - PASS",
                                    fg=self.colors['green'])
        elif overall_status == "INTERRUPTED":
            self.phase_label.config(text="⚠ COMBO TEST PRZERWANY",
                                    fg=self.colors['orange'])
        else:
            self.phase_label.config(text="✗ COMBO TEST - FAIL",
                                    fg=self.colors['red'])

        self.progress_label.config(
            text=f"Raport zapisany: {test_id} | Czas: {total_duration}s"
        )

        # Odblokuj przyciski
        self.start_btn.config(state=tk.NORMAL,
                              bg=self.colors['button_bg'],
                              fg=self.colors['button_fg'])
        self.stop_btn.config(state=tk.DISABLED)
        self.load_track_btn.config(state=tk.NORMAL)
        self.fragment_check.config(state=tk.NORMAL if self.playlist else tk.DISABLED)

        print(f"[COMBO] ZAKOŃCZONY - {overall_status} | {test_id}")

        # Pokaż okno skanowania nowego S/N
        self.window.after(3000, self.show_complete_message)

    def show_complete_message(self):
        """Pokazuje komunikat zakończenia i skanuje nowy S/N"""
        msg_window = tk.Toplevel(self.window)
        msg_window.title("Test zakończony")
        msg_window.geometry("400x150")
        msg_window.configure(bg='#FFFFFF')
        msg_window.resizable(False, False)
        msg_window.attributes('-topmost', True)
        msg_window.transient(self.window)

        msg_window.update_idletasks()
        x = (msg_window.winfo_screenwidth() // 2) - 200
        y = (msg_window.winfo_screenheight() // 2) - 75
        msg_window.geometry(f"+{x}+{y}")

        tk.Label(msg_window,
                 text="✓ COMBO Test zakończony!",
                 font=('Arial', 12, 'bold'),
                 bg='#FFFFFF',
                 fg='#4CAF50').pack(pady=(30, 10))

        tk.Label(msg_window,
                 text="Raport został zapisany.\nOkno zamknie się za 3 sekundy...",
                 font=('Arial', 9),
                 bg='#FFFFFF',
                 fg='#666666').pack()

        msg_window.after(3000, lambda: self.restart_after_success(msg_window))

    def restart_after_success(self, msg_window):
        """Zamyka komunikat i skanuje nowy S/N"""
        try:
            msg_window.destroy()

            if self.scan_callback:
                new_serial = self.scan_callback("COMBO TEST")

                if new_serial:
                    self.device_serial = new_serial
                    print(f"[COMBO] Nowy S/N: {new_serial}")

                    # Resetuj wyniki
                    self.test1_data = {}
                    self.test2_data = {}
                    self.test3_data = {}
                    self.set_test_status(1, 'waiting')
                    self.set_test_status(2, 'waiting')
                    self.set_test_status(3, 'waiting')
                    self.phase_label.config(
                        text="Gotowy do uruchomienia",
                        fg=self.colors['text_primary']
                    )
                    self.progress_label.config(text="")

                    # ZAKTUALIZUJ LABELKĘ S/N  <-- DODANE
                    self.sn_label.config(
                        text=f"Operator: {self.operator_hrid}  |  S/N: {self.device_serial}"
                    )

                    # PRZYWRÓĆ FOCUS
                    self.window.lift()
                    self.window.focus_force()

                else:
                    self.back_to_menu()
            else:
                self.back_to_menu()

        except Exception as e:
            print(f"[COMBO] Blad restartu: {e}")
            self.back_to_menu()

    def stop_combo_test(self):
        """Zatrzymuje COMBO test"""
        if not self.combo_running:
            return

        self.combo_running = False
        self.t3_stop_sound = True

        # Anuluj zaplanowane zadania
        if self.combo_job:
            self.window.after_cancel(self.combo_job)
            self.combo_job = None
        if self.sweep_job:
            self.window.after_cancel(self.sweep_job)
            self.sweep_job = None
        if self.t3_job:
            self.window.after_cancel(self.t3_job)
            self.t3_job = None

        # Zatrzymaj dźwięki
        pygame.mixer.stop()
        pygame.mixer.music.stop()

        # Ustaw statusy przerwanych testów
        if self.current_phase == 'test1':
            self.set_test_status(1, 'interrupted')
        elif self.current_phase == 'test2':
            self.set_test_status(1, 'pass')
            self.set_test_status(2, 'interrupted')
        elif self.current_phase in ('test3', 'break'):
            self.set_test_status(1, 'pass')
            self.set_test_status(2, 'pass')
            self.set_test_status(3, 'interrupted')

        self.finish_combo(interrupted=True)

    def back_to_menu(self):
        """Wraca do głównego menu"""
        self.combo_running = False
        self.t3_stop_sound = True
        pygame.mixer.stop()
        pygame.mixer.music.stop()

        if self.close_callback:
            self.close_callback()
        else:
            self.window.destroy()
