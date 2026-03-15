"""
Test 4: COMBO Test (TEST 1 + TEST 2 + TEST 3)
Bose Audio Multi-Tool
Fragment per-utwór pobierany z configu (Tryb Inżynieryjny)
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

        self.t1_step_duration = config_mgr.get('test1_auto.step_duration', 2)
        self.t1_volume_levels = config_mgr.get('test1_auto.volume_levels',
                                                [10, 20, 30, 40, 50, 60, 70, 80])
        self.t2_freq_min = config_mgr.get('test2_auto.freq_min', 20)
        self.t2_freq_max = config_mgr.get('test2_auto.freq_max', 20000)
        self.t2_duration = config_mgr.get('test2_auto.duration', 11)
        self.t2_volume = config_mgr.get('test2_auto.volume', 50)
        self.t2_wave_type = config_mgr.get('test2_auto.wave_type', 'sine')
        self.t3_duration_per_channel = config_mgr.get('test3_auto.duration_per_channel', 5)
        self.t3_frequency = config_mgr.get('test3_auto.frequency', 1000)
        self.t3_volume = config_mgr.get('test3_auto.volume', 50)

        # === STAN ===
        self.combo_running = False
        self.combo_start_time = None
        self.current_phase = None
        self.combo_job = None
        self.total_duration = 0
        self.interrupted = False

        # Playlista i fragmenty per-utwór z configu
        saved_playlist = config_mgr.get('music_player.playlist', [])
        self.playlist = [f for f in saved_playlist if os.path.exists(f)]
        self.fragments_config = config_mgr.get('music_player.fragments', {})
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

        # Wyniki
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

        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        self.create_widgets()

    # ─────────────────────────────────────────
    # CONFIG HELPERS
    # ─────────────────────────────────────────

    def reload_config(self):
        """Przeładowuje playlistę i fragmenty z pliku configu"""
        config_mgr = get_config_manager()
        config_mgr.reload_config()
        saved_playlist = config_mgr.get('music_player.playlist', [])
        self.playlist = [f for f in saved_playlist if os.path.exists(f)]
        self.fragments_config = config_mgr.get('music_player.fragments', {})

    def get_fragment_for_file(self, filepath):
        """Zwraca (start_pct, end_pct) dla pliku, domyślnie (0, 100)"""
        frag = self.fragments_config.get(filepath, {})
        return frag.get('start_pct', 0), frag.get('end_pct', 100)

    # ─────────────────────────────────────────
    # GUI
    # ─────────────────────────────────────────

    def create_widgets(self):
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
            text=f"Operator: {self.operator_hrid} | S/N: {self.device_serial or 'N/A'}",
            font=('Arial', 8),
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary']
        )
        self.sn_label.pack(pady=(2, 0))

        tk.Frame(self.window, height=2,
                 bg=self.colors['border']).pack(fill='x', padx=20, pady=(8, 10))

        main = tk.Frame(self.window, bg=self.colors['bg_main'])
        main.pack(fill='both', expand=True, padx=20)

        # === STATUS TESTÓW ===
        status_frame = tk.LabelFrame(main,
                                     text="STATUS TESTOW",
                                     font=('Arial', 11, 'bold'),
                                     bg=self.colors['bg_main'],
                                     fg=self.colors['text_primary'],
                                     bd=2, relief=tk.SOLID)
        status_frame.pack(fill='x', pady=(0, 10))

        status_grid = tk.Frame(status_frame, bg=self.colors['bg_main'])
        status_grid.pack(pady=10, padx=10)

        for col, (num, name, subtitle) in enumerate([
            (1, "TEST 1", "Music Player"),
            (2, "TEST 2", "Tone Generator"),
            (3, "TEST 3", "Stereo L/R")
        ]):
            if col > 0:
                tk.Label(status_grid, text="→",
                         font=('Arial', 18, 'bold'),
                         bg=self.colors['bg_main'],
                         fg=self.colors['text_secondary']).grid(
                    row=0, column=col * 2 - 1, padx=3)

            frame = tk.Frame(status_grid,
                             bg=self.colors['bg_card'],
                             relief=tk.SOLID, bd=1)
            frame.grid(row=0, column=col * 2, padx=5, pady=3, ipadx=10, ipady=5)

            tk.Label(frame, text=name,
                     font=('Arial', 10, 'bold'),
                     bg=self.colors['bg_card'],
                     fg=self.colors['text_primary']).pack()
            tk.Label(frame, text=subtitle,
                     font=('Arial', 9),
                     bg=self.colors['bg_card'],
                     fg=self.colors['text_secondary']).pack()

            status_lbl = tk.Label(frame, text="OCZEKUJE",
                                  font=('Arial', 8, 'bold'),
                                  bg=self.colors['bg_card'],
                                  fg=self.colors['text_secondary'])
            status_lbl.pack()

            if num == 1:
                self.t1_status_frame = frame
                self.t1_status_label = status_lbl
            elif num == 2:
                self.t2_status_frame = frame
                self.t2_status_label = status_lbl
            else:
                self.t3_status_frame = frame
                self.t3_status_label = status_lbl

        # === INFO UTWÓR / FRAGMENT (tylko do odczytu) ===
        playlist_frame = tk.LabelFrame(main,
                                       text="PLAYLISTA",
                                       font=('Arial', 11, 'bold'),
                                       bg=self.colors['bg_main'],
                                       fg=self.colors['text_primary'],
                                       bd=2, relief=tk.SOLID)
        playlist_frame.pack(fill='x', pady=(0, 10))

        tk.Label(playlist_frame,
                 text="Wybierz utwór przed startem testu:",
                 font=('Arial', 9),
                 bg=self.colors['bg_main'],
                 fg=self.colors['text_secondary']).pack(anchor='w', padx=10, pady=(6, 2))

        list_container = tk.Frame(playlist_frame, bg=self.colors['bg_main'])
        list_container.pack(fill='x', padx=8, pady=(0, 8))

        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side='right', fill='y')

        self.playlist_listbox = tk.Listbox(
            list_container,
            font=('Arial', 10),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary'],
            selectbackground=self.colors['text_primary'],
            selectforeground=self.colors['bg_main'],
            bd=0, highlightthickness=0,
            yscrollcommand=scrollbar.set,
            height=4
        )
        self.playlist_listbox.pack(side='left', fill='x', expand=True)
        scrollbar.config(command=self.playlist_listbox.yview)

        # Wypełnij listbox
        for fp in self.playlist:
            self.playlist_listbox.insert(tk.END, os.path.basename(fp))
        if self.playlist:
            self.playlist_listbox.selection_set(0)

        self.info_frag_label = tk.Label(
            playlist_frame,
            text="Fragment: konfigurowany przez ENG",
            font=('Arial', 9),
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary']
        )
        self.info_frag_label.pack(anchor='w', padx=10, pady=(0, 6))

        # === POSTĘP ===
        progress_frame = tk.LabelFrame(main,
                                       text="POSTEP",
                                       font=('Arial', 11, 'bold'),
                                       bg=self.colors['bg_main'],
                                       fg=self.colors['text_primary'],
                                       bd=2, relief=tk.SOLID)
        progress_frame.pack(fill='x', pady=(0, 10))

        self.phase_label = tk.Label(progress_frame,
                                    text="Gotowy do uruchomienia",
                                    font=('Arial', 16, 'bold'),
                                    bg=self.colors['bg_main'],
                                    fg=self.colors['text_primary'])
        self.phase_label.pack(pady=(12, 4))

        self.progress_label = tk.Label(progress_frame,
                                       text="",
                                       font=('Arial', 12),
                                       bg=self.colors['bg_main'],
                                       fg=self.colors['text_secondary'])
        self.progress_label.pack(pady=(0, 12))

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
                                   bd=2, relief=tk.SOLID, width=20,
                                   command=self.start_combo_test)
        self.start_btn.pack(side='left', padx=5)

        self.stop_btn = tk.Button(btn_frame,
                                  text="⏹ STOP",
                                  font=('Arial', 10, 'bold'),
                                  bg=self.colors['button_bg'],
                                  fg=self.colors['button_fg'],
                                  activebackground=self.colors['button_active'],
                                  activeforeground=self.colors['button_active_fg'],
                                  bd=2, relief=tk.SOLID, width=10,
                                  state=tk.DISABLED,
                                  command=self.stop_combo_test)
        self.stop_btn.pack(side='left', padx=5)

        tk.Button(main,
                  text="← POWROT DO MENU",
                  font=('Arial', 8),
                  bg=self.colors['bg_main'],
                  fg=self.colors['text_secondary'],
                  activebackground=self.colors['button_active'],
                  activeforeground=self.colors['button_active_fg'],
                  bd=1, relief=tk.SOLID,
                  command=self.back_to_menu).pack(pady=(0, 10))

    # ─────────────────────────────────────────
    # COMBO FLOW
    # ─────────────────────────────────────────

    def start_combo_test(self):
        # Przeładuj świeżą konfigurację
        self.reload_config()

        if not self.playlist:
            messagebox.showwarning("Brak utworu",
                                   "Brak pliku audio w playliście!\n"
                                   "Dodaj pliki w Trybie Inżynieryjnym → Playlista & Fragmenty.")
            return

        # Zaktualizuj info-bar
        # Pobierz zaznaczony utwór z listboxa
        selection = self.playlist_listbox.curselection()
        if selection:
            self.current_index = selection[0]

        fp = self.playlist[self.current_index]
        s, e = self.get_fragment_for_file(fp)
        frag_text = f"Fragment: {s}% → {e}%" if (s != 0 or e != 100) else "Cały utwór"
        self.info_frag_label.config(text=f"{frag_text} | konfigurowany przez ENG")

        # Resetuj wyniki
        self.test1_data = {}
        self.test2_data = {}
        self.test3_data = {}
        self.interrupted = False
        self.combo_start_time = datetime.now()
        self.combo_running = True

        self.set_test_status(1, 'waiting')
        self.set_test_status(2, 'waiting')
        self.set_test_status(3, 'waiting')

        self.start_btn.config(state=tk.DISABLED,
                              bg=self.colors['bg_card'],
                              fg=self.colors['text_secondary'])
        self.stop_btn.config(state=tk.NORMAL)

        print(f"[COMBO] START - S/N: {self.device_serial}")
        self.run_test1()

    def set_test_status(self, test_num, status):
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
        elif status == 'done':
            label.config(text="UKOŃCZONY ✓", fg=self.colors['blue'])
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

        bg = frame.cget('bg')
        for widget in frame.winfo_children():
            if widget != label:
                widget.config(bg=bg)
        label.config(bg=bg)

    # ─────────────────────────────────────────
    # TEST 1
    # ─────────────────────────────────────────

    def run_test1(self):
        self.current_phase = 'test1'
        self.test1_start_time = datetime.now()
        self.set_test_status(1, 'running')
        self.phase_label.config(text="TEST 1: Music Player", fg=self.colors['blue'])

        volume_levels = self.t1_volume_levels
        step_duration = self.t1_step_duration
        total_steps = len(volume_levels)

        self.t1_current_step = 0
        self.t1_volume_levels_copy = volume_levels[:]

        filepath = self.playlist[self.current_index]

        # Pobierz długość i fragment per-utwór z configu
        if self.song_length == 0:
            self.song_length = self.get_song_length(filepath)

        start_pct, end_pct = self.get_fragment_for_file(filepath)
        self.fragment_enabled = (start_pct != 0 or end_pct != 100)
        self.fragment_start = (start_pct / 100.0) * self.song_length
        self.fragment_end = (end_pct / 100.0) * self.song_length

        print(f"[COMBO] Fragment: {self.format_time(self.fragment_start)} → {self.format_time(self.fragment_end)}")

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
            if not self.combo_running:
                return

            if self.t1_current_step >= total_steps:
                pygame.mixer.music.stop()
                self.is_playing = False
                duration = int((datetime.now() - self.test1_start_time).total_seconds())
                self.test1_data = {
                    'status': 'PASS',
                    'duration': duration,
                    'audio_file': audio_file,
                    'volume_levels': self.t1_volume_levels_copy
                }
                self.set_test_status(1, 'done')
                print(f"[COMBO] TEST 1 ukończony ({duration}s)")
                self.start_break(2, self.run_test2)

                return

            vol = self.t1_volume_levels_copy[self.t1_current_step]
            pygame.mixer.music.set_volume(vol / 82.0)

            self.progress_label.config(
                text=f"Krok {self.t1_current_step + 1}/{total_steps} | Glosnosc: {vol}% | Czas: {step_duration}s"
            )

            # Pętlowanie fragmentu
            if self.fragment_enabled and self.fragment_end > 0:
                pos_ms = pygame.mixer.music.get_pos()
                if pos_ms >= 0:
                    current_pos = pos_ms / 1000.0 + self.fragment_start
                    if current_pos >= self.fragment_end:
                        pygame.mixer.music.stop()
                        pygame.mixer.music.load(filepath)
                        pygame.mixer.music.play(start=self.fragment_start)
                        pygame.mixer.music.set_volume(vol / 82.0)

            self.t1_current_step += 1
            self.combo_job = self.window.after(step_duration * 1000, t1_step)

        t1_step()

    # ─────────────────────────────────────────
    # TEST 2
    # ─────────────────────────────────────────

    def run_test2(self):
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
                if self.t2_sound:
                    self.t2_sound.stop()
                duration = int((datetime.now() - self.test2_start_time).total_seconds())
                self.test2_data = {
                    'status': 'PASS',
                    'duration': duration,
                    'wave_type': self.t2_wave_type,
                    'freq_range': f"{self.t2_freq_min}-{self.t2_freq_max}"
                }
                self.set_test_status(2, 'done')
                print(f"[COMBO] TEST 2 ukończony ({duration}s)")
                self.start_break(2, self.run_test3)
                return

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

            if self.t2_sound:
                self.t2_sound.stop()

            wave = self.generate_tone_wave(current_freq, self.t2_volume, self.t2_wave_type)
            self.t2_sound = pygame.sndarray.make_sound(wave)
            self.t2_sound.play(loops=-1)

            self.sweep_job = self.window.after(50, sweep_step)

        sweep_step()

    def generate_tone_wave(self, frequency, volume, wave_type, duration=1.0, sample_rate=44100):
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

    # ─────────────────────────────────────────
    # TEST 3
    # ─────────────────────────────────────────

    def run_test3(self):
        self.current_phase = 'test3'
        self.test3_start_time = datetime.now()
        self.set_test_status(3, 'running')
        self.phase_label.config(text="TEST 3: Stereo L/R", fg=self.colors['blue'])

        channels = ['left', 'right', 'both']
        self.t3_channel_index = 0
        self.t3_stop_sound = False

        def play_next_channel():
            if not self.combo_running or self.t3_channel_index >= len(channels):
                self.t3_stop_sound = True
                pygame.mixer.stop()
                duration = int((datetime.now() - self.test3_start_time).total_seconds())
                self.test3_data = {
                    'status': 'PASS',
                    'duration': duration,
                    'duration_per_channel': self.t3_duration_per_channel
                }
                self.set_test_status(3, 'done')
                print(f"[COMBO] TEST 3 ukończony ({duration}s)")
                self.finish_combo(interrupted=False)
                return

            channel = channels[self.t3_channel_index]
            channel_names = {'left': 'Lewy', 'right': 'Prawy', 'both': 'Oba'}

            self.progress_label.config(
                text=f"Kanal: {channel_names[channel]} ({self.t3_channel_index + 1}/3)"
            )

            self.t3_stop_sound = True
            pygame.mixer.stop()
            time.sleep(0.05)

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

    # ─────────────────────────────────────────
    # PRZERWA
    # ─────────────────────────────────────────

    def start_break(self, seconds, next_func):
        self.current_phase = 'break'

        def countdown(remaining):
            if not self.combo_running:
                return
            if remaining <= 0:
                next_func()
                return
            self.phase_label.config(
                text=f"Przerwa — nastepny test za: {remaining}s",
                fg=self.colors['orange']
            )
            self.combo_job = self.window.after(1000, lambda: countdown(remaining - 1))

        countdown(seconds)

    # ─────────────────────────────────────────
    # ZAKOŃCZENIE
    # ─────────────────────────────────────────

    def finish_combo(self, interrupted=False):
        self.combo_running = False
        self.interrupted = interrupted

        pygame.mixer.stop()
        pygame.mixer.music.stop()
        self.t3_stop_sound = True

        self.total_duration = 0
        if self.combo_start_time:
            self.total_duration = int((datetime.now() - self.combo_start_time).total_seconds())

        if not self.test1_data:
            self.test1_data = {'status': 'INTERRUPTED', 'duration': 0,
                               'audio_file': 'N/A', 'volume_levels': []}
        if not self.test2_data:
            self.test2_data = {'status': 'INTERRUPTED', 'duration': 0,
                               'wave_type': self.t2_wave_type,
                               'freq_range': f"{self.t2_freq_min}-{self.t2_freq_max}"}
        if not self.test3_data:
            self.test3_data = {'status': 'INTERRUPTED', 'duration': 0,
                               'duration_per_channel': self.t3_duration_per_channel}

        self.start_btn.config(state=tk.NORMAL,
                              bg=self.colors['button_bg'],
                              fg=self.colors['button_fg'])
        self.stop_btn.config(state=tk.DISABLED)

        if interrupted:
            self._save_and_finish(
                t1_status='INTERRUPTED',
                t2_status='INTERRUPTED',
                t3_status='INTERRUPTED',
                notes=''
            )
        else:
            self.window.after(500, self.show_operator_evaluation)

    def show_complete_message(self):
        msg_window = tk.Toplevel(self.window)
        msg_window.title("Test zakończony")
        msg_window.geometry("380x130")
        msg_window.configure(bg='#FFFFFF')
        msg_window.resizable(False, False)
        msg_window.attributes('-topmost', True)
        msg_window.transient(self.window)

        msg_window.update_idletasks()
        x = (msg_window.winfo_screenwidth() // 2) - 190
        y = (msg_window.winfo_screenheight() // 2) - 65
        msg_window.geometry(f"+{x}+{y}")

        tk.Label(msg_window, text="✓ Raport zapisany!",
                 font=('Arial', 12, 'bold'),
                 bg='#FFFFFF', fg='#4CAF50').pack(pady=(25, 5))

        tk.Label(msg_window,
                 text="Okno zamknie się za 3 sekundy...",
                 font=('Arial', 9),
                 bg='#FFFFFF', fg='#666666').pack()

        msg_window.after(3000, lambda: self.restart_after_success(msg_window))

    def show_operator_evaluation(self):
        eval_window = tk.Toplevel(self.window)
        eval_window.title("Ocena wyników testu")
        eval_window.configure(bg='#FFFFFF')
        eval_window.resizable(False, False)
        eval_window.attributes('-topmost', True)
        eval_window.transient(self.window)
        eval_window.grab_set()

        w, h = 420, 420
        eval_window.update_idletasks()
        x = (eval_window.winfo_screenwidth() // 2) - (w // 2)
        y = (eval_window.winfo_screenheight() // 2) - (h // 2)
        eval_window.geometry(f"{w}x{h}+{x}+{y}")

        tk.Label(eval_window, text="OCENA WYNIKÓW TESTU",
                 font=('Arial', 13, 'bold'),
                 bg='#FFFFFF', fg='#000000').pack(pady=(18, 2))

        tk.Label(eval_window, text="Zaznacz wynik dla każdego testu:",
                 font=('Arial', 9),
                 bg='#FFFFFF', fg='#666666').pack(pady=(0, 10))

        tk.Frame(eval_window, bg='#000000', height=1).pack(fill='x', padx=20, pady=(0, 10))

        t1_var = tk.StringVar(value='PASS')
        t2_var = tk.StringVar(value='PASS')
        t3_var = tk.StringVar(value='PASS')

        for label_text, var in [
            ("TEST 1 — Music Player", t1_var),
            ("TEST 2 — Tone Generator", t2_var),
            ("TEST 3 — Stereo L/R", t3_var),
        ]:
            row = tk.Frame(eval_window, bg='#F5F5F5', relief=tk.SOLID, bd=1)
            row.pack(fill='x', padx=20, pady=5, ipady=6)

            tk.Label(row, text=label_text,
                     font=('Arial', 9, 'bold'),
                     bg='#F5F5F5', fg='#000000',
                     anchor='w').pack(side='left', padx=12)

            btn_frame = tk.Frame(row, bg='#F5F5F5')
            btn_frame.pack(side='right', padx=12)

            tk.Radiobutton(btn_frame, text="PASS",
                           variable=var, value='PASS',
                           font=('Arial', 9, 'bold'),
                           bg='#F5F5F5', fg='#4CAF50',
                           selectcolor='#FFFFFF',
                           activebackground='#F5F5F5').pack(side='left', padx=8)

            tk.Radiobutton(btn_frame, text="FAIL",
                           variable=var, value='FAIL',
                           font=('Arial', 9, 'bold'),
                           bg='#F5F5F5', fg='#F44336',
                           selectcolor='#FFFFFF',
                           activebackground='#F5F5F5').pack(side='left', padx=8)

        tk.Frame(eval_window, bg='#CCCCCC', height=1).pack(fill='x', padx=20, pady=(8, 4))

        tk.Label(eval_window, text="Uwagi (opcjonalnie):",
                 font=('Arial', 8),
                 bg='#FFFFFF', fg='#666666',
                 anchor='w').pack(fill='x', padx=20)

        notes_entry = tk.Entry(eval_window,
                               font=('Arial', 9),
                               bg='#F5F5F5', fg='#000000',
                               insertbackground='#000000',
                               bd=1, relief=tk.SOLID)
        notes_entry.pack(fill='x', padx=20, pady=(3, 10), ipady=4)

        def on_confirm():
            notes = notes_entry.get().strip()
            eval_window.destroy()
            self._save_and_finish(
                t1_status=t1_var.get(),
                t2_status=t2_var.get(),
                t3_status=t3_var.get(),
                notes=notes
            )

        tk.Button(eval_window, text="✔  ZATWIERDŹ WYNIKI",
                  font=('Arial', 10, 'bold'),
                  bg='#000000', fg='#FFFFFF',
                  activebackground='#333333',
                  activeforeground='#FFFFFF',
                  bd=0, relief=tk.FLAT,
                  width=22, height=2,
                  command=on_confirm).pack(pady=(0, 15))

    def _save_and_finish(self, t1_status, t2_status, t3_status, notes=''):
        self.test1_data['status'] = t1_status
        self.test2_data['status'] = t2_status
        self.test3_data['status'] = t3_status

        if notes:
            self.test1_data['notes'] = notes
            self.test2_data['notes'] = notes
            self.test3_data['notes'] = notes

        reporter = get_test_reporter()
        test_id, overall_status = reporter.save_combo_result(
            operator_hrid=self.operator_hrid,
            device_serial=self.device_serial,
            test1_data=self.test1_data,
            test2_data=self.test2_data,
            test3_data=self.test3_data,
            total_duration=self.total_duration,
            interrupted=self.interrupted
        )

        color_map = {
            'PASS': self.colors['green'],
            'FAIL': self.colors['red'],
            'INTERRUPTED': self.colors['orange']
        }
        self.phase_label.config(
            text=f"{'✓' if overall_status == 'PASS' else '✗'} COMBO TEST — {overall_status}",
            fg=color_map.get(overall_status, self.colors['text_primary'])
        )
        self.progress_label.config(
            text=f"Raport zapisany: {test_id} | Czas: {self.total_duration}s"
        )

        for num, status in [(1, t1_status), (2, t2_status), (3, t3_status)]:
            self.set_test_status(num, status.lower())

        print(f"[COMBO] ZAPISANO — {overall_status} | {test_id}")
        self.window.after(2000, self.show_complete_message)

    def restart_after_success(self, msg_window):
        try:
            msg_window.destroy()

            if self.scan_callback:
                new_serial = self.scan_callback("COMBO TEST")
                if new_serial:
                    self.device_serial = new_serial
                    print(f"[COMBO] Nowy S/N: {new_serial}")

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
                    self.sn_label.config(
                        text=f"Operator: {self.operator_hrid} | S/N: {self.device_serial}"
                    )
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
        if not self.combo_running:
            return

        self.combo_running = False
        self.t3_stop_sound = True

        if self.combo_job:
            self.window.after_cancel(self.combo_job)
            self.combo_job = None
        if self.sweep_job:
            self.window.after_cancel(self.sweep_job)
            self.sweep_job = None
        if self.t3_job:
            self.window.after_cancel(self.t3_job)
            self.t3_job = None

        pygame.mixer.stop()
        pygame.mixer.music.stop()

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

    # ─────────────────────────────────────────
    # UTILS
    # ─────────────────────────────────────────

    def get_song_length(self, filepath):
        try:
            try:
                from mutagen import File as MutagenFile
                audio = MutagenFile(filepath)
                if audio and audio.info:
                    return audio.info.length
            except ImportError:
                pass
            temp_sound = pygame.mixer.Sound(filepath)
            return temp_sound.get_length()
        except Exception as e:
            print(f"[COMBO] Blad pobierania dlugosci: {e}")
            return 0

    def format_time(self, seconds):
        seconds = int(seconds)
        m = seconds // 60
        s = seconds % 60
        return f"{m}:{s:02d}"

    def back_to_menu(self):
        self.combo_running = False
        self.t3_stop_sound = True
        pygame.mixer.stop()
        pygame.mixer.music.stop()

        if self.close_callback:
            self.close_callback()
        else:
            self.window.destroy()
