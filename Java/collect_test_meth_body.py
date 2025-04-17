import sys
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language
import csv
import json


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
# Step 1: Find method node
method_body = find_test_method_node(root, test_method_only)
called_method_names = extract_method_calls(method_body, code) if method_body else set()

# Step 2: Add "Called-level" to executed_methods
rows = []
with open(executed_csv_path, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        matched = False
        full_method = f"{row['Class']}.{row['Method']}".split('$')[0]  # remove inner class if needed
        for _, called in called_method_names:
            #print(f"Checking if {full_method} ends with .{called}")

            if full_method.endswith(f".{called}"):
                row["Called-level"] = "1"
                #print("I AM HERE ****")
                matched = True
                break
            else:
                row["Called-level"] = ""

        #if row["Method"] in called_method_names:
        #    row["Called-level"] = "1"
        #else:
        #    row["Called-level"] = ""
        rows.append(row)

output_csv_path="/home/shanto/Latest/ICSE-Artifact/FlakeSync_Artifact_Full/scripts/NOD-Test-Repair/Java/tmp.csv"
# Step 3: Write to new CSV
with open(output_csv_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

#print(f"Output written to: {output_csv_path}")


'''with open(executed_csv_path, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        executed_methods.add(f"{row['Class']}.{row['Method']}")

#method_body = extract_test_method_body(root, test_method_only)
method_body = find_test_method_node(root, test_method_only)

if method_body:
    #print(code[method_body.start_byte:method_body.end_byte].decode())
    #print("\n Matched calls from _executed_methods.csv:")
    calls = extract_method_calls(method_body, code)
    matched_calls = []

    for obj, method in sorted(calls):
        for em in executed_methods:
            if em.endswith(f".{method}"):
                matched_calls.append(f"{obj}.{method} → {em}")
                break
    print(json.dumps(matched_calls))  # Send back as JSON array

else:
    #print("❌ Test method not found.")
    print(json.dumps([]))  # Return empty if not found'''

