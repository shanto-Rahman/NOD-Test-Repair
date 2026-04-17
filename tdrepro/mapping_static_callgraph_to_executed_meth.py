import sys
import csv

def load_call_depths(static_csv_path):
    depth_map = {}
    with open(static_csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            method = row["Method"].strip()
            if not method.endswith(")"):
                method += "()"  # Normalize method format
            depth_map[method] = row["Depth"]
    return depth_map

def augment_with_depth(exec_csv_path, output_csv_path, depth_map):
    with open(exec_csv_path, newline="") as infile, open(output_csv_path, "w", newline="") as outfile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ["CallDepth"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            full_method = f'{row["Class"]}:{row["Method"]}'
            if not full_method.endswith(")"):
                full_method += "()"  # Normalize to match static callgraph keys
            row["CallDepth"] = depth_map.get(full_method, "-1")
            writer.writerow(row)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 script.py static_callgraphs.csv executed_method_bodies.csv output.csv")
        sys.exit(1)

    static_csv = sys.argv[1]
    executed_csv = sys.argv[2]
    output_csv = sys.argv[3]

    call_depths = load_call_depths(static_csv)
    augment_with_depth(executed_csv, output_csv, call_depths)
    print(f"[INFO] CallDepth values added and saved to '{output_csv}'")

