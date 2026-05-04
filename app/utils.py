# app/utils.py

import json
import csv


def save_report_json(report):
    with open("output/report.json", "w") as file:
        json.dump(report, file, indent=4)

def save_report_csv(report):
    with open("output/report.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Title", "Priority", "Category", "Status"])
        for ticket in report:
            writer.writerow([ticket["title"], ticket["priority"], ticket["category"], ticket["status"]])
