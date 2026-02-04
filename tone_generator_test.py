"""
Test 2: Generator Częstotliwości
Moduł testowy dla Audio Testing Multi-Tool
Bose Style - White Theme (wersja polska)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pygame
import numpy as np
import time
from datetime import datetime
from test_reporter import get_test_reporter


class ToneGeneratorTest:
    def __init__(self, parent_frame, return_callback, operator_hrid="UNKNOWN", device_serial=None):
        self.parent_frame = parent_frame
        self.return_callback = return_callback
        self.operator_hrid = operator_hrid
        self.device_serial = device_serial

        # === KOLORY BOSE WHITE THEME ===
        self.colors = {
            'bg_main': '#FFFFFF',
            'bg_card': '#F5F5F5',
            'text_primary': '#000000',
            'text_secondary': '#666666',
            'border': '#000000',
            'wave_color': '#00FF00',
            'button_bg': '#FFFFFF',
            'button_fg': '#000000',
            'button_active': '#000000',
            'button_active_fg': '#FFFFFF'
        }

        pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

        self.frequency = 20
        self.volume = 50
        self.wave_type = "sine"
        self.is_playing = False
        self.is_paused = False
        self.sound = None
        self.animation_running = False

        # === ZMIENNE AUTO TESTU ===
        self.auto_test_running = False
        self.auto_test_start_time = None
        self.auto_test_job = None
        self.auto_freq_min = 20
        self.auto_freq_max = 20000
        self.auto_duration = 10
        self.auto_volume = 50
        self.auto_wave_type = "sine"

        self.create_widgets()

        # Zatrzymaj dźwięk przy zamykaniu okna
        parent_frame.winfo_toplevel().protocol("WM_DELETE_WINDOW", self.cleanup_and_return)

    def create_widgets(self):
        """Tworzenie interfejsu - kompaktowy"""
        main_frame = tk.Frame(self.parent_frame, bg=self.colors['bg_main'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Tytuł
        title = tk.Label(
            main_frame,
            text="GENERATOR CZĘSTOTLIWOŚCI",
            font=("Arial", 14, "bold"),
            bg=self.colors['bg_main'],
            fg=self.colors['text_primary']
        )
        title.pack(pady=(0, 3))

        subtitle = tk.Label(
            main_frame,
            text="Test 2",
            font=("Arial", 8),
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary']
        )
        subtitle.pack(pady=(0, 12))

        # === WIZUALIZACJA ===
        viz_frame = tk.Frame(main_frame, bg=self.colors['bg_main'], relief=tk.SOLID, bd=2)
        viz_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        self.canvas = tk.Canvas(
            viz_frame,
            width=500,
            height=140,
            bg=self.colors['bg_main'],
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack()

        self.freq_label_id = self.canvas.create_text(
            250, 25,
            text=f"{self.frequency} Hz",
            fill=self.colors['wave_color'],
            font=("Arial", 18, "bold")
        )

        # === AUTO TEST ===
        auto_test_frame = tk.LabelFrame(
            main_frame,
            text="AUTOMATYCZNY TEST",
            font=("Arial", 8, "bold"),
            bg=self.colors['bg_main'],
            fg=self.colors['text_primary'],
            bd=2,
            relief=tk.SOLID
        )
        auto_test_frame.pack(fill=tk.X, pady=(0, 10))

        auto_container = tk.Frame(auto_test_frame, bg=self.colors['bg_main'])
        auto_container.pack(fill=tk.X, padx=8, pady=8)

        self.auto_description_label = tk.Label(
            auto_container,
            text="Przejazd częstotliwości: 20 Hz → 20000 Hz (10s)",
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
            bg=self.colors['button_bg'],
            fg=self.colors['button_fg'],
            activebackground=self.colors['button_active'],
            activeforeground=self.colors['button_active_fg'],
            bd=2,
            relief=tk.SOLID,
            width=18,
            command=self.start_auto_test
        )
        self.auto_start_btn.pack(side=tk.LEFT, padx=3)

        self.auto_stop_btn = tk.Button(
            auto_buttons,
            text="⏹ STOP AUTO TEST",
            font=('Arial', 8, 'bold'),
            bg=self.colors['button_bg'],
            fg=self.colors['button_fg'],
            activebackground=self.colors['button_active'],
            activeforeground=self.colors['button_active_fg'],
            bd=2,
            relief=tk.SOLID,
            width=18,
            state=tk.DISABLED,
            command=self.stop_auto_test
        )
        self.auto_stop_btn.pack(side=tk.LEFT, padx=3)

        # Status auto testu
        self.auto_status_label = tk.Label(
            auto_container,
            text="",
            font=('Arial', 8),
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary']
        )
        self.auto_status_label.pack(pady=(5, 0))

        # === KSZTAŁT FALI ===
        wave_frame = tk.LabelFrame(
            main_frame,
            text="KSZTAŁT FALI",
            font=("Arial", 8, "bold"),
            bg=self.colors['bg_main'],
            fg=self.colors['text_primary'],
            bd=1,
            relief=tk.SOLID
        )
        wave_frame.pack(fill=tk.X, pady=(0, 10))

        self.wave_var = tk.StringVar(value="sine")

        waves = [
            ("SINUSOIDALNA", "sine"),
            ("KWADRATOWA", "square"),
            ("PIŁOKSZTAŁTNA", "sawtooth"),
            ("TRÓJKĄTNA", "triangle")
        ]

        wave_buttons_frame = tk.Frame(wave_frame, bg=self.colors['bg_main'])
        wave_buttons_frame.pack(pady=6)

        for text, value in waves:
            rb = tk.Radiobutton(
                wave_buttons_frame,
                text=text,
                variable=self.wave_var,
                value=value,
                font=("Arial", 8),
                bg=self.colors['bg_main'],
                fg=self.colors['text_primary'],
                selectcolor=self.colors['bg_card'],
                activebackground=self.colors['bg_main'],
                activeforeground=self.colors['text_primary'],
                command=self.on_wave_change,
                bd=0,
                highlightthickness=0
            )
            rb.pack(side=tk.LEFT, padx=10)

        # === CZĘSTOTLIWOŚĆ ===
        freq_frame = tk.LabelFrame(
            main_frame,
            text="CZĘSTOTLIWOŚĆ",
            font=("Arial", 8, "bold"),
            bg=self.colors['bg_main'],
            fg=self.colors['text_primary'],
            bd=1,
            relief=tk.SOLID
        )
        freq_frame.pack(fill=tk.X, pady=(0, 10))

        # Entry
        freq_controls = tk.Frame(freq_frame, bg=self.colors['bg_main'])
        freq_controls.pack(pady=6)

        tk.Label(
            freq_controls,
            text="CZĘSTOTLIWOŚĆ:",
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary'],
            font=("Arial", 8)
        ).pack(side=tk.LEFT, padx=3)

        self.freq_entry = tk.Entry(
            freq_controls,
            width=8,
            font=("Arial", 10),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary'],
            insertbackground=self.colors['text_primary'],
            bd=1,
            relief=tk.SOLID
        )
        self.freq_entry.insert(0, str(self.frequency))
        self.freq_entry.pack(side=tk.LEFT, padx=3)
        self.freq_entry.bind("<Return>", lambda e: self.update_frequency_from_entry())

        tk.Label(
            freq_controls,
            text="Hz",
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary'],
            font=("Arial", 8)
        ).pack(side=tk.LEFT)

        # Suwak
        slider_frame = tk.Frame(freq_frame, bg=self.colors['bg_main'])
        slider_frame.pack(fill=tk.X, padx=15, pady=(3, 6))

        tk.Label(
            slider_frame,
            text="20",
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary'],
            font=("Arial", 7)
        ).pack(side=tk.LEFT)

        self.freq_slider = tk.Scale(
            slider_frame,
            from_=20,
            to=20000,
            orient=tk.HORIZONTAL,
            bg=self.colors['bg_main'],
            fg=self.colors['text_primary'],
            troughcolor=self.colors['bg_card'],
            highlightthickness=0,
            command=self.on_slider_change,
            showvalue=0,
            length=320,
            bd=0,
            relief=tk.FLAT
        )
        self.freq_slider.set(self.frequency)
        self.freq_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        tk.Label(
            slider_frame,
            text="20000",
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary'],
            font=("Arial", 7)
        ).pack(side=tk.LEFT)

        # Przyciski +/-
        button_frame = tk.Frame(freq_frame, bg=self.colors['bg_main'])
        button_frame.pack(pady=(0, 6))

        increments = [(-100, "-100"), (-10, "-10"), (-1, "-1"), (1, "+1"), (10, "+10"), (100, "+100")]

        for delta, text in increments:
            btn = tk.Button(
                button_frame,
                text=text,
                width=5,
                font=("Arial", 7),
                bg=self.colors['button_bg'],
                fg=self.colors['button_fg'],
                activebackground=self.colors['button_active'],
                activeforeground=self.colors['button_active_fg'],
                bd=1,
                relief=tk.SOLID,
                command=lambda d=delta: self.adjust_frequency(d)
            )
            btn.pack(side=tk.LEFT, padx=2)

        # === GŁOŚNOŚĆ ===
        vol_frame = tk.LabelFrame(
            main_frame,
            text="GŁOŚNOŚĆ",
            font=("Arial", 8, "bold"),
            bg=self.colors['bg_main'],
            fg=self.colors['text_primary'],
            bd=1,
            relief=tk.SOLID
        )
        vol_frame.pack(fill=tk.X, pady=(0, 10))

        vol_controls = tk.Frame(vol_frame, bg=self.colors['bg_main'])
        vol_controls.pack(pady=6)

        tk.Label(
            vol_controls,
            text="0%",
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary'],
            font=("Arial", 7)
        ).pack(side=tk.LEFT)

        self.vol_slider = tk.Scale(
            vol_controls,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            bg=self.colors['bg_main'],
            fg=self.colors['text_primary'],
            troughcolor=self.colors['bg_card'],
            highlightthickness=0,
            command=self.on_volume_change,
            showvalue=0,
            length=320,
            bd=0,
            relief=tk.FLAT
        )
        self.vol_slider.set(self.volume)
        self.vol_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        tk.Label(
            vol_controls,
            text="100%",
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary'],
            font=("Arial", 7)
        ).pack(side=tk.LEFT)

        self.vol_label = tk.Label(
            vol_frame,
            text=f"POZIOM: {self.volume}%",
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary'],
            font=("Arial", 8)
        )
        self.vol_label.pack()

        # === STEROWANIE ===
        control_frame = tk.Frame(main_frame, bg=self.colors['bg_main'])
        control_frame.pack(pady=12)

        self.play_btn = tk.Button(
            control_frame,
            text="▶ ODTWÓRZ",
            width=10,
            font=("Arial", 9, "bold"),
            bg=self.colors['button_bg'],
            fg=self.colors['button_fg'],
            activebackground=self.colors['button_active'],
            activeforeground=self.colors['button_active_fg'],
            bd=2,
            relief=tk.SOLID,
            command=self.play_tone
        )
        self.play_btn.pack(side=tk.LEFT, padx=4)

        self.pause_btn = tk.Button(
            control_frame,
            text="⏸ PAUZA",
            width=10,
            font=("Arial", 9, "bold"),
            bg=self.colors['bg_card'],
            fg=self.colors['text_secondary'],
            activebackground=self.colors['button_active'],
            activeforeground=self.colors['button_active_fg'],
            bd=2,
            relief=tk.SOLID,
            command=self.pause_tone,
            state=tk.DISABLED
        )
        self.pause_btn.pack(side=tk.LEFT, padx=4)

        self.stop_btn = tk.Button(
            control_frame,
            text="⏹ STOP",
            width=10,
            font=("Arial", 9, "bold"),
            bg=self.colors['bg_card'],
            fg=self.colors['text_secondary'],
            activebackground=self.colors['button_active'],
            activeforeground=self.colors['button_active_fg'],
            bd=2,
            relief=tk.SOLID,
            command=self.stop_tone,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=4)

        # === POWRÓT ===
        back_btn = tk.Button(
            main_frame,
            text="← POWRÓT DO MENU",
            font=("Arial", 8),
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary'],
            activebackground=self.colors['button_active'],
            activeforeground=self.colors['button_active_fg'],
            bd=1,
            relief=tk.SOLID,
            command=self.cleanup_and_return
        )
        back_btn.pack(pady=8)

    # === AUTO TEST METHODS ===

    def start_auto_test(self):
        """Uruchamia automatyczny test - frequency sweep"""
        # Wczytaj konfigurację z trybu inżynieryjnego
        from config_manager import get_config_manager
        config_mgr = get_config_manager()
        config_mgr.reload_config()

        self.auto_freq_min = config_mgr.get('test2_auto.freq_min', 20)
        self.auto_freq_max = config_mgr.get('test2_auto.freq_max', 20000)
        self.auto_duration = config_mgr.get('test2_auto.duration', 10)
        self.auto_volume = config_mgr.get('test2_auto.volume', 50)
        self.auto_wave_type = config_mgr.get('test2_auto.wave_type', 'sine')

        # Zaktualizuj opis
        wave_names = {
            'sine': 'Sinusoidalna',
            'square': 'Kwadratowa',
            'sawtooth': 'Piłokształtna',
            'triangle': 'Trójkątna'
        }
        self.auto_description_label.config(
            text=f"Przejazd: {self.auto_freq_min} Hz → {self.auto_freq_max} Hz ({self.auto_duration}s, {wave_names.get(self.auto_wave_type, 'Sinusoidalna')})"
        )

        # Zatrzymaj normalny test jeśli działa
        if self.is_playing:
            self.stop_tone()

        # Ustaw parametry
        self.wave_var.set(self.auto_wave_type)
        self.volume = self.auto_volume
        self.vol_slider.set(self.auto_volume)
        self.vol_label.config(text=f"POZIOM: {self.auto_volume}%")

        # Zablokuj kontrolki
        self.auto_test_running = True
        self.auto_test_start_time = datetime.now()

        # Przyciski sterowania
        self.play_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.pause_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.stop_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])

        # Suwaki i kontrolki
        self.freq_slider.config(state=tk.DISABLED)
        self.vol_slider.config(state=tk.DISABLED)
        self.freq_entry.config(state=tk.DISABLED)

        # Radiobuttony fali
        for widget in self.parent_frame.winfo_children():
            self._disable_radiobuttons(widget)

        # Przyciski auto testu
        self.auto_start_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.auto_stop_btn.config(state=tk.NORMAL, bg=self.colors['button_bg'], fg=self.colors['button_fg'])

        # Start sweep
        self.run_frequency_sweep()

    def _disable_radiobuttons(self, widget):
        """Rekurencyjnie wyłącza radiobuttony"""
        if isinstance(widget, tk.Radiobutton):
            widget.config(state=tk.DISABLED)
        for child in widget.winfo_children():
            self._disable_radiobuttons(child)

    def _enable_radiobuttons(self, widget):
        """Rekurencyjnie włącza radiobuttony"""
        if isinstance(widget, tk.Radiobutton):
            widget.config(state=tk.NORMAL)
        for child in widget.winfo_children():
            self._enable_radiobuttons(child)

    def run_frequency_sweep(self):
        """Wykonuje przejazd częstotliwości"""
        if not self.auto_test_running:
            return

        start_time = time.time()
        end_time = start_time + self.auto_duration

        # Ustaw początkową częstotliwość
        self.frequency = self.auto_freq_min
        self.freq_slider.set(self.frequency)
        self.freq_entry.delete(0, tk.END)
        self.freq_entry.insert(0, str(self.frequency))
        self.canvas.itemconfig(self.freq_label_id, text=f"{self.frequency} Hz")

        # Start dźwięku
        wave_data = self.generate_wave(self.frequency)
        self.sound = pygame.sndarray.make_sound(wave_data)
        self.sound.play(loops=-1)
        self.is_playing = True

        # Animacja
        if not self.animation_running:
            self.animation_running = True
            self.animate_wave()

        # Aktualizuj częstotliwość w pętli
        self.sweep_step(start_time, end_time)

    def sweep_step(self, start_time, end_time):
        """Jeden krok frequency sweep"""
        if not self.auto_test_running:
            return

        current_time = time.time()
        elapsed = current_time - start_time
        total_duration = end_time - start_time

        if current_time >= end_time:
            # Test zakończony
            self.save_test_report(status="PASS", interrupted=False)
            self.stop_auto_test(save_report=False)
            messagebox.showinfo("Auto Test", "Test automatyczny zakończony pomyślnie!\n\nRaport został zapisany.")
            return

        # Oblicz aktualną częstotliwość (interpolacja logarytmiczna dla lepszego efektu)
        progress = elapsed / total_duration

        # Logarytmiczna interpolacja (brzmi lepiej dla audio)
        log_min = np.log10(self.auto_freq_min)
        log_max = np.log10(self.auto_freq_max)
        current_freq = int(10 ** (log_min + progress * (log_max - log_min)))

        # Aktualizuj częstotliwość
        self.frequency = current_freq
        self.freq_slider.set(current_freq)
        self.freq_entry.delete(0, tk.END)
        self.freq_entry.insert(0, str(current_freq))
        self.canvas.itemconfig(self.freq_label_id, text=f"{current_freq} Hz")

        # Aktualizuj status
        remaining = int(total_duration - elapsed)
        self.auto_status_label.config(
            text=f"Częstotliwość: {current_freq} Hz | Pozostało: {remaining}s",
            fg=self.colors['text_primary']
        )

        # Aktualizuj dźwięk
        if self.sound:
            self.sound.stop()
        wave_data = self.generate_wave(current_freq)
        self.sound = pygame.sndarray.make_sound(wave_data)
        self.sound.play(loops=-1)

        # Następny krok za 50ms
        self.auto_test_job = self.parent_frame.after(50, lambda: self.sweep_step(start_time, end_time))

    def stop_auto_test(self, save_report=True):
        """Zatrzymuje automatyczny test"""
        # Zapisz raport jeśli przerwano
        if self.auto_test_running and save_report:
            self.save_test_report(status="INTERRUPTED", interrupted=True)

        self.auto_test_running = False

        # Anuluj zaplanowane kroki
        if self.auto_test_job:
            self.parent_frame.after_cancel(self.auto_test_job)
            self.auto_test_job = None

        # Zatrzymaj dźwięk
        if self.sound:
            self.sound.stop()
        self.is_playing = False
        self.animation_running = False

        # Odblokuj kontrolki
        self.play_btn.config(state=tk.NORMAL, bg=self.colors['button_bg'], fg=self.colors['button_fg'])
        self.pause_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.stop_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])

        self.freq_slider.config(state=tk.NORMAL)
        self.vol_slider.config(state=tk.NORMAL)
        self.freq_entry.config(state=tk.NORMAL)

        # Radiobuttony
        for widget in self.parent_frame.winfo_children():
            self._enable_radiobuttons(widget)

        # Przyciski auto testu
        self.auto_start_btn.config(state=tk.NORMAL, bg=self.colors['button_bg'], fg=self.colors['button_fg'])
        self.auto_stop_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])

        # Wyczyść status
        self.auto_status_label.config(text="")
        self.canvas.delete("wave_line")

    def save_test_report(self, status, interrupted):
        """Zapisuje raport z testu do CSV"""
        try:
            if not self.auto_test_start_time:
                return

            # Oblicz czas trwania
            duration = int((datetime.now() - self.auto_test_start_time).total_seconds())

            wave_names = {
                'sine': 'Sinusoidalna',
                'square': 'Kwadratowa',
                'sawtooth': 'Piłokształtna',
                'triangle': 'Trójkątna'
            }

            # Zapisz do CSV
            reporter = get_test_reporter()
            reporter.save_test2_result(
                operator_hrid=self.operator_hrid,
                device_serial=self.device_serial,
                wave_type=wave_names.get(self.auto_wave_type, self.auto_wave_type),
                freq_range=f"{self.auto_freq_min}-{self.auto_freq_max}",
                duration=duration,
                volume=self.auto_volume,
                status=status,
                interrupted=interrupted
            )
        except Exception as e:
            print(f"Błąd zapisu raportu TEST 2: {e}")

    # === ORIGINAL METHODS (bez zmian) ===

    def generate_wave(self, frequency, duration=1.0, sample_rate=44100):
        """Generuje falę dźwiękową"""
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples, False)

        wave_type = self.wave_var.get()

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

        amplitude = self.volume / 100.0
        wave = wave * amplitude
        wave = np.int16(wave * 32767)
        wave = np.repeat(wave.reshape(-1, 1), 2, axis=1)

        return wave

    def play_tone(self):
        if self.is_playing and not self.is_paused:
            return

        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
        else:
            wave_data = self.generate_wave(self.frequency)
            self.sound = pygame.sndarray.make_sound(wave_data)
            self.sound.play(loops=-1)

        self.is_playing = True
        self.play_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'])
        self.pause_btn.config(state=tk.NORMAL, bg=self.colors['button_bg'], fg=self.colors['button_fg'])
        self.stop_btn.config(state=tk.NORMAL, bg=self.colors['button_bg'], fg=self.colors['button_fg'])

        if not self.animation_running:
            self.animation_running = True
            self.animate_wave()

    def pause_tone(self):
        if self.is_playing and not self.is_paused:
            if self.sound:
                self.sound.stop()
            self.is_paused = True
            self.play_btn.config(state=tk.NORMAL, bg=self.colors['button_bg'])
            self.pause_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'])

    def stop_tone(self):
        if self.sound:
            self.sound.stop()
        self.is_playing = False
        self.is_paused = False
        self.animation_running = False

        self.play_btn.config(state=tk.NORMAL, bg=self.colors['button_bg'])
        self.pause_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.stop_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])

        self.canvas.delete("wave_line")

    def on_slider_change(self, value):
        self.frequency = int(float(value))
        self.freq_entry.delete(0, tk.END)
        self.freq_entry.insert(0, str(self.frequency))
        self.canvas.itemconfig(self.freq_label_id, text=f"{self.frequency} Hz")

        if self.is_playing and not self.is_paused:
            if self.sound:
                self.sound.stop()
            wave_data = self.generate_wave(self.frequency)
            self.sound = pygame.sndarray.make_sound(wave_data)
            self.sound.play(loops=-1)

    def update_frequency_from_entry(self):
        try:
            freq = int(self.freq_entry.get())
            if 20 <= freq <= 20000:
                self.frequency = freq
                self.freq_slider.set(freq)
                self.canvas.itemconfig(self.freq_label_id, text=f"{self.frequency} Hz")

                if self.is_playing and not self.is_paused:
                    if self.sound:
                        self.sound.stop()
                    wave_data = self.generate_wave(self.frequency)
                    self.sound = pygame.sndarray.make_sound(wave_data)
                    self.sound.play(loops=-1)
            else:
                self.freq_entry.delete(0, tk.END)
                self.freq_entry.insert(0, str(self.frequency))
        except ValueError:
            self.freq_entry.delete(0, tk.END)
            self.freq_entry.insert(0, str(self.frequency))

    def adjust_frequency(self, delta):
        new_freq = self.frequency + delta
        new_freq = max(20, min(20000, new_freq))
        self.frequency = new_freq
        self.freq_slider.set(new_freq)
        self.freq_entry.delete(0, tk.END)
        self.freq_entry.insert(0, str(new_freq))
        self.canvas.itemconfig(self.freq_label_id, text=f"{self.frequency} Hz")

        if self.is_playing and not self.is_paused:
            if self.sound:
                self.sound.stop()
            wave_data = self.generate_wave(self.frequency)
            self.sound = pygame.sndarray.make_sound(wave_data)
            self.sound.play(loops=-1)

    def on_volume_change(self, value):
        self.volume = int(float(value))
        self.vol_label.config(text=f"POZIOM: {self.volume}%")

        if self.is_playing and not self.is_paused:
            if self.sound:
                self.sound.stop()
            wave_data = self.generate_wave(self.frequency)
            self.sound = pygame.sndarray.make_sound(wave_data)
            self.sound.play(loops=-1)

    def on_wave_change(self):
        if self.is_playing and not self.is_paused:
            if self.sound:
                self.sound.stop()
            wave_data = self.generate_wave(self.frequency)
            self.sound = pygame.sndarray.make_sound(wave_data)
            self.sound.play(loops=-1)

    def animate_wave(self):
        if not self.animation_running:
            return

        self.canvas.delete("wave_line")

        width = 500
        height = 140
        num_points = width

        cycles = 3
        t = np.linspace(0, cycles / self.frequency, num_points)

        wave_type = self.wave_var.get()

        if wave_type == "sine":
            y = np.sin(2 * np.pi * self.frequency * t)
        elif wave_type == "square":
            y = np.sign(np.sin(2 * np.pi * self.frequency * t))
        elif wave_type == "sawtooth":
            y = 2 * (t * self.frequency - np.floor(t * self.frequency + 0.5))
        elif wave_type == "triangle":
            y = 2 * np.abs(2 * (t * self.frequency - np.floor(t * self.frequency + 0.5))) - 1
        else:
            y = np.sin(2 * np.pi * self.frequency * t)

        y_scaled = height / 2 + (y * (height / 2 - 30))

        points = []
        for i in range(num_points):
            x = i
            points.append((x, y_scaled[i]))

        for i in range(len(points) - 1):
            self.canvas.create_line(
                points[i][0], points[i][1],
                points[i + 1][0], points[i + 1][1],
                fill=self.colors['wave_color'],
                width=2,
                tags="wave_line"
            )

        if self.animation_running:
            self.canvas.after(50, self.animate_wave)

    def cleanup_and_return(self):
        # Zatrzymaj auto test jeśli działa
        if self.auto_test_running:
            self.stop_auto_test()

        self.stop_tone()
        self.return_callback()
