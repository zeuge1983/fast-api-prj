# app/utils.py

import json
import csv
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output"


def save_report_json(report: dict) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    with open(OUTPUT_DIR / "report.json", "w") as file:
        json.dump(report, file, indent=4)

def save_report_csv(report: list) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    with open(OUTPUT_DIR / "report.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Title", "Priority", "Category", "Status"])
        for ticket in report:
            writer.writerow([ticket["title"], ticket["priority"], ticket["category"], ticket["status"]])
