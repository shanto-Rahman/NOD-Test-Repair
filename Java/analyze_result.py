import re
import numpy as np
import pandas as pd
import re
import numpy as np
import pandas as pd
import sys

csv_path = sys.argv[1] #"results/gpt_result_idoft.csv"
MAX_CALLS = 5           # total GPT calls attempted when decision == "10"
K = 10                  # suggestions per GPT call
SENTINEL = "10"         # means: no success after all attempts

# Adjust these if your file has headers; here we assume 7 columns like your sample
cols = ["repo","commit","module","test","location","decision","time_sec"]
df = pd.read_csv(csv_path, header=None, names=cols)

# Parse decision column -> success, call_idx (0-based), suggestion_idx (1..K)
def parse_decision(x: str):
    x = str(x).strip()
    if x == SENTINEL:
        return {"success": False, "call_idx": np.nan, "suggestion_idx": np.nan}
    m = re.match(r"^(\d+)_(\d+)$", x)
    if m:
        return {
            "success": True,
            "call_idx": int(m.group(1)),       # 0-based call index
            "suggestion_idx": int(m.group(2))  # 1..K suggestion index
        }
    # Unknown token -> treat as failure
    return {"success": False, "call_idx": np.nan, "suggestion_idx": np.nan}

parsed = df["decision"].apply(parse_decision).apply(pd.Series)
df = pd.concat([df, parsed], axis=1)

# Ensure numeric (NaNs for failures/unknowns)
df["call_idx"] = pd.to_numeric(df["call_idx"], errors="coerce")
df["suggestion_idx"] = pd.to_numeric(df["suggestion_idx"], errors="coerce")

# Derive metrics with masking -> fill -> cast (prevents NaN->int errors)
calls_success = df["call_idx"] + 1
runs_success  = df["call_idx"] * K + df["suggestion_idx"]

df["gpt_calls_used"] = calls_success.where(df["success"]).fillna(MAX_CALLS).astype(int)
df["test_runs_until_failure"] = runs_success.where(df["success"]).fillna(MAX_CALLS * K).astype(int)

# Summary
n = len(df)
n_success = int(df["success"].sum())
n_fail = n - n_success
success_rate = (n_success / n * 100) if n else float("nan")

print(f"Total tests: {n}")
print(f"Successes: {n_success} ({success_rate:.1f}%)  |  Failures: {n_fail} ({100 - success_rate:.1f}%)")

# Averages (overall, counting failures as max attempts)
print(f"\nAverage GPT calls used (overall): {df['gpt_calls_used'].mean():.2f}")
print(f"Average test runs until failure (overall): {df['test_runs_until_failure'].mean():.2f}")

# Success-only stats
succ = df[df["success"]]
if not succ.empty:
    print("\nSuccess-only:")
    print(f"  Average GPT calls used: {succ['gpt_calls_used'].mean():.2f}")
    print(f"  Median GPT calls used:  {succ['gpt_calls_used'].median():.2f}")
    print(f"  Average runs until failure: {succ['test_runs_until_failure'].mean():.2f}")
    print(f"  Median runs until failure:  {succ['test_runs_until_failure'].median():.2f}")


