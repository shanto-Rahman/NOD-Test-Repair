from collections import deque
import os
from tree_sitter import Language, Parser
import sys
import csv
# Set up parser
from tree_sitter_languages import get_language
JAVA_LANGUAGE = get_language("java")
parser = Parser()
parser.set_language(JAVA_LANGUAGE)


# ——————————————————————————————————————————————————————————————————————————————
#  Helpers: AST traversal, invocation collection, method lookup
# ——————————————————————————————————————————————————————————————————————————————
def iterate(node):
    yield node
    for c in node.children:
        yield from iterate(c)

def find_method_node(root, name):
    """Find the first method_declaration whose name matches."""
    for n in iterate(root):
        if n.type == "method_declaration":
            nm = n.child_by_field_name("name")
            if nm and nm.text.decode() == name:
                return n
    return None

def collect_invocations(body_node):
    """Collect all simple method_invocation names under a block."""
    calls = set()
    for n in iterate(body_node):
        if n.type == "method_invocation":
            nm = n.child_by_field_name("name")
            if nm:
                calls.add(nm.text.decode())
    return calls

# ——————————————————————————————————————————————————————————————————————————————
#  Load executed_methods.csv into a set and map Method → Class (slash-notation)
# ——————————————————————————————————————————————————————————————————————————————
def load_executed(csv_path):
    executed = set()
    method_to_class = {}
    with open(csv_path, newline='') as f:
        r = csv.DictReader(f)
        for row in r:
            m = row["Method"]
            executed.add(m)
            # convert dot → slash so we can locate its .java
            cls = row["Class"].replace('.', '/')
            method_to_class[m] = cls
    return executed, method_to_class

# ——————————————————————————————————————————————————————————————————————————————
#  For a code-under-test method, parse its .java (based on class→file under src_root)
# ——————————————————————————————————————————————————————————————————————————————
def load_under_test_method_body(src_root, class_path, method_name):
    """
    class_path: e.g. 'org/java_websocket/client/WebSocketClient'
    method_name: 'connectBlocking'
    Returns its AST block node or None.
    """
    file_path = os.path.join(src_root, class_path + ".java")
    if not os.path.isfile(file_path):
        return None
    src = open(file_path, encoding='utf8').read()
    tree = parser.parse(src.encode())
    root = tree.root_node
    mnode = find_method_node(root, method_name)
    if not mnode:
        return None
    return next((c for c in mnode.children if c.type == "block"), None)

# ——————————————————————————————————————————————————————————————————————————————
#  Main: BFS up to depth 10
# ——————————————————————————————————————————————————————————————————————————————
if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: recurse_calls.py "
              "<Test.java> <testMethod> <executed_methods.csv> "
              "<src_root> <output.csv>")
        sys.exit(1)

    test_file, test_meth, executed_csv, src_root, out_csv = sys.argv[1:]
    executed, method_to_class = load_executed(executed_csv)

    # Parse the test class
    test_src = open(test_file, encoding='utf8').read()
    test_root = parser.parse(test_src.encode()).root_node
    test_node = find_method_node(test_root, test_meth)
    if not test_node:
        print(f"❌ Could not find method `{test_meth}` in {test_file}")
        sys.exit(1)

    # Seed: direct calls in test → depth 0
    test_block = next((c for c in test_node.children if c.type == "block"), None)
    seed_calls = collect_invocations(test_block) if test_block else set()

    # BFS queue: (method_name, depth, source), source is "test" or "code"
    q = deque()
    depths = {}
    for m in seed_calls:
        depths[m] = 0
        q.append((m, 0, "test"))

    # Explore up to depth 10
    while q:
        meth, d, src = q.popleft()
        if d >= 10:
            continue

        # Find its body
        if src == "test":
            node = find_method_node(test_root, meth)
            body = next((c for c in node.children if c.type=="block"), None) if node else None
        else:
            cls = method_to_class.get(meth)
            body = load_under_test_method_body(src_root, cls, meth)

        if not body:
            continue

        # For each invocation inside
        for cal in collect_invocations(body):
            if cal in depths:
                continue
            # only keep it if we can find its definition
            in_test = find_method_node(test_root, cal) is not None
            in_code = cal in executed
            if not (in_test or in_code):
                continue

            depths[cal] = d + 1
            next_src = "test" if in_test else "code"
            q.append((cal, d + 1, next_src))

    # Write out
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Method","Depth"])
        for m, depth in sorted(depths.items(), key=lambda kv: kv[1]):
            w.writerow([m, depth])

    print(f"Wrote depths for {len(depths)} methods to {out_csv}")
