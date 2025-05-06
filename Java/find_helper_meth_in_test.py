from tree_sitter import Language, Parser
import sys
import csv
# Set up parser
from tree_sitter_languages import get_language
JAVA_LANGUAGE = get_language("java")
parser = Parser()
parser.set_language(JAVA_LANGUAGE)

def iterate(node):
    """Yield node and all its descendants in preorder."""
    yield node
    for c in node.children:
        yield from iterate(c)

def find_method(root, name):
    """Return the method_declaration whose .name == name, or None."""
    for n in iterate(root):
        if n.type == "method_declaration":
            nm = n.child_by_field_name("name")
            if nm and nm.text.decode() == name:
                return n
    return None

def collect_invocations(body_node):
    """Return a set of all method-invocation names under this block."""
    calls = set()
    for n in iterate(body_node):
        if n.type == "method_invocation":
            nm = n.child_by_field_name("name")
            if nm:
                calls.add(nm.text.decode())
    return calls

def load_executed_methods(csv_path):
    seen = set()
    with open(csv_path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            seen.add(row["Method"])
    return seen

# ——————————————————————————————————————————————————————————————————————————————
#  Main
# ——————————————————————————————————————————————————————————————————————————————
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: recurse_calls.py <Test.java> <testMethod> <executed_methods.csv>")
        sys.exit(1)

    java_file, test_meth, executed_csv = sys.argv[1:]
    src = open(java_file, encoding="utf8").read()
    tree = parser.parse(src.encode())
    root = tree.root_node

    # 1) find the test method itself
    test_node = find_method(root, test_meth)
    if not test_node:
        print(f"❌  Could not find method `{test_meth}`")
        sys.exit(1)

    # 2) collect direct calls in the test
    test_body = next((c for c in test_node.children if c.type == "block"), None)
    direct = collect_invocations(test_body) if test_body else set()

    print(f"Direct calls in `{test_meth}`:")
    for c in sorted(direct):
        print(f"  • {c}()")

    # 3) if runTestScenario is in there, recurse into it
    helper_name = "runTestScenario"
    if helper_name in direct:
        helper_node = find_method(root, helper_name)
        if not helper_node:
            print(f"⚠️  Called `{helper_name}` but could not find its declaration")
            sys.exit(1)

        helper_body = next((c for c in helper_node.children if c.type == "block"), None)
        helper_calls = collect_invocations(helper_body) if helper_body else set()

        print(f"\nCalls *inside* `{helper_name}`:")
        for c in sorted(helper_calls):
            print(f"  • {c}()")
    else:
        helper_calls = set()

    # 4) load your executed_methods.csv and intersect
    executed = load_executed_methods(executed_csv)
    relevant = helper_calls & executed

    print(f"\nOf those, which actually appear in `{executed_csv}`:")
    if relevant:
        for c in sorted(relevant):
            print(f"  ✅ {c}()")
    else:
        print("  (none)")

