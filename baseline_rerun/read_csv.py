import pandas as pd

import csv

csv_file = "extracted_failures.csv"

with open(csv_file, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        filename = row["filename"]
        print(filename)
