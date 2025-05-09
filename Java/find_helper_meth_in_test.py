import sys
from collections import defaultdict, deque

from collections import deque, defaultdict
import re

import re
from collections import defaultdict, deque

import re
import csv
from collections import defaultdict, deque

def parse_callgraph(filepath):
    edges = defaultdict(list)
    with open(filepath) as f:
        for line in f:
            if line.startswith("M:"):
                match = re.match(r"M:(.+?)\s+\(\w\)(.+)", line.strip())
                if match:
                    caller, callee = match.groups()
                    edges[caller].append(callee)
    return edges

def bfs_callgraph(edges, start_method, max_depth):
    visited = set()
    queue = deque([(start_method, 0)])
    depth_map = defaultdict(list)

    while queue:
        current, depth = queue.popleft()
        if current in visited or depth > max_depth:
            continue
        visited.add(current)
        depth_map[depth].append(current)
        for callee in edges.get(current, []):
            queue.append((callee, depth + 1))
    
    return depth_map

def write_callgraph_csv(depth_map, output_file):
    with open(output_file, mode="w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Depth", "Method"])
        for depth in sorted(depth_map):
            for method in depth_map[depth]:
                writer.writerow([depth, method])

if __name__ == "__main__":
    callgraph_file = "method_calls.txt"
    output_csv = "callgraph_depth_map.csv"
    start_method = "org.java_websocket.issues.Issue580Test:runNoCloseBlockingTestScenario2()"
    max_depth = 20

    edges = parse_callgraph(callgraph_file)
    depth_map = bfs_callgraph(edges, start_method, max_depth)
    write_callgraph_csv(depth_map, output_csv)
    print(f"Call graph written to {output_csv}")


#def parse_callgraph(filepath):
##    edges = defaultdict(list)
#    with open(filepath) as f:
#        for line in f:
#            if line.startswith("M:"):
#                match = re.match(r"M:(.+?)\s+\(\w\)(.+)", line.strip())
#                if match:
#                    caller, callee = match.groups()
#                    edges[caller].append(callee)
#    return edges
#
#def bfs_callgraph(edges, start_method, max_depth):
#    visited = set()
#    queue = deque([(start_method, 0)])
#    depth_map = defaultdict(list)
#
#    while queue:
#        current, depth = queue.popleft()
#        if current in visited or depth > max_depth:
#            continue
#        visited.add(current)
#        depth_map[depth].append(current)
#        for callee in edges.get(current, []):
#            queue.append((callee, depth + 1))
#    
#    return depth_map
#
#def print_callgraph(depth_map, start_method, max_depth):
#    print(f"Call graph from '{start_method}' (up to depth {max_depth}):")
#    for d in sorted(depth_map):
#        print(f"\nDepth {d}:")
#        for meth in depth_map[d]:
#            print(f"  {meth}")
#
#if __name__ == "__main__":
#    callgraph_file = "method_calls.txt"
#    start_method = "org.java_websocket.issues.Issue580Test:runNoCloseBlockingTestScenario2()"
#    max_depth = 20
#
#    edges = parse_callgraph(callgraph_file)
#    depth_map = bfs_callgraph(edges, start_method, max_depth)
#    print_callgraph(depth_map, start_method, max_depth)
#
### Step 1: Parse the callgraph lines into caller → [callees]
##edges = defaultdict(list)
##with open("method_calls.txt") as f:
##    for line in f:
##        if line.startswith("M:"):
##            match = re.match(r"M:(.+?)\s+\(\w\)(.+)", line.strip())
##            if match:
##                caller, callee = match.groups()
##                edges[caller].append(callee)
##
### Step 2: BFS traversal starting from your test method
##start_method = "org.java_websocket.issues.Issue580Test:runNoCloseBlockingTestScenario2()"
##visited = set()
##queue = deque([(start_method, 0)])
##max_depth = 20
##depth_map = defaultdict(list)
##
##while queue:
##    current, depth = queue.popleft()
##    if current in visited or depth > max_depth:
##        continue
##    visited.add(current)
##    depth_map[depth].append(current)
##    for callee in edges.get(current, []):
##        queue.append((callee, depth + 1))
##
### Step 3: Print output
##print(f"Call graph from '{start_method}' (up to depth {max_depth}):")
##for d in sorted(depth_map):
##    print(f"\nDepth {d}:")
##    for meth in depth_map[d]:
##        print(f"  {meth}")
