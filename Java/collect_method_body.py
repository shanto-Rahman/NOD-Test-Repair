import csv 
import sys
from pathlib import Path
from tree_sitter import Parser
from tree_sitter_languages import get_language
import re

# Parse input arguments
#main_module, test_name, slug, *modules = sys.argv[1:]

main_module = sys.argv[1]
test_name = sys.argv[2]
slug = sys.argv[3]
modules = sys.argv[4:]

#print(main_module)
#print(test_name)
#print(slug)
#print(modules)

module_with_underscore = "_".join([m.replace("/", "_") for m in modules])
main_module_with_underscore = main_module.replace("/", "_")
slug = slug.replace("/", "_")

# Set up Tree-sitter Java parser
JAVA_LANGUAGE = get_language("java")
parser = Parser()
parser.set_language(JAVA_LANGUAGE)

# Load executed methods from CSV
executed_methods_file = f"{slug}_{main_module_with_underscore}_{test_name}_executed_methods.csv"
executed_methods = set()
class_to_methods = {}
coverage_map = {}

with open(executed_methods_file, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        full_class_name = row["Class"]
        method_name = row["Method"]
        descriptor_name = row["Descriptor"]
        key = (full_class_name, method_name, descriptor_name)
        executed_methods.add(key)
        class_to_methods.setdefault(full_class_name, set()).add((method_name, descriptor_name))
        # Store coverage info
        coverage_map[key] = (
            row.get("Lines Covered", ""),
            row.get("Total Lines", ""),
            row.get("Coverage %", "")
        )

# Container for extracted methods
extracted = []
seen = set()

def extract_methods(code: bytes, class_name: str):
    tree = parser.parse(code)
    root = tree.root_node

    def find_methods_recursive(node, current_class):
        # Method or constructor
        if node.type in ("method_declaration", "constructor_declaration"):
            name_node = node.child_by_field_name("name")
            method_name = "<init>" if node.type == "constructor_declaration" else (
                code[name_node.start_byte:name_node.end_byte].decode() if name_node else None
            )
            if method_name:
                for descriptor in (d for (m, d) in class_to_methods.get(current_class, set()) if m == method_name):
                    key = (current_class, method_name, descriptor)
                    if key in executed_methods and key not in seen:
                        seen.add(key)
                        start_line, _ = node.start_point
                        end_line, _ = node.end_point
                        rng = f"{start_line + 1}-{end_line + 1}"
                        body = code[node.start_byte:node.end_byte].decode()
                        #extracted.append((current_class, method_name, descriptor, body, rng))
                        lines_covered, total_lines, coverage_pct = coverage_map.get(key, ("", "", ""))
                        extracted.append((
                            current_class,
                            method_name,
                            descriptor,
                            lines_covered,
                            total_lines,
                            coverage_pct,
                            body,
                            rng
                        ))


        # Nested classes
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

# Search source files for each executed method
for class_name in class_to_methods:
    rel_path = class_name.replace(".", "/").split("$")[0] + ".java"
    found = False
    for module in modules + [main_module]:
        src_root = Path(module) / "src/main/java"
        full_path = src_root / rel_path
        if full_path.exists():
            with open(full_path, "rb") as f:
                code = f.read()
            extract_methods(code, class_name)
            found = True
            break
    if not found:
        #print(f"[WARN] Source not found for: {class_name}")
        print(f"[WARN] Source not found for: {class_name}", file=sys.stderr)

# Save extracted methods
output_csv = f"{slug}_{main_module_with_underscore}_{test_name}_executed_method_bodies.csv"
with open(output_csv, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Class", "Method", "Descriptor", "Lines Covered", "Total Lines", "Coverage %", "Body", "LineRange"])
    writer.writerows(extracted)

# 1) Number of executed methods we actually extracted
executed_methods_count = len(extracted)

# 2) Total token count across all extracted method bodies
total_token_count = sum(
    len(re.findall(r"\w+", body))
        for (_, _, _, _, _, _, body, _) in extracted
            )

print(f"executed_methods_count={executed_methods_count}:total_token_count={total_token_count}")

