import csv
import re
import sys
from tree_sitter_languages import get_language
from collections import defaultdict, deque
from tree_sitter import Language, Parser

if len(sys.argv) != 6:
    print("Usage: python depth_labeler.py "
          "   <test_source.java> <test_method_name> "
          "<executed_methods.csv> <static_call_graph.csv> "
          "<output_with_depth.csv>")
    sys.exit(1)

test_src, test_method, executed_csv, callgraph_csv, out_csv = sys.argv[1:]

# --- 1) set up Tree-sitter for Java ---
# build once: Language.build_library('build/my-langs.so', ['path/to/tree-sitter-java'])
#JAVA = Language('build/my-langs.so', 'java')
#parser = Parser()
#parser.set_language(JAVA)

# Set up parser
JAVA_LANGUAGE = get_language("java")
parser = Parser()
parser.set_language(JAVA_LANGUAGE)

# --- 2) find the test method node and extract direct invocations ---
def find_method_node(node, name):
    if node.type == 'method_declaration':
        ident = node.child_by_field_name('name')
        if ident and ident.text.decode() == name:
            return node
    for c in node.children:
        found = find_method_node(c, name)
        if found:
            return found
    return None

def extract_invocations(node):
    invs = set()
    # look for method_invocation nodes
    if node.type == 'method_invocation':
        obj = node.child_by_field_name('object')
        m   = node.child_by_field_name('name')
        if m:
            if obj:
                invs.add(f"{obj.text.decode()}.{m.text.decode()}")
            else:
                invs.add(m.text.decode())
    for c in node.children:
        invs |= extract_invocations(c)
    return invs

# parse and extract
with open(test_src, 'rb') as f:
    tree = parser.parse(f.read())
root = tree.root_node
test_node = find_method_node(root, test_method)
if not test_node:
    raise RuntimeError(f"Test method {test_method} not found in {test_src}")
direct_invs = extract_invocations(test_node)
print("Direct invocations found in test:", direct_invs)

# --- 3) load executed methods and build a set of FQNs ---
executed = set()
with open(executed_csv) as f:
    dr = csv.DictReader(f)
    for r in dr:
        fq = f"{r['Class']}.{r['Method']}"
        executed.add(fq)

# --- 4) load static call graph edges into graph[caller]→[callee,...] ---
graph = defaultdict(list)
with open(callgraph_csv) as f:
    dr = csv.DictReader(f)
    for r in dr:
        graph[r['caller']].append(r['callee'])

# --- 5) initialize depths: any direct invocation that matches an executed FQN → depth 0
depth = {}
for inv in direct_invs:
    # inv might be unqualified; match by suffix
    for fq in executed:
        if fq.endswith(f".{inv}"):
            depth[fq] = 0

# --- 6) BFS up the graph to assign depth+1 to callees ---
queue = deque(depth.keys())
while queue:
    caller = queue.popleft()
    d = depth[caller]
    for callee in graph.get(caller, []):
        if callee in executed:
            if callee not in depth or depth[callee] > d + 1:
                depth[callee] = d + 1
                queue.append(callee)

# --- 7) write out the new CSV with an added depth_level column ---
with open(executed_csv) as fin, open(out_csv, 'w', newline='') as fout:
    reader = csv.DictReader(fin)
    fieldnames = reader.fieldnames + ['depth_level']
    writer = csv.DictWriter(fout, fieldnames=fieldnames)
    writer.writeheader()
    for row in reader:
        fq = f"{row['Class']}.{row['Method']}"
        row['depth_level'] = depth.get(fq, '')
        writer.writerow(row)

print(f"Wrote depths into {out_csv}")

