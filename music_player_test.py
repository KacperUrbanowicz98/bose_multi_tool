"""
Test 1: Odtwarzacz Muzyki
Moduł testowy dla Audio Testing Multi-Tool
Z pełną obsługą błędów i walidacją
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pygame
import os
import json
# Na początku pliku dodaj:
from config_manager import get_config_manager
from resource_manager import get_resource_manager


class MusicPlayerTest:
    def __init__(self, parent_window):
        self.window = parent_window

        # === MENEDŻERY ===
        self.config_mgr = get_config_manager()
        self.resource_mgr = get_resource_manager()

        # Załaduj konfigurację music playera
        mp_config = self.config_mgr.get_music_player_config()

        # Zmienne stanu
        self.current_file = None
        self.is_playing = False
        self.volume = mp_config.get('last_volume', 70) / 100
        self.default_volume = mp_config.get('last_volume', 70)
        self.supported_formats = mp_config.get('supported_formats', ['.mp3', '.wav'])
        self.max_file_size_mb = mp_config.get('max_file_size_mb', 500)

        # NIE używamy już osobnego pliku JSON - wszystko w ConfigManager

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.create_widgets()
        self.load_state()

    def save_state(self):
        """Zapisuje stan przez ConfigManager"""
        files = list(self.file_listbox.get(0, tk.END))
        volume = self.volume_scale.get()

        self.config_mgr.update_music_player_state(
            files=files,
            volume=volume
        )

    def load_state(self):
        """Ładuje stan z ConfigManager"""
        mp_config = self.config_mgr.get_music_player_config()

        # Przywróć pliki
        for file_path in mp_config.get('last_files', []):
            if os.path.exists(file_path):
                self.file_listbox.insert(tk.END, file_path)

        # Przywróć głośność
        volume = mp_config.get('last_volume', 70)
        self.volume_scale.set(volume)
        self.change_volume(volume)

    def on_closing(self):
        """Zamknięcie z zapisem i wyrejestrowaniem"""
        self.save_state()
        self.resource_mgr.stop_all_sounds()
        self.resource_mgr.unregister_window(self.window)
        self.window.destroy()


class MusicPlayerTest:
    """
    Test odtwarzacza muzyki z kontrolą głośności i przewijaniem.
    Prosty odtwarzacz do testowania jakości dźwięku słuchawek/głośników.
    """

    def __init__(self, parent_window):
        """
        Inicjalizacja testu odtwarzacza z obsługą błędów.

        Args:
            parent_window: Okno rodzic (tk.Toplevel) w którym test jest wyświetlany
        """
        self.window = parent_window

        # Zmienne stanu odtwarzacza
        self.current_file = None
        self.is_playing = False
        self.volume = 0.7
        self.current_position = 0
        self.config_file = "music_player_config.json"

        # DOMYŚLNE WARTOŚCI
        self.default_volume = 70

        # Obsługiwane formaty audio
        self.supported_formats = ['.mp3', '.wav', '.ogg', '.flac', '.m4a']

        # Maksymalny rozmiar pliku (500 MB)
        self.max_file_size_mb = 500

        # Ustawienie zamykania okna
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Budowanie interfejsu
        try:
            self.create_widgets()
        except Exception as e:
            messagebox.showerror("Błąd inicjalizacji",
                               f"Nie można utworzyć interfejsu:\n{str(e)}")
            raise

        # Załadowanie zapisanego stanu
        try:
            self.load_state()
        except Exception as e:
            print(f"Ostrzeżenie: Nie można załadować zapisanego stanu: {e}")
            # Kontynuuj z domyślnymi wartościami

    def create_widgets(self):
        """Tworzy wszystkie widgety z walidacją"""

        # === GŁÓWNY KONTENER ===
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # === SEKCJA WYBORU PLIKÓW ===
        file_frame = ttk.LabelFrame(main_frame, text="Wybór utworu", padding="10")
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)

        # Listbox z plikami audio
        self.file_listbox = tk.Listbox(file_frame, height=10, width=80)
        self.file_listbox.grid(row=0, column=0, columnspan=2, pady=5)

        # Przyciski zarządzania listą
        ttk.Button(file_frame, text="Dodaj pliki",
                  command=self.add_files).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(file_frame, text="Usuń zaznaczony",
                  command=self.remove_file).grid(row=1, column=1, padx=5, pady=5)

        # === SEKCJA ODTWARZACZA ===
        player_frame = ttk.LabelFrame(main_frame, text="Odtwarzacz", padding="15")
        player_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)

        # Przyciski sterowania
        control_frame = ttk.Frame(player_frame)
        control_frame.grid(row=0, column=0, pady=10)

        ttk.Button(control_frame, text="⏪ -10s",
                  command=self.rewind_10s, width=12).pack(side=tk.LEFT, padx=3)

        self.play_button = ttk.Button(control_frame, text="▶ Play",
                                     command=self.play_pause, width=15)
        self.play_button.pack(side=tk.LEFT, padx=3)

        ttk.Button(control_frame, text="⏹ Stop",
                  command=self.stop, width=15).pack(side=tk.LEFT, padx=3)

        ttk.Button(control_frame, text="⏩ +10s",
                  command=self.forward_10s, width=12).pack(side=tk.LEFT, padx=3)

        # Status odtwarzacza
        self.status_label = ttk.Label(player_frame,
                                     text="Brak załadowanego utworu",
                                     font=('Arial', 10))
        self.status_label.grid(row=1, column=0, pady=10)

        # Kontrola głośności
        volume_frame = ttk.LabelFrame(player_frame, text="Głośność", padding="10")
        volume_frame.grid(row=2, column=0, pady=10, sticky=(tk.W, tk.E))

        vol_control = ttk.Frame(volume_frame)
        vol_control.pack(expand=True)

        self.volume_label = ttk.Label(vol_control, text="70%", width=8,
                                     font=('Arial', 11, 'bold'))
        self.volume_label.pack(side=tk.RIGHT, padx=10)

        self.volume_scale = ttk.Scale(vol_control, from_=0, to=100,
                                     orient=tk.HORIZONTAL,
                                     command=self.change_volume, length=400)
        self.volume_scale.set(70)
        self.volume_scale.pack(side=tk.LEFT, padx=10)

        # === SEPARATOR I PRZYCISKI ===
        ttk.Separator(main_frame, orient='horizontal').grid(row=2, column=0,
                                                            sticky=(tk.W, tk.E),
                                                            pady=15)

        button_frame = ttk.Frame(main_frame, padding="5")
        button_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))

        ttk.Button(button_frame, text="⚙ Przywróć ustawienia domyślne",
                  command=self.restore_defaults, width=30).pack(side=tk.LEFT, padx=10)

        ttk.Button(button_frame, text="✖ Zamknij test",
                  command=self.close_test, width=25).pack(side=tk.RIGHT, padx=10)

        # === KONFIGURACJA GRID ===
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

    def validate_audio_file(self, file_path):
        """
        Waliduje plik audio przed dodaniem do listy.

        Args:
            file_path: Ścieżka do pliku

        Returns:
            tuple: (bool: czy plik jest poprawny, str: komunikat błędu lub None)
        """
        # Sprawdź czy plik istnieje
        if not os.path.exists(file_path):
            return False, "Plik nie istnieje"

        # Sprawdź czy to plik (nie folder)
        if not os.path.isfile(file_path):
            return False, "To nie jest plik"

        # Sprawdź rozszerzenie
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in self.supported_formats:
            return False, f"Nieobsługiwany format: {file_ext}"

        # Sprawdź rozmiar pliku
        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                return False, f"Plik zbyt duży: {file_size_mb:.1f} MB (max {self.max_file_size_mb} MB)"
        except OSError as e:
            return False, f"Nie można odczytać rozmiaru pliku: {str(e)}"

        return True, None

    def add_files(self):
        """Otwiera dialog wyboru plików i dodaje je do listy z walidacją"""
        try:
            files = filedialog.askopenfilenames(
                title="Wybierz pliki audio",
                filetypes=[
                    ("Pliki audio", "*.mp3 *.wav *.ogg *.flac *.m4a"),
                    ("Wszystkie pliki", "*.*")
                ]
            )
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd otwierania dialogu:\n{str(e)}")
            return

        if not files:
            return

        added_count = 0
        error_count = 0
        errors = []

        for file in files:
            # Walidacja pliku
            is_valid, error_msg = self.validate_audio_file(file)

            if is_valid:
                # Sprawdź czy plik już nie jest na liście
                if file not in self.file_listbox.get(0, tk.END):
                    self.file_listbox.insert(tk.END, file)
                    added_count += 1
                else:
                    errors.append(f"{os.path.basename(file)}: Już na liście")
                    error_count += 1
            else:
                errors.append(f"{os.path.basename(file)}: {error_msg}")
                error_count += 1

        # Podsumowanie
        if error_count > 0:
            error_text = "\n".join(errors[:5])  # Pokaż max 5 błędów
            if len(errors) > 5:
                error_text += f"\n... i {len(errors) - 5} więcej"

            messagebox.showwarning(
                "Ostrzeżenie",
                f"Dodano: {added_count} plików\n"
                f"Odrzucono: {error_count} plików\n\n"
                f"Błędy:\n{error_text}"
            )
        elif added_count > 0:
            self.status_label.config(text=f"Dodano {added_count} plików")

    def remove_file(self):
        """Usuwa zaznaczony plik z listy z walidacją"""
        try:
            selected = self.file_listbox.curselection()
            if not selected:
                messagebox.showinfo("Info", "Nie wybrano pliku do usunięcia")
                return

            file_name = os.path.basename(self.file_listbox.get(selected[0]))

            # Potwierdź usunięcie
            response = messagebox.askyesno(
                "Potwierdzenie",
                f"Czy na pewno usunąć z listy:\n{file_name}?"
            )

            if response:
                self.file_listbox.delete(selected)
                self.status_label.config(text="Usunięto plik z listy")

        except tk.TclError:
            messagebox.showwarning("Uwaga", "Nie można usunąć pliku")
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd usuwania pliku:\n{str(e)}")

    def play_pause(self):
        """Odtwarza lub pauzuje muzykę z pełną obsługą błędów"""
        if not self.is_playing:
            # Tryb PLAY
            selected = self.file_listbox.curselection()

            if not selected:
                messagebox.showinfo("Info", "Wybierz utwór z listy")
                return

            self.current_file = self.file_listbox.get(selected[0])

            # Walidacja przed odtworzeniem
            is_valid, error_msg = self.validate_audio_file(self.current_file)
            if not is_valid:
                messagebox.showerror("Błąd", f"Nie można odtworzyć pliku:\n{error_msg}")
                return

            try:
                pygame.mixer.music.load(self.current_file)
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play()

                self.is_playing = True
                self.play_button.config(text="⏸ Pause")
                filename = os.path.basename(self.current_file)
                self.status_label.config(text=f"Odtwarzanie: {filename}")

            except pygame.error as e:
                self.status_label.config(text="Błąd: Nieobsługiwany format")
                messagebox.showerror(
                    "Błąd odtwarzania",
                    f"Nie można odtworzyć pliku:\n\n"
                    f"Szczegóły: {str(e)}\n\n"
                    f"Spróbuj innego formatu (WAV, OGG)"
                )
            except Exception as e:
                self.status_label.config(text=f"Błąd: {str(e)}")
                messagebox.showerror("Błąd", f"Nieoczekiwany błąd:\n{str(e)}")
        else:
            # Tryb PAUSE/UNPAUSE
            try:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.pause()
                    self.play_button.config(text="▶ Play")
                    self.is_playing = False
                    self.status_label.config(text="Wstrzymano")
                else:
                    pygame.mixer.music.unpause()
                    self.play_button.config(text="⏸ Pause")
                    self.is_playing = True
                    filename = os.path.basename(self.current_file)
                    self.status_label.config(text=f"Odtwarzanie: {filename}")
            except Exception as e:
                messagebox.showerror("Błąd", f"Błąd pauzowania:\n{str(e)}")

    def stop(self):
        """Zatrzymuje odtwarzanie z obsługą błędów"""
        try:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.current_position = 0
            self.play_button.config(text="▶ Play")
            self.status_label.config(text="Zatrzymano")
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd zatrzymywania:\n{str(e)}")

    def rewind_10s(self):
        """Przewija utwór 10 sekund wstecz z walidacją"""

        # Walidacja: Czy jest załadowany plik?
        if not self.current_file:
            messagebox.showinfo("Info", "Najpierw wybierz i uruchom utwór")
            return

        # Walidacja: Czy coś gra?
        if not pygame.mixer.music.get_busy():
            messagebox.showinfo("Info", "Najpierw uruchom odtwarzanie")
            return

        # Walidacja: Czy plik nadal istnieje?
        if not os.path.exists(self.current_file):
            messagebox.showerror("Błąd", "Plik został usunięty z dysku!")
            self.stop()
            return

        try:
            current_pos = pygame.mixer.music.get_pos()
            new_pos = max(0, current_pos - 10000)

            pygame.mixer.music.stop()
            pygame.mixer.music.load(self.current_file)
            pygame.mixer.music.play(start=new_pos / 1000.0)
            pygame.mixer.music.set_volume(self.volume)

            self.status_label.config(text="Przewinięto -10s")

        except pygame.error as e:
            self.status_label.config(text="Błąd przewijania")
            messagebox.showwarning(
                "Uwaga",
                f"Przewijanie nie działa dla tego formatu.\n\n"
                f"Szczegóły: {str(e)}\n\n"
                f"Spróbuj formatu OGG lub WAV dla lepszego przewijania."
            )
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd przewijania:\n{str(e)}")

    def forward_10s(self):
        """Przewija utwór 10 sekund do przodu z walidacją"""

        if not self.current_file:
            messagebox.showinfo("Info", "Najpierw wybierz i uruchom utwór")
            return

        if not pygame.mixer.music.get_busy():
            messagebox.showinfo("Info", "Najpierw uruchom odtwarzanie")
            return

        if not os.path.exists(self.current_file):
            messagebox.showerror("Błąd", "Plik został usunięty z dysku!")
            self.stop()
            return

        try:
            current_pos = pygame.mixer.music.get_pos()
            new_pos = current_pos + 10000

            pygame.mixer.music.stop()
            pygame.mixer.music.load(self.current_file)
            pygame.mixer.music.play(start=new_pos / 1000.0)
            pygame.mixer.music.set_volume(self.volume)

            self.status_label.config(text="Przewinięto +10s")

        except pygame.error as e:
            self.status_label.config(text="Błąd przewijania")
            messagebox.showwarning(
                "Uwaga",
                f"Przewijanie nie działa dla tego formatu.\n\n"
                f"Szczegóły: {str(e)}\n\n"
                f"Spróbuj formatu OGG lub WAV."
            )
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd przewijania:\n{str(e)}")

    def change_volume(self, value):
        """Zmienia głośność z walidacją"""
        try:
            volume_percent = float(value)

            # Walidacja zakresu
            volume_percent = max(0, min(100, volume_percent))

            self.volume = volume_percent / 100
            pygame.mixer.music.set_volume(self.volume)
            self.volume_label.config(text=f"{int(volume_percent)}%")

        except (ValueError, TypeError) as e:
            print(f"Błąd zmiany głośności: {e}")
            self.volume_scale.set(self.volume * 100)
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd zmiany głośności:\n{str(e)}")

    def restore_defaults(self):
        """Przywraca ustawienia domyślne z potwierdzeniem"""
        response = messagebox.askyesno(
            "Przywracanie ustawień",
            "Czy na pewno chcesz przywrócić głośność do 70%?"
        )

        if response:
            try:
                self.volume_scale.set(self.default_volume)
                self.change_volume(self.default_volume)
                messagebox.showinfo("Gotowe",
                                  "Głośność została przywrócona do wartości domyślnej!")
            except Exception as e:
                messagebox.showerror("Błąd", f"Błąd przywracania ustawień:\n{str(e)}")

    def close_test(self):
        """Zamyka okno testu z zapisem stanu"""
        self.on_closing()

    def save_state(self):
        """Zapisuje stan do JSON z obsługą błędów"""
        state = {
            'files': list(self.file_listbox.get(0, tk.END)),
            'volume': self.volume_scale.get()
        }

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Błąd zapisu konfiguracji: {e}")
        except Exception as e:
            print(f"Nieoczekiwany błąd zapisu: {e}")

    def load_state(self):
        """Ładuje zapisany stan z JSON z obsługą błędów"""
        if not os.path.exists(self.config_file):
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

            # Przywróć listę plików (tylko te które istnieją)
            files_loaded = 0
            for file_path in state.get('files', []):
                is_valid, _ = self.validate_audio_file(file_path)
                if is_valid:
                    self.file_listbox.insert(tk.END, file_path)
                    files_loaded += 1

            if files_loaded > 0:
                self.status_label.config(text=f"Załadowano {files_loaded} plików z poprzedniej sesji")

            # Przywróć głośność
            volume = state.get('volume', self.default_volume)
            volume = max(0, min(100, volume))  # Walidacja
            self.volume_scale.set(volume)
            self.change_volume(volume)

        except json.JSONDecodeError as e:
            print(f"Błąd parsowania JSON: {e}")
        except IOError as e:
            print(f"Błąd odczytu pliku konfiguracji: {e}")
        except Exception as e:
            print(f"Nieoczekiwany błąd ładowania stanu: {e}")

    def on_closing(self):
        """Obsługa zamykania okna testu z czyszczeniem zasobów"""
        try:
            self.save_state()
        except Exception as e:
            print(f"Błąd zapisu stanu przy zamykaniu: {e}")

        try:
            pygame.mixer.music.stop()
        except Exception as e:
            print(f"Błąd zatrzymywania muzyki: {e}")

        try:
            self.window.destroy()
        except Exception as e:
            print(f"Błąd zamykania okna: {e}")
