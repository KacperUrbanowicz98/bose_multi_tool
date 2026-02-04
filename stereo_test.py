"""
Test 3: Test Stereo (Lewa/Prawa)
Bose Style - White Theme (wersja polska)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pygame
import numpy as np
import threading
import time
from datetime import datetime
from test_reporter import get_test_reporter


class StereoTest:
    def __init__(self, window, operator_hrid="UNKNOWN", device_serial=None):
        self.window = window
        self.window.configure(bg='#FFFFFF')
        self.operator_hrid = operator_hrid
        self.device_serial = device_serial

        # === KOLORY BOSE WHITE THEME ===
        self.colors = {
            'bg_main': '#FFFFFF',
            'bg_card': '#F5F5F5',
            'text_primary': '#000000',
            'text_secondary': '#666666',
            'border': '#000000',
            'button_bg': '#FFFFFF',
            'button_fg': '#000000',
            'button_hover': '#000000',
            'button_hover_fg': '#FFFFFF',
            'button_active': '#000000',
            'button_active_fg': '#FFFFFF',
            'slider_bg': '#F5F5F5',
            'slider_fg': '#000000'
        }

        # Inicjalizacja pygame
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        # Zmienne stanu
        self.is_playing = False
        self.current_channel = None  # 'left', 'right', 'both'
        self.volume = 50
        self.frequency = 1000
        self.sound_thread = None
        self.stop_sound = False

        # === ZMIENNE AUTO TESTU ===
        self.auto_test_running = False
        self.auto_test_start_time = None
        self.auto_test_job = None
        self.auto_duration_per_channel = 5  # domyślnie 5 sekund
        self.auto_frequency = 1000
        self.auto_volume = 50
        self.current_test_index = 0


        # Utwórz interfejs
        self.create_widgets()

    def create_widgets(self):
        """Tworzy interfejs użytkownika"""

        # === NAGŁÓWEK ===
        header_frame = tk.Frame(self.window, bg=self.colors['bg_main'], pady=12)
        header_frame.pack(fill='x')

        title_label = tk.Label(
            header_frame,
            text="TEST LEWA/PRAWA",
            font=('Arial', 18, 'bold'),
            bg=self.colors['bg_main'],
            fg=self.colors['text_primary']
        )
        title_label.pack()

        subtitle_label = tk.Label(
            header_frame,
            text="Test kanałów audio - lewy i prawy",
            font=('Arial', 10),
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary']
        )
        subtitle_label.pack(pady=(5, 0))

        # === SEPARATOR ===
        separator = tk.Frame(self.window, height=2, bg=self.colors['border'])
        separator.pack(fill='x', padx=30, pady=(0,10))

        # === GŁÓWNY KONTENER ===
        main_container = tk.Frame(self.window, bg=self.colors['bg_main'])
        main_container.pack(fill='both', expand=True, padx=30, pady=15)

        # === AUTO TEST ===
        auto_test_frame = tk.LabelFrame(
            main_container,
            text="AUTOMATYCZNY TEST",
            font=("Arial", 9, "bold"),
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
            text="Test: Lewy → Prawy → Oba (5s każdy)",
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

        # === SEKCJA WIZUALIZACJI KANAŁÓW ===
        viz_frame = tk.Frame(main_container, bg=self.colors['bg_card'], relief='solid', borderwidth=1)
        viz_frame.pack(fill='x', pady=(0, 12))

        viz_title = tk.Label(
            viz_frame,
            text="WIZUALIZACJA KANAŁÓW",
            font=('Arial', 11, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary']
        )
        viz_title.pack(pady=(10, 8))

        # Kontener na kanały
        channels_container = tk.Frame(viz_frame, bg=self.colors['bg_card'])
        channels_container.pack(pady=(0, 10))

        # Lewy kanał
        left_frame = tk.Frame(channels_container, bg=self.colors['bg_card'])
        left_frame.pack(side='left', padx=20)

        self.left_canvas = tk.Canvas(
            left_frame,
            width=80,
            height=80,
            bg=self.colors['bg_main'],
            highlightthickness=2,
            highlightbackground=self.colors['border']
        )
        self.left_canvas.pack()
        self.left_circle = self.left_canvas.create_oval(8, 8, 72, 72, fill=self.colors['bg_card'], outline=self.colors['border'], width=2)

        left_label = tk.Label(
            left_frame,
            text="LEWY KANAŁ",
            font=('Arial', 10, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary']
        )
        left_label.pack(pady=(10, 0))

        # Prawy kanał
        right_frame = tk.Frame(channels_container, bg=self.colors['bg_card'])
        right_frame.pack(side='left', padx=20)

        self.right_canvas = tk.Canvas(
            right_frame,
            width=80,
            height=80,
            bg=self.colors['bg_main'],
            highlightthickness=2,
            highlightbackground=self.colors['border']
        )
        self.right_canvas.pack()
        self.right_circle = self.right_canvas.create_oval(8, 8, 72, 72, fill=self.colors['bg_card'], outline=self.colors['border'], width=2)

        right_label = tk.Label(
            right_frame,
            text="PRAWY KANAŁ",
            font=('Arial', 10, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary']
        )
        right_label.pack(pady=(10, 0))

        # === SEKCJA KONTROLI ===
        control_frame = tk.Frame(main_container, bg=self.colors['bg_card'], relief='solid', borderwidth=1)
        control_frame.pack(fill='x', pady=(0, 12))

        control_title = tk.Label(
            control_frame,
            text="KONTROLA KANAŁÓW",
            font=('Arial', 11, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary']
        )
        control_title.pack(pady=(10, 10))

        # Przyciski kanałów
        buttons_container = tk.Frame(control_frame, bg=self.colors['bg_card'])
        buttons_container.pack(pady=(0, 10))

        # Styl przycisków
        button_config = {
            'font': ('Arial', 11, 'bold'),
            'bg': self.colors['button_bg'],
            'fg': self.colors['button_fg'],
            'relief': 'solid',
            'borderwidth': 2,
            'width': 12,
            'height': 2,
            'cursor': 'hand2'
        }

        self.btn_left = tk.Button(
            buttons_container,
            text="◄ LEWY",
            command=lambda: self.play_channel('left'),
            **button_config
        )
        self.btn_left.pack(side='left', padx=5)
        self._bind_hover(self.btn_left)

        self.btn_both = tk.Button(
            buttons_container,
            text="◄► OBA",
            command=lambda: self.play_channel('both'),
            **button_config
        )
        self.btn_both.pack(side='left', padx=5)
        self._bind_hover(self.btn_both)

        self.btn_right = tk.Button(
            buttons_container,
            text="PRAWY ►",
            command=lambda: self.play_channel('right'),
            **button_config
        )
        self.btn_right.pack(side='left', padx=5)
        self._bind_hover(self.btn_right)

        # Przycisk STOP
        self.btn_stop = tk.Button(
            control_frame,
            text="■ STOP",
            command=self.stop_playback,
            font=('Arial', 11, 'bold'),
            bg=self.colors['button_bg'],
            fg=self.colors['button_fg'],
            relief='solid',
            borderwidth=2,
            width=30,
            height=2,
            cursor='hand2'
        )
        self.btn_stop.pack(pady=(0, 10))
        self._bind_hover(self.btn_stop)

        # === SEKCJA USTAWIEŃ ===
        settings_frame = tk.Frame(main_container, bg=self.colors['bg_card'], relief='solid', borderwidth=1)
        settings_frame.pack(fill='x')

        settings_title = tk.Label(
            settings_frame,
            text="USTAWIENIA",
            font=('Arial', 11, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary']
        )
        settings_title.pack(pady=(10, 8))

        # Częstotliwość
        freq_container = tk.Frame(settings_frame, bg=self.colors['bg_card'])
        freq_container.pack(fill='x', padx=20, pady=(0, 10))

        freq_label_frame = tk.Frame(freq_container, bg=self.colors['bg_card'])
        freq_label_frame.pack(fill='x')

        freq_label = tk.Label(
            freq_label_frame,
            text="Częstotliwość tonu testowego:",
            font=('Arial', 10),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary']
        )
        freq_label.pack(side='left')

        self.freq_value_label = tk.Label(
            freq_label_frame,
            text=f"{self.frequency} Hz",
            font=('Arial', 10, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary']
        )
        self.freq_value_label.pack(side='right')

        self.freq_slider = tk.Scale(
            freq_container,
            from_=100,
            to=5000,
            orient='horizontal',
            command=self.update_frequency,
            bg=self.colors['slider_bg'],
            fg=self.colors['text_primary'],
            highlightthickness=0,
            troughcolor=self.colors['bg_main'],
            activebackground=self.colors['text_primary'],
            relief='flat'
        )
        self.freq_slider.set(self.frequency)
        self.freq_slider.pack(fill='x', pady=(5, 0))

        # Głośność
        vol_container = tk.Frame(settings_frame, bg=self.colors['bg_card'])
        vol_container.pack(fill='x', padx=20, pady=(8, 10))

        vol_label_frame = tk.Frame(vol_container, bg=self.colors['bg_card'])
        vol_label_frame.pack(fill='x')

        vol_label = tk.Label(
            vol_label_frame,
            text="Głośność:",
            font=('Arial', 10),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary']
        )
        vol_label.pack(side='left')

        self.vol_value_label = tk.Label(
            vol_label_frame,
            text=f"{self.volume}%",
            font=('Arial', 10, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary']
        )
        self.vol_value_label.pack(side='right')

        self.vol_slider = tk.Scale(
            vol_container,
            from_=0,
            to=100,
            orient='horizontal',
            command=self.update_volume,
            bg=self.colors['slider_bg'],
            fg=self.colors['text_primary'],
            highlightthickness=0,
            troughcolor=self.colors['bg_main'],
            activebackground=self.colors['text_primary'],
            relief='flat'
        )
        self.vol_slider.set(self.volume)
        self.vol_slider.pack(fill='x', pady=(5, 0))

        # === PRZYCISK POWROTU ===
        back_button = tk.Button(
            main_container,
            text="← POWRÓT DO MENU",
            command=self.window.destroy,
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary'],
            activebackground=self.colors['button_active'],
            activeforeground=self.colors['button_active_fg'],
            bd=2,
            relief=tk.SOLID,
            font=('Arial', 8),
            width=20,
            cursor='hand2'
        )
        back_button.pack(pady=(15, 0))

    # === AUTO TEST METHODS ===

    def start_auto_test(self):
        """Uruchamia automatyczny test kanałów"""
        # Wczytaj konfigurację
        from config_manager import get_config_manager
        config_mgr = get_config_manager()
        config_mgr.reload_config()

        self.auto_duration_per_channel = config_mgr.get('test3_auto.duration_per_channel', 5)
        self.auto_frequency = config_mgr.get('test3_auto.frequency', 1000)
        self.auto_volume = config_mgr.get('test3_auto.volume', 50)

        # Zaktualizuj opis
        total_time = self.auto_duration_per_channel * 3
        self.auto_description_label.config(
            text=f"Test: Lewy → Prawy → Oba ({self.auto_duration_per_channel}s każdy, {total_time}s total)"
        )

        # Ustaw parametry
        self.frequency = self.auto_frequency
        self.volume = self.auto_volume
        self.freq_slider.set(self.auto_frequency)
        self.vol_slider.set(self.auto_volume)
        self.freq_value_label.config(text=f"{self.auto_frequency} Hz")
        self.vol_value_label.config(text=f"{self.auto_volume}%")

        # Zatrzymaj normalny test
        if self.is_playing:
            self.stop_playback()

        # Zablokuj kontrolki
        self.auto_test_running = True
        self.auto_test_start_time = datetime.now()

        self.btn_left.config(state=tk.DISABLED)
        self.btn_right.config(state=tk.DISABLED)
        self.btn_both.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.DISABLED)
        self.freq_slider.config(state=tk.DISABLED)
        self.vol_slider.config(state=tk.DISABLED)

        self.auto_start_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.auto_stop_btn.config(state=tk.NORMAL, bg=self.colors['button_bg'], fg=self.colors['button_fg'])

        # Start testu - lewy kanał
        self.run_auto_test_sequence()

    def run_auto_test_sequence(self):
        """Wykonuje sekwencję testu"""
        if not self.auto_test_running:
            return

        # Sekwencja: lewy → prawy → oba
        channels = ['left', 'right', 'both']
        self.current_test_index = 0


        def test_next_channel():
            """Testuje następny kanał w sekwencji"""

            if not self.auto_test_running or self.current_test_index >= len(channels):
                # Test zakończony
                self.save_test_report(status="PASS", interrupted=False)
                self.stop_auto_test(save_report=False)
                messagebox.showinfo("Auto Test", "Test automatyczny zakończony pomyślnie!\n\nRaport został zapisany.")
                return

            channel = channels[self.current_test_index]
            channel_names = {'left': 'Lewy', 'right': 'Prawy', 'both': 'Oba'}

            # Aktualizuj status
            self.auto_status_label.config(
                text=f"Test kanału: {channel_names[channel]} ({self.current_test_index + 1}/3)",
                fg=self.colors['text_primary']
            )

            # Odtwórz kanał
            self.play_channel(channel)

            # Zwiększ indeks
            self.current_test_index += 1

            # Zaplanuj następny kanał
            self.auto_test_job = self.window.after(
                self.auto_duration_per_channel * 1000,
                test_next_channel
            )

        # Start od pierwszego kanału
        test_next_channel()

    def stop_auto_test(self, save_report=True):
        """Zatrzymuje automatyczny test"""
        # Zapisz raport jeśli przerwano
        if self.auto_test_running and save_report:
            self.save_test_report(status="INTERRUPTED", interrupted=True)

        self.auto_test_running = False

        # Anuluj zaplanowane kroki
        if self.auto_test_job:
            self.window.after_cancel(self.auto_test_job)
            self.auto_test_job = None

        # Zatrzymaj dźwięk
        self.stop_playback()

        # Odblokuj kontrolki
        self.btn_left.config(state=tk.NORMAL)
        self.btn_right.config(state=tk.NORMAL)
        self.btn_both.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.NORMAL)
        self.freq_slider.config(state=tk.NORMAL)
        self.vol_slider.config(state=tk.NORMAL)

        self.auto_start_btn.config(state=tk.NORMAL, bg=self.colors['button_bg'], fg=self.colors['button_fg'])
        self.auto_stop_btn.config(state=tk.DISABLED, bg=self.colors['bg_card'], fg=self.colors['text_secondary'])

        # Wyczyść status
        self.auto_status_label.config(text="")

    def save_test_report(self, status, interrupted):
        """Zapisuje raport z testu do CSV"""
        try:
            if not self.auto_test_start_time:
                return

            # Oblicz czas trwania
            duration = int((datetime.now() - self.auto_test_start_time).total_seconds())

            # Zapisz do CSV
            reporter = get_test_reporter()
            reporter.save_test3_result(
                operator_hrid=self.operator_hrid,
                device_serial=self.device_serial,
                frequency=self.auto_frequency,
                volume=self.auto_volume,
                duration_per_channel=self.auto_duration_per_channel,
                total_duration=duration,
                status=status,
                interrupted=interrupted
            )
        except Exception as e:
            print(f"Błąd zapisu raportu TEST 3: {e}")

    # === ORIGINAL METHODS (bez zmian) ===

    def _bind_hover(self, button):
        """Dodaje efekt hover do przycisku"""
        def on_enter(e):
            if button['state'] != tk.DISABLED:
                button['bg'] = self.colors['button_hover']
                button['fg'] = self.colors['button_hover_fg']

        def on_leave(e):
            if button['state'] != tk.DISABLED:
                button['bg'] = self.colors['button_bg']
                button['fg'] = self.colors['button_fg']

        button.bind('<Enter>', on_enter)
        button.bind('<Leave>', on_leave)

    def update_frequency(self, value):
        """Aktualizuje częstotliwość"""
        self.frequency = int(float(value))
        self.freq_value_label.config(text=f"{self.frequency} Hz")

        # Jeśli gra, zaktualizuj dźwięk
        if self.is_playing and not self.auto_test_running:
            self.play_channel(self.current_channel, restart=True)

    def update_volume(self, value):
        """Aktualizuje głośność"""
        self.volume = int(float(value))
        self.vol_value_label.config(text=f"{self.volume}%")

    def generate_tone(self, frequency, duration, sample_rate=44100):
        """Generuje ton sinusoidalny"""
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        tone = np.sin(frequency * 2 * np.pi * t)

        # Normalizacja do 16-bit
        tone = (tone * 32767).astype(np.int16)

        return tone

    def play_channel(self, channel, restart=False):
        """Odtwarza dźwięk na wybranym kanale"""
        if self.is_playing and not restart and not self.auto_test_running:  # <-- ZMIEŃ WARUNEK
            return

        # Zatrzymaj poprzedni dźwięk
        if self.is_playing:
            self.stop_sound = True  # Oznacz do zatrzymania
            pygame.mixer.stop()

            # Poczekaj aż wątek się zatrzyma (max 1 sekunda)
            if self.sound_thread and self.sound_thread.is_alive():
                self.sound_thread.join(timeout=1.0)

            time.sleep(0.1)

        self.current_channel = channel
        self.is_playing = True
        self.stop_sound = False

        # Uruchom wątek generujący dźwięk
        self.sound_thread = threading.Thread(target=self._play_sound_thread, args=(channel,))
        self.sound_thread.daemon = True
        self.sound_thread.start()

        # Zaktualizuj wizualizację
        self.update_visualization(channel)

    def _play_sound_thread(self, channel):
        """Wątek odtwarzający dźwięk"""
        try:

            while not self.stop_sound:
                # Generuj krótki odcinek tonu (0.5 sekundy)
                tone = self.generate_tone(self.frequency, 0.5)

                # Utwórz stereo (2 kanały)
                if channel == 'left':
                    stereo_tone = np.zeros((len(tone), 2), dtype=np.int16)
                    stereo_tone[:, 0] = tone  # Lewy kanał                elif channel == 'right':
                    stereo_tone = np.zeros((len(tone), 2), dtype=np.int16)
                    stereo_tone[:, 1] = tone  # Prawy kanał
                else:  # both
                    stereo_tone = np.column_stack((tone, tone))

                # Zastosuj głośność
                volume_factor = self.volume / 100.0
                stereo_tone = (stereo_tone * volume_factor).astype(np.int16)

                # Odtwórz dźwięk
                sound = pygame.sndarray.make_sound(stereo_tone)
                sound.play()

                # Czekaj na zakończenie odtwarzania
                while pygame.mixer.get_busy() and not self.stop_sound:
                    time.sleep(0.05)
        except Exception as e:
            print(f"Błąd w wątku dźwięku: {e}")
        finally:
            self.is_playing = False

    def stop_playback(self):
        """Zatrzymuje odtwarzanie"""
        self.stop_sound = True
        self.is_playing = False
        pygame.mixer.stop()

        # Resetuj wizualizację
        self.update_visualization(None)

    def update_visualization(self, channel):
        """Aktualizuje wizualizację kanałów"""
        # Resetuj oba kanały
        self.left_canvas.itemconfig(self.left_circle, fill=self.colors['bg_card'])
        self.right_canvas.itemconfig(self.right_circle, fill=self.colors['bg_card'])

        # Podświetl aktywne kanały
        if channel == 'left' or channel == 'both':
            self.left_canvas.itemconfig(self.left_circle, fill=self.colors['text_primary'])

        if channel == 'right' or channel == 'both':
            self.right_canvas.itemconfig(self.right_circle, fill=self.colors['text_primary'])

    def cleanup(self):
        """Czyszczenie zasobów"""
        if self.auto_test_running:
            self.stop_auto_test()
        self.stop_playback()
