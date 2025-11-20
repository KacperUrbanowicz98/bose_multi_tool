"""
Ekran logowania - HRID Verification
Bose Audio Multi-Tool
"""

import tkinter as tk
from tkinter import messagebox
import json
import os


class LoginScreen:
    """Ekran logowania z weryfikacją HRID"""

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

    def __init__(self, root, on_success_callback):
        self.root = root
        self.on_success = on_success_callback
        self.config_file = "audio_tool_config.json"

        # Załaduj listę operatorów
        self.operators = self.load_operators()

        self.create_login_screen()

    def load_operators(self):
        """Wczytuje listę HRID operatorów z konfiguracji"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('operators', {}).get('hrid_list', [])
        except:
            pass

        # Domyślna lista operatorów (jeśli nie ma w config)
        return [
            "OP001",
            "OP002",
            "ADMIN"
        ]

    def create_login_screen(self):
        """Tworzy ekran logowania"""
        # Ramka główna
        main_frame = tk.Frame(self.root, bg=self.COLORS['bg_main'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=50)

        # Logo / Tytuł
        if os.path.exists("logo.png"):
            try:
                original_image = tk.PhotoImage(file="logo.png")
                scale = max(1, original_image.width() // 120)
                self.logo_image = original_image.subsample(scale, scale)
                tk.Label(main_frame, image=self.logo_image,
                         bg=self.COLORS['bg_main']).pack(pady=(0, 20))
            except:
                tk.Label(main_frame, text="♪", font=('Arial', 40),
                         bg=self.COLORS['bg_main'],
                         fg=self.COLORS['text_primary']).pack(pady=(0, 20))
        else:
            tk.Label(main_frame, text="♪", font=('Arial', 40),
                     bg=self.COLORS['bg_main'],
                     fg=self.COLORS['text_primary']).pack(pady=(0, 20))

        tk.Label(main_frame,
                 text="TESTOWANIE AUDIO",
                 font=('Arial', 24, 'bold'),
                 bg=self.COLORS['bg_main'],
                 fg=self.COLORS['text_primary']).pack()

        tk.Label(main_frame,
                 text="MULTI-TOOL",
                 font=('Arial', 24, 'bold'),
                 bg=self.COLORS['bg_main'],
                 fg=self.COLORS['text_primary']).pack(pady=(0, 10))

        # Separator
        tk.Frame(main_frame, bg=self.COLORS['border'], height=2).pack(fill=tk.X, pady=20)

        # Informacja
        tk.Label(main_frame,
                 text="Zaloguj się używając HRID",
                 font=('Arial', 10),
                 bg=self.COLORS['bg_main'],
                 fg=self.COLORS['text_secondary']).pack(pady=(0, 20))

        # Pole HRID
        login_container = tk.Frame(main_frame, bg=self.COLORS['bg_card'],
                                   bd=2, relief=tk.SOLID)
        login_container.pack(pady=10, ipady=15, ipadx=20)

        tk.Label(login_container,
                 text="HRID:",
                 font=('Arial', 9, 'bold'),
                 bg=self.COLORS['bg_card'],
                 fg=self.COLORS['text_primary']).pack(pady=(0, 8))

        self.hrid_entry = tk.Entry(
            login_container,
            font=('Arial', 14),
            width=20,
            bg=self.COLORS['bg_main'],
            fg=self.COLORS['text_primary'],
            insertbackground=self.COLORS['text_primary'],
            bd=2,
            relief=tk.SOLID,
            justify='center'
        )
        self.hrid_entry.pack(pady=(0, 10))
        self.hrid_entry.focus()

        # Enter = login
        self.hrid_entry.bind('<Return>', lambda e: self.verify_login())

        # Przycisk logowania
        login_btn = tk.Button(
            login_container,
            text="ZALOGUJ",
            font=('Arial', 10, 'bold'),
            bg=self.COLORS['button_bg'],
            fg=self.COLORS['button_fg'],
            activebackground=self.COLORS['button_hover'],
            activeforeground=self.COLORS['button_hover_fg'],
            bd=2,
            relief=tk.SOLID,
            width=18,
            command=self.verify_login
        )
        login_btn.pack(pady=(0, 5))

        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="",
            font=('Arial', 8),
            bg=self.COLORS['bg_main'],
            fg='red'
        )
        self.status_label.pack(pady=(15, 0))

        # Stopka
        footer_frame = tk.Frame(main_frame, bg=self.COLORS['bg_main'])
        footer_frame.pack(side=tk.BOTTOM, pady=(30, 0))

        tk.Label(footer_frame,
                 text="Kacper Urbanowicz | Rafał Kobylecki",
                 font=('Arial', 7),
                 bg=self.COLORS['bg_main'],
                 fg=self.COLORS['text_secondary']).pack()

        tk.Label(footer_frame,
                 text="v1.0.0",
                 font=('Arial', 6),
                 bg=self.COLORS['bg_main'],
                 fg=self.COLORS['text_secondary']).pack()

    def verify_login(self):
        """Weryfikuje HRID operatora"""
        hrid = self.hrid_entry.get().strip().upper()

        if not hrid:
            self.status_label.config(text="⚠ Wprowadź HRID", fg='red')
            return

        if hrid in self.operators:
            # Sukces!
            self.status_label.config(text="✓ Logowanie...", fg='green')
            self.root.after(500, lambda: self.on_success(hrid))
        else:
            # Błąd
            self.status_label.config(text="✗ Nieprawidłowy HRID", fg='red')
            self.hrid_entry.delete(0, tk.END)
            self.hrid_entry.focus()
