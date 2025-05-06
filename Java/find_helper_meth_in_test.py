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


#def all_nodes(node):
#    yield node
#    for c in node.children:
#        yield from all_nodes(c)
#
#def find_method_by_name(root, src_bytes, method_name):
#    """Find the method_declaration node whose name equals `method_name`."""
#    for n in all_nodes(root):
#        if n.type != "method_declaration":
#            continue
#        name_node = n.child_by_field_name("name")
#        if name_node and name_node.text.decode() == method_name:
#            return n
#    return None
#
#def collect_invocations(node, invocations):
#    """Recursively gather all invoked method names under `node`."""
#    if node.type == "method_invocation":
#        name = node.child_by_field_name("name")
#        if name:
#            invocations.add(name.text.decode())
#    for c in node.children:
#        collect_invocations(c, invocations)
#
#if __name__ == "__main__":
#    if len(sys.argv) != 3:
#        print("Usage: extract_calls.py <SomeTest.java> <methodName>")
#        sys.exit(1)
#
#    java_file, target_method = sys.argv[1], sys.argv[2]
#    src = open(java_file, encoding="utf8").read()
#    tree = parser.parse(src.encode())
#    root = tree.root_node
#
#    # 2) find the method node
#    m = find_method_by_name(root, src.encode(), target_method)
#    if not m:
#        print(f"❌  Could not find method `{target_method}` in {java_file}")
#        sys.exit(1)
#
#    # 3) collect invocations
#    calls = set()
#    # skip the signature; dive into its body (the last child is usually the block)
#    body = next((c for c in m.children if c.type == "block"), None)
#    if body:
#        collect_invocations(body, calls)
#
#    # 4) report
#    if not calls:
#        print(f"No method calls found inside `{target_method}`.")
#    else:
#        print(f"Methods called by `{target_method}`:")
#        for name in sorted(calls):
#            print(f"  • {name}()")
#
##def all_nodes(node):
##    yield node
##    for c in node.children:
##        yield from all_nodes(c)
##
##def is_test_method(node, src_bytes):
##    if node.type != "method_declaration":
##        return False
##    for c in node.children:
##        if c.type in ("annotation", "marker_annotation"):
##            name = c.child_by_field_name("name")
##            if name and name.text.decode() == "Test":
##                return True
##    return False
##
##def find_test_method(root, src_bytes, test_name):
##    for n in all_nodes(root):
##        if n.type != "method_declaration":
##            continue
##        name_node = n.child_by_field_name("name")
##        if name_node and name_node.text.decode() == test_name and is_test_method(n, src_bytes):
##            return n
##    return None
##
##def collect_invocations(node, out):
##    if node.type == "method_invocation":
##        m = node.child_by_field_name("name")
##        if m:
##            out.add(m.text.decode())
##    for c in node.children:
##        collect_invocations(c, out)
##
##def collect_helpers(root):
##    helpers = set()
##    for n in all_nodes(root):
##        if n.type == "method_declaration" and not is_test_method(n, None):
##            name = n.child_by_field_name("name")
##            if name:
##                helpers.add(name.text.decode())
##    return helpers
##
##if __name__ == "__main__":
##    if len(sys.argv) != 3:
##        print("Usage: extract_helpers.py <TestFile.java> <TestMethodName>")
##        sys.exit(1)
##
##    path, test_name = sys.argv[1:]
##    src = open(path, encoding="utf8").read()
##    src_b = src.encode()
##    tree = parser.parse(src_b)
##    root = tree.root_node
##
##    test_node = find_test_method(root, src_b, test_name)
##    if not test_node:
##        print(f"❌  Could not find @Test method {test_name}() in {path}")
##        sys.exit(1)
##
##    invoked = set()
##    collect_invocations(test_node, invoked)
##
##    helpers = collect_helpers(root)
##    called_helpers = sorted(invoked & helpers)
##
##    print(f"\nHelper methods _invoked_ by `{test_name}()`:\n")
##    if not called_helpers:
##        print("  (none!)")
##    else:
##        for h in called_helpers:
##            print(f"  • {h}()")
##
###def node_text(n, src_b):
###    return src_b[n.start_byte:n.end_byte].decode()
###
###def all_nodes(node):
###    yield node
###    for c in node.children:
###        yield from all_nodes(c)
###
###def find_test_method(root, src_b, test_name):
###    for n in all_nodes(root):
###        if n.type != "method_declaration":
###            continue
###        name = n.child_by_field_name("name")
###        if not name or name.text.decode() != test_name:
###            continue
###        # look for @Test
###        for c in n.children:
###            if c.type.endswith("annotation") and "@Test" in node_text(c, src_b):
###                return n
###    return None
###
###def collect_invoked(n, out):
###    if n.type == "method_invocation":
###        m = n.child_by_field_name("name")
###        if m:
###            out.add(m.text.decode())
###    for c in n.children:
###        collect_invoked(c, out)
###
###def collect_helpers(root, src_b):
###    h = set()
###    for n in all_nodes(root):
###        if n.type != "method_declaration":
###            continue
###        name = n.child_by_field_name("name")
###        if not name:
###            continue
###        # skip real @Test
###        if any(c.type.endswith("annotation") and "@Test" in node_text(c, src_b)
###               for c in n.children):
###            continue
###        h.add(name.text.decode())
###    return h
###
###if __name__ == "__main__":
###    if len(sys.argv) != 3:
###        print("Usage: extract_helpers.py <TestFile.java> <TestMethodName>")
###        sys.exit(1)
###
###    path, test_name = sys.argv[1:]
###    src = open(path, encoding="utf8").read()
###    src_b = src.encode()
###    tree = parser.parse(src_b)
###    root = tree.root_node
###
###    test_node = find_test_method(root, src_b, test_name)
###    if not test_node:
###        print(f"❌  Could not find @Test method {test_name}() in {path}")
###        sys.exit(1)
###
###    invoked = set()
###    collect_invoked(test_node, invoked)
###
###    helpers = collect_helpers(root, src_b)
###    called_helpers = sorted(invoked & helpers)
###
###    print(f"\nHelper methods _invoked_ by `{test_name}()`:\n")
###    if not called_helpers:
###        print("  (none!)")
###    else:
###        for h in called_helpers:
###            print(f"  • {h}()")
###
####def node_text(n, src):
####    return src[n.start_byte:n.end_byte].decode()
####
####def find_test_method(root, src, test_name):
####    for cursor in root.walk():
####        n = cursor.node
####        if n.type != "method_declaration":
####            continue
####        name = n.child_by_field_name("name")
####        if not name or name.text.decode() != test_name:
####            continue
####        # look for an '@Test' annotation
####        for c in n.children:
####            if c.type.endswith("annotation") and "@Test" in node_text(c, src):
####                return n
####    return None
####
####def collect_invoked(n, out):
####    if n.type == "method_invocation":
####        m = n.child_by_field_name("name")
####        if m:
####            out.add(m.text.decode())
####    for c in n.children:
####        collect_invoked(c, out)
####
####def collect_helpers(root, src):
####    helpers = set()
####    for cursor in root.walk():
####        n = cursor.node
####        if n.type != "method_declaration":
####            continue
####        name = n.child_by_field_name("name")
####        if not name:
####            continue
####        # skip real @Test methods
####        if any(c.type.endswith("annotation") and "@Test" in node_text(c, src)
####               for c in n.children):
####            continue
####        helpers.add(name.text.decode())
####    return helpers
####
####if __name__ == "__main__":
####    if len(sys.argv) != 3:
####        print("Usage: extract_helpers.py <TestFile.java> <TestMethodName>")
####        sys.exit(1)
####
####    path, test_name = sys.argv[1:]
####    src = open(path, encoding="utf8").read()
####    src_b = src.encode()
####    tree = parser.parse(src_b)
####    root = tree.root_node
####
####    test_node = find_test_method(root, src_b, test_name)
####    if not test_node:
####        print(f"❌  Could not find @Test method {test_name}() in {path}")
####        sys.exit(1)
####
####    invoked = set()
####    collect_invoked(test_node, invoked)
####
####    helpers = collect_helpers(root, src_b)
####    called_helpers = sorted(invoked & helpers)
####
####    print(f"\nHelper methods _invoked_ by `{test_name}()`:\n")
####    if not called_helpers:
####        print("  (none!)")
####    else:
####        for h in called_helpers:
####            print(f"  • {h}()")
