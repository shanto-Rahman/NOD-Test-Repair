import xml.etree.ElementTree as ET
import csv
import sys

module = sys.argv[1]
module_with_underscore = module.replace("/", "_")
test_name = sys.argv[2]
slug = sys.argv[3].replace("/", "_")
# Load the XML
tree = ET.parse(module+"/target/coverage.xml")
root = tree.getroot()

executed_methods = []

# Walk through classes and methods
for package in root.findall("package"):
    package_name = package.get("name")
    for clazz in package.findall("class"):
        class_name = clazz.get("name").replace("/", ".")
        for method in clazz.findall("method"):
            method_name = method.get("name")
            desc = method.get("desc")
            # Determine if the method was executed
            line_counter = method.find("counter[@type='LINE']")

            if line_counter is None:
                continue
            covered = int(line_counter.get("covered", 0))
            missed  = int(line_counter.get("missed", 0))
            total   = covered + missed
            if total == 0:
                pct = 0.0
            else:
                pct = covered / total * 100.0
            
            # record only methods that were executed at least once
            if covered > 0:
                executed_methods.append([
                    package_name, class_name, method_name, desc,
                    covered, total, f"{pct:.1f}%"
                ])
            
            '''for counter in line_counters:
                covered = int(counter.get("covered", 0))
                if covered > 0:
                    executed_methods.append([package_name, class_name, method_name, desc])
                    break'''  # If covered once, record and skip rest

# Write to CSV
executed_meth_csv = slug+"_"+module_with_underscore+"_"+test_name+"_executed_methods.csv"
with open(executed_meth_csv, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Package", "Class", "Method", "Descriptor", "Lines Covered", "Total Lines", "Coverage %"])
    writer.writerows(executed_methods)


def count_total_tokens(methods):
    import re
    total = 0
    for _, _, _, desc, _, _, _ in methods:
        print('***desc=', desc)
        tokens = re.findall(r'\w+', desc)
        total += len(tokens)
    return total

token_count = count_total_tokens(executed_methods)

print(f"count_executed_methods = {len(executed_methods)} : total_token_count = {token_count}")


#print(f"✅ Extracted {len(executed_methods)} executed methods to executed_methods.csv")

