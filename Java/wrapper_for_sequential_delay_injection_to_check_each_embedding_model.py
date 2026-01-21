import csv
import os
import subprocess
from pathlib import Path
from typing import Optional
from modify_java_file import inject_sleep_before_line
import re
import time
import sys

#def has_errors_or_failures(path):
#    with open(path, 'r') as f:
#        text = f.read()
#    return 'Errors: 1' in text or 'Failures: 1' in text
def save_result(output_csv, slug, module, test, row_id, line_number, actual_line, log_file, class_name, method_name, total_time_seconds, iteration_count):
    with open(output_csv, "a", newline='') as outf:
        writer = csv.DictWriter(outf, fieldnames=output_fields)
        if outf.tell() == 0:
            writer.writeheader()
        writer.writerow({
            "slug": slug,
            "module": module,
            "test": test,
            "method_id": row_id,
            "line_number": line_number,
            "actual_line": actual_line,
            "log_file": log_file,
            "class_name": class_name,
            "method_name": method_name,
            "total_time_seconds": round(total_time_seconds, 2),
            "iteration_count": iteration_count
        })
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

input_csv=sys.argv[3] #"../data/all_82_tests.csv"
#input_csv="../data/l.csv"
#input_csv="l"
model_name = "gpt2" #"llama" #"tf-idf"#"gpt2"
cosine_weight = sys.argv[2] #70_30
output_csv = "results/output_found_failures_"+model_name+"_"+cosine_weight+"_embedding.csv"
output_fields = ["slug", "module", "test", "method_id", "line_number", "actual_line", "log_file", "class_name", "method_name", "total_time_seconds", "iteration_count"]

def run_once(run_id, class_path_list, line_number, method_name, descriptor, code_line, slug, module, test, retry_count, idx):
    inject_sleep_before_line(class_path_list, line_number, method_name, descriptor, code_line)
    #exit()
    tag = f"{retry_count}_{idx}_{run_id}"
    try:
        print("./run_test.sh", slug, module, test, tag, cosine_weight)
        result_run = subprocess.run(
            ["./run_test.sh", slug, module, test, tag, cosine_weight],
            check=True, text=True, capture_output=True
        )
        out = result_run.stdout.strip()
        print("***out****", out)
        firstLine = out.splitlines()[0]  # "Failure not found." or "Failure found."
        return (firstLine == "Failure found.")
    except subprocess.CalledProcessError as e:
        print("run_test.sh failed with exit code", e.returncode)
        print("--- stdout ---"); print(e.stdout)
        print("--- stderr ---"); print(e.stderr)

        # Inspect produced log to decide if it was a failure
        currentDir_when_exception_occurs = os.getcwd()
        before, after = test.rsplit('.', 1)
        test_with_hash = f"{before}#{after}"
        log_file = (currentDir_when_exception_occurs + "/logs-to-reproduce/" +cosine_weight+"/"+
                    f"{test_with_hash}-con-after-changedCode-{tag}.txt")
        print("log file name=", log_file)
        if has_errors_or_failures(log_file):
            print("Found Errors: 1 or Failures: 1")
            return True
        else:
            print("No Errors: 1 or Failures: 1")
            return False

with open(input_csv, newline='') as inf:
    reader = csv.DictReader(inf)
    for test_info in reader: #For each test
        failure_count = 0
        iteration_count = 0
        start_time = time.time()
        id = test_info['id']
        slug = test_info['slug']
        commit = test_info['commit']
        module = test_info['module']
        test = test_info['test']
        method_count = 0
        test_with_dot = test.replace("#", ".")
        csv_file = sys.argv[1] #"metadata/embedings/"
        csv_file = csv_file + test_with_dot +"_"+model_name+ "_embeddings.csv"
        # Open and read the CSV data
        with open(csv_file, newline='') as f:  #ranked_method_list
            reader = csv.DictReader(f)
            #for row in reader:
            for ranked_meth_id, ranked_meth in enumerate(reader):
                if method_count > 10:
                    continue
                method_count +=1
                class_name = ranked_meth['Class']
                if '$' in class_name:
                    class_name = class_name.split('$', 1)[0]
                method_name = ranked_meth['Method']
                descriptor = ranked_meth['Descriptor']
                line_range = ranked_meth['LineRange']
                # Parse line range (e.g., "555-570")
                if '-' in line_range:
                    start_line, end_line = map(int, line_range.split('-'))
                else:
                    start_line = end_line = int(line_range)
                # Construct file path from class name (package to path)
                #Java file not found for tachyon/thrift/WorkerService$Client.java
                class_path = class_name.replace('.', os.sep) + ".java"
                java_file_path = find_source_file_with_find("projects", slug, class_path)
                print("Resolved:", java_file_path)
                if java_file_path is None or not os.path.exists(java_file_path):
                    print(f"Java file not found for {class_path}, skipping...", flush=True)
                    print("Failure_count=", failure_count)
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
                        failure_count = 0
                        iteration_count += 1
                        code_line = original_lines[line_no - 1]
                        print("**** code_line=", code_line)
                        currentDir_when_exception_occurs = os.getcwd()
                        os.makedirs(currentDir_when_exception_occurs+"/logs-to-reproduce/"+cosine_weight+"/", exist_ok=True)
                        first_failed = run_once(0, candidates, line_no, method_name, descriptor, code_line, slug, module, test_with_dot, retry_count, idx)

                        if not first_failed:
                            print("First run: no failure; skipping additional runs.")
                            print("Only 0/1 runs failed. Not considering as valid failure.")
                        else:
                           # First run failed → run 4 more times (total 5)
                            failure_count = 1
                            for run_id in range(1, 5):
                                if run_once(run_id, candidates, line_no, method_name, descriptor, code_line, slug, module, test_with_dot, retry_count, idx):
                                    failure_count += 1
                            if failure_count >=3:
                                before, after = test_with_dot.rsplit('.', 1)
                                test_with_hash = f"{before}#{after}"
                                print(f"Failure found in {failure_count}/5 runs.")
                                # currentDir_when_exception_occurs = os.getcwd()
                                log_file = currentDir_when_exception_occurs+"/logs-to-reproduce/"+cosine_weight+"/"+test_with_hash+"-con-after-changedCode-"+str(retry_count) +"_" +str(idx)+ "_" + str(run_id)+".txt"
                                total_time_seconds = time.time() - start_time
                                save_result(output_csv, slug, module, test_with_dot, ranked_meth_id, line_no, code_line, log_file, class_name, method_name, total_time_seconds, iteration_count)
                                break
                                #return line, f"{retry_count}_{idx}", "Failure found."
                            else:
                                print("Only {failure_count}/5 runs failed. Not considering as valid failure.")
                if failure_count >=3:
                    break
        if failure_count == 0:
            total_time_seconds = time.time() - start_time
            save_result(output_csv, slug, module, test, "no_test_failure", "NA", "NA", "NA", "NA", "NA", total_time_seconds, iteration_count)
            print("I AM HERE", output_csv, slug, module, test, "no_test_failure", "NA", "NA", "NA", "NA", "NA", total_time_seconds, iteration_count)
        
        #exit()        

