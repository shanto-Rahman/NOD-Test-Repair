import csv
import os
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language

# Step 1: Build the Tree-sitter language library (run once)
#Language.build_library(
#    'build/my-languages.so',
#    ['tree-sitter-java']
#)

# Step 2: Initialize parser with Java language
#JAVA_LANGUAGE = Language("java")
JAVA_LANGUAGE = get_language("java")
parser = Parser()
parser.set_language(JAVA_LANGUAGE)

# Step 3: Load target methods from the CSV
def load_target_methods(csv_file_path):
    target_methods = set()
    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            fq_name = f"{row['Class']}.{row['Method']}"
            target_methods.add(fq_name)
    return target_methods

# Step 4: Extract method calls from Java source code
def extract_calls_from_code(code, target_methods, file_path):
    tree = parser.parse(bytes(code, "utf8"))
    root_node = tree.root_node
    call_edges = []

    def walk(node, class_name=None, method_name=None):
        nonlocal call_edges
        if node.type == "class_declaration":
            for child in node.children:
                if child.type == "identifier":
                    class_name = child.text.decode()

        if node.type == "method_declaration":
            for child in node.children:
                if child.type == "identifier":
                    method_name = child.text.decode()

        if node.type == "method_invocation":
            callee_node = node.child_by_field_name("name")
            if callee_node and class_name and method_name:
                fq_caller = f"{class_name}.{method_name}"
                callee = callee_node.text.decode()
                for target in target_methods:
                    if target.endswith(f".{callee}"):
                        call_edges.append((fq_caller, target))

        for child in node.children:
            walk(child, class_name, method_name)

    walk(root_node)
    return call_edges

# Step 5: Process all Java files in source folder
def collect_call_graph(java_source_root, target_method_csv):
    target_methods = load_target_methods(target_method_csv)
    call_graph = []

    for root, _, files in os.walk(java_source_root):
        for file in files:
            if file.endswith(".java"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    code = f.read()
                    call_graph.extend(extract_calls_from_code(code, target_methods, os.path.join(root, file)))

    return call_graph

# Step 6: Write the call graph to CSV
def write_call_graph_to_csv(call_graph, output_file="call_graph_output.csv"):
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Caller", "Callee"])
        writer.writerows(call_graph)

# Example usage
if __name__ == "__main__":
    java_src_root = "projects/apache/incubator-uniffle/common/src/main/java"
    target_methods_file = "traces/apache_incubator-uniffle_common_org.apache.uniffle.common.rpc.GrpcServerTest#testGrpcExecutorPool_executed_methods.csv"
    call_graph = collect_call_graph(java_src_root, target_methods_file)
    write_call_graph_to_csv(call_graph)
    print("Call graph written to call_graph_output.csv")


'''from tree_sitter import Language, Parser
import os

module = sys.argv[1].replace("/", "_")
test_name = sys.argv[2]
slug = sys.argv[3].replace("/", "_")


# Build the Java parser library once
Language.build_library(
    'build/my-languages.so',
    ['tree-sitter-java']
)

JAVA_LANGUAGE = Language('build/my-languages.so', 'java')

parser = Parser()
parser.set_language(JAVA_LANGUAGE)

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def extract_calls_from_code(code, file_path):
    tree = parser.parse(bytes(code, "utf8"))
    root = tree.root_node

    call_graph = []
    current_class = None
    current_method = None

    def traverse(node, class_ctx, method_ctx):
        nonlocal call_graph

        if node.type == "class_declaration":
            for child in node.children:
                if child.type == "identifier":
                    class_ctx = child.text.decode()
        elif node.type == "method_declaration":
            for child in node.children:
                if child.type == "identifier":
                    method_ctx = child.text.decode()

        if node.type == "method_invocation":
            callee = node.child_by_field_name("name")
            if callee and class_ctx and method_ctx:
                call_graph.append((class_ctx, method_ctx, callee.text.decode()))

        for child in node.children:
            traverse(child, class_ctx, method_ctx)

    traverse(root, None, None)
    return call_graph

# Example
java_dir = module+"/src/main/java"
call_edges = []

for root, dirs, files in os.walk(java_dir):
    for file in files:
        if file.endswith(".java"):
            fpath = os.path.join(root, file)
            code = read_file(fpath)
            call_edges += extract_calls_from_code(code, fpath)

# Output call graph
with open("static_callgraph.csv", "w") as out:
    out.write("CallerClass,CallerMethod,CalleeMethod\n")
    for caller_cls, caller_mtd, callee_mtd in call_edges:
        out.write(f"{caller_cls},{caller_mtd},{callee_mtd}\n")
'''
