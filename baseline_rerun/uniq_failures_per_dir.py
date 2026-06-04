import csv
import re
from collections import Counter, defaultdict
from pathlib import Path
import sys

INPUT_CSV = sys.argv[1]
OUTPUT_CSV = "unique_failures_per_directory.csv"

def extract_signature(failure_text):
    lines = failure_text.splitlines()

    for line in lines:
        line = line.strip()
        if re.search(r"(Exception|Error):", line):
            return line

    for line in lines:
        line = line.strip()
        if line and not line.startswith("[INFO]") and not line.startswith("[ERROR]"):
            return line

    return failure_text.strip()

def extract_dir_id(filename):
    parts = Path(filename).parts

    # Find numeric directory after hbase_artifacts_baseline_10k
    for i, part in enumerate(parts):
        if part == "hbase_artifacts_baseline_10k" and i + 1 < len(parts):
            return parts[i + 1]

    # Fallback: first numeric part in path
    for part in parts:
        if part.isdigit():
            return part

    return "UNKNOWN"

# directory_id -> Counter(signature)
dir_counters = defaultdict(Counter)

# (directory_id, signature) -> example files
dir_examples = defaultdict(list)

with open(INPUT_CSV, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        filename = row["filename"]
        failure = row["failure"]

        dir_id = extract_dir_id(filename)
        signature = extract_signature(failure)

        dir_counters[dir_id][signature] += 1
        dir_examples[(dir_id, signature)].append(filename)

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["directory", "unique_failure_count", "count", "failure_signature", "example_files"])

    for dir_id in sorted(dir_counters.keys(), key=lambda x: int(x) if x.isdigit() else x):
        unique_count = len(dir_counters[dir_id])

        for signature, count in dir_counters[dir_id].most_common():
            writer.writerow([
                dir_id,
                unique_count,
                count,
                signature,
                "; ".join(dir_examples[(dir_id, signature)][:5])
            ])

print(f"Processed {len(dir_counters)} directories")
print(f"Saved results to {OUTPUT_CSV}")

#for dir_id in sorted(dir_counters.keys(), key=lambda x: int(x) if x.isdigit() else x):
#    print(f"Directory {dir_id}: {len(dir_counters[dir_id])} unique failures")
for dir_id in sorted(dir_counters.keys(), key=lambda x: int(x) if x.isdigit() else x):
    signatures = list(dir_counters[dir_id].keys())

    print(f"\nDirectory {dir_id}: {len(signatures)} unique failures")

    for idx, sig in enumerate(signatures, start=1):
        print(f"  {idx}. {sig}")
