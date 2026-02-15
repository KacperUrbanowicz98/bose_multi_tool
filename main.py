"""
Audio Testing Multi-Tool
Menu główne - Bose White Theme (wersja polska)
Wersja: 1.0.0
Autorzy: Kacper Urbanowicz, Rafał Kobylecki
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
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
        eng_window.geometry("800x850")
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

        # === ZAKŁADKA 5: TEST 1 AUTO CONFIG ===
        test1_auto_tab = tk.Frame(notebook, bg=self.COLORS['bg_main'], padx=15, pady=15)
        notebook.add(test1_auto_tab, text="TEST 1 AUTO")

        # === DODAJ KOLOROWY PASEK NA GÓRZE ===
        auto_indicator = tk.Frame(test1_auto_tab, bg='#4CAF50', height=5)  # Zielony pasek
        auto_indicator.pack(fill='x', pady=(0, 10))

        tk.Label(test1_auto_tab,
                 text="⚙ Konfiguracja Automatycznego Testu 1",
                 font=('Arial', 12, 'bold'),
                 bg=self.COLORS['bg_main'],
                 fg=self.COLORS['text_primary']).pack(pady=(0, 15))

        # === CZAS TRWANIA KROKU ===
        duration_frame = tk.Frame(test1_auto_tab, bg=self.COLORS['bg_card'], relief=tk.SOLID, bd=1)
        duration_frame.pack(padx=10, pady=10, fill='x')

        tk.Label(duration_frame,
                 text="⏱ Czas trwania jednego kroku (sekundy):",
                 font=('Arial', 9, 'bold'),
                 bg=self.COLORS['bg_card'],
                 fg=self.COLORS['text_primary']).pack(pady=(10, 5), padx=10, anchor='w')

        current_duration = self.config_mgr.get('test1_auto.step_duration', 5)
        print(f"[DEBUG] Wczytano z config: {current_duration}")

        # Stwórz zmienną Tkinter która WYMUSZA wartość
        duration_var = tk.StringVar(value=str(current_duration))

        duration_spinbox = tk.Spinbox(duration_frame,
                                      from_=1,
                                      to=60,
                                      textvariable=duration_var,
                                      width=10,
                                      font=('Arial', 10))

        duration_spinbox.pack(pady=(0, 10), padx=10, anchor='w')

        # === POZIOMY GŁOŚNOŚCI ===
        volume_frame_outer = tk.Frame(test1_auto_tab, bg=self.COLORS['bg_card'], relief=tk.SOLID, bd=1)
        volume_frame_outer.pack(padx=10, pady=10, fill='both', expand=True)

        tk.Label(volume_frame_outer,
                 text="🔊 Poziomy głośności do sprawdzenia:",
                 font=('Arial', 9, 'bold'),
                 bg=self.COLORS['bg_card'],
                 fg=self.COLORS['text_primary']).pack(pady=(10, 5), padx=10, anchor='w')

        volume_content = tk.Frame(volume_frame_outer, bg=self.COLORS['bg_card'])
        volume_content.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # Listbox z poziomami
        current_volumes = self.config_mgr.get('test1_auto.volume_levels', [10, 20, 30, 40, 50, 60, 70, 80])

        list_frame = tk.Frame(volume_content, bg=self.COLORS['bg_card'])
        list_frame.pack(side='left', fill='both', expand=True)

        volumes_listbox = tk.Listbox(list_frame,
                                     height=8,
                                     font=('Arial', 9),
                                     selectmode=tk.SINGLE,
                                     bg='#FFFFFF',
                                     fg=self.COLORS['text_primary'],
                                     bd=1,
                                     relief=tk.SOLID)
        volumes_listbox.pack(side='left', fill='both', expand=True)

        scrollbar = tk.Scrollbar(list_frame, command=volumes_listbox.yview)
        scrollbar.pack(side='left', fill='y')
        volumes_listbox.config(yscrollcommand=scrollbar.set)

        for vol in current_volumes:
            volumes_listbox.insert(tk.END, f"{vol}%")

        # Przyciski do zarządzania
        button_frame = tk.Frame(volume_content, bg=self.COLORS['bg_card'])
        button_frame.pack(side='left', padx=10)

        def add_volume():
            try:
                new_vol = tk.simpledialog.askinteger("Dodaj poziom",
                                                     "Podaj poziom głośności (1-100):",
                                                     minvalue=1,
                                                     maxvalue=100)
                if new_vol:
                    volumes_listbox.insert(tk.END, f"{new_vol}%")
            except:
                pass

        def remove_volume():
            selected = volumes_listbox.curselection()
            if selected:
                volumes_listbox.delete(selected[0])
            else:
                messagebox.showwarning("Brak wyboru", "Wybierz poziom do usunięcia!")

        tk.Button(button_frame,
                  text="➕ Dodaj",
                  command=add_volume,
                  bg=self.COLORS['button_bg'],
                  fg=self.COLORS['button_fg'],
                  activebackground=self.COLORS['button_hover'],
                  activeforeground=self.COLORS['button_hover_fg'],
                  bd=2,
                  relief=tk.SOLID,
                  font=('Arial', 8),
                  width=10).pack(pady=2)

        tk.Button(button_frame,
                  text="➖ Usuń",
                  command=remove_volume,
                  bg=self.COLORS['button_bg'],
                  fg=self.COLORS['button_fg'],
                  activebackground=self.COLORS['button_hover'],
                  activeforeground=self.COLORS['button_hover_fg'],
                  bd=2,
                  relief=tk.SOLID,
                  font=('Arial', 8),
                  width=10).pack(pady=2)

        # === PODGLĄD TESTU ===
        preview_frame = tk.Frame(test1_auto_tab, bg=self.COLORS['bg_card'], relief=tk.SOLID, bd=1)
        preview_frame.pack(padx=10, pady=10, fill='x')

        tk.Label(preview_frame,
                 text="📊 Podgląd testu:",
                 font=('Arial', 9, 'bold'),
                 bg=self.COLORS['bg_card'],
                 fg=self.COLORS['text_primary']).pack(pady=(10, 5), padx=10, anchor='w')

        preview_label = tk.Label(preview_frame,
                                 text="",
                                 font=('Arial', 9),
                                 bg=self.COLORS['bg_card'],
                                 fg=self.COLORS['text_secondary'],
                                 justify='left')
        preview_label.pack(padx=10, pady=(0, 10), anchor='w')

        def update_preview():
            print(f"[DEBUG] update_preview() wywołane!")
            try:
                duration_value = duration_var.get()
                print(f"[DEBUG] Wartość ze zmiennej: '{duration_value}'")
                duration = int(duration_value)
                print(f"[DEBUG] Duration jako int: {duration}")

                num_steps = volumes_listbox.size()
                total_time = duration * num_steps

                preview_text = f"⏱ Liczba kroków: {num_steps}\n"
                preview_text += f"⏱ Czas każdego kroku: {duration} sek\n"
                preview_text += f"⏱ Łączny czas testu: {total_time} sek ({total_time // 60} min {total_time % 60} sek)"
                preview_label.config(text=preview_text)
                print(f"[DEBUG] Podgląd zaktualizowany: {total_time}s")
            except Exception as e:
                print(f"[DEBUG] BŁĄD w update_preview: {e}")
                preview_label.config(text="⚠ Błąd w konfiguracji")

        # === PRZYCISK ZAPISU ===
        def save_test1_config():
            try:
                # Pobierz wartości
                duration = int(duration_var.get())
                print(f"[DEBUG] Zapisuję duration: {duration}")

                if duration < 1 or duration > 60:
                    messagebox.showerror("Błąd", "Czas trwania musi być między 1 a 60 sekund!")
                    return

                volumes = []
                for i in range(volumes_listbox.size()):
                    vol_str = volumes_listbox.get(i).replace('%', '').strip()
                    volumes.append(int(vol_str))

                if not volumes:
                    messagebox.showerror("Błąd", "Lista poziomów nie może być pusta!")
                    return

                # Sortuj poziomy rosnąco
                volumes.sort()

                # Zapisz do konfiguracji
                self.config_mgr.set('test1_auto.step_duration', duration)
                self.config_mgr.set('test1_auto.volume_levels', volumes)
                self.config_mgr.save_config()

                levels_str = ", ".join([f"{v}%" for v in volumes])
                messagebox.showinfo("Zapisano ✓",
                                    f"Konfiguracja TEST 1 AUTO zapisana:\n\n"
                                    f"• Czas kroku: {duration} sek\n"
                                    f"• Poziomy: {levels_str}")
                update_preview()

            except ValueError:
                messagebox.showerror("Błąd", "Nieprawidłowe wartości w konfiguracji!")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można zapisać:\n{str(e)}")

        # Przycisk ZAPISZ
        tk.Button(test1_auto_tab,
                  text="💾 ZAPISZ KONFIGURACJĘ",
                  command=save_test1_config,
                  bg=self.COLORS['button_bg'],
                  fg=self.COLORS['button_fg'],
                  activebackground=self.COLORS['button_hover'],
                  activeforeground=self.COLORS['button_hover_fg'],
                  bd=2,
                  relief=tk.SOLID,
                  font=('Arial', 9, 'bold'),
                  width=30,
                  height=2).pack(pady=15)

        # === ZAKŁADKA 6: TEST 2 AUTO CONFIG ===
        test2_auto_tab = tk.Frame(notebook, bg=self.COLORS['bg_main'], padx=15, pady=15)
        notebook.add(test2_auto_tab, text="TEST 2 AUTO")

        tk.Label(test2_auto_tab,
                 text="⚙ Konfiguracja Automatycznego Testu 2",
                 font=('Arial', 12, 'bold'),
                 bg=self.COLORS['bg_main'],
                 fg=self.COLORS['text_primary']).pack(pady=(0, 15))

        # === TYP FALI ===
        wave_frame = tk.Frame(test2_auto_tab, bg=self.COLORS['bg_card'], relief=tk.SOLID, bd=1)
        wave_frame.pack(padx=10, pady=10, fill='x')

        tk.Label(wave_frame,
                 text="🌊 Typ generowanej fali:",
                 font=('Arial', 9, 'bold'),
                 bg=self.COLORS['bg_card'],
                 fg=self.COLORS['text_primary']).pack(pady=(10, 5), padx=10, anchor='w')

        current_wave = self.config_mgr.get('test2_auto.wave_type', 'sine')

        wave_options = [
            ('Sinusoidalna', 'sine'),
            ('Kwadratowa', 'square'),
            ('Piłokształtna', 'sawtooth'),
            ('Trójkątna', 'triangle')
        ]

        wave_var = tk.StringVar(value=current_wave)

        for label, value in wave_options:
            tk.Radiobutton(wave_frame,
                           text=label,
                           variable=wave_var,
                           value=value,
                           font=('Arial', 9),
                           bg=self.COLORS['bg_card'],
                           fg=self.COLORS['text_primary'],
                           selectcolor=self.COLORS['bg_main'],
                           activebackground=self.COLORS['bg_card'],
                           activeforeground=self.COLORS['text_primary']).pack(anchor='w', padx=30, pady=2)

        # === ZAKRES CZĘSTOTLIWOŚCI ===
        freq_frame = tk.Frame(test2_auto_tab, bg=self.COLORS['bg_card'], relief=tk.SOLID, bd=1)
        freq_frame.pack(padx=10, pady=10, fill='x')

        tk.Label(freq_frame,
                 text="🎚 Zakres częstotliwości (Hz):",
                 font=('Arial', 9, 'bold'),
                 bg=self.COLORS['bg_card'],
                 fg=self.COLORS['text_primary']).pack(pady=(10, 5), padx=10, anchor='w')

        freq_container = tk.Frame(freq_frame, bg=self.COLORS['bg_card'])
        freq_container.pack(padx=10, pady=(0, 10))

        # Od
        tk.Label(freq_container,
                 text="Od:",
                 font=('Arial', 9),
                 bg=self.COLORS['bg_card'],
                 fg=self.COLORS['text_primary']).pack(side='left', padx=(0, 5))

        current_freq_min = self.config_mgr.get('test2_auto.freq_min', 20)
        freq_min_spinbox = tk.Spinbox(freq_container,
                                      from_=20,
                                      to=20000,
                                      width=8,
                                      font=('Arial', 9))
        freq_min_spinbox.delete(0, tk.END)
        freq_min_spinbox.insert(0, str(current_freq_min))
        freq_min_spinbox.pack(side='left', padx=5)

        tk.Label(freq_container,
                 text="Hz    Do:",
                 font=('Arial', 9),
                 bg=self.COLORS['bg_card'],
                 fg=self.COLORS['text_primary']).pack(side='left', padx=5)

        current_freq_max = self.config_mgr.get('test2_auto.freq_max', 20000)
        freq_max_spinbox = tk.Spinbox(freq_container,
                                      from_=20,
                                      to=20000,
                                      width=8,
                                      font=('Arial', 9))
        freq_max_spinbox.delete(0, tk.END)
        freq_max_spinbox.insert(0, str(current_freq_max))
        freq_max_spinbox.pack(side='left', padx=5)

        tk.Label(freq_container,
                 text="Hz",
                 font=('Arial', 9),
                 bg=self.COLORS['bg_card'],
                 fg=self.COLORS['text_primary']).pack(side='left')

        # === CZAS TRWANIA I GŁOŚNOŚĆ ===
        settings_frame = tk.Frame(test2_auto_tab, bg=self.COLORS['bg_card'], relief=tk.SOLID, bd=1)
        settings_frame.pack(padx=10, pady=10, fill='x')

        # Czas trwania
        tk.Label(settings_frame,
                 text="⏱ Czas trwania testu (sekundy):",
                 font=('Arial', 9, 'bold'),
                 bg=self.COLORS['bg_card'],
                 fg=self.COLORS['text_primary']).pack(pady=(10, 5), padx=10, anchor='w')

        current_duration = self.config_mgr.get('test2_auto.duration', 10)
        duration_spinbox = tk.Spinbox(settings_frame,
                                      from_=5,
                                      to=300,
                                      width=10,
                                      font=('Arial', 9))
        duration_spinbox.delete(0, tk.END)
        duration_spinbox.insert(0, str(current_duration))
        duration_spinbox.pack(padx=10, pady=(0, 10), anchor='w')

        # Głośność
        tk.Label(settings_frame,
                 text="🔊 Głośność testu (%):",
                 font=('Arial', 9, 'bold'),
                 bg=self.COLORS['bg_card'],
                 fg=self.COLORS['text_primary']).pack(pady=(5, 5), padx=10, anchor='w')

        current_volume = self.config_mgr.get('test2_auto.volume', 50)
        volume_spinbox = tk.Spinbox(settings_frame,
                                    from_=10,
                                    to=82,
                                    width=10,
                                    font=('Arial', 9))
        volume_spinbox.delete(0, tk.END)
        volume_spinbox.insert(0, str(current_volume))
        volume_spinbox.pack(padx=10, pady=(0, 10), anchor='w')

        # === PODGLĄD ===
        preview_frame2 = tk.Frame(test2_auto_tab, bg=self.COLORS['bg_card'], relief=tk.SOLID, bd=1)
        preview_frame2.pack(padx=10, pady=10, fill='x')

        tk.Label(preview_frame2,
                 text="📊 Podgląd testu:",
                 font=('Arial', 9, 'bold'),
                 bg=self.COLORS['bg_card'],
                 fg=self.COLORS['text_primary']).pack(pady=(10, 5), padx=10, anchor='w')

        preview_label2 = tk.Label(preview_frame2,
                                  text="",
                                  font=('Arial', 9),
                                  bg=self.COLORS['bg_card'],
                                  fg=self.COLORS['text_secondary'],
                                  justify='left')
        preview_label2.pack(padx=10, pady=(0, 10), anchor='w')

        def update_preview2():
            try:
                wave_type_display = {
                    'sine': 'Sinusoidalna',
                    'square': 'Kwadratowa',
                    'sawtooth': 'Piłokształtna',
                    'triangle': 'Trójkątna'
                }

                wave = wave_var.get()
                freq_min = int(freq_min_spinbox.get())
                freq_max = int(freq_max_spinbox.get())
                duration = int(duration_spinbox.get())
                volume = int(volume_spinbox.get())

                preview_text = f"• Typ fali: {wave_type_display.get(wave, wave)}\n"
                preview_text += f"• Zakres: {freq_min} Hz → {freq_max} Hz\n"
                preview_text += f"• Czas trwania: {duration} sek\n"
                preview_text += f"• Głośność: {volume}%"

                preview_label2.config(text=preview_text)
            except:
                preview_label2.config(text="⚠ Błąd w konfiguracji")

        # Odśwież przy zmianie
        for widget in [freq_min_spinbox, freq_max_spinbox, duration_spinbox, volume_spinbox]:
            widget.config(command=lambda: update_preview2())

        for _, _ in wave_options:
            pass  # Radiobuttony automatycznie zaktualizują przezwave_var

        wave_var.trace('w', lambda *args: update_preview2())
        update_preview2()

        # === PRZYCISK ZAPISU ===
        def save_test2_config():
            try:
                wave_type = wave_var.get()
                freq_min = int(freq_min_spinbox.get())
                freq_max = int(freq_max_spinbox.get())
                duration = int(duration_spinbox.get())
                volume = int(volume_spinbox.get())

                # Walidacja
                if freq_min >= freq_max:
                    messagebox.showerror("Błąd", "Częstotliwość początkowa musi być mniejsza niż końcowa!")
                    return

                if freq_min < 20 or freq_max > 20000:
                    messagebox.showerror("Błąd", "Zakres częstotliwości: 20 - 20000 Hz")
                    return

                if duration < 5 or duration > 300:
                    messagebox.showerror("Błąd", "Czas trwania: 5 - 300 sekund")
                    return

                if volume < 10 or volume > 82:
                    messagebox.showerror("Błąd", "Głośność: 10 - 82%")
                    return

                # Zapisz
                self.config_mgr.set('test2_auto.wave_type', wave_type)
                self.config_mgr.set('test2_auto.freq_min', freq_min)
                self.config_mgr.set('test2_auto.freq_max', freq_max)
                self.config_mgr.set('test2_auto.duration', duration)
                self.config_mgr.set('test2_auto.volume', volume)
                self.config_mgr.save_config()

                wave_names = {
                    'sine': 'Sinusoidalna',
                    'square': 'Kwadratowa',
                    'sawtooth': 'Piłokształtna',
                    'triangle': 'Trójkątna'
                }

                messagebox.showinfo("Zapisano ✓",
                                    f"Konfiguracja TEST 2 AUTO zapisana:\n\n"
                                    f"• Fala: {wave_names[wave_type]}\n"
                                    f"• Zakres: {freq_min}-{freq_max} Hz\n"
                                    f"• Czas: {duration} sek\n"
                                    f"• Głośność: {volume}%")
                update_preview2()

            except ValueError:
                messagebox.showerror("Błąd", "Nieprawidłowe wartości!")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można zapisać:\n{str(e)}")

        tk.Button(test2_auto_tab,
                  text="💾 ZAPISZ KONFIGURACJĘ",
                  command=save_test2_config,
                  bg=self.COLORS['button_bg'],
                  fg=self.COLORS['button_fg'],
                  activebackground=self.COLORS['button_hover'],
                  activeforeground=self.COLORS['button_hover_fg'],
                  bd=2,
                  relief=tk.SOLID,
                  font=('Arial', 9, 'bold'),
                  width=30,
                  height=2).pack(pady=15)

        # === ZAKŁADKA 7: TEST 3 AUTO CONFIG ===
        test3_auto_tab = tk.Frame(notebook, bg=self.COLORS['bg_main'], padx=15, pady=15)
        notebook.add(test3_auto_tab, text="TEST 3 AUTO")

        tk.Label(test3_auto_tab,
                 text="⚙ Konfiguracja Automatycznego Testu 3",
                 font=('Arial', 12, 'bold'),
                 bg=self.COLORS['bg_main'],
                 fg=self.COLORS['text_primary']).pack(pady=(0, 15))

        # === CZAS TRWANIA KANAŁU ===
        duration_frame3 = tk.Frame(test3_auto_tab, bg=self.COLORS['bg_card'], relief=tk.SOLID, bd=1)
        duration_frame3.pack(padx=10, pady=10, fill='x')

        tk.Label(duration_frame3,
                 text="⏱ Czas trwania testu każdego kanału (sekundy):",
                 font=('Arial', 9, 'bold'),
                 bg=self.COLORS['bg_card'],
                 fg=self.COLORS['text_primary']).pack(pady=(10, 5), padx=10, anchor='w')

        current_duration3 = self.config_mgr.get('test3_auto.duration_per_channel', 5)
        duration3_spinbox = tk.Spinbox(duration_frame3,
                                       from_=3,
                                       to=60,
                                       width=10,
                                       font=('Arial', 9))
        duration3_spinbox.delete(0, tk.END)
        duration3_spinbox.insert(0, str(current_duration3))
        duration3_spinbox.pack(pady=(0, 10), padx=10, anchor='w')

        # === CZĘSTOTLIWOŚĆ ===
        freq_frame3 = tk.Frame(test3_auto_tab, bg=self.COLORS['bg_card'], relief=tk.SOLID, bd=1)
        freq_frame3.pack(padx=10, pady=10, fill='x')

        tk.Label(freq_frame3,
                 text="🎚 Częstotliwość tonu testowego (Hz):",
                 font=('Arial', 9, 'bold'),
                 bg=self.COLORS['bg_card'],
                 fg=self.COLORS['text_primary']).pack(pady=(10, 5), padx=10, anchor='w')

        current_freq3 = self.config_mgr.get('test3_auto.frequency', 1000)
        freq3_spinbox = tk.Spinbox(freq_frame3,
                                   from_=100,
                                   to=5000,
                                   width=10,
                                   font=('Arial', 9))
        freq3_spinbox.delete(0, tk.END)
        freq3_spinbox.insert(0, str(current_freq3))
        freq3_spinbox.pack(pady=(0, 10), padx=10, anchor='w')

        # === GŁOŚNOŚĆ ===
        volume_frame3 = tk.Frame(test3_auto_tab, bg=self.COLORS['bg_card'], relief=tk.SOLID, bd=1)
        volume_frame3.pack(padx=10, pady=10, fill='x')

        tk.Label(volume_frame3,
                 text="🔊 Głośność testu (%):",
                 font=('Arial', 9, 'bold'),
                 bg=self.COLORS['bg_card'],
                 fg=self.COLORS['text_primary']).pack(pady=(10, 5), padx=10, anchor='w')

        current_volume3 = self.config_mgr.get('test3_auto.volume', 50)
        volume3_spinbox = tk.Spinbox(volume_frame3,
                                     from_=10,
                                     to=100,
                                     width=10,
                                     font=('Arial', 9))
        volume3_spinbox.delete(0, tk.END)
        volume3_spinbox.insert(0, str(current_volume3))
        volume3_spinbox.pack(pady=(0, 10), padx=10, anchor='w')

        # === PODGLĄD ===
        preview_frame3 = tk.Frame(test3_auto_tab, bg=self.COLORS['bg_card'], relief=tk.SOLID, bd=1)
        preview_frame3.pack(padx=10, pady=10, fill='x')

        tk.Label(preview_frame3,
                 text="📊 Podgląd testu:",
                 font=('Arial', 9, 'bold'),
                 bg=self.COLORS['bg_card'],
                 fg=self.COLORS['text_primary']).pack(pady=(10, 5), padx=10, anchor='w')

        preview_label3 = tk.Label(preview_frame3,
                                  text="",
                                  font=('Arial', 9),
                                  bg=self.COLORS['bg_card'],
                                  fg=self.COLORS['text_secondary'],
                                  justify='left')
        preview_label3.pack(padx=10, pady=(0, 10), anchor='w')

        def update_preview3():
            try:
                duration = int(duration3_spinbox.get())
                freq = int(freq3_spinbox.get())
                volume = int(volume3_spinbox.get())

                total_time = duration * 3  # Lewy + Prawy + Oba

                preview_text = f"• Sekwencja: Lewy → Prawy → Oba\n"
                preview_text += f"• Czas każdego: {duration} sek\n"
                preview_text += f"• Łączny czas: {total_time} sek\n"
                preview_text += f"• Częstotliwość: {freq} Hz\n"
                preview_text += f"• Głośność: {volume}%"

                preview_label3.config(text=preview_text)
            except:
                preview_label3.config(text="⚠ Błąd w konfiguracji")

        # Odśwież przy zmianie
        for widget in [duration3_spinbox, freq3_spinbox, volume3_spinbox]:
            widget.config(command=lambda: update_preview3())

        update_preview3()

        # === PRZYCISK ZAPISU ===
        def save_test3_config():
            try:
                duration = int(duration3_spinbox.get())
                freq = int(freq3_spinbox.get())
                volume = int(volume3_spinbox.get())

                # Walidacja
                if duration < 3 or duration > 60:
                    messagebox.showerror("Błąd", "Czas trwania: 3 - 60 sekund")
                    return

                if freq < 100 or freq > 5000:
                    messagebox.showerror("Błąd", "Częstotliwość: 100 - 5000 Hz")
                    return

                if volume < 10 or volume > 100:
                    messagebox.showerror("Błąd", "Głośność: 10 - 100%")
                    return

                # Zapisz
                self.config_mgr.set('test3_auto.duration_per_channel', duration)
                self.config_mgr.set('test3_auto.frequency', freq)
                self.config_mgr.set('test3_auto.volume', volume)
                self.config_mgr.save_config()

                total_time = duration * 3
                messagebox.showinfo("Zapisano ✓",
                                    f"Konfiguracja TEST 3 AUTO zapisana:\n\n"
                                    f"• Czas każdego kanału: {duration} sek\n"
                                    f"• Łączny czas: {total_time} sek\n"
                                    f"• Częstotliwość: {freq} Hz\n"
                                    f"• Głośność: {volume}%")
                update_preview3()

            except ValueError:
                messagebox.showerror("Błąd", "Nieprawidłowe wartości!")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można zapisać:\n{str(e)}")

        tk.Button(test3_auto_tab,
                  text="💾 ZAPISZ KONFIGURACJĘ",
                  command=save_test3_config,
                  bg=self.COLORS['button_bg'],
                  fg=self.COLORS['button_fg'],
                  activebackground=self.COLORS['button_hover'],
                  activeforeground=self.COLORS['button_hover_fg'],
                  bd=2,
                  relief=tk.SOLID,
                  font=('Arial', 9, 'bold'),
                  width=30,
                  height=2).pack(pady=15)

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
        add_window.transient(self.root)  # Okno zawsze nad rodzicem
        add_window.lift()
        add_window.focus_force()
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
                 text="BOSE",
                 font=('Arial', 20, 'bold'),
                 bg=self.COLORS['bg_main'],
                 fg=self.COLORS['text_primary']).pack()

        tk.Label(main_frame,
                 text="AUDIO-MULTI-TOOL",
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
            ("TEST 1", "Test głośności", self.open_music_player_test, 'normal'),
            ("TEST 2", "Generator Częstotliwości", self.open_tone_generator_test, 'normal'),
            ('TEST 3', 'Test Stereo', self.open_stereo_test, 'normal'),
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
                 text="Kacper Urbanowicz",
                 font=('Arial', 8),
                 bg=self.COLORS['bg_main'],
                 fg=self.COLORS['text_secondary']).pack()

        version = self.config_mgr.get('app.version', '1.0.0')
        tk.Label(footer_frame,
                 text=f"v{version}",
                 font=('Arial', 6),
                 bg=self.COLORS['bg_main'],
                 fg=self.COLORS['text_secondary']).pack()

        # Na końcu create_main_menu() dodaj:
        # Okno główne zawsze pod testami
        self.root.attributes('-topmost', False)

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

    def scan_serial_number(self, test_name):
        """
        Wyświetla okno do skanowania numeru seryjnego przed testem

        Args:
            test_name: Nazwa testu (np. "TEST 1", "TEST 2", "TEST 3")

        Returns:
            str lub None: Numer seryjny lub None jeśli anulowano
        """
        scan_window = tk.Toplevel(self.root)
        scan_window.title(f"{test_name} - Skanowanie")
        scan_window.geometry("450x220")
        scan_window.configure(bg=self.COLORS['bg_main'])
        scan_window.resizable(False, False)
        scan_window.attributes('-topmost', True)  # <-- DODAJ TO!
        scan_window.transient(self.root)
        scan_window.grab_set()

        # Wyśrodkuj okno
        scan_window.update_idletasks()
        x = (scan_window.winfo_screenwidth() // 2) - (450 // 2)
        y = (scan_window.winfo_screenheight() // 2) - (220 // 2)
        scan_window.geometry(f"+{x}+{y}")

        tk.Label(scan_window,
                 text=f"📦 {test_name}",
                 font=('Arial', 14, 'bold'),
                 bg=self.COLORS['bg_main'],
                 fg=self.COLORS['text_primary']).pack(pady=(20, 5))

        tk.Label(scan_window,
                 text="Zeskanuj numer seryjny urządzenia",
                 font=('Arial', 10),
                 bg=self.COLORS['bg_main'],
                 fg=self.COLORS['text_secondary']).pack(pady=(0, 20))

        entry_frame = tk.Frame(scan_window, bg=self.COLORS['bg_main'])
        entry_frame.pack(pady=10)

        tk.Label(entry_frame,
                 text="S/N:",
                 font=('Arial', 10, 'bold'),
                 bg=self.COLORS['bg_main'],
                 fg=self.COLORS['text_primary']).pack(side='left', padx=(0, 10))

        serial_var = tk.StringVar()
        serial_entry = tk.Entry(entry_frame,
                                textvariable=serial_var,
                                font=('Arial', 12),
                                width=25,
                                bg=self.COLORS['bg_card'],
                                fg=self.COLORS['text_primary'],
                                insertbackground=self.COLORS['text_primary'],
                                bd=2,
                                relief=tk.SOLID,
                                justify='center')
        serial_entry.pack(side='left')
        serial_entry.focus()

        result = {'serial': None}

        def confirm():
            serial = serial_var.get().strip().upper()
            print(f"[DEBUG] Potwierdzam S/N: '{serial}'")
            if not serial:
                messagebox.showwarning("Brak numeru", "Numer seryjny nie może być pusty!")
                serial_entry.focus()
                return
            print(f"[DEBUG] Ustawiam result['serial'] = {serial}")
            result['serial'] = serial
            print(f"[DEBUG] Zamykam okno skanowania")
            scan_window.destroy()

        def cancel():
            print(f"[DEBUG] Anulowano skanowanie")
            scan_window.destroy()

        # Binding Enter - MUSI BYĆ PRZED przyciskami
        serial_entry.bind('<Return>', lambda e: confirm())

        btn_frame = tk.Frame(scan_window, bg=self.COLORS['bg_main'])
        btn_frame.pack(pady=20)

        tk.Button(btn_frame,
                  text="✓ ZATWIERDŹ",
                  command=confirm,
                  bg=self.COLORS['button_bg'],
                  fg=self.COLORS['button_fg'],
                  activebackground=self.COLORS['button_hover'],
                  activeforeground=self.COLORS['button_hover_fg'],
                  bd=2,
                  relief=tk.SOLID,
                  font=('Arial', 9, 'bold'),
                  width=12).pack(side='left', padx=3)

        tk.Button(btn_frame,
                  text="← WYJDŹ",
                  command=cancel,
                  bg=self.COLORS['bg_main'],
                  fg=self.COLORS['text_secondary'],
                  activebackground=self.COLORS['button_hover'],
                  activeforeground=self.COLORS['button_hover_fg'],
                  bd=2,
                  relief=tk.SOLID,
                  font=('Arial', 9),
                  width=12).pack(side='left', padx=3)

        # Czekaj aż okno się zamknie
        scan_window.wait_window()

        # Zwróć wynik
        print(f"[DEBUG] Zwracam result['serial']: {result['serial']}")
        return result['serial']

    def open_music_player_test(self):
        """Otwiera Test 1"""
        # SKANOWANIE NUMERU SERYJNEGO
        device_serial = self.scan_serial_number("TEST 1 - Odtwarzacz Muzyki")
        if not device_serial:
            return  # Anulowano skanowanie

        if self.current_test_window is not None:
            try:
                self.resource_mgr.unregister_window(self.current_test_window)
                self.current_test_window.destroy()
            except:
                pass

        geometry = self.config_mgr.get('app.window_geometry.music_player', '650x720')

        try:
            test_window = tk.Toplevel(self.root)
            test_window.title("Test 1: Odtwarzacz Muzyki")
            test_window.geometry(geometry)
            test_window.configure(bg=self.COLORS['bg_main'])
            test_window.attributes('-topmost', True)  # <-- DODAJ TO!

            from music_player_test import MusicPlayerTest

            print(f"[DEBUG] Przekazuję do TEST1 - Operator: {self.logged_operator}, Device: {device_serial}")

            test = MusicPlayerTest(test_window,
                                   operator_hrid=self.logged_operator,
                                   device_serial=device_serial,
                                   scan_callback=self.scan_serial_number)  # <-- DODAJ

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
        # SKANOWANIE NUMERU SERYJNEGO
        device_serial = self.scan_serial_number("TEST 2 - Generator Częstotliwości")
        if not device_serial:
            return  # Anulowano skanowanie

        if self.current_test_window is not None:
            try:
                self.resource_mgr.unregister_window(self.current_test_window)
                self.current_test_window.destroy()
            except:
                pass

        geometry = self.config_mgr.get('app.window_geometry.tone_generator', '580x820')

        try:
            test_window = tk.Toplevel(self.root)
            test_window.title("Test 2: Generator Częstotliwości")
            test_window.geometry(geometry)
            test_window.configure(bg=self.COLORS['bg_main'])
            test_window.attributes('-topmost', True)  # <-- DODAJ

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

            test = ToneGeneratorTest(test_frame, close_test,
                                     operator_hrid=self.logged_operator,
                                     device_serial=device_serial,
                                     scan_callback=self.scan_serial_number)  # <-- DODAJ

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
        # SKANOWANIE NUMERU SERYJNEGO
        device_serial = self.scan_serial_number("TEST 3 - Test Stereo")
        if not device_serial:
            return  # Anulowano skanowanie

        if self.current_test_window is not None:
            try:
                self.resource_mgr.unregister_window(self.current_test_window)
                self.current_test_window.destroy()
            except:
                pass

        geometry = self.config_mgr.get('app.window_geometry.stereo_test', '500x750')

        try:
            test_window = tk.Toplevel(self.root)
            test_window.title("Test 3: Stereo (Lewa/Prawa)")
            test_window.geometry(geometry)
            test_window.configure(bg=self.COLORS['bg_main'])

            test = StereoTest(test_window,
                              operator_hrid=self.logged_operator,
                              device_serial=device_serial)  # <-- Użyj zeskanowanego

            def close_test():
                try:
                    test.cleanup()
                    self.resource_mgr.unregister_window(test_window)
                    test_window.destroy()
                    self.current_test_window = None
                except:
                    pass

            test_window.protocol("WM_DELETE_WINDOW", close_test)

            self.resource_mgr.register_window(test_window, 'stereo_test')
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