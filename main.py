"""
Audio Testing Multi-Tool
Menu główne z zarządzaniem zasobami i centralną konfiguracją
Wersja: 1.0.0
Autorzy: Kacper Urbanowicz, Rafał Kobylecki
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
import os
import json

# Import menedżerów
from resource_manager import get_resource_manager
from config_manager import get_config_manager


class AudioMultiTool:
    """Główna klasa aplikacji z menu wyboru testów"""

    def __init__(self, root):
        self.root = root

        # === MENEDŻERY ===
        self.resource_mgr = get_resource_manager()
        self.config_mgr = get_config_manager()

        # Załaduj geometrię okna z konfiguracji
        window_geometry = self.config_mgr.get('app.window_geometry.main', '550x600')
        self.root.title("Audio Testing Multi-Tool")
        self.root.geometry(window_geometry)

        # === TRYB INŻYNIERYJNY ===
        self.engineering_mode_active = False
        self.key_sequence = []  # Lista wciśniętych klawiszy dla sekwencji Ctrl+Shift+DDD
        self.last_key_time = 0

        # Bind do wykrywania sekwencji klawiszy
        self.root.bind('<KeyPress>', self.check_engineering_mode_sequence)

        # Inicjalizacja pygame przez ResourceManager
        audio_config = self.config_mgr.get_audio_config()
        success = self.resource_mgr.init_pygame(
            frequency=audio_config.get('sample_rate', 44100),
            size=-16,
            channels=audio_config.get('channels', 2),
            buffer=audio_config.get('buffer_size', 512)
        )

        if not success:
            messagebox.showerror(
                "Błąd krytyczny",
                "Nie można zainicjować systemu audio!\n\n"
                "Sprawdź czy:\n"
                "• Masz działającą kartę dźwiękową\n"
                "• Sterowniki audio są zainstalowane\n"
                "• Żadna inna aplikacja nie blokuje audio"
            )
            sys.exit(1)

        # Aktualnie otwarte okno testu
        self.current_test_window = None

        # Ustawienie funkcji zamykania
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        # Stwórz menu
        self.create_main_menu()

        # Oznacz że nie jest to pierwszy start (BEZ wiadomości powitalnej)
        if self.config_mgr.get('app.first_run', True):
            self.config_mgr.set('app.first_run', False)
            self.config_mgr.save_config()

    def check_engineering_mode_sequence(self, event):
        """
        Wykrywa sekwencję Ctrl+Shift+D+D+D dla trybu inżynieryjnego.
        Wzorowane na PSU-19.
        """
        import time

        current_time = time.time()

        # Reset sekwencji jeśli minęło więcej niż 2 sekundy od ostatniego klawisza
        if current_time - self.last_key_time > 2.0:
            self.key_sequence = []

        self.last_key_time = current_time

        # Sprawdź czy Ctrl i Shift są wciśnięte + klawisz D
        if event.state & 0x0004 and event.state & 0x0001:  # Ctrl + Shift
            if event.keysym.lower() == 'd':
                self.key_sequence.append('d')

                # Trzy razy "D" = otwórz tryb inżynieryjny
                if len(self.key_sequence) >= 3:
                    self.open_engineering_mode()
                    self.key_sequence = []

    def open_engineering_mode(self):
        """Otwiera okno trybu inżynieryjnego z dostępem do konfiguracji"""

        if self.engineering_mode_active:
            return

        self.engineering_mode_active = True

        # Nowe okno
        eng_window = tk.Toplevel(self.root)
        eng_window.title("🔧 Tryb Inżynieryjny")
        eng_window.geometry("800x600")
        eng_window.protocol("WM_DELETE_WINDOW", lambda: self.close_engineering_mode(eng_window))

        # === NAGŁÓWEK ===
        header_frame = ttk.Frame(eng_window, padding="10")
        header_frame.pack(fill=tk.X)

        ttk.Label(header_frame,
                 text="🔧 Tryb Inżynieryjny",
                 font=('Arial', 16, 'bold')).pack()

        ttk.Label(header_frame,
                 text="Zaawansowane ustawienia i diagnostyka",
                 font=('Arial', 9),
                 foreground='gray').pack()

        ttk.Separator(eng_window, orient='horizontal').pack(fill=tk.X, pady=10)

        # === NOTEBOOK (ZAKŁADKI) ===
        notebook = ttk.Notebook(eng_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # ZAKŁADKA 1: Konfiguracja
        config_tab = ttk.Frame(notebook, padding="10")
        notebook.add(config_tab, text="📋 Konfiguracja")

        # Edytor JSON
        ttk.Label(config_tab, text="Plik konfiguracyjny (audio_tool_config.json):",
                 font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))

        self.config_text = scrolledtext.ScrolledText(config_tab,
                                                     wrap=tk.WORD,
                                                     width=80,
                                                     height=20,
                                                     font=('Courier', 9))
        self.config_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # Załaduj aktualną konfigurację
        self.load_config_to_editor()

        # Przyciski konfiguracji
        config_btn_frame = ttk.Frame(config_tab)
        config_btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(config_btn_frame, text="💾 Zapisz zmiany",
                  command=self.save_config_from_editor).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_btn_frame, text="🔄 Przeładuj",
                  command=self.load_config_to_editor).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_btn_frame, text="⚠️ Reset do domyślnych",
                  command=self.reset_config_with_confirmation).pack(side=tk.LEFT, padx=5)

        # ZAKŁADKA 2: Status zasobów
        resources_tab = ttk.Frame(notebook, padding="10")
        notebook.add(resources_tab, text="📊 Zasoby")

        ttk.Label(resources_tab, text="Status menedżera zasobów:",
                 font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))

        self.resources_text = scrolledtext.ScrolledText(resources_tab,
                                                        wrap=tk.WORD,
                                                        width=80,
                                                        height=15,
                                                        font=('Courier', 9),
                                                        state='disabled')
        self.resources_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # Przyciski zasobów
        res_btn_frame = ttk.Frame(resources_tab)
        res_btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(res_btn_frame, text="🔄 Odśwież status",
                  command=self.update_resources_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(res_btn_frame, text="🧹 Wymuś Garbage Collection",
                  command=self.force_gc).pack(side=tk.LEFT, padx=5)
        ttk.Button(res_btn_frame, text="🔇 Zatrzymaj wszystkie dźwięki",
                  command=self.stop_all_sounds).pack(side=tk.LEFT, padx=5)

        # Załaduj status zasobów
        self.update_resources_status()

        # ZAKŁADKA 3: Logi
        logs_tab = ttk.Frame(notebook, padding="10")
        notebook.add(logs_tab, text="📝 Logi")

        ttk.Label(logs_tab, text="Logi aplikacji:",
                 font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 10))

        self.logs_text = scrolledtext.ScrolledText(logs_tab,
                                                   wrap=tk.WORD,
                                                   width=80,
                                                   height=20,
                                                   font=('Courier', 9),
                                                   state='disabled')
        self.logs_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # Dodaj przykładowe logi
        self.update_logs()

        # === STOPKA ===
        footer_frame = ttk.Frame(eng_window, padding="10")
        footer_frame.pack(fill=tk.X)

        ttk.Label(footer_frame,
                 text="⚠️ Uwaga: Modyfikacja konfiguracji może wpłynąć na stabilność aplikacji",
                 font=('Arial', 8),
                 foreground='red').pack()

        ttk.Button(footer_frame, text="✖ Zamknij tryb inżynieryjny",
                  command=lambda: self.close_engineering_mode(eng_window),
                  width=30).pack(pady=10)

    def load_config_to_editor(self):
        """Ładuje konfigurację do edytora JSON"""
        self.config_text.delete('1.0', tk.END)
        config_json = json.dumps(self.config_mgr.config, indent=4, ensure_ascii=False)
        self.config_text.insert('1.0', config_json)

    def save_config_from_editor(self):
        """Zapisuje konfigurację z edytora"""
        try:
            # Pobierz tekst z edytora
            config_text = self.config_text.get('1.0', tk.END)

            # Parsuj JSON
            new_config = json.loads(config_text)

            # Walidacja - sprawdź czy ma podstawowe klucze
            required_keys = ['app', 'audio', 'music_player']
            for key in required_keys:
                if key not in new_config:
                    messagebox.showerror("Błąd walidacji",
                                       f"Brak wymaganego klucza: '{key}'")
                    return

            # Zapisz nową konfigurację
            self.config_mgr.config = new_config
            self.config_mgr.save_config()

            messagebox.showinfo("Sukces", "Konfiguracja zapisana pomyślnie!")

        except json.JSONDecodeError as e:
            messagebox.showerror("Błąd JSON",
                               f"Nieprawidłowy format JSON:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Błąd",
                               f"Nie można zapisać konfiguracji:\n{str(e)}")

    def reset_config_with_confirmation(self):
        """Resetuje konfigurację po potwierdzeniu"""
        response = messagebox.askyesno(
            "Potwierdzenie resetu",
            "Czy na pewno chcesz zresetować całą konfigurację do wartości domyślnych?\n\n"
            "Ta operacja jest nieodwracalna!"
        )

        if response:
            self.config_mgr.reset_to_defaults()
            self.load_config_to_editor()
            messagebox.showinfo("Reset", "Konfiguracja zresetowana do domyślnych wartości")

    def update_resources_status(self):
        """Aktualizuje status zasobów w zakładce"""
        self.resources_text.config(state='normal')
        self.resources_text.delete('1.0', tk.END)

        # Pobierz status
        status = self.resource_mgr.get_status()

        # Formatuj output
        output = "=" * 60 + "\n"
        output += "STATUS MENEDŻERA ZASOBÓW\n"
        output += "=" * 60 + "\n\n"

        output += f"Pygame zainicjowany:     {'✓ TAK' if status['pygame_initialized'] else '✗ NIE'}\n"
        output += f"Otwarte okna testów:     {status['open_windows']}\n"
        output += f"Pliki w cache:           {status['cached_files']}\n"
        output += f"Aktywne dźwięki:         {status['active_sounds']}\n\n"

        output += "=" * 60 + "\n"
        output += "LISTA OTWARTYCH OKIEN\n"
        output += "=" * 60 + "\n\n"

        if self.resource_mgr.open_windows:
            for i, win_info in enumerate(self.resource_mgr.open_windows, 1):
                output += f"{i}. {win_info['name']}\n"
        else:
            output += "Brak otwartych okien testowych\n"

        output += "\n" + "=" * 60 + "\n"

        self.resources_text.insert('1.0', output)
        self.resources_text.config(state='disabled')

    def force_gc(self):
        """Wymusza garbage collection"""
        collected = self.resource_mgr.force_garbage_collection()
        messagebox.showinfo("Garbage Collection",
                          f"Wyczyszczono {collected} obiektów z pamięci")
        self.update_resources_status()

    def stop_all_sounds(self):
        """Zatrzymuje wszystkie dźwięki"""
        self.resource_mgr.stop_all_sounds()
        messagebox.showinfo("Stop", "Zatrzymano wszystkie dźwięki")

    def update_logs(self):
        """Aktualizuje zakładkę z logami"""
        self.logs_text.config(state='normal')
        self.logs_text.delete('1.0', tk.END)

        logs = "=" * 60 + "\n"
        logs += "LOGI APLIKACJI\n"
        logs += "=" * 60 + "\n\n"
        logs += "[INFO] Aplikacja uruchomiona pomyślnie\n"
        logs += "[INFO] Pygame zainicjowany: 44100Hz, 2 kanały\n"
        logs += "[INFO] Konfiguracja załadowana\n"
        logs += "[INFO] Tryb inżynieryjny aktywowany (Ctrl+Shift+DDD)\n\n"
        logs += "Pełne logowanie będzie dostępne w przyszłych wersjach.\n"

        self.logs_text.insert('1.0', logs)
        self.logs_text.config(state='disabled')

    def close_engineering_mode(self, window):
        """Zamyka tryb inżynieryjny"""
        self.engineering_mode_active = False
        window.destroy()

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

        # Test 1: Odtwarzacz - AKTYWNY
        btn1 = ttk.Button(button_frame,
                          text="🎵 Test 1: Odtwarzacz Muzyki",
                          style='Big.TButton',
                          command=self.open_music_player_test,
                          width=42)
        btn1.grid(row=0, column=0, pady=6, padx=15)

        # Test 2-5: WYŁĄCZONE
        for i, (emoji, name) in enumerate([
            ("🔊", "Generator Tonów"),
            ("🎧", "Test Stereo"),
            ("📊", "Frequency Sweep"),
            ("📢", "Pink/White Noise")
        ], start=2):
            btn = ttk.Button(button_frame,
                            text=f"{emoji} Test {i}: {name} (w budowie)",
                            style='Big.TButton',
                            command=self.show_under_construction,
                            width=42,
                            state='disabled')
            btn.grid(row=i-1, column=0, pady=6, padx=15)

        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=3, column=0,
                                                            sticky=(tk.W, tk.E), pady=15)

        # Przycisk wyjścia
        exit_btn = ttk.Button(main_frame,
                              text="✖ Wyjdź z aplikacji",
                              command=self.exit_app,
                              width=22)
        exit_btn.grid(row=4, column=0, pady=8)

        # === STOPKA Z LOGO I AUTOREM ===
        footer_frame = ttk.Frame(main_frame)
        footer_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(20, 0))

        # Logo po lewej
        left_footer = ttk.Frame(footer_frame)
        left_footer.pack(side=tk.LEFT, anchor=tk.W)

        logo_loaded = False
        for logo_name in ["logo.png", "Logo.png", "logo.PNG"]:
            if os.path.exists(logo_name):
                try:
                    original_image = tk.PhotoImage(file=logo_name)
                    orig_width = original_image.width()
                    orig_height = original_image.height()

                    if orig_width > 0 and orig_height > 0:
                        scale = min(max(1, orig_width // 100), max(1, orig_height // 50))
                        self.logo_image = original_image.subsample(scale, scale) if scale > 1 else original_image
                        ttk.Label(left_footer, image=self.logo_image).pack(side=tk.LEFT, padx=3)
                        logo_loaded = True
                        break
                except:
                    continue

        if not logo_loaded:
            ttk.Label(left_footer, text="🎧", font=('Arial', 12)).pack(side=tk.LEFT, padx=3)

        # Autorzy po prawej
        right_footer = ttk.Frame(footer_frame)
        right_footer.pack(side=tk.RIGHT, anchor=tk.E)
        ttk.Label(right_footer,
                 text="Autor: Kacper Urbanowicz | Rafał Kobylecki",
                 font=('Arial', 8),
                 foreground='gray').pack(side=tk.RIGHT, padx=3)

        # === STATUS BAR ===
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

        version = self.config_mgr.get('app.version', '1.0.0')
        self.status_bar = ttk.Label(status_frame,
                                    text=f"Gotowy | v{version} | Tryb inżynieryjny: Ctrl+Shift+DDD",
                                    font=('Arial', 8),
                                    foreground='gray')
        self.status_bar.pack(side=tk.LEFT)

        # Konfiguracja rozciągania
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

    def open_music_player_test(self):
        """Otwiera Test 1 - Odtwarzacz"""

        if self.current_test_window is not None:
            try:
                self.resource_mgr.unregister_window(self.current_test_window)
                self.current_test_window.destroy()
            except:
                pass

        geometry = self.config_mgr.get('app.window_geometry.music_player', '700x600')

        try:
            test_window = tk.Toplevel(self.root)
            test_window.title("Test 1: Odtwarzacz Muzyki")
            test_window.geometry(geometry)

            from music_player_test import MusicPlayerTest
            test = MusicPlayerTest(test_window)

            self.resource_mgr.register_window(test_window, 'music_player')
            self.current_test_window = test_window
            self.status_bar.config(text="Test 1: Odtwarzacz - Uruchomiony")

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można załadować testu:\n{str(e)}")
            try:
                test_window.destroy()
            except:
                pass

    def show_under_construction(self):
        """Informacja o testach w budowie"""
        messagebox.showinfo("W budowie",
                          "Ten test będzie dostępny w kolejnych wersjach.")

    def exit_app(self):
        """Zamyka aplikację"""
        if self.config_mgr.get('ui.confirm_exit', True):
            if not messagebox.askyesno("Wyjście", "Zamknąć aplikację?"):
                return

        try:
            self.config_mgr.set('app.window_geometry.main', self.root.geometry())
            self.config_mgr.save_config()
            self.resource_mgr.shutdown()
            self.root.destroy()
        except:
            self.root.destroy()


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = AudioMultiTool(root)
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
