import csv
import re

def get_line_range(csv_path, target_class, target_method):
    with open(csv_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Class"] == target_class and row["Method"] == target_method:
                return row["LineRange"]
    return None

def extract_method_calls(code_body):
    # Simple regex to match Java-style method calls like Object.wait() or OutputStream.flush()
    return re.findall(r'\b[\w\.]+\(.*?\)', code_body)

def find_api_match_with_flakerake(df, timing_related_api_txt_file):
    with open(timing_related_api_txt_file, "r") as f:
        known_apis = [line.strip() for line in f if line.strip()]

    known_api_set = set(known_apis) 
    print(known_api_set)
    print("**API list**")
    matches_per_row = []
    body_df_column = df["Body"]
    for idx, code_body in body_df_column.items():
        found_matches = []
        method_calls = extract_method_calls(code_body)

        for call in method_calls:
            # Optionally normalize the format to match your known API list (e.g., replace dots with slashes)
            # This depends on your data format
            normalized_call = call.replace('.', '/')
            if normalized_call in known_api_set:
                found_matches.append(normalized_call) 

        matches_per_row.append(found_matches)

    # Add to your DataFrame if needed
    df["Matched_APIs"] = matches_per_row

