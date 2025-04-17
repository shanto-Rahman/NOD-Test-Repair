import sys
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language
import csv


module = sys.argv[1]
module_with_underscore = module.replace("/", "_")
test_name = sys.argv[2]
slug = sys.argv[3].replace("/", "_")
test_file_name= sys.argv[4]
test_method_only = test_name.split("#")[1] 

JAVA_LANGUAGE = get_language("java")
#JAVA_LANGUAGE = Language('build/my-languages.so', 'java')
parser = Parser()
parser.set_language(JAVA_LANGUAGE)
with open(test_file_name, "r") as f:
    code = f.read().encode()

tree = parser.parse(code)
root = tree.root_node

def find_test_method_node(node, target_name):
    for child in node.children:
        if child.type == 'method_declaration':
            method_name = child.child_by_field_name("name")
            if method_name and method_name.text.decode() == target_name:
                return child
        result = find_test_method_node(child, target_name)
        if result:
            return result
    return None

#def extract_test_method_body(node, target_name):
#    for child in node.children:
#        if child.type == 'method_declaration':
#            method_name = child.child_by_field_name("name")
#            if method_name and method_name.text.decode() == target_name:
#                return code[child.start_byte:child.end_byte].decode()
#        body = extract_test_method_body(child, target_name)
#        if body:
#            return body

#print(extract_test_method_body(root, test_method_only))
#test_code_body = extract_test_method_body(root, test_method_only)

def extract_method_calls(node, code_bytes):
    calls = set()
    if node.type == "method_invocation":
        method_name = node.child_by_field_name("name")
        object_node = node.child_by_field_name("object")
        if method_name:
            if object_node:
                calls.add((object_node.text.decode(), method_name.text.decode()))
            else:
                calls.add(("this", method_name.text.decode()))
    for child in node.children:
        calls.update(extract_method_calls(child, code_bytes))
    return calls

# Load executed methods
executed_methods = set()
executed_csv_path = "/home/shanto/Latest/ICSE-Artifact/FlakeSync_Artifact_Full/scripts/NOD-Test-Repair/Java/traces/apache_incubator-uniffle_common_org.apache.uniffle.common.rpc.GrpcServerTest#testGrpcExecutorPool_executed_methods.csv"
with open(executed_csv_path, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        executed_methods.add(f"{row['Class']}.{row['Method']}")

#method_body = extract_test_method_body(root, test_method_only)
method_body = find_test_method_node(root, test_method_only)

if method_body:
    print(code[method_body.start_byte:method_body.end_byte].decode())
    print("\n✅ Matched calls from _executed_methods.csv:")
    calls = extract_method_calls(method_body, code)
    for obj, method in sorted(calls):
        for em in executed_methods:
            if em.endswith(f".{method}"):
                print(f"{obj}.{method} → {em}")
else:
    print("❌ Test method not found.")
