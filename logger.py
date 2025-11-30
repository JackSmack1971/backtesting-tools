import csv
import os
from datetime import datetime
import json

class SignalLogger:
    def __init__(self, filepath="monitor_log.csv"):
        self.filepath = filepath
        self.headers = [
            "timestamp", "price", "scenario_flags", "rotation_phase", 
            "sentiment", "funding", "btc_dom", "atr_pct"
        ]
        self._init_file()

    def _init_file(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)

    def log_run(self, data: dict):
        """
        Log a run to the CSV file.
        """
        row = [
            datetime.now().isoformat(),
            data.get("price"),
            ";".join(data.get("scenario_flags", [])),
            data.get("rotation_phase"),
            data.get("sentiment_tag"),
            data.get("funding"),
            data.get("btc_dom"),
            data.get("atr_pct")
        ]
        
        with open(self.filepath, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(row)
