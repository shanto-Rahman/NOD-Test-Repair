from pathlib import Path
import csv 
import re

ROOT = Path("hbase_artifacts_baseline_10k")
OUT_CSV = "extracted_errors_1_failures.csv"

ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")

def clean_text(text):
    return ansi_escape.sub("", text)

def extract_failure(text):
    text = clean_text(text)

    # Keep only text before BUILD FAILURE
    build_idx = text.find("BUILD FAILURE")
    if build_idx != -1: 
        text = text[:build_idx]

    # Start from the last "Running ..." line
    running_idx = text.rfind("Running ")
    if running_idx != -1: 
        text = text[running_idx:]

    return text.strip()

rows = []

for path in ROOT.rglob("*"):
    if not path.is_file():
        continue

    try:
        text = path.read_text(errors="ignore")
    except Exception:
        continue

    if "Errors: 1" not in text:
        continue

    failure_text = extract_failure(text)

    rows.append({
        "filename": str(path),
        "failure": failure_text
    })  

with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["filename", "failure"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Found {len(rows)} files containing 'Errors: 1'")
print(f"Saved results to {OUT_CSV}")
