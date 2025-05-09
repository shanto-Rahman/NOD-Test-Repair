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

#def build_call_graph(callgraph_lines):
#    graph = defaultdict(set)
##    for line in callgraph_lines:
#        if not line.startswith("M:"):
#            continue
#        line = line[2:].strip()
##        if ')' not in line or '(' not in line:
#            continue
#        caller, rest = line.split(')', 1)
#        rest = rest.strip()
#        if not rest or ':' not in rest:
#            continue
#        # Remove tag like (M), (O), etc.
#        callee = rest.split(')', 1)[-1].strip()
#        graph[caller.strip()].add(callee)
#    return graph
#
#def bfs_traversal(graph, start_method, max_depth=10):
#    visited = set()
#    queue = deque([(start_method, 0)])
#    depth_map = defaultdict(list)
#
#    while queue:
#        current, depth = queue.popleft()
#        if depth > max_depth or current in visited:
#            continue
#        visited.add(current)
#        depth_map[depth].append(current)
#        for callee in graph.get(current, []):
#            queue.append((callee, depth + 1))
#
#    return depth_map
#
#if __name__ == "__main__":
#    if len(sys.argv) != 3:
#        print("Usage: python bfs_call_graph.py <callgraph.txt> <starting_method>")
#        sys.exit(1)
#
#    callgraph_file = sys.argv[1]
#    start_method = sys.argv[2]
#
#    with open(callgraph_file, "r") as f:
#        lines = f.readlines()
#
#    graph = build_call_graph(lines)
#    result = bfs_traversal(graph, start_method)
#
#    print(f"\nCall graph from '{start_method}' (up to depth 10):\n")
#    for depth in sorted(result.keys()):
#        print(f"Depth {depth}:")
#        for method in sorted(result[depth]):
#            print(f"  {method}")
#
#
#import sys
#import re
#from tree_sitter import Language, Parser

# Load Java grammar
#Language.build_library(
#    'build/my-languages.so',
#    ['tree-sitter-java']
#)
#JAVA_LANGUAGE = Language('build/my-languages.so', 'java')
#import sys
#from collections import defaultdict, deque
##
#def parse_callgraph(file_path):
#    call_map = defaultdict(set)
#    with open(file_path, 'r') as f:
#        for line in f:
#            if not line.startswith("M:"):
#                continue
#            parts = line.strip()[2:].split(" ", 1)
#            if len(parts) != 2:
#                continue
#            caller, callee = parts
#            # Remove (O), (M), etc.
#            callee = callee.strip()
#            if callee.startswith(('(O)', '(M)', '(S)', '(I)', '(D)')):
#                callee = callee[3:]
#            call_map[caller].add(callee)
#    return call_map
#
#def dfs_calls(start, call_map):
#    visited = set()
#    stack = [start]
#    while stack:
#        current = stack.pop()
#        if current not in visited:
#            visited.add(current)
#            stack.extend(call_map.get(current, []))
#    return visited
#
#if __name__ == "__main__":
#    if len(sys.argv) != 3:
#        print("Usage: python extract_test_calls.py <callgraph.txt> <testMethod>")
#        sys.exit(1)
#
#    callgraph_file = sys.argv[1]
#    test_method = sys.argv[2]  # e.g., org.java_websocket.issues.Issue580Test:runNoCloseBlockingTestScenario2
#
#    call_map = parse_callgraph(callgraph_file)
#    reachable = dfs_calls(test_method, call_map)
#
#    print(f"Call graph starting from {test_method}:\n")
#    for callee in sorted(reachable):
#        print(callee)
#
#
##from collections import deque
##import os
###from tree_sitter import Language, Parser
##import sys
##import csv
### Set up parser
##from tree_sitter_languages import get_language
##JAVA_LANGUAGE = get_language("java")
##parser = Parser()
##parser.set_language(JAVA_LANGUAGE)
##
###parser = Parser()
###parser.set_language(JAVA_LANGUAGE)
##
##import sys
##from collections import defaultdict, deque
##
##def parse_call_graph(file_path):
##    call_graph = defaultdict(set)
##    method_lines = []
##
##    with open(file_path, "r") as f:
##        for line in f:
##            if line.startswith("M:"):
##                method_lines.append(line.strip()[2:])
##
##    for line in method_lines:
##        parts = line.split(" ")
##        if len(parts) < 2:
##            continue
##        caller = parts[0]
##        callee = parts[1].split(":")[1] if ":" in parts[1] else parts[1]
##        call_graph[caller].add(parts[1])
##
##    return call_graph
##
##def collect_reachable_calls(call_graph, entry_point):
##    visited = set()
##    queue = deque([entry_point])
##    result = set()
##
##    while queue:
##        current = queue.popleft()
##        if current in visited:
##            continue
##        visited.add(current)
##        result.add(current)
##        for callee in call_graph.get(current, []):
##            if callee not in visited:
##                queue.append(callee)
##
##    return result
##
##if __name__ == "__main__":
##    if len(sys.argv) != 3:
##        print("Usage: python extract_calls.py <callgraph.txt> <TestClass:testMethod>")
##        sys.exit(1)
##
##    callgraph_file = sys.argv[1]
##    entry = sys.argv[2]
##
##    call_graph = parse_call_graph(callgraph_file)
##    reachable = collect_reachable_calls(call_graph, entry)
##
##    print(f"Call graph starting from {entry}:\n")
##    for method in sorted(reachable):
##        print(method)
##
##
