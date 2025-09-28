import csv
import os
import subprocess
from pathlib import Path
from typing import Optional
from modify_java_file import inject_sleep_before_line
import re
import time

#def has_errors_or_failures(path):
#    with open(path, 'r') as f:
#        text = f.read()
#    return 'Errors: 1' in text or 'Failures: 1' in text

def has_errors_or_failures(path):
    with open(path, 'r') as f:
        text = f.read()
    # Match 'Errors: N' or 'Failures: N' where N > 0
    errors = re.search(r'Errors:\s*[1-9][0-9]*', text)
    failures = re.search(r'Failures:\s*[1-9][0-9]*', text)
    return errors is not None or failures is not None

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
            print(f"Multiple files named {fname}; consider using package path to disambiguate.")
        return hits[0]

    print(f"No file found for {class_path} under {base}")
    return None

# Configuration: path to the CSV data file
#csv_file = 'metadata/embedings/org.java_websocket.issues.Issue580Test.runNoCloseBlockingTestScenario2_bigbird_embeddings.csv'  # Update this to the actual CSV filename/path
# Variables for the test run command (ensure these are set to real values as needed)
#slug = "your-project-slug"        # e.g., "org.java-websocket/Java-WebSocket"
#module = "your-module-path"       # e.g., "" (if root project) or "module-name"
#test  = "your.test.ClassName#testMethod"  # e.g., a specific test to run
retry_count = 0
run_id = 0

input_csv="../data/all_82_tests.csv"
model_name = "qwen"
output_csv = "results/output_found_failures_"+model_name+"_embedding.csv"
output_fields = ["slug", "module", "test", "row_id", "line_number", "log_file", "class_name", "method_name", "total_time_seconds", "iteration_count"]

with open(input_csv, newline='') as inf:
    reader = csv.DictReader(inf)
    for row in reader:
        failure_count = 0
        iteration_count = 0
        start_time = time.time()
        id = row['id']
        slug = row['slug']
        commit = row['commit']
        module = row['module']
        test = row['test']
        row_count = 0
        test_with_dot = test.replace("#", ".")
        csv_file = "metadata/embedings/"
        csv_file = csv_file + test_with_dot +"_"+model_name+ "_embeddings.csv"
        # Open and read the CSV data
        with open(csv_file, newline='') as f:  #ranked_method_list
            reader = csv.DictReader(f)
            #for row in reader:
            for row_id, row in enumerate(reader):
                if row_count > 10:
                    continue
                row_count +=1
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
                if java_file_path is None or not os.path.exists(java_file_path):
                    print(f"Java file not found for {class_path}, skipping...", flush=True)
                    continue
                
                print("slug, commit, module, test, class_name, method_name, descriptor, line_range=",slug, commit, module, test, class_name, method_name, descriptor, line_range, start_line, end_line, class_path)
                #"projects"+slug+module+
                candidates = [str(java_file_path)]   # list of one or more paths

                # Read original file content to restore later
                with open(java_file_path, 'r') as source_file:
                    original_lines = source_file.readlines()

                    # Iterate through each line inside the method body (exclude signature and closing brace)
                    #for line_no in range(start_line + 1, end_line):
                    for idx, line_no in enumerate(range(start_line + 1, end_line)):
                        iteration_count += 1
                        # Get the exact code line from original content for verification
                        print("line_no - 1=", line_no - 1)
                        code_line = original_lines[line_no - 1]
                        print(code_line)
                        print(line_no)
                        # Inject sleep before this line
                        inject_sleep_before_line(candidates, line_no, method_name, descriptor, code_line)
                        #exit()
                        try:
                            print("About to run run_test.sh", flush=True)
                            result_run = subprocess.run([
                                "./run_test.sh", slug, module, test_with_dot, str(retry_count) + "_" + str(idx) + "_" + str(run_id)
                            ], text=True, capture_output=True, timeout=1400)
                            #print("Finished run_test.sh", flush=True)
                            #print("--- STDOUT ---", flush=True)
                            #print(result_run.stdout, flush=True)
                            #print("--- STDERR ---", flush=True)
                            #print(result_run.stderr, flush=True)
                            #print("HI I AM HERE", flush=True)
                            out = result_run.stdout.strip()
                            #print("***out****", out, flush=True)
                            #if out:
                            #    firstLine = out.splitlines()[0]
                            #else:
                            #    firstLine = ""
                            #if firstLine == "Failure found.":
                            #    print("***Failure found.", flush=True)
                            #else:
                            #    print("***Output:", out, flush=True)
                            # Also check the log file for Maven errors/failures
                            currentDir_when_exception_occurs = os.getcwd()
                            before, after = test_with_dot.rsplit('.', 1)
                            test_with_hash = f"{before}#{after}"
                            log_file = currentDir_when_exception_occurs+"/logs-to-reproduce/"+test_with_hash+"-con-after-changedCode-"+str(retry_count) +"_" +str(idx)+ "_" + str(run_id)+".txt"
                            print("Checking log file:", log_file, flush=True)
                            if has_errors_or_failures(log_file):
                                print("Found Errors: 1 or Failures: 1", flush=True)
                                failure_count += 1
                                total_time_seconds = time.time() - start_time
                                # Save to output CSV
                                with open(output_csv, "a", newline='') as outf:
                                    writer = csv.DictWriter(outf, fieldnames=output_fields)
                                    if outf.tell() == 0:
                                        writer.writeheader()
                                    writer.writerow({
                                        "slug": slug,
                                        "module": module,
                                        "test": test,
                                        "row_id": row_id,
                                        "line_number": line_no,
                                        "log_file": log_file,
                                        "class_name": class_name,
                                        "method_name": method_name,
                                        "total_time_seconds": round(total_time_seconds, 2),
                                        "iteration_count": iteration_count
                                    })
                                    break
                            else:
                                print("No Errors: 1 or Failures: 1", flush=True)
                            #exit()
                        except subprocess.TimeoutExpired:
                            print("run_test.sh timed out!", flush=True)
                            exit()
                        except Exception as e:
                            print("run_test.sh failed with exception:", e, flush=True)
                            print("--- STDOUT ---", flush=True)
                            print(result_run.stdout if 'result_run' in locals() else '', flush=True)
                            print("--- STDERR ---", flush=True)
                            print(result_run.stderr if 'result_run' in locals() else '', flush=True)
                            exit()
                if failure_count > 0:
                    break
            #exit()

