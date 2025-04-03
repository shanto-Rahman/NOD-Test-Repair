from tree_sitter import Language, Parser
from tree_sitter_languages import get_language

JAVA_LANGUAGE = get_language('java')

#JAVA_LANGUAGE = Language('build/my-languages.so', 'java')
parser = Parser()
parser.set_language(JAVA_LANGUAGE)

# Load Java source
with open('common/src/main/java/org/apache/uniffle/common/metrics/GRPCMetrics.java', 'r') as f:
    code = f.read().encode()

tree = parser.parse(code)
root = tree.root_node

# Find and print all method names
def find_methods(node):
    if node.type == 'method_declaration':
        print("Method:", code[node.start_byte:node.end_byte].decode())
    for child in node.children:
        find_methods(child)

find_methods(root)

