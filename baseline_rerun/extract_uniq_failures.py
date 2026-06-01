import csv
import re
from collections import Counter, defaultdict
import sys

INPUT_CSV = sys.argv[1] #"extracted_errors_1_failures.csv"
OUTPUT_CSV = "unique_failures.csv"

def extract_signature(failure_text):
    """
    Extract the main failure signature from the failure block.
    Example:
    java.net.BindException: Address already in use (Bind failed)
    """

    lines = failure_text.splitlines()

    # Look for exception/error line
    for line in lines:
        line = line.strip()

        if re.search(r"(Exception|Error):", line):
            return line

    # Fallback: look inside Maven Results -> Errors section
    for line in lines:
        line = line.strip()

        if line and not line.startswith("[INFO]") and not line.startswith("[ERROR]"):
            return line

    return failure_text.strip()


counter = Counter()
examples = defaultdict(list)

with open(INPUT_CSV, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        filename = row["filename"]
        failure = row["failure"]

        signature = extract_signature(failure)

        counter[signature] += 1
        examples[signature].append(filename)


with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["count", "failure_signature", "example_files"])

    for signature, count in counter.most_common():
        writer.writerow([
            count,
            signature,
            "; ".join(examples[signature][:5])
        ])

print(f"Found {len(counter)} unique failures")
print(f"Saved results to {OUTPUT_CSV}")
