import sys
import pandas as pd
import csv
import os

def main():
    # "$slug_org" "$sha" "$module_org" "$testName" "$file_reproducing_script"
    if len(sys.argv) != 6:
        print("Usage: python find_reproducing_script.py <slug> <sha> <module_org> <testName> <fail_log_filename>")
        sys.exit(1)

    _, slug, sha, module_org, testName, reproduction_script_filename = sys.argv

    result_csv = "/home/tbaral/research/llm_flaky_tests/NOD-Test-Repair/Java/results/gpt.csv"

    # CSV format (NO HEADER ROW):
    # slug, sha, module, test_name, reproduction_script, cot_count, time_taken
    # column_names = [
    #     "#proj_name",
    #     "sha",
    #     "module",
    #     "test_name",
    #     "reproduction_script",
    #     "cot_count",
    #     "time_taken",
    # ]

    # Read CSV with provided header names
    df = pd.read_csv(result_csv)

    # Remove leading "#" from slug column, if present
    # df["slug"] = df["slug"].astype(str).str.lstrip("#")
    # replace # in test_name by .
    testName = testName.replace("#", ".")

    # Match
    # #proj_name,sha,module,test_name,changed_code_to_get_fail,file,method,line_range,cot_count,total_time
    matched_rows = df[
        (df["#proj_name"] == slug)
        & (df["sha"] == sha)
        & (df["module"] == module_org)
        & (df["test_name"] == testName)
    ]

    if matched_rows.empty:
        print(f"No matching row found for slug={slug}, sha={sha}, module={module_org}, test_name={testName}")
        sys.exit(1)

    # Extract reproduction script text
    reproduction_script = matched_rows.iloc[0]["changed_code_to_get_fail"]

    # Create directory if needed
    out_dir = os.path.dirname(reproduction_script_filename)
    if out_dir != "":
        os.makedirs(out_dir, exist_ok=True)

    # Write file
    with open(reproduction_script_filename, "w") as f:
        f.write(reproduction_script)

    print(f"Reproduction script written to {reproduction_script_filename}")


if __name__ == "__main__":
    main()
    sys.exit(0)
