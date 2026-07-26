#from generating_reproducing_script import extract_block 
from get_similarity_score_stacktrace import semantic_similarity_score, sanitize_stacktrace
import sys
import re
import csv
def extract_block(path, test):
    test_class = test.rsplit('.', 1)[0]
    start_re = re.compile(fr"Running {test_class}")
    end_re   = re.compile(r"There are test failures")
    drop_re  = re.compile(r'^\s*at\s+(org\.junit|org\.apache\.maven\.surefire|java.base)')
    buf = []

    in_block = False

    with open(path) as f:
        for line in f:
            if not in_block and start_re.search(line):
                in_block = True
            if in_block:
                if end_re.search(line):
                    break
                if drop_re.match(line):
                    continue

                buf.append(line.rstrip("\n"))
                # print(line, end="")

    # if the stacktrace contains "Time elapsed: __ s(ec)" then remove that part
    #buf = [line for line in buf if not re.search(r'Time elapsed: \d+\.\d+ s', line)] #we just want to remove the part from line, not the whole line
    buf = [re.sub(r'Time\s+elapsed:?\s*\d+(?:\.\d+)?\s*(?:s|sec)\b', '', line) for line in buf]


    # # also remove the "Total time:  11.854 s" and "Finished at: 2024-01-30T16:00:00" from the stacktrace
    buf = [re.sub(r'Total time: \s+\d+\.\d+ s', '', line) for line in buf]
    buf = [re.sub(r'Finished at:\s*\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+-]\d{2}:\d{2})?', '', line) for line in buf]

    return buf
def save_log_into_a_file(filtered_fail_log_txt):
    #print("HI ***")
    fail_log_csv="tmp-rq2-log.csv"
    cleaned_fail_log = [line for line in filtered_fail_log_txt if line.strip()]

    # 2) drop lines that are just “[INFO]” (with optional spaces)
    info_only = re.compile(r'^\[INFO\]\s*$')
    cleaned_fail_log = [line for line in cleaned_fail_log if not info_only.match(line)]
    #print("fail cleaned=", cleaned_fail_log)

    #big_block = "\n".join(filtered_fail_log_txt)
    big_block_fail_log = "\n".join(cleaned_fail_log)

    with open(fail_log_csv, "w", newline="") as fw:
        writer = csv.writer(fw,
                        delimiter=",",
                        quoting=csv.QUOTE_MINIMAL)      # wrap everything in quotes
        writer.writerow(["Failure"])
        writer.writerow([big_block_fail_log]) 

def read_panda(baseline_csv, mvn_test_log_csv):
    import pandas as pd
    # Read the CSV file
    df_baseline = pd.read_csv(baseline_csv)
    baseline_failures = df_baseline['Failure'].dropna().tolist()

    df_mvn_test_log = pd.read_csv(mvn_test_log_csv)
    
    # Display only the failure message (excluding the header)
    return baseline_failures, df_mvn_test_log['Failure'][0]

if __name__ == "__main__":
    _, baseline_log, maven_test_run_log_full, test_name = sys.argv
    #print("((((-====",_, baseline_log, maven_test_run_log_full, test_name)
    mvn_fail_log_by_this_script = extract_block(maven_test_run_log_full, test_name)
    save_log_into_a_file(mvn_fail_log_by_this_script)

    #tmp-rq2-log.csv baseline_log
    baseline_failures, mvn_log_now = read_panda(baseline_log, "tmp-rq2-log.csv")
    print(f"Found {len(baseline_failures)} baseline failure(s) to check against.")

    mvn_log_now = sanitize_stacktrace(mvn_log_now)
    
    matched = False
    for idx, baseline in enumerate(baseline_failures):
        print(f"--- Checking baseline failure #{idx + 1} ---")
        baseline = sanitize_stacktrace(baseline)
        print("baseline_log=", baseline)

        score = semantic_similarity_score(baseline, mvn_log_now)
        print("score=", score)

        if score >= 0.9:
            print(f"Matched (against baseline failure #{idx + 1})")
            matched = True
            break  # stop at the first match; remove this if you want to check all and report every match

    if not matched:
        print("MisMatched (no baseline failure matched)")

    '''print("mvn_log=", mvn_log_now)
    print("baseline_log= ", baseline)
    score = semantic_similarity_score(baseline, mvn_log_now)
    print("score=", score)
    if score >= 0.9:
        print("Matched")
    else:
        print("MisMatched")'''
