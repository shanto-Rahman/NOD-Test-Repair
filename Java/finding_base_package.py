import csv
from collections import Counter
import sys

#module = sys.argv[1]
#module_with_underscore = module.replace("/", "_")
#test_name = sys.argv[2]
#slug = sys.argv[3].replace("/", "_")
##csv_file = "traces/apache_incubator-uniffle_common_org.apache.uniffle.common.rpc.GrpcServerTest#testGrpcExecutorPool_executed_methods.csv" #"your_file.csv"  # Replace with your actual file path
csv_file = sys.argv[1] #"traces/"+slug+"_"+module_with_underscore + "_" + test_name

base_package_counts = []

with open(csv_file, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        class_path = row["Class"]
        parts = class_path.split(".")
        if len(parts) >= 3:
            base_package = ".".join(parts[:3])  # Get base package like org.apache.uniffle
            base_package_counts.append(base_package)

# Find the most common base package
most_common_base, _ = Counter(base_package_counts).most_common(1)[0]

#print(f"The base package is: {most_common_base}.")
print(most_common_base)


