import pandas as pd
import os
import numpy as np
import re
from utils import proj_clone
import sys
from parsing_test_code_info import extract_test_function

def data_from_row(row):
    git_proj = row['gitproj_name'] 
    if git_proj.strip().startswith('#'):
        return None
    sha = row['sha']
    print("row['test_name']=", row['test_name'])
    test_file_path, test_name = row['test_name'].split("::", 1)
    print(test_file_path, test_name)
    return git_proj, sha,  test_file_path, test_name

if __name__ == "__main__":
    #model_weights_path = sys.argv[2]
    #results_file = sys.argv[3]
    #data_name = sys.argv[4]
    #technique = sys.argv[5]
    #initialize_environment(42)
    dataset_path = sys.argv[1]
    output_data = []  # List to store extracted data
    df = pd.read_csv(dataset_path)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    projects_dir = os.path.join(script_dir, "projects")
    for index, row in df.iterrows():
        row_data = data_from_row(row)
        if row_data is None:
            continue
        git_proj, sha, test_file_path, test_name = row_data
        project_name = full_path_after_3 = "/".join(git_proj.split("/")[3:]) 
        proj_clone(project_name, sha, projects_dir)
        proj_name = git_proj.split("/")[-1]
        print(proj_name)
        print(test_file_path)
        print(test_name)
        print("projects/"+proj_name+"/"+test_file_path)
        test_code, start_line, end_line = extract_test_function("projects/"+proj_name+"/"+test_file_path, test_name)
        print('test_code=', test_code)
        print('start_line=', start_line)
        print('end_line=', end_line)
        # Append the extracted information into a dictionary
        output_data.append({
            "git_proj": git_proj,
            "sha": sha,
            "test_file_path": test_file_path,
            "test_name": test_name,
            "test_code": test_code,
            "start_line": start_line,
            "end_line": end_line
        })
        #exit()

    output_df = pd.DataFrame(output_data)
    # Save to CSV
    output_csv_path = "extracted_tests.csv"
    output_df.to_csv(output_csv_path, index=False)  
