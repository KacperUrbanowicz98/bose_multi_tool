"""
Test Reporter - Moduł raportowania wyników testów
Bose Audio Multi-Tool
"""

import csv
import os
from datetime import datetime


class TestReporter:
    """Klasa do zapisywania wyników testów do CSV"""

    def __init__(self, report_dir="test_reports"):
        self.report_dir = report_dir
        self.csv_file = os.path.join(report_dir, "test_history.csv")

        # Utwórz folder jeśli nie istnieje
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)

        # Utwórz plik CSV z nagłówkami jeśli nie istnieje
        if not os.path.exists(self.csv_file):
            self.create_csv_file()

    def create_csv_file(self):
        """Tworzy plik CSV z nagłówkami"""
        headers = [
            'Test ID',
            'Test Type',
            'Device Serial',
            'Operator HRID',
            'Date',
            'Time',
            'Duration (s)',
            'Audio File',
            'Status',
            'Steps Completed',
            'Total Steps',
            'Volumes Tested',
            'Interrupted',
            'Notes'
        ]

        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    def save_test1_result(self, operator_hrid, device_serial, audio_file,
                          status, completed_steps, total_steps,
                          volumes_tested, duration, interrupted=False, notes=""):
        """
        Zapisuje wynik TEST 1 (Music Player Auto Test)

        Args:
            operator_hrid: HRID operatora (str)
            device_serial: Numer seryjny urządzenia (str) - może być None
            audio_file: Nazwa pliku audio (str)
            status: Status testu - "PASS" / "FAIL" / "INTERRUPTED" (str)
            completed_steps: Ile kroków ukończono (int)
            total_steps: Łącznie kroków (int)
            volumes_tested: Lista głośności [10, 20, 30, ...] (list)
            duration: Czas trwania w sekundach (int)
            interrupted: Czy przerwano (bool)
            notes: Dodatkowe notatki (str)
        """
        now = datetime.now()
        test_id = f"TEST1_{now.strftime('%Y%m%d_%H%M%S')}"
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')

        # Konwertuj listę głośności na string
        volumes_str = ','.join([f"{v}%" for v in volumes_tested])

        # Jeśli brak numeru seryjnego
        if not device_serial:
            device_serial = "N/A"

        row = [
            test_id,
            "Music Player Auto Test",
            device_serial,
            operator_hrid,
            date_str,
            time_str,
            duration,
            audio_file,
            status,
            completed_steps,
            total_steps,
            volumes_str,
            "Yes" if interrupted else "No",
            notes
        ]

        # Dopisz do pliku CSV
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)

        print(f"✓ Raport zapisany: {test_id}")
        return test_id


# Singleton - jedna instancja dla całej aplikacji
_reporter_instance = None


def get_test_reporter():
    """Zwraca singleton TestReporter"""
    global _reporter_instance
    if _reporter_instance is None:
        _reporter_instance = TestReporter()
    return _reporter_instance
