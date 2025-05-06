from tree_sitter import Language, Parser
# Set up parser
from tree_sitter_languages import get_language
JAVA_LANGUAGE = get_language("java")
parser = Parser()
parser.set_language(JAVA_LANGUAGE)

def all_nodes(node):
    yield node
    for c in node.children:
        yield from all_nodes(c)

def find_all_helpers(java_source: str, exclude_tests=True):
    """
    Return every method_declaration in this source file,
    skipping the ones annotated @Test (if exclude_tests=True).
    """
    tree = parser.parse(java_source.encode())
    root = tree.root_node

    helpers = []
    for node in all_nodes(root):
        if node.type != "method_declaration":
            continue
        name_node = node.child_by_field_name("name")
        if not name_node:
            continue
        mname = name_node.text.decode()

        # skip real @Test methods if desired
        if exclude_tests:
            for ann in node.children:
                if ann.type in ("annotation", "marker_annotation"):
                    ann_name = ann.child_by_field_name("name")
                    if ann_name and ann_name.text.decode() == "Test":
                        break
            else:
                # no @Test annotation found — that’s a helper
                helpers.append((mname, node.start_point[0] + 1))
        else:
            helpers.append((mname, node.start_point[0] + 1))

    return sorted(helpers)
#def all_nodes(node):
#    yield node
#    for c in node.children:
#        yield from all_nodes(c)
#
#def find_helper_methods_for_test(java_source: str, test_name: str):
#    tree = parser.parse(java_source.encode())
#    root = tree.root_node
#
#    # 1) find the method_declaration named `test_name`
#    test_node = None
#    for node in all_nodes(root):
#        if node.type == "method_declaration":
#            name_node = node.child_by_field_name("name")
#            if name_node and name_node.text.decode() == test_name:
#                test_node = node
#                break
#
#    if not test_node:
#        found = [
#            n.child_by_field_name("name").text.decode()
#            for n in all_nodes(root)
#            if n.type == "method_declaration"
#        ]
#        raise RuntimeError(
#            f"Could not find method `{test_name}()` in this file.\n"
#            f"Methods I did see were: {found}"
#        )
#
#    # 2) collect all invoked helper names inside that test body
#    invoked = set()
#    def collect_calls(n):
#        if n.type == "method_invocation":
#            m = n.child_by_field_name("name")
#            if m:
#                invoked.add(m.text.decode())
#        for c in n.children:
#            collect_calls(c)
#    collect_calls(test_node)
#
#    # 3) index all declared (non‐test) methods
#    declared = {}
#    for node in all_nodes(root):
#        if node.type == "method_declaration":
#            name_node = node.child_by_field_name("name")
#            if not name_node:
#                continue
#            mname = name_node.text.decode()
#            declared[mname] = node
#
#    # 4) report only those declared methods that were actually invoked
#    helpers = []
#    for mname in sorted(invoked):
#        if mname in declared:
#            line = declared[mname].start_point[0] + 1
#            helpers.append((mname, line))
#
#    return helpers

if __name__ == "__main__":
    src = open("projects/TooTallNate/Java-WebSocket/src/test/java/org/java_websocket/issues/Issue580Test.java").read()
    for name, line in find_all_helpers(
            src,
            "runNoCloseBlockingTestScenario0"
    ):
        print(f"  • {name}() at line {line}")

