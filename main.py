"""
Audio Testing Multi-Tool
Menu główne z wyborem różnych testów audio
"""

import tkinter as tk
from tkinter import ttk
import pygame
import os


class AudioMultiTool:
    """Główna klasa aplikacji z menu wyboru testów"""

    def __init__(self, root):
        self.root = root
        self.root.title("Audio Testing Multi-Tool")
        self.root.geometry("550x600")

        # Inicjalizacja pygame
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        # Aktualnie otwarte okno testu (tylko jedno na raz)
        self.current_test_window = None

        self.create_main_menu()

    def create_main_menu(self):
        """Tworzy główne menu z przyciskami wyboru testów"""

        # Ramka główna
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Tytuł
        title_label = ttk.Label(main_frame,
                                text="Audio Testing Multi-Tool",
                                font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=15)

        subtitle_label = ttk.Label(main_frame,
                                   text="Wybierz test do uruchomienia:",
                                   font=('Arial', 10))
        subtitle_label.grid(row=1, column=0, pady=8)

        # Style dla przycisków
        style = ttk.Style()
        style.configure('Big.TButton', font=('Arial', 10), padding=12)

        # Kontener na przyciski
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=15)

        # === PRZYCISKI TESTÓW ===

        # Test 1: Odtwarzacz z EQ
        btn1 = ttk.Button(button_frame,
                          text="🎵 Test 1: Odtwarzacz Muzyki + Equalizer",
                          style='Big.TButton',
                          command=self.open_music_player_test,
                          width=42)
        btn1.grid(row=0, column=0, pady=6, padx=15)

        # Test 2: Generator tonów
        btn2 = ttk.Button(button_frame,
                          text="🔊 Test 2: Generator Tonów (20Hz - 20kHz)",
                          style='Big.TButton',
                          command=self.open_tone_generator_test,
                          width=42)
        btn2.grid(row=1, column=0, pady=6, padx=15)

        # Test 3: Test stereo
        btn3 = ttk.Button(button_frame,
                          text="🎧 Test 3: Test Separacji Stereo (L/R)",
                          style='Big.TButton',
                          command=self.open_stereo_test,
                          width=42)
        btn3.grid(row=2, column=0, pady=6, padx=15)

        # Test 4: Frequency Sweep
        btn4 = ttk.Button(button_frame,
                          text="📊 Test 4: Frequency Sweep",
                          style='Big.TButton',
                          command=self.open_sweep_test,
                          width=42)
        btn4.grid(row=3, column=0, pady=6, padx=15)

        # Test 5: Pink/White Noise (do zaimplementowania)
        btn5 = ttk.Button(button_frame,
                          text="📢 Test 5: Pink/White Noise",
                          style='Big.TButton',
                          command=self.open_noise_test,
                          width=42,
                          state='disabled')
        btn5.grid(row=4, column=0, pady=6, padx=15)

        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=3, column=0,
                                                            sticky=(tk.W, tk.E), pady=15)

        # Przycisk wyjścia
        exit_btn = ttk.Button(main_frame,
                              text="✖ Wyjdź z aplikacji",
                              command=self.exit_app,
                              width=22)
        exit_btn.grid(row=4, column=0, pady=8)

        # === STOPKA Z LOGO I AUTOREM - ZWIĘKSZONY ODSTĘP ===
        footer_frame = ttk.Frame(main_frame)
        footer_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(20, 0))  # BYŁO 8, TERAZ 20

        # Logo po lewej
        left_footer = ttk.Frame(footer_frame)
        left_footer.pack(side=tk.LEFT, anchor=tk.W)

        # Szukaj logo w różnych formatach
        logo_loaded = False
        for logo_name in ["logo.png", "Logo.png", "logo.PNG", "logo.ico", "logo.jpg", "logo.jpeg"]:
            if os.path.exists(logo_name):
                try:
                    original_image = tk.PhotoImage(file=logo_name)

                    orig_width = original_image.width()
                    orig_height = original_image.height()

                    target_width = 100
                    target_height = 50

                    scale_x = max(1, orig_width // target_width)
                    scale_y = max(1, orig_height // target_height)

                    scale = min(scale_x, scale_y)

                    if scale > 1:
                        self.logo_image = original_image.subsample(scale, scale)
                    else:
                        self.logo_image = original_image

                    logo_label = ttk.Label(left_footer, image=self.logo_image)
                    logo_label.pack(side=tk.LEFT, padx=3)
                    logo_loaded = True
                    break
                except Exception as e:
                    continue

        if not logo_loaded:
            logo_text = ttk.Label(left_footer, text="🎧", font=('Arial', 12))
            logo_text.pack(side=tk.LEFT, padx=3)

        # Autorzy po prawej
        right_footer = ttk.Frame(footer_frame)
        right_footer.pack(side=tk.RIGHT, anchor=tk.E)

        author_label = ttk.Label(right_footer,
                                text="Autor: Kacper Urbanowicz | Rafał Kobylecki",
                                font=('Arial', 8),
                                foreground='gray')
        author_label.pack(side=tk.RIGHT, padx=3)

        # Konfiguracja rozciągania
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

    def open_music_player_test(self):
        """Otwiera Test 1 - Odtwarzacz z EQ"""
        if self.current_test_window is not None:
            self.current_test_window.destroy()

        # Nowe okno dla testu
        test_window = tk.Toplevel(self.root)
        test_window.title("Test 1: Odtwarzacz Muzyki + Equalizer")
        test_window.geometry("700x600")

        # Tu będzie cała klasa AudioTester z poprzedniego kodu
        from music_player_test import MusicPlayerTest
        test = MusicPlayerTest(test_window)

        self.current_test_window = test_window

    def open_tone_generator_test(self):
        """Otwiera Test 2 - Generator Tonów"""
        if self.current_test_window is not None:
            self.current_test_window.destroy()

        test_window = tk.Toplevel(self.root)
        test_window.title("Test 2: Generator Tonów")
        test_window.geometry("600x500")

        # Tu będzie klasa ToneGeneratorTest
        from tone_generator_test import ToneGeneratorTest
        test = ToneGeneratorTest(test_window)

        self.current_test_window = test_window

    def open_stereo_test(self):
        """Otwiera Test 3 - Test Stereo"""
        # Placeholder - do implementacji
        pass

    def open_sweep_test(self):
        """Otwiera Test 4 - Sweep Test"""
        # Placeholder - do implementacji
        pass

    def open_noise_test(self):
        """Otwiera Test 5 - Pink/White Noise"""
        # Placeholder - do implementacji
        pass

    def exit_app(self):
        """Zamyka aplikację"""
        pygame.mixer.quit()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioMultiTool(root)
    root.mainloop()
