import xml.etree.ElementTree as ET
import csv
import sys

module_name = sys.argv[1]
# Load the XML
tree = ET.parse(module_name+"/target/coverage.xml")
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
            line_counters = method.findall("counter[@type='LINE']")
            for counter in line_counters:
                covered = int(counter.get("covered", 0))
                if covered > 0:
                    executed_methods.append([package_name, class_name, method_name, desc])
                    break  # If covered once, record and skip rest

# Write to CSV
with open("executed_methods.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Package", "Class", "Method", "Descriptor"])
    writer.writerows(executed_methods)

print(f"✅ Extracted {len(executed_methods)} executed methods to executed_methods.csv")

