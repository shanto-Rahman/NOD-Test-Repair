import csv
import os
import subprocess
from pathlib import Path
from typing import Optional
from modify_java_file import inject_sleep_before_line

def find_source_file_with_find(repos_root: str, slug: str, class_path: str) -> Optional[Path]:
    """
    Search under repos_root/slug for a file matching class_path.
    First try exact package tail (*/org/foo/Bar.java), then fall back to filename only.
    """
    base = Path(repos_root) / Path(*slug.split("/"))

    # 1) Prefer exact package path match
    cmd = ["find", str(base), "-type", "f", "-path", f"*/{class_path}"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    hits = [Path(p) for p in res.stdout.splitlines() if p.strip()]
    if hits:
        if len(hits) > 1:
            print(f"⚠️ Multiple matches for {class_path}; using first:\n" + "\n".join(str(h) for h in hits))
        return hits[0]

    # 2) Fallback: filename only (case-insensitive)
    fname = Path(class_path).name
    cmd = ["find", str(base), "-type", "f", "-iname", fname]
    res = subprocess.run(cmd, capture_output=True, text=True)
    hits = [Path(p) for p in res.stdout.splitlines() if p.strip()]
    if hits:
        if len(hits) > 1:
            print(f"⚠️ Multiple files named {fname}; consider using package path to disambiguate.")
        return hits[0]

    print(f"❌ No file found for {class_path} under {base}")
    return None

# Configuration: path to the CSV data file
csv_file = 'metadata/embedings/org.java_websocket.issues.Issue580Test.runNoCloseBlockingTestScenario2_bigbird_embeddings.csv'  # Update this to the actual CSV filename/path

# Variables for the test run command (ensure these are set to real values as needed)
#slug = "your-project-slug"        # e.g., "org.java-websocket/Java-WebSocket"
#module = "your-module-path"       # e.g., "" (if root project) or "module-name"
#test  = "your.test.ClassName#testMethod"  # e.g., a specific test to run
retry_count = 0
run_id = 0

input_csv="../data/all_82_tests.csv"
with open(input_csv, newline='') as inf:
    reader = csv.DictReader(inf)
    for row in reader:
        id = row['id']
        slug = row['slug']
        commit = row['commit']
        module = row['module']
        test = row['test']
        # Open and read the CSV data
        with open(csv_file, newline='') as f:  # newline='' for proper CSV parsing:contentReference[oaicite:4]{index=4}
            reader = csv.DictReader(f)
            for row in reader:
                class_name = row['Class']
                method_name = row['Method']
                descriptor = row['Descriptor']
                line_range = row['LineRange']
                # Parse line range (e.g., "555-570")
                if '-' in line_range:
                    start_line, end_line = map(int, line_range.split('-'))
                else:
                    start_line = end_line = int(line_range)
                # Construct file path from class name (package to path)
                class_path = class_name.replace('.', os.sep) + ".java"
                java_file_path = find_source_file_with_find("projects", slug, class_path)
                print("Resolved:", java_file_path)

                
                print("slug, commit, module, test, class_name, method_name, descriptor, line_range=",slug, commit, module, test, class_name, method_name, descriptor, line_range, start_line, end_line, class_path)
                #"projects"+slug+module+
                candidates = [str(java_file_path)]   # list of one or more paths

                # Read original file content to restore later
                with open(java_file_path, 'r') as source_file:
                    original_lines = source_file.readlines()

                    # Iterate through each line inside the method body (exclude signature and closing brace)
                    for line_no in range(start_line + 1, end_line):
                        # Get the exact code line from original content for verification
                        code_line = original_lines[line_no - 1]
                        print(code_line)
                        print(line_no)
                        # Inject sleep before this line
                        inject_sleep_before_line(candidates, line_no, method_name, descriptor, code_line)
                        exit()

