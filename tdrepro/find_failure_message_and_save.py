import sys
import pandas as pd
import csv

def main():
    if len(sys.argv) != 9:
        print("Usage: python extract_failure_log.py <id> <slug> <sha> <module_org> <testName> <fail_log_filename> module_with_dot, proj_name_only")
        sys.exit(1)

    _, id_arg, slug, sha, module_org, testName, fail_log_filename, module_with_dot, proj_name_only = sys.argv

    # Output file: save to <id>_stacktrace.txt
    if module_with_dot == ".":
        print("proj_name_only=", proj_name_only)
        output_csv = f"logs/{id_arg}_{proj_name_only}_{testName}_stacktrace.csv"
    else:
        output_csv = f"logs/{id_arg}_{module_with_dot}_{testName}_stacktrace.csv"

    print("output_csv=", output_csv)
    print("fail_log_filename=", fail_log_filename)
    # Load the CSV
    try:
        df = pd.read_csv(fail_log_filename)
        #print("df=", df)
    except Exception as e:
        print(f"[ERROR] Failed to load CSV: {e}")
        sys.exit(1)

    # Check required columns
    required_cols = ['slug', 'sha', 'module', 'test_name', 'stacktrace']
    for col in required_cols:
        if col not in df.columns:
            print(f"[ERROR] Required column '{col}' not found in CSV.")
            sys.exit(1)

    # Filter rows
    matched_rows = df[
        (df['slug'] == slug) &
        (df['sha'] == sha) &
        (df['module'] == module_org) &
        (df['test_name'] == testName)
    ]
    print("id_arg, slug, sha, module_org, testName=", id_arg, slug, sha, module_org, testName)
    if matched_rows.empty:
        print("[INFO] No matching rows found.")
        return

    # Collect every non-empty stacktrace instead of stopping at the first one
    all_stacktraces = []
    for _, row in matched_rows.iterrows():
        stacktrace = row.get('stacktrace', '')
        if pd.notna(stacktrace) and stacktrace.strip():
            all_stacktraces.append(stacktrace.strip())

    if not all_stacktraces:
        print("[INFO] Matching rows found, but no non-empty stacktrace.")
        return

    with open(output_csv, "w", newline="") as fw:
        writer = csv.writer(fw, delimiter=",", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Failure"])
        for st in all_stacktraces:
            writer.writerow([st])
    
    print(f"[INFO] {len(all_stacktraces)} stacktrace(s) saved to {output_csv}")


if __name__ == "__main__":
    main()

