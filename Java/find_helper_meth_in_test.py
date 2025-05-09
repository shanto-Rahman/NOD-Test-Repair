import sys
from collections import defaultdict, deque

from collections import deque, defaultdict
import re

# Step 1: Parse the callgraph lines into caller → [callees]
edges = defaultdict(list)
with open("method_calls.txt") as f:
    for line in f:
        if line.startswith("M:"):
            match = re.match(r"M:(.+?)\s+\(\w\)(.+)", line.strip())
            if match:
                caller, callee = match.groups()
                edges[caller].append(callee)

# Step 2: BFS traversal starting from your test method
start_method = "org.java_websocket.issues.Issue580Test:runNoCloseBlockingTestScenario2()"
visited = set()
queue = deque([(start_method, 0)])
max_depth = 20
depth_map = defaultdict(list)

while queue:
    current, depth = queue.popleft()
    if current in visited or depth > max_depth:
        continue
    visited.add(current)
    depth_map[depth].append(current)
    for callee in edges.get(current, []):
        queue.append((callee, depth + 1))

# Step 3: Print output
print(f"Call graph from '{start_method}' (up to depth {max_depth}):")
for d in sorted(depth_map):
    print(f"\nDepth {d}:")
    for meth in depth_map[d]:
        print(f"  {meth}")
