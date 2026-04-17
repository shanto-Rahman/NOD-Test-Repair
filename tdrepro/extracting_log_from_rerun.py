import csv
import sys
def get_stacktrace_csv(csv_path: str, slug: str, sha: str, module: str, test_name: str):
    """Return the FIRST stacktrace matching slug/sha/module/test_name (no run_id logic)."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            #print(row.get("slug", ""), row.get("sha", ""),  row.get("module", "").strip(), row.get("test_name", "").strip())
            #print(slug, sha, module, test_name)
            if (row.get("slug", "").strip() == slug and
                row.get("sha", "").strip() == sha and
                row.get("module", "").strip() == module and
                row.get("test_name", "").strip() == test_name):
                return row.get("stacktrace", "")
    return None

slug=sys.argv[1]
sha=sys.argv[2]
module=sys.argv[3]
test_name=sys.argv[4]
csv_path=sys.argv[5] #../Results/unique_failures_10K_reruns_181_unique_only.csv or ../Results/unique_failures_10K_reruns_flakerake_775.csv"

stack = get_stacktrace_csv(csv_path, slug, sha, module, test_name)
if not stack:
    print("No match")
    sys.exit(1)

# Write a 1-column CSV with header 'stacktrace'
with open("tmp.txt", "w", encoding="utf-8", newline="") as out:
    w = csv.writer(out)
    w.writerow(["Failure"])
    w.writerow([stack])

