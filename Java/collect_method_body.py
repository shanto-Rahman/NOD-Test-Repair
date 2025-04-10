import csv
from pathlib import Path
from tree_sitter import Parser
from tree_sitter_languages import get_language
import sys

module = sys.argv[1]
module_with_underscore = module.replace("/", "_")
test_name = sys.argv[2]
slug = sys.argv[3].replace("/", "_")

# Set up parser
JAVA_LANGUAGE = get_language("java")
parser = Parser()
parser.set_language(JAVA_LANGUAGE)

# Load executed methods from CSV
#executed_methods_file = "executed_methods.csv"
executed_methods_file = slug+"_"+module_with_underscore+"_"+test_name+"_executed_methods.csv"
executed_methods = set()
class_to_methods = {}

with open(executed_methods_file, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        full_class_name = row["Class"]
        method_name = row["Method"]
        executed_methods.add((full_class_name, method_name))
        class_to_methods.setdefault(full_class_name, set()).add(method_name)

# Root directory for source files
src_root = Path(module+"/src/main/java")

# Store extracted method bodies
extracted = []

def extract_methods(code: bytes, class_name: str):
    tree = parser.parse(code)
    root = tree.root_node

    def find_methods_recursive(node, current_class):
        # Handle methods
        if node.type in ("method_declaration", "constructor_declaration"):
            name_node = node.child_by_field_name("name")
            method_name = "<init>" if node.type == "constructor_declaration" else (
                code[name_node.start_byte:name_node.end_byte].decode() if name_node else None
            )
            if method_name and (current_class, method_name) in executed_methods:
                body = code[node.start_byte:node.end_byte].decode()
                extracted.append((current_class, method_name, body))

        # Handle nested classes
        if node.type == "class_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                nested_class_name = code[name_node.start_byte:name_node.end_byte].decode()
                nested_full_name = f"{class_name}${nested_class_name}"
                for child in node.children:
                    find_methods_recursive(child, nested_full_name)

        for child in node.children:
            find_methods_recursive(child, class_name)

    find_methods_recursive(root, class_name)

# Walk through the expected class files
for class_name in class_to_methods:
    rel_path = class_name.replace(".", "/").split("$")[0] + ".java"
    full_path = src_root / rel_path
    if full_path.exists():
        with open(full_path, "rb") as f:
            code = f.read()
        extract_methods(code, class_name)

# Save extracted method bodies to a CSV
#output_path = "extracted_method_bodies.csv"
executed_meth_csv = slug+"_"+module_with_underscore+"_"+test_name+"_executed_method_bodies.csv"
#with open(executed_meth_csv, "w", newline="") as f:
with open(executed_meth_csv, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Class", "Method", "Body"])
    writer.writerows(extracted)

print(executed_meth_csv)

