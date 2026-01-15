import json
import csv
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class JsonIO:
    """Handles JSON file I/O."""
    
    def save(self, data: list | dict, path: Path):
        """Saves data to a JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            logger.info(f"Saved data to {path}")
        except OSError as e:
            logger.error(f"Failed to save {path}: {e}")

    def load(self, path: Path) -> list:
        """Loads data from a JSON file. Returns empty list if missing."""
        if not path.exists():
            return []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load {path}: {e}")
            return []

class StatsLogger:
    """Handles appending stats to a CSV log."""
    
    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self.fieldnames = [
            "run_date",
            "total_links",
            "client_side_links",
            "excluded_links",
            "video_links",
            "minutes_links",
        ]

    def log_stats(self, stats: dict):
        """Appends a row of stats to the CSV."""
        run_date = datetime.now().strftime("%Y-%m-%d")
        row = {"run_date": run_date}
        # Safely get fields, defaulting to 0
        row.update({k: stats.get(k, 0) for k in self.fieldnames if k != "run_date"})
        
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        file_exists = self.csv_path.exists()

        try:
            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(row)
            logger.info(f"Stats logged to {self.csv_path}")
        except OSError as e:
            logger.error(f"Failed to log stats to CSV: {e}")
