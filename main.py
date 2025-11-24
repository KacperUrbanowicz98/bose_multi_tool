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
from stereo_test import StereoTest



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

    def __init__(self, root, logged_operator="UNKNOWN"):
        self.root = root
        self.root.configure(bg=self.COLORS['bg_main'])

        self.resource_mgr = get_resource_manager()
        self.config_mgr = get_config_manager()

        self.logged_operator = logged_operator

        window_geometry = '550x700'
        self.root.title("Narzędzie Testowania Audio")
        self.root.geometry(window_geometry)
        self.root.resizable(True, True)
        self.root.minsize(480, 550)

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
        """Tryb inżynieryjny z weryfikacją hasłem"""
        if self.engineering_mode_active:
            return

        stored_password = self.config_mgr.get('security.engineering_password', 'bose2024')

        password_window = tk.Toplevel(self.root)
        password_window.title("Tryb Inżynieryjny - Weryfikacja")
        password_window.geometry("400x200")
        password_window.configure(bg=self.COLORS['bg_main'])
        password_window.resizable(False, False)
        password_window.grab_set()

        password_window.transient(self.root)
        password_window.update_idletasks()
        x = (password_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (password_window.winfo_screenheight() // 2) - (200 // 2)
        password_window.geometry(f"+{x}+{y}")

        tk.Label(password_window,
                text="TRYB INŻYNIERYJNY",
                font=('Arial', 14, 'bold'),
                bg=self.COLORS['bg_main'],
                fg=self.COLORS['text_primary']).pack(pady=(20, 5))

        tk.Label(password_window,
                text="Wprowadź hasło dostępu",
                font=('Arial', 9),
                bg=self.COLORS['bg_main'],
                fg=self.COLORS['text_secondary']).pack(pady=(0, 15))

        password_entry = tk.Entry(
            password_window,
            font=('Arial', 12),
            width=20,
            show='●',
            bg=self.COLORS['bg_card'],
            fg=self.COLORS['text_primary'],
            insertbackground=self.COLORS['text_primary'],
            bd=2,
            relief=tk.SOLID,
            justify='center'
        )
        password_entry.pack(pady=10)
        password_entry.focus()

        status_label = tk.Label(
            password_window,
            text="",
            font=('Arial', 8),
            bg=self.COLORS['bg_main'],
            fg='red'
        )
        status_label.pack(pady=5)

        def verify_password():
            entered = password_entry.get()
            if entered == stored_password:
                password_window.destroy()
                self.launch_engineering_mode()
            else:
                status_label.config(text="✗ Nieprawidłowe hasło", fg='red')
                password_entry.delete(0, tk.END)
                password_entry.focus()

        password_entry.bind('<Return>', lambda e: verify_password())

        tk.Button(password_window,
                 text="ZALOGUJ",
                 command=verify_password,
                 bg=self.COLORS['button_bg'],
                 fg=self.COLORS['button_fg'],
                 activebackground=self.COLORS['button_hover'],
                 activeforeground=self.COLORS['button_hover_fg'],
                 bd=2,
                 relief=tk.SOLID,
                 font=('Arial', 9),
                 width=15).pack(pady=10)

    def launch_engineering_mode(self):
        """Uruchamia tryb inżynieryjny po weryfikacji"""
        self.engineering_mode_active = True

        eng_window = tk.Toplevel(self.root)
        eng_window.title("Tryb Inżynieryjny")
        eng_window.geometry("800x600")
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

        # === ZAKŁADKA 1: OPERATORZY ===
        operators_tab = tk.Frame(notebook, bg=self.COLORS['bg_main'], padx=15, pady=15)
        notebook.add(operators_tab, text="Operatorzy (HRID)")

        tk.Label(operators_tab,
                text="Zarządzanie operatorami:",
                font=('Arial', 10, 'bold'),
                bg=self.COLORS['bg_main'],
                fg=self.COLORS['text_primary']).pack(anchor=tk.W, pady=(0, 10))

        list_frame = tk.Frame(operators_tab, bg=self.COLORS['bg_main'])
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.operators_listbox = tk.Listbox(
            list_frame,
            font=('Arial', 10),
            bg=self.COLORS['bg_card'],
            fg=self.COLORS['text_primary'],
            selectbackground=self.COLORS['text_primary'],
            selectforeground=self.COLORS['bg_main'],
            bd=2,
            relief=tk.SOLID,
            yscrollcommand=scrollbar.set,
            height=15
        )
        self.operators_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.operators_listbox.yview)

        self.refresh_operators_list()

        btn_frame = tk.Frame(operators_tab, bg=self.COLORS['bg_main'])
        btn_frame.pack(fill=tk.X, pady=10)

        tk.Button(btn_frame,
                 text="+ DODAJ HRID",
                 command=self.add_operator,
                 bg=self.COLORS['button_bg'],
                 fg=self.COLORS['button_fg'],
                 activebackground=self.COLORS['button_hover'],
                 activeforeground=self.COLORS['button_hover_fg'],
                 bd=2,
                 relief=tk.SOLID,
                 font=('Arial', 8),
                 width=15).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame,
                 text="✖ USUŃ",
                 command=self.remove_operator,
                 bg=self.COLORS['button_bg'],
                 fg=self.COLORS['button_fg'],
                 activebackground=self.COLORS['button_hover'],
                 activeforeground=self.COLORS['button_hover_fg'],
                 bd=2,
                 relief=tk.SOLID,
                 font=('Arial', 8),
                 width=15).pack(side=tk.LEFT, padx=5)

        # === ZAKŁADKA 2: USTAWIENIA AUDIO ===
        audio_tab = tk.Frame(notebook, bg=self.COLORS['bg_main'], padx=15, pady=15)
        notebook.add(audio_tab, text="Ustawienia Audio")

        tk.Label(audio_tab,
                text="Parametry systemu audio:",
                font=('Arial', 10, 'bold'),
                bg=self.COLORS['bg_main'],
                fg=self.COLORS['text_primary']).pack(anchor=tk.W, pady=(0, 15))

        sr_frame = tk.Frame(audio_tab, bg=self.COLORS['bg_main'])
        sr_frame.pack(fill=tk.X, pady=5)

        tk.Label(sr_frame,
                text="Sample Rate (Hz):",
                font=('Arial', 9),
                bg=self.COLORS['bg_main'],
                fg=self.COLORS['text_primary'],
                width=20,
                anchor='w').pack(side=tk.LEFT)

        self.sample_rate_var = tk.StringVar(value=str(self.config_mgr.get('audio.sample_rate', 44100)))
        sample_rate_combo = ttk.Combobox(sr_frame, textvariable=self.sample_rate_var,
                                         values=['22050', '44100', '48000', '96000'],
                                         width=15, state='readonly')
        sample_rate_combo.pack(side=tk.LEFT, padx=10)

        ch_frame = tk.Frame(audio_tab, bg=self.COLORS['bg_main'])
        ch_frame.pack(fill=tk.X, pady=5)

        tk.Label(ch_frame,
                text="Kanały:",
                font=('Arial', 9),
                bg=self.COLORS['bg_main'],
                fg=self.COLORS['text_primary'],
                width=20,
                anchor='w').pack(side=tk.LEFT)

        self.channels_var = tk.StringVar(value=str(self.config_mgr.get('audio.channels', 2)))
        channels_combo = ttk.Combobox(ch_frame, textvariable=self.channels_var,
                                      values=['1', '2'],
                                      width=15, state='readonly')
        channels_combo.pack(side=tk.LEFT, padx=10)

        buf_frame = tk.Frame(audio_tab, bg=self.COLORS['bg_main'])
        buf_frame.pack(fill=tk.X, pady=5)

        tk.Label(buf_frame,
                text="Buffer Size:",
                font=('Arial', 9),
                bg=self.COLORS['bg_main'],
                fg=self.COLORS['text_primary'],
                width=20,
                anchor='w').pack(side=tk.LEFT)

        self.buffer_var = tk.StringVar(value=str(self.config_mgr.get('audio.buffer_size', 512)))
        buffer_combo = ttk.Combobox(buf_frame, textvariable=self.buffer_var,
                                    values=['256', '512', '1024', '2048'],
                                    width=15, state='readonly')
        buffer_combo.pack(side=tk.LEFT, padx=10)

        tk.Button(audio_tab,
                 text="ZAPISZ USTAWIENIA AUDIO",
                 command=self.save_audio_settings,
                 bg=self.COLORS['button_bg'],
                 fg=self.COLORS['button_fg'],
                 activebackground=self.COLORS['button_hover'],
                 activeforeground=self.COLORS['button_hover_fg'],
                 bd=2,
                 relief=tk.SOLID,
                 font=('Arial', 9, 'bold'),
                 width=25).pack(pady=20)

        tk.Label(audio_tab,
                text="⚠ Zmiany wymagają restartu aplikacji",
                font=('Arial', 8),
                bg=self.COLORS['bg_main'],
                fg=self.COLORS['text_secondary']).pack()

        # === ZAKŁADKA 3: USTAWIENIA UI ===
        ui_tab = tk.Frame(notebook, bg=self.COLORS['bg_main'], padx=15, pady=15)
        notebook.add(ui_tab, text="Ustawienia UI")

        tk.Label(ui_tab,
                 text="Ustawienia interfejsu:",
                 font=('Arial', 10, 'bold'),
                 bg=self.COLORS['bg_main'],
                 fg=self.COLORS['text_primary']).pack(anchor=tk.W, pady=(0, 15))

        self.confirm_exit_var = tk.BooleanVar(value=self.config_mgr.get('ui.confirm_exit', True))
        tk.Checkbutton(ui_tab,
                       text="Potwierdzaj wyjście z aplikacji",
                       variable=self.confirm_exit_var,
                       font=('Arial', 9),
                       bg=self.COLORS['bg_main'],
                       fg=self.COLORS['text_primary'],
                       selectcolor=self.COLORS['bg_card'],
                       activebackground=self.COLORS['bg_main'],
                       activeforeground=self.COLORS['text_primary']).pack(anchor=tk.W, pady=5)

        vol_frame = tk.Frame(ui_tab, bg=self.COLORS['bg_main'])
        vol_frame.pack(fill=tk.X, pady=10)

        tk.Label(vol_frame,
                 text="Max głośność (Music Player):",
                 font=('Arial', 9),
                 bg=self.COLORS['bg_main'],
                 fg=self.COLORS['text_primary'],
                 width=30,
                 anchor='w').pack(side=tk.LEFT)

        self.max_volume_var = tk.StringVar(value=str(self.config_mgr.get('music_player.max_volume', 82)))
        max_vol_spin = tk.Spinbox(vol_frame,
                                  from_=1,
                                  to=100,
                                  textvariable=self.max_volume_var,
                                  width=10,
                                  font=('Arial', 9))
        max_vol_spin.pack(side=tk.LEFT, padx=10)

        tk.Label(vol_frame,
                 text="%",
                 font=('Arial', 9),
                 bg=self.COLORS['bg_main'],
                 fg=self.COLORS['text_primary']).pack(side=tk.LEFT)

        tk.Button(ui_tab,
                  text="ZAPISZ USTAWIENIA UI",
                  command=self.save_ui_settings,
                  bg=self.COLORS['button_bg'],
                  fg=self.COLORS['button_fg'],
                  activebackground=self.COLORS['button_hover'],
                  activeforeground=self.COLORS['button_hover_fg'],
                  bd=2,
                  relief=tk.SOLID,
                  font=('Arial', 9, 'bold'),
                  width=25).pack(pady=20)

        # === ZAKŁADKA 4: KONFIGURACJA (RAW JSON) ===
        config_tab = tk.Frame(notebook, bg=self.COLORS['bg_main'], padx=10, pady=10)
        notebook.add(config_tab, text="Konfiguracja (Zaawansowane)")

        tk.Label(config_tab,
                 text="⚠ UWAGA: Edycja dla zaawansowanych użytkowników",
                 font=('Arial', 9, 'bold'),
                 bg=self.COLORS['bg_main'],
                 fg='red').pack(anchor=tk.W, pady=(0, 5))

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
                  width=18).pack()

    def refresh_operators_list(self):
        """Odświeża listę operatorów"""
        self.operators_listbox.delete(0, tk.END)
        operators = self.config_mgr.get('operators.hrid_list', [])
        for op in operators:
            self.operators_listbox.insert(tk.END, op)

    def add_operator(self):
        """Dodaje nowego operatora"""
        add_window = tk.Toplevel(self.root)
        add_window.title("Dodaj operatora")
        add_window.geometry("350x150")
        add_window.configure(bg=self.COLORS['bg_main'])
        add_window.resizable(False, False)
        add_window.grab_set()

        tk.Label(add_window,
                 text="Nowy HRID operatora:",
                 font=('Arial', 9),
                 bg=self.COLORS['bg_main'],
                 fg=self.COLORS['text_primary']).pack(pady=(20, 5))

        hrid_entry = tk.Entry(add_window,
                              font=('Arial', 11),
                              width=20,
                              bg=self.COLORS['bg_card'],
                              fg=self.COLORS['text_primary'],
                              bd=2,
                              relief=tk.SOLID,
                              justify='center')
        hrid_entry.pack(pady=10)
        hrid_entry.focus()

        def save_new_operator():
            new_hrid = hrid_entry.get().strip().upper()
            if not new_hrid:
                messagebox.showwarning("Błąd", "HRID nie może być pusty")
                return

            operators = self.config_mgr.get('operators.hrid_list', [])
            if new_hrid in operators:
                messagebox.showwarning("Błąd", "Ten HRID już istnieje")
                return

            operators.append(new_hrid)
            self.config_mgr.set('operators.hrid_list', operators)
            self.config_mgr.save_config()
            self.refresh_operators_list()
            add_window.destroy()
            messagebox.showinfo("Sukces", f"Dodano operatora: {new_hrid}")

        hrid_entry.bind('<Return>', lambda e: save_new_operator())

        tk.Button(add_window,
                  text="DODAJ",
                  command=save_new_operator,
                  bg=self.COLORS['button_bg'],
                  fg=self.COLORS['button_fg'],
                  activebackground=self.COLORS['button_hover'],
                  activeforeground=self.COLORS['button_hover_fg'],
                  bd=2,
                  relief=tk.SOLID,
                  font=('Arial', 8),
                  width=15).pack(pady=10)

    def remove_operator(self):
        """Usuwa operatora"""
        selection = self.operators_listbox.curselection()
        if not selection:
            messagebox.showwarning("Uwaga", "Wybierz operatora do usunięcia")
            return

        hrid = self.operators_listbox.get(selection[0])

        if not messagebox.askyesno("Potwierdzenie", f"Usunąć operatora:\n{hrid}?"):
            return

        operators = self.config_mgr.get('operators.hrid_list', [])
        if hrid in operators:
            operators.remove(hrid)
            self.config_mgr.set('operators.hrid_list', operators)
            self.config_mgr.save_config()
            self.refresh_operators_list()
            messagebox.showinfo("Sukces", f"Usunięto operatora: {hrid}")

    def save_audio_settings(self):
        """Zapisuje ustawienia audio"""
        try:
            self.config_mgr.set('audio.sample_rate', int(self.sample_rate_var.get()))
            self.config_mgr.set('audio.channels', int(self.channels_var.get()))
            self.config_mgr.set('audio.buffer_size', int(self.buffer_var.get()))
            self.config_mgr.save_config()
            messagebox.showinfo("Sukces", "Ustawienia audio zapisane!\n\nZrestartuj aplikację aby zastosować zmiany.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zapisać ustawień:\n{str(e)}")

    def save_ui_settings(self):
        """Zapisuje ustawienia UI"""
        try:
            self.config_mgr.set('ui.confirm_exit', self.confirm_exit_var.get())
            self.config_mgr.set('music_player.max_volume', int(self.max_volume_var.get()))
            self.config_mgr.save_config()
            messagebox.showinfo("Sukces", "Ustawienia UI zapisane!")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zapisać ustawień:\n{str(e)}")

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

            required_keys = ['app', 'audio', 'music_player', 'operators', 'security']
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

        # === STATUS BAR - ZALOGOWANY OPERATOR ===
        status_bar = tk.Frame(main_frame, bg=self.COLORS['bg_card'], bd=2, relief=tk.SOLID)
        status_bar.pack(fill=tk.X, pady=(0, 15))

        status_left = tk.Frame(status_bar, bg=self.COLORS['bg_card'])
        status_left.pack(side=tk.LEFT, padx=10, pady=8)

        tk.Label(status_left,
                 text="ZALOGOWANO JAKO:",
                 font=('Arial', 7, 'bold'),
                 bg=self.COLORS['bg_card'],
                 fg=self.COLORS['text_secondary']).pack(side=tk.LEFT)

        tk.Label(status_left,
                 text=f"  {self.logged_operator}",
                 font=('Arial', 9, 'bold'),
                 bg=self.COLORS['bg_card'],
                 fg=self.COLORS['text_primary']).pack(side=tk.LEFT, padx=5)

        tk.Button(status_bar,
                  text="WYLOGUJ",
                  command=self.logout,
                  bg=self.COLORS['button_bg'],
                  fg=self.COLORS['button_fg'],
                  activebackground=self.COLORS['button_hover'],
                  activeforeground=self.COLORS['button_hover_fg'],
                  bd=1,
                  relief=tk.SOLID,
                  font=('Arial', 7, 'bold'),
                  width=10).pack(side=tk.RIGHT, padx=10, pady=5)

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
            ('TEST 3', 'Test Stereo', self.open_stereo_test, 'normal'),
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
                 text=f"v{version}",
                 font=('Arial', 6),
                 bg=self.COLORS['bg_main'],
                 fg=self.COLORS['text_secondary']).pack()

    def logout(self):
        """Wylogowanie - powrót do ekranu logowania"""
        if messagebox.askyesno("Wylogowanie", f"Wylogować operatora {self.logged_operator}?"):
            if self.current_test_window is not None:
                try:
                    self.resource_mgr.unregister_window(self.current_test_window)
                    self.current_test_window.destroy()
                except:
                    pass

            for widget in self.root.winfo_children():
                widget.destroy()

            self.logged_operator = None
            self.engineering_mode_active = False

            self.root.title("Audio Testing Multi-Tool - Login")
            self.root.geometry("500x600")

            from login_screen import LoginScreen

            def on_login_success(hrid):
                """Callback po ponownym logowaniu"""
                for widget in self.root.winfo_children():
                    widget.destroy()

                self.logged_operator = hrid

                self.root.title("Narzędzie Testowania Audio")
                self.root.geometry("550x700")
                self.create_main_menu()

            login = LoginScreen(self.root, on_login_success)

    def open_music_player_test(self):
        """Otwiera Test 1"""
        if self.current_test_window is not None:
            try:
                self.resource_mgr.unregister_window(self.current_test_window)
                self.current_test_window.destroy()
            except:
                pass

        geometry = self.config_mgr.get('app.window_geometry.music_player', '650x620')

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

    def open_stereo_test(self):
        """Otwiera Test 3 - Stereo"""
        if self.current_test_window is not None:
            try:
                self.resource_mgr.unregister_window(self.current_test_window)
                self.current_test_window.destroy()
            except:
                pass

        geometry = self.config_mgr.get('app.window_geometry.stereotest', '500x750')

        try:
            test_window = tk.Toplevel(self.root)
            test_window.title("Test 3: Stereo (Lewa/Prawa)")
            test_window.geometry(geometry)
            test_window.configure(bg=self.COLORS['bg_main'])

            test = StereoTest(test_window)

            def close_test():
                try:
                    test.cleanup()
                    self.resource_mgr.unregister_window(test_window)
                    test_window.destroy()
                    self.current_test_window = None
                except:
                    pass

            test_window.protocol("WM_DELETE_WINDOW", close_test)
            self.resource_mgr.register_window(test_window, 'stereotest')
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

        logged_hrid = None


        def on_login_success(hrid):
            """Callback po udanym logowaniu"""
            global logged_hrid
            logged_hrid = hrid

            for widget in root.winfo_children():
                widget.destroy()

            root.title("Narzędzie Testowania Audio")
            root.geometry("550x650")

            app = AudioMultiTool(root, logged_operator=hrid)


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