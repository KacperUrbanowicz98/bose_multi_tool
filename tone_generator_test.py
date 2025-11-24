"""
Test 2: Generator Częstotliwości
Moduł testowy dla Audio Testing Multi-Tool
Bose Style - White Theme (wersja polska)
"""

import tkinter as tk
from tkinter import ttk
import pygame
import numpy as np

class ToneGeneratorTest:
    def __init__(self, parent_frame, return_callback):
        self.parent_frame = parent_frame
        self.return_callback = return_callback

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
        self.stop_tone()
        self.return_callback()
