
import pandas as pd
import re
from collections import defaultdict

# Load executed methods CSV
executed_df = pd.read_csv("traces/TooTallNate_Java-WebSocket_._org.java_websocket.issues.Issue580Test#runNoCloseBlockingTestScenario0_executed_method_bodies.csv")

# Parse calltrace.txt
depth_map = defaultdict(list)
entry_pattern = re.compile(r'>\[(\d+)]\[\d+](.+?):(.+?)=')

with open("projects/TooTallNate/Java-WebSocket/calltrace.txt", "r") as f:
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
executed_df.to_csv("executed_with_call_depth.csv", index=False)
print("Saved to executed_with_call_depth.csv")

