"""
Audio Testing Multi-Tool
Menu główne - Bose White Theme (wersja polska)
Wersja: 1.0.0
Autorzy: Kacper Urbanowicz, Rafał Kobylecki
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
import os
import json


from resource_manager import get_resource_manager
from config_manager import get_config_manager
from login_screen import LoginScreen

class AudioMultiTool:
    """Główna klasa aplikacji - Bose White Style"""

    COLORS = {
        'bg_main': '#FFFFFF',
        'bg_card': '#F5F5F5',
        'text_primary': '#000000',
        'text_secondary': '#666666',
        'border': '#000000',
        'button_bg': '#FFFFFF',
        'button_fg': '#000000',
        'button_hover': '#000000',
        'button_hover_fg': '#FFFFFF'
    }

    def __init__(self, root):
        self.root = root
        self.root.configure(bg=self.COLORS['bg_main'])

        self.resource_mgr = get_resource_manager()
        self.config_mgr = get_config_manager()

        window_geometry = '480x550'
        self.root.title("Narzędzie Testowania Audio")
        self.root.geometry(window_geometry)

        self.engineering_mode_active = False
        self.key_sequence = []
        self.last_key_time = 0
        self.root.bind('<KeyPress>', self.check_engineering_mode_sequence)

        audio_config = self.config_mgr.get_audio_config()
        success = self.resource_mgr.init_pygame(
            frequency=audio_config.get('sample_rate', 44100),
            size=-16,
            channels=audio_config.get('channels', 2),
            buffer=audio_config.get('buffer_size', 512)
        )

        if not success:
            messagebox.showerror("Błąd", "Nie można zainicjować systemu audio!")
            sys.exit(1)

        self.current_test_window = None
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        self.create_main_menu()

        if self.config_mgr.get('app.first_run', True):
            self.config_mgr.set('app.first_run', False)
            self.config_mgr.save_config()

    def check_engineering_mode_sequence(self, event):
        """Wykrywa Ctrl+Shift+DDD"""
        import time
        current_time = time.time()

        if current_time - self.last_key_time > 2.0:
            self.key_sequence = []

        self.last_key_time = current_time

        if event.state & 0x0004 and event.state & 0x0001:
            if event.keysym.lower() == 'd':
                self.key_sequence.append('d')
                if len(self.key_sequence) >= 3:
                    self.open_engineering_mode()
                    self.key_sequence = []

    def open_engineering_mode(self):
        """Tryb inżynieryjny"""
        if self.engineering_mode_active:
            return

        self.engineering_mode_active = True

        eng_window = tk.Toplevel(self.root)
        eng_window.title("Tryb Inżynieryjny")
        eng_window.geometry("750x550")
        eng_window.configure(bg=self.COLORS['bg_main'])
        eng_window.protocol("WM_DELETE_WINDOW", lambda: self.close_engineering_mode(eng_window))

        header_frame = tk.Frame(eng_window, bg=self.COLORS['bg_main'], padx=15, pady=15)
        header_frame.pack(fill=tk.X)

        tk.Label(header_frame,
                text="TRYB INŻYNIERYJNY",
                font=('Arial', 16, 'bold'),
                bg=self.COLORS['bg_main'],
                fg=self.COLORS['text_primary']).pack()

        tk.Label(header_frame,
                text="Zaawansowane ustawienia i diagnostyka",
                font=('Arial', 8),
                bg=self.COLORS['bg_main'],
                fg=self.COLORS['text_secondary']).pack(pady=(3, 0))

        tk.Frame(eng_window, bg=self.COLORS['border'], height=2).pack(fill=tk.X, pady=8)

        notebook = ttk.Notebook(eng_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        config_tab = tk.Frame(notebook, bg=self.COLORS['bg_main'], padx=10, pady=10)
        notebook.add(config_tab, text="Konfiguracja")

        tk.Label(config_tab,
                text="Plik konfiguracyjny (audio_tool_config.json):",
                font=('Arial', 9, 'bold'),
                bg=self.COLORS['bg_main'],
                fg=self.COLORS['text_primary']).pack(anchor=tk.W, pady=(0, 5))

        self.config_text = scrolledtext.ScrolledText(config_tab,
                                                     wrap=tk.WORD,
                                                     width=75,
                                                     height=18,
                                                     font=('Courier', 8),
                                                     bg=self.COLORS['bg_card'],
                                                     fg=self.COLORS['text_primary'],
                                                     insertbackground=self.COLORS['text_primary'],
                                                     bd=2,
                                                     relief=tk.SOLID)
        self.config_text.pack(fill=tk.BOTH, expand=True, pady=5)

        self.load_config_to_editor()

        config_btn_frame = tk.Frame(config_tab, bg=self.COLORS['bg_main'])
        config_btn_frame.pack(fill=tk.X, pady=8)

        for text, cmd in [("ZAPISZ", self.save_config_from_editor),
                         ("PRZEŁADUJ", self.load_config_to_editor),
                         ("RESETUJ", self.reset_config_with_confirmation)]:
            tk.Button(config_btn_frame,
                     text=text,
                     command=cmd,
                     bg=self.COLORS['button_bg'],
                     fg=self.COLORS['button_fg'],
                     activebackground=self.COLORS['button_hover'],
                     activeforeground=self.COLORS['button_hover_fg'],
                     bd=2,
                     relief=tk.SOLID,
                     font=('Arial', 8)).pack(side=tk.LEFT, padx=4)

        footer_frame = tk.Frame(eng_window, bg=self.COLORS['bg_main'], padx=15, pady=15)
        footer_frame.pack(fill=tk.X)

        tk.Label(footer_frame,
                text="⚠ Uwaga: Modyfikacja konfiguracji może wpłynąć na stabilność aplikacji",
                font=('Arial', 7),
                bg=self.COLORS['bg_main'],
                fg=self.COLORS['text_secondary']).pack()

        tk.Button(footer_frame,
                 text="ZAMKNIJ",
                 command=lambda: self.close_engineering_mode(eng_window),
                 bg=self.COLORS['button_bg'],
                 fg=self.COLORS['button_fg'],
                 activebackground=self.COLORS['button_hover'],
                 activeforeground=self.COLORS['button_hover_fg'],
                 bd=2,
                 relief=tk.SOLID,
                 font=('Arial', 8, 'bold'),
                 width=18).pack(pady=8)

    def load_config_to_editor(self):
        """Ładuje konfigurację"""
        self.config_text.delete('1.0', tk.END)
        config_json = json.dumps(self.config_mgr.config, indent=4, ensure_ascii=False)
        self.config_text.insert('1.0', config_json)

    def save_config_from_editor(self):
        """Zapisuje konfigurację"""
        try:
            config_text = self.config_text.get('1.0', tk.END)
            new_config = json.loads(config_text)

            required_keys = ['app', 'audio', 'music_player']
            for key in required_keys:
                if key not in new_config:
                    messagebox.showerror("Błąd walidacji", f"Brak wymaganego klucza: '{key}'")
                    return

            self.config_mgr.config = new_config
            self.config_mgr.save_config()
            messagebox.showinfo("Sukces", "Konfiguracja zapisana pomyślnie!")

        except json.JSONDecodeError as e:
            messagebox.showerror("Błąd JSON", f"Nieprawidłowy format JSON:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zapisać konfiguracji:\n{str(e)}")

    def reset_config_with_confirmation(self):
        """Reset konfiguracji"""
        response = messagebox.askyesno(
            "Potwierdzenie",
            "Zresetować konfigurację do wartości domyślnych?\n\nTa operacja jest nieodwracalna!"
        )

        if response:
            self.config_mgr.reset_to_defaults()
            self.load_config_to_editor()
            messagebox.showinfo("Reset", "Konfiguracja zresetowana do domyślnych wartości")

    def close_engineering_mode(self, window):
        """Zamyka tryb inżynieryjny"""
        self.engineering_mode_active = False
        window.destroy()

    def create_main_menu(self):
        """Menu główne - kompaktowe"""
        main_frame = tk.Frame(self.root, bg=self.COLORS['bg_main'], padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        logo_frame = tk.Frame(main_frame, bg=self.COLORS['bg_main'])
        logo_frame.pack(pady=(0, 15))

        if os.path.exists("logo.png"):
            try:
                original_image = tk.PhotoImage(file="logo.png")
                scale = max(1, original_image.width() // 100)
                self.logo_image = original_image.subsample(scale, scale)
                tk.Label(logo_frame, image=self.logo_image, bg=self.COLORS['bg_main']).pack()
            except:
                tk.Label(logo_frame, text="♪", font=('Arial', 28),
                        bg=self.COLORS['bg_main'], fg=self.COLORS['text_primary']).pack()
        else:
            tk.Label(logo_frame, text="♪", font=('Arial', 28),
                    bg=self.COLORS['bg_main'], fg=self.COLORS['text_primary']).pack()

        tk.Label(main_frame,
                text="TESTOWANIE AUDIO",
                font=('Arial', 20, 'bold'),
                bg=self.COLORS['bg_main'],
                fg=self.COLORS['text_primary']).pack()

        tk.Label(main_frame,
                text="MULTI-TOOL",
                font=('Arial', 20, 'bold'),
                bg=self.COLORS['bg_main'],
                fg=self.COLORS['text_primary']).pack(pady=(0, 3))

        tk.Label(main_frame,
                text="Wybierz test do uruchomienia",
                font=('Arial', 8),
                bg=self.COLORS['bg_main'],
                fg=self.COLORS['text_secondary']).pack(pady=(0, 15))

        tk.Frame(main_frame, bg=self.COLORS['border'], height=2).pack(fill=tk.X, pady=(0, 20))

        button_frame = tk.Frame(main_frame, bg=self.COLORS['bg_main'])
        button_frame.pack(pady=8)

        tests = [
            ("TEST 1", "Odtwarzacz Muzyki + EQ", self.open_music_player_test, 'normal'),
            ("TEST 2", "Generator Częstotliwości", self.open_tone_generator_test, 'normal'),
            ("TEST 3", "Test Stereo", self.show_under_construction, 'disabled'),
            ("TEST 4", "Przejazd Częstotliwości", self.show_under_construction, 'disabled'),
            ("TEST 5", "Szum Różowy/Biały", self.show_under_construction, 'disabled')
        ]

        for i, (title, subtitle, cmd, state) in enumerate(tests):
            btn_container = tk.Frame(button_frame, bg=self.COLORS['bg_main'])
            btn_container.pack(pady=5)

            btn = tk.Button(
                btn_container,
                text=f"{title}\n{subtitle}",
                font=('Arial', 9, 'bold'),
                bg=self.COLORS['button_bg'] if state == 'normal' else self.COLORS['bg_card'],
                fg=self.COLORS['button_fg'] if state == 'normal' else self.COLORS['text_secondary'],
                activebackground=self.COLORS['button_hover'],
                activeforeground=self.COLORS['button_hover_fg'],
                bd=2,
                relief=tk.SOLID,
                width=30,
                height=2,
                command=cmd,
                state=state
            )
            btn.pack()

        tk.Frame(main_frame, bg=self.COLORS['border'], height=2).pack(fill=tk.X, pady=20)

        tk.Button(main_frame,
                 text="WYJDŹ Z APLIKACJI",
                 command=self.exit_app,
                 bg=self.COLORS['bg_main'],
                 fg=self.COLORS['text_secondary'],
                 activebackground=self.COLORS['button_hover'],
                 activeforeground=self.COLORS['button_hover_fg'],
                 bd=2,
                 relief=tk.SOLID,
                 font=('Arial', 8),
                 width=22).pack(pady=8)

        footer_frame = tk.Frame(main_frame, bg=self.COLORS['bg_main'])
        footer_frame.pack(side=tk.BOTTOM, pady=(10, 0))

        tk.Label(footer_frame,
                text="Kacper Urbanowicz | Rafał Kobylecki",
                font=('Arial', 7),
                bg=self.COLORS['bg_main'],
                fg=self.COLORS['text_secondary']).pack()

        version = self.config_mgr.get('app.version', '1.0.0')
        tk.Label(footer_frame,
                text=f"v{version} | Tryb inżynieryjny: Ctrl+Shift+DDD",
                font=('Arial', 6),
                bg=self.COLORS['bg_main'],
                fg=self.COLORS['text_secondary']).pack()

    def open_music_player_test(self):
        """Otwiera Test 1"""
        if self.current_test_window is not None:
            try:
                self.resource_mgr.unregister_window(self.current_test_window)
                self.current_test_window.destroy()
            except:
                pass

        geometry = self.config_mgr.get('app.window_geometry.music_player', '650x580')

        try:
            test_window = tk.Toplevel(self.root)
            test_window.title("Test 1: Odtwarzacz Muzyki")
            test_window.geometry(geometry)
            test_window.configure(bg=self.COLORS['bg_main'])

            from music_player_test import MusicPlayerTest
            test = MusicPlayerTest(test_window)

            self.resource_mgr.register_window(test_window, 'music_player')
            self.current_test_window = test_window

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można załadować testu:\n{str(e)}")
            try:
                test_window.destroy()
            except:
                pass

    def open_tone_generator_test(self):
        """Otwiera Test 2"""
        if self.current_test_window is not None:
            try:
                self.resource_mgr.unregister_window(self.current_test_window)
                self.current_test_window.destroy()
            except:
                pass

        geometry = self.config_mgr.get('app.window_geometry.tone_generator', '580x680')

        try:
            test_window = tk.Toplevel(self.root)
            test_window.title("Test 2: Generator Częstotliwości")
            test_window.geometry(geometry)
            test_window.configure(bg=self.COLORS['bg_main'])

            from tone_generator_test import ToneGeneratorTest

            test_frame = tk.Frame(test_window, bg=self.COLORS['bg_main'])
            test_frame.pack(fill=tk.BOTH, expand=True)

            def close_test():
                try:
                    self.resource_mgr.unregister_window(test_window)
                    test_window.destroy()
                    self.current_test_window = None
                except:
                    pass

            test = ToneGeneratorTest(test_frame, close_test)

            self.resource_mgr.register_window(test_window, 'tone_generator')
            self.current_test_window = test_window

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można załadować testu:\n{str(e)}")
            try:
                test_window.destroy()
            except:
                pass

    def show_under_construction(self):
        """Testy w budowie"""
        messagebox.showinfo("W budowie",
                          "Ten test będzie dostępny w przyszłych wersjach.")

    def exit_app(self):
        """Zamyka aplikację"""
        if self.config_mgr.get('ui.confirm_exit', True):
            if not messagebox.askyesno("Wyjście", "Zamknąć aplikację?"):
                return

        try:
            self.config_mgr.reload_config()
            self.config_mgr.set('app.window_geometry.main', self.root.geometry())
            self.config_mgr.save_config()
            self.resource_mgr.shutdown()
            self.root.destroy()
        except Exception as e:
            print(f"Błąd zamykania: {e}")
            self.root.destroy()


if __name__ == "__main__":
    try:
        root = tk.Tk()
        root.configure(bg='#FFFFFF')
        root.title("Audio Testing Multi-Tool - Login")
        root.geometry("500x600")

        # Zmienna do przechowania HRID
        logged_hrid = None


        def on_login_success(hrid):
            """Callback po udanym logowaniu"""
            global logged_hrid
            logged_hrid = hrid

            # Usuń ekran logowania
            for widget in root.winfo_children():
                widget.destroy()

            # Zmień tytuł i rozmiar
            root.title("Narzędzie Testowania Audio")
            root.geometry("480x600")

            # Uruchom główną aplikację
            app = AudioMultiTool(root)
            app.logged_operator = hrid  # Zapisz HRID w aplikacji


        # Pokaż ekran logowania
        login = LoginScreen(root, on_login_success)

        root.mainloop()
    except KeyboardInterrupt:
        print("\nAplikacja przerwana (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        try:
            messagebox.showerror("Błąd krytyczny", str(e))
        except:
            print(f"BŁĄD: {e}")
        sys.exit(1)

