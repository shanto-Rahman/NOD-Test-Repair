import sys
import pandas as pd
import re
from collections import defaultdict

dyn_calltrace = sys.argv[1]
executed_method_bodies = sys.argv[2]
output_csv = sys.argv[3]

print(dyn_calltrace)
print(executed_method_bodies)
print(output_csv)

# Load executed methods CSV
executed_df = pd.read_csv(executed_method_bodies)

# Parse calltrace.txt
depth_map = defaultdict(list)
entry_pattern = re.compile(r'>\[(\d+)]\[\d+](.+?):(.+?)=')

with open(dyn_calltrace, "r") as f:
    for line in f:
        match = entry_pattern.match(line)
        if match:
            depth = int(match.group(1))
            class_name = match.group(2).strip()
            method_name = match.group(3).strip()
            depth_map[(class_name, method_name)].append(depth)

# Assign minimum depth to each row in the CSV
call_depths = []
for _, row in executed_df.iterrows():
    key = (row['Class'].strip(), row['Method'].strip())
    if key in depth_map:
        call_depths.append(min(depth_map[key]))
    else:
        call_depths.append(-1)  # Not found

executed_df["CallDepth"] = call_depths

# Save or display result
executed_df.to_csv(output_csv, index=False)
print("Saved to ", output_csv)

