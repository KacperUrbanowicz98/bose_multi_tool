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
        self.combo_csv_file = os.path.join(report_dir, "combo_test_history.csv")

        # Utwórz folder jeśli nie istnieje
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)

        # Utwórz pliki CSV z nagłówkami jeśli nie istnieją
        if not os.path.exists(self.csv_file):
            self.create_csv_file()

        if not os.path.exists(self.combo_csv_file):
            self.create_combo_csv_file()

    def create_csv_file(self):
        """Tworzy plik CSV z nagłówkami"""
        headers = [
            'Test ID', 'Test Type', 'Device Serial', 'Operator HRID',
            'Date', 'Time', 'Duration (s)', 'Audio File', 'Status',
            'Steps Completed', 'Total Steps', 'Volumes Tested',
            'Interrupted', 'Notes'
        ]
        with open(self.csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    def create_combo_csv_file(self):
        """Tworzy plik CSV dla COMBO testów"""
        headers = [
            'Test ID',
            'Test Type',
            'Device Serial',
            'Operator HRID',
            'Date',
            'Time',
            'TEST1_Status',
            'TEST1_Duration',
            'TEST1_Audio_File',
            'TEST1_Volumes',
            'TEST2_Status',
            'TEST2_Duration',
            'TEST2_WaveType',
            'TEST2_FreqRange',
            'TEST3_Status',
            'TEST3_Duration',
            'TEST3_Channels',
            'Overall_Status',
            'Total_Duration',
            'Interrupted',
            'Notes'
        ]
        with open(self.combo_csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    def save_test1_result(self, operator_hrid, device_serial, test_duration,
                          audio_file, status, total_steps, completed_steps,
                          volume_levels, interrupted, notes=""):
        now = datetime.now()
        test_id = f"TEST1_{now.strftime('%Y%m%d_%H%M%S')}"
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')

        volumes_str = ','.join([f"{v}%" for v in volume_levels])

        if not device_serial:
            device_serial = "N/A"

        row = [
            test_id, "Music Player Auto Test", device_serial, operator_hrid,
            date_str, time_str, test_duration, audio_file, status,
            completed_steps, total_steps, volumes_str,
            "Yes" if interrupted else "No", notes
        ]

        with open(self.csv_file, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(row)

        print(f"✓ Raport zapisany: {test_id}")
        return test_id

    def save_test2_result(self, operator_hrid, device_serial, wave_type,
                          freq_range, duration, volume, status, interrupted, notes=""):
        now = datetime.now()
        test_id = f"TEST2_{now.strftime('%Y%m%d_%H%M%S')}"
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')

        if not device_serial:
            device_serial = "N/A"

        row = [
            test_id, "Tone Generator Auto Test", device_serial, operator_hrid,
            date_str, time_str, duration, f"{wave_type} ({freq_range} Hz)",
            status, "N/A", "N/A", f"{volume}%",
            "Yes" if interrupted else "No", notes
        ]

        with open(self.csv_file, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(row)

        print(f"✓ Raport TEST 2 zapisany: {test_id}")
        return test_id

    def save_test3_result(self, operator_hrid, device_serial, frequency,
                          volume, duration_per_channel, total_duration,
                          status, interrupted, notes=""):
        now = datetime.now()
        test_id = f"TEST3_{now.strftime('%Y%m%d_%H%M%S')}"
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')

        if not device_serial:
            device_serial = "N/A"

        row = [
            test_id, "Stereo Test (L/R) Auto", device_serial, operator_hrid,
            date_str, time_str, total_duration,
            f"Tone {frequency}Hz (Left - Right - Both)",
            status, "3", "3", f"{volume}% ({duration_per_channel}s per channel)",
            "Yes" if interrupted else "No", notes
        ]

        with open(self.csv_file, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(row)

        print(f"✓ Raport TEST 3 zapisany: {test_id}")
        return test_id

    def save_combo_result(self, operator_hrid, device_serial,
                          test1_data, test2_data, test3_data,
                          total_duration, interrupted, notes=""):
        """
        Zapisuje wynik COMBO testu (TEST 1 + TEST 2 + TEST 3)

        Args:
            operator_hrid: HRID operatora
            device_serial: Numer seryjny urządzenia
            test1_data: dict z wynikami TEST 1
            test2_data: dict z wynikami TEST 2
            test3_data: dict z wynikami TEST 3
            total_duration: Łączny czas wszystkich testów (s)
            interrupted: Czy przerwano
            notes: Notatki
        """
        now = datetime.now()
        test_id = f"COMBO_{now.strftime('%Y%m%d_%H%M%S')}"
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')

        if not device_serial:
            device_serial = "N/A"

        # Overall status - PASS tylko gdy wszystkie 3 = PASS
        all_statuses = [
            test1_data.get('status', 'N/A'),
            test2_data.get('status', 'N/A'),
            test3_data.get('status', 'N/A')
        ]
        if interrupted:
            overall_status = "INTERRUPTED"
        elif all(s == "PASS" for s in all_statuses):
            overall_status = "PASS"
        else:
            overall_status = "FAIL"

        # TEST 1 dane
        t1_volumes = ','.join([f"{v}%" for v in test1_data.get('volume_levels', [])])

        row = [
            test_id,
            "COMBO Test (1+2+3)",
            device_serial,
            operator_hrid,
            date_str,
            time_str,
            # TEST 1
            test1_data.get('status', 'N/A'),
            test1_data.get('duration', 'N/A'),
            test1_data.get('audio_file', 'N/A'),
            t1_volumes,
            # TEST 2
            test2_data.get('status', 'N/A'),
            test2_data.get('duration', 'N/A'),
            test2_data.get('wave_type', 'N/A'),
            test2_data.get('freq_range', 'N/A'),
            # TEST 3
            test3_data.get('status', 'N/A'),
            test3_data.get('duration', 'N/A'),
            f"{test3_data.get('duration_per_channel', 'N/A')}s per channel",
            # Overall
            overall_status,
            total_duration,
            "Yes" if interrupted else "No",
            notes
        ]

        with open(self.combo_csv_file, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(row)

        print(f"✓ Raport COMBO zapisany: {test_id} | Status: {overall_status}")
        return test_id, overall_status


# Singleton
_reporter_instance = None


def get_test_reporter():
    """Zwraca singleton TestReporter"""
    global _reporter_instance
    if _reporter_instance is None:
        _reporter_instance = TestReporter()
    return _reporter_instance
