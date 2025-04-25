import csv

def get_line_range(csv_path, target_class, target_method):
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Class"] == target_class and row["Method"] == target_method:
                return row["LineRange"]
    return None
