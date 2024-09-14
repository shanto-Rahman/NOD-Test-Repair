#HERE we aim for collecting fm that are changed during regression, but the tests are not changed. csv_file=updated_file_sequential_combined_file_with_code2_with_correct_key_names_csv.csv
import pandas as pd
from modify_python_file import hack_into_sut, hack_into_test
from change_curation_helper import run_test_for_real_example
import os

def data_from_row(row):
    # print(row.keys())

    proj_name = row['Project'] 
    if proj_name.strip().startswith('#'):
        return None
    old_commit_id = row['OldCommitId']
    new_commit_id = row['CommitId']

    test_file_path = row['TestCaseFile']
    unit_test_name_new = row['OriginalTestCaseFunction'] #     unit_test_name_new = row['TestCaseMethod']
    unit_test_name_old = row['OldTestCaseFunction']
    unit_test_code_new = row['original_test_case_code']
    unit_test_code_old = row['old_test_case_code']
    unit_test_new_lines = row["TestCaseLines"]

    fm_file_path = row['FocalMethodFile']
    fm_name_new = row['OriginalFocalMethodFunction']
    fm_name_old = row['OldFocalMethodFunction']
    fm_code_new = row['original_focal_method_code']
    fm_code_old = row['old_focal_method_code']
    # test_case_changed = row['TestCaseChanged']


    # print(row["TestCaseLines"])
    print(unit_test_name_new, unit_test_name_old, fm_name_new, fm_name_old)
    # print(test_file_path)
    # print("+++++++++++++++")
    # print(unit_test_code_new)
    # print("+++++++++++++++")
    # print(unit_test_code_old)
    # print("+++++++++++++++")
    # print(fm_code_new)
    # print("+++++++++++++++")
    # print(fm_code_old)
    # exit()

    return proj_name, new_commit_id, test_file_path, unit_test_name_new, unit_test_name_old, fm_file_path, fm_name_new, unit_test_code_old, unit_test_code_new, unit_test_new_lines, old_commit_id
    # exit()
    # proj_name = row['Project'] 
    # if proj_name.strip().startswith('#'):
    #     return None
    
    # old_commit_id = row['OldCommitId']
    # new_commit_id = row['CommitId']
    # test_file_path = row['TestCaseFile']
    # unit_test_name_new = row['TestCaseMethod']
    # #unit_test_name_old = row['TestCaseMethod']
    # fm_file_path = row['FocalMethodFile']
    # fm_name = row['FocalMethod']
    # test_case_changed = row['TestCaseChanged']
    # old_commit_test_body = row['OldCommitId_TestCase']
    # new_commit_test_body = row['CommitId_TestCase']
    # new_test_lines = row['TestCaseLines'] #.replace('[', '').replace(']', '')

    # # old_commit_test_body, "/path/"+test_file_path, unit_test_name, new_test_lines

    # #error_type = row['test_pass/fail']
    # #coverage_percentage = row['coverage_percentage']
    # #if not is_valid_fm_code(changed_fm_code): #pd.isna(changed_fm_code) or changed_fm_code == "NA":
    # #    return None
    # return proj_name, new_commit_id, test_file_path, unit_test_name_new, fm_file_path, fm_name, old_commit_test_body, new_commit_test_body, test_case_changed, new_test_lines, old_commit_id

if __name__ == "__main__":
    #file_name = "/mnt/efs/people/urshanto/real_data/real_data_fm_update2.csv"
    file_name = "temp.csv"
    df = pd.read_csv(file_name)
    #print("Row_count=", len(df))
    # Access the 'test_case_diff' column
    test_case_diff_values = df['TestCaseChanged']
    
    # If you want to print the column values
    #print(test_case_diff_values)
    #test_case_diff_values.to_csv("X.csv", index=False)
     
    for index, row in df.iterrows():
        row_data = data_from_row(row)
        if row_data is None:
            continue
        proj_name, new_commit_id, test_file_path, unit_test_name_new, unit_test_name_old, fm_file_path, fm_name_new, unit_test_code_old, unit_test_code_new, unit_test_new_lines, old_commit_id = row_data
        if "airtable-python-wrapper" in proj_name:
            continue
        # print(proj_name, new_commit_id, test_file_path, unit_test_name_new, fm_file_path, fm_name_new, unit_test_new_lines, old_commit_id)
        # exit()
        # As we already have checkout the new_commit_id, we are not again checkingout that. 
        hack_into_test(unit_test_code_old, "/home/sr53282/utg/change_aware_utg/test_analysis/projects/"+test_file_path, unit_test_name_new, unit_test_new_lines)

        current_dir = os.getcwd()
        print(current_dir)
        #run_test_for_real_example(proj_name, new_commit_id, test_file_path, unit_test_name, fm_file_path, fm_name, old_commit_test_body, new_commit_test_body, test_case_changed, new_test_lines)
        # run_test_for_real_example(proj_name, fm_file_path, fm_name, unit_test_name, test_file_path, old_commit, new_commit, objective="Real_data_find")
        run_test_for_real_example(proj_name, fm_file_path, fm_name_new, unit_test_name_old, test_file_path, old_commit_id, new_commit_id, objective="Real_data_find")
        exit()
    
