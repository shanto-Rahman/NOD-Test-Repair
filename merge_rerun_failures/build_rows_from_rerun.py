#!/usr/bin/env python3
"""
Turn a rerun batch produced by tdrepro/re-run_baseline.sh (or the 10K-style
baseline reruns, e.g. missing_reruns/<id>/) into rows that match the schema
of Results/merged_failures.csv:

    ID,slug,sha,module,test_name,run_id,stacktrace_md5,stacktrace

Input is a single directory containing:
    <input_dir>/rerun-logs/{id}-{test_name}-{run_idx}.txt   raw `mvn test` logs
    <input_dir>/result.csv  (or Re-run-Baseline-Result.csv)  Project-Name,SHA,Module,Test-Name,Failure-Found,Time

`Failure-Found` is a ';'-separated list of per-run failure counts; position i
(1-indexed) corresponds to the log file whose filename ends in "-{i}.txt".
Only positions with a count >= 1 produce an output row.

The "stacktrace" field is built the same way the existing rows in
merged_failures.csv are: the raw log from the "Running <TestClass>" line to
the end of the file, ANSI color codes stripped, newlines removed (matches the
flattened, single-line style already present in merged_failures.csv).

Usage:
    python3 build_rows_from_rerun.py <input_dir> [-o output.csv] [--dedup-against ../Results/merged_failures.csv]

    # e.g.
    python3 build_rows_from_rerun.py ../missing_reruns/13 -o new_rows_13.csv \
        --dedup-against ../Results/merged_failures.csv

    # then append the new rows to the real file:
    tail -n +2 new_rows_13.csv >> ../Results/merged_failures.csv
"""
import argparse
import csv
import hashlib
import os
import re
import sys

# NOTE: tdrepro/get_stacktrace_from_mvn_log.py has the same md5 logic
# (get_md5_from_stacktrace), but importing that module pulls in pandas and
# sentence_transformers just for a hashlib.md5() call, and neither package is
# installed in this environment. Reimplemented inline to avoid that dependency.
def get_md5_from_stacktrace(stacktrace):
    return hashlib.md5(stacktrace.encode("utf-8")).hexdigest()


def normalize_stacktrace_text(stacktrace):
    """Replace volatile Maven timing lines so rerun logs hash consistently."""
    stacktrace = re.sub(r'(?m)Time elapsed: [0-9.]+ s', 'Time elapsed: X s', stacktrace)
    stacktrace = re.sub(r'(?m)^\[INFO\] Total time:.*$', '[INFO] Total time: X', stacktrace)
    stacktrace = re.sub(r'(?m)^\[INFO\] Finished at:.*$', '[INFO] Finished at: X', stacktrace)
    return stacktrace


LOG_FILENAME_RE = re.compile(r'^(\d+)-(.+)-(\d+)\.txt$')
RUNNING_RE = re.compile(r'Running\s')
ANSI_ESCAPE_RE = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

FIELDNAMES = ["ID", "slug", "sha", "module", "test_name", "run_id", "stacktrace_md5", "stacktrace"]

RESULT_CSV_CANDIDATES = ["result.csv", "Re-run-Baseline-Result.csv", "RQ2-Result.csv"]


def find_input_files(input_dir):
    logs_dir = os.path.join(input_dir, "rerun-logs")
    if not os.path.isdir(logs_dir):
        logs_dir = input_dir  # allow passing a dir of .txt logs directly

    result_csv = None
    for candidate in RESULT_CSV_CANDIDATES:
        p = os.path.join(input_dir, candidate)
        if os.path.isfile(p):
            result_csv = p
            break
    if result_csv is None:
        csvs = [f for f in os.listdir(input_dir) if f.endswith(".csv")]
        if len(csvs) == 1:
            result_csv = os.path.join(input_dir, csvs[0])

    if result_csv is None:
        raise SystemExit(f"[ERROR] could not find a result CSV in {input_dir} "
                          f"(looked for {RESULT_CSV_CANDIDATES} or a single *.csv)")
    if not os.path.isdir(logs_dir):
        raise SystemExit(f"[ERROR] could not find a rerun-logs directory under {input_dir}")

    return logs_dir, result_csv


def extract_flattened_block(log_path):
    """Reproduce the flattening seen in merged_failures.csv: everything from the
    'Running <TestClass>' line to EOF, ANSI codes stripped, '\\n' removed (not replaced)."""
    with open(log_path, encoding="utf-8", errors="replace") as f:
        text = f.read()

    text = ANSI_ESCAPE_RE.sub("", text)
    lines = text.splitlines(keepends=True)

    start_idx = None
    for i, line in enumerate(lines):
        if RUNNING_RE.search(line):
            start_idx = i
            break
    if start_idx is None:
        return None

    block = "".join(lines[start_idx:])
    block = normalize_stacktrace_text(block)
    return block.replace("\n", "")


def find_log_files(logs_dir, test_name):
    """Match files named '{id}-{test_name}-{run_idx}.txt' inside logs_dir."""
    matches = []
    for fname in os.listdir(logs_dir):
        m = LOG_FILENAME_RE.match(fname)
        if not m:
            continue
        test_id, fname_test_name, run_idx = m.groups()
        if fname_test_name == test_name:
            matches.append((test_id, int(run_idx), os.path.join(logs_dir, fname)))
    matches.sort(key=lambda x: x[1])
    return matches


def load_existing_keys(merged_failures_csv):
    """Stream merged_failures.csv and collect stacktrace_md5 values already present,
    so we don't emit duplicate rows."""
    existing = set()
    with open(merged_failures_csv, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) < 8:
                continue
            normalized = normalize_stacktrace_text(row[7].strip())
            existing.add(get_md5_from_stacktrace(normalized))
    return existing


def append_rows_to_csv(csv_path, rows):
    """Append CSV rows to an existing merged failures file, writing the header only if needed."""
    file_exists = os.path.isfile(csv_path)
    write_header = not file_exists or os.path.getsize(csv_path) == 0
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, quoting=csv.QUOTE_MINIMAL)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input_dir", help="dir containing rerun-logs/ and result.csv (e.g. missing_reruns/13)")
    ap.add_argument("-o", "--output", default="new_merged_failure_rows.csv", help="where to write the new rows (default: %(default)s)")
    ap.add_argument("--dedup-against", metavar="merged_failures2.csv",
                     help="skip rows whose stacktrace_md5 already exist in this CSV and append unique rows to it")
    args = ap.parse_args()

    logs_dir, result_csv = find_input_files(args.input_dir)
    print(f"[INFO] logs_dir={logs_dir}", file=sys.stderr)
    print(f"[INFO] result_csv={result_csv}", file=sys.stderr)

    existing_md5s = set()
    if args.dedup_against:
        print(f"[INFO] scanning {args.dedup_against} for existing stacktrace_md5 values...", file=sys.stderr)
        existing_md5s = load_existing_keys(args.dedup_against)
        print(f"[INFO] {len(existing_md5s)} existing rows loaded", file=sys.stderr)

    seen_md5s = set(existing_md5s)

    with open(result_csv, newline="", encoding="utf-8") as f:
        result_rows = list(csv.DictReader(f))

    out_rows = []
    for row in result_rows:
        slug = row["Project-Name"].strip()
        sha = row["SHA"].strip()
        module = row["Module"].strip()
        test_name = row["Test-Name"].strip()
        failure_flags = [x.strip() for x in row["Failure-Found"].split(";") if x.strip() != ""]

        log_matches = find_log_files(logs_dir, test_name)
        if not log_matches:
            print(f"[WARN] no log files found for test '{test_name}' in {logs_dir}", file=sys.stderr)
            continue

        test_id = log_matches[0][0]
        num_failed_runs = 0

        for _, run_idx, log_path in log_matches:
            if run_idx - 1 >= len(failure_flags):
                print(f"[WARN] no Failure-Found flag for run {run_idx} of '{test_name}'", file=sys.stderr)
                continue
            try:
                failed = int(failure_flags[run_idx - 1]) >= 1
            except ValueError:
                failed = False
            if not failed:
                continue
            num_failed_runs += 1

            block = extract_flattened_block(log_path)
            if not block or not block.strip():
                print(f"[WARN] could not extract a stacktrace block from {log_path}", file=sys.stderr)
                continue

            stacktrace_md5 = get_md5_from_stacktrace(block)

            if stacktrace_md5 in seen_md5s:
                print(f"[INFO] skipping duplicate stacktrace_md5={stacktrace_md5} for ID={test_id} run={run_idx}", file=sys.stderr)
                continue

            seen_md5s.add(stacktrace_md5)

            out_rows.append({
                "ID": test_id,
                "slug": slug,
                "sha": sha,
                "module": module,
                "test_name": test_name,
                "run_id": run_idx,
                "stacktrace_md5": stacktrace_md5,
                "stacktrace": block,
            })

        print(f"[INFO] {test_name}: {len(log_matches)} log(s), {num_failed_runs} failing run(s)", file=sys.stderr)

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(out_rows)

    if args.dedup_against and out_rows:
        append_rows_to_csv(args.dedup_against, out_rows)
        print(f"[INFO] appended {len(out_rows)} row(s) to {args.dedup_against}", file=sys.stderr)

    print(f"[INFO] wrote {len(out_rows)} row(s) to {args.output}", file=sys.stderr)
    if args.dedup_against:
        print(f"[INFO] dedup target was also updated in place: {args.dedup_against}", file=sys.stderr)
    else:
        print(f"[INFO] to append: tail -n +2 {args.output} >> <path to Results/merged_failures.csv>", file=sys.stderr)


if __name__ == "__main__":
    main()
