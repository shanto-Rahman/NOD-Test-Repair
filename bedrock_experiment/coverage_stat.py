import time
from parse_git_change import collect_git_diff
import csv
from modify_python_file import hack_into_sut
from change_curation_helper import run_test
import pandas as pd
#Now Need to run these tests again to collect the coverage percentage only for the changed lines of fm by the existing tests


def get_fm_line_num(data, proj_name, test_file_path, unit_test_name, fm_file_path, fm_name):
    #print(fm_file_path)
    for row in data:
        #print(row['proj_name'] )
        #print(row['test_filename'] )
        #print(row['test_method'] )
        #print(row['fm_filename'] )
        #print(row['fm_method'] )
        if (row['proj_name'] == proj_name
            and row['test_filename'] == test_file_path 
            and row['test_method'] == unit_test_name
            #and row['fm_filename'] == fm_file_path):
            and fm_file_path in row['fm_filename']
            and row['fm_method'] == fm_name):
            print('FOUND**') 
            return row['fm_line_num'], row['test_line_num']
        #exit()

def is_valid_fm_code(changed_fm_code):
    if pd.isna(changed_fm_code) or changed_fm_code == "NA":
        print("NA found")
        return False
    return True

def data_from_row(row):
    proj_name = row['proj_name'] 
    if proj_name.strip().startswith('#'):
        return None
    test_file_path = row['test_filename']
    unit_test_name = row['test_method']
    fm_file_path = row['fm_filename']
    fm_name = row['fm_method']
    changed_fm_code = row['changed_fm']
    error_type = row['test_pass/fail']
    if not is_valid_fm_code(changed_fm_code): #pd.isna(changed_fm_code) or changed_fm_code == "NA":
        return None
    return proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, changed_fm_code


def read_csv_to_dict(csv_file_path):
    with open(csv_file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        data = [row for row in reader]
    return data

def bad_line_handler(bad_line):
    # Print or log the bad line to inspect it
    print(f"Bad line: {bad_line}")

# List to store bad lines for later use
#bad_lines = []

if __name__ == "__main__":
    filename_for_test_generation = "data/Claude3-5_690_tests_with_Changed_Focal_Meth_CC_Updated.csv" # File that contains covered_lines_when_considering_full_fm,coverage_percentage_when_considering_full_fm
    #df = pd.read_csv(filename_for_test_generation) 
    #filtered_df = df[df['test_pass/fail'] == 'test_pass']
    #filename_for_test_generation = "data/missing_in_second_file.csv"
    '''oo = "Results/Coverage_of_Only_Changed_Lines_in_FM.csv"
    df1 = pd.read_csv(filename_for_test_generation)
    print(df1['covered_lines'])
    df2 = pd.read_csv(oo)
    # Select only the relevant columns for comparison
    columns_to_compare = ['proj_name', 'test_filename', 'test_method', 'fm_filename']
    # Filter out rows where 'covered_lines' and 'coverage_percentage' are both NaN or empty
    df1_filtered = df1[~(    df1['covered_lines'].isna() & df1['coverage_percentage'].isna())]
    df1_subset = df1_filtered[columns_to_compare]
    df2_subset = df2[columns_to_compare]
    
    # Find rows in df1 that are not in df2
    missing_in_df2 = pd.merge(df1_subset, df2_subset, on=columns_to_compare, how='left', indicator=True).query('_merge == "left_only"').drop('_merge', axis=1)
    #missing_in_df2 = pd.merge(df1_filtered, df2_subset, on=columns_to_compare, how='left', indicator=True).query('_merge == "left_only"').drop('_merge', axis=1)
    
    # Save the missing rows to a CSV file (optional)
    missing_in_df2.to_csv('missing_in_second_file.csv', index=False)
    exit() '''



    #filename_for_test_generation = "x.csv" #data/Claude3-5_690_tests_with_Changed_Focal_Meth_CC_Updated.csv" # File that contains covered_lines_when_considering_full_fm,coverage_percentage_when_considering_full_fm
    '''df = pd.read_csv(filename_for_test_generation)
    
    for index, row in df.iterrows():
        row_data = data_from_row(row)
        if row_data is None:
            continue
        proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, changed_fm_code = row_data
    
        csv_file_path = "Results/Combined_result_of_fm_and_tests.csv" 
        data = read_csv_to_dict(csv_file_path)
        #print(data.head(10))
    
        fm_lines, test_lines = get_fm_line_num(data, proj_name, test_file_path, unit_test_name, fm_file_path, fm_name)
    
        changed_fm_code = changed_fm_code.strip()
        if changed_fm_code.startswith('"') and changed_fm_code.endswith('"'):
            changed_fm_code = changed_fm_code[1:-1].strip()
        fm_lines = hack_into_sut(changed_fm_code, fm_file_path, fm_name, fm_lines) #added the change into CUT by removing existing method code
        diff_fm, changed_line_numbers, diff_fm_with_line_numbers = collect_git_diff(fm_file_path, "../test_analysis/projects/"+proj_name, proj_name) 
        start_time = time.time()
        print(fm_file_path, fm_name, fm_lines, unit_test_name, test_file_path)
        coverage_percentage, dyn, covered_lines = run_test("XX", fm_file_path, fm_name, fm_lines, unit_test_name, test_file_path, "Results/Coverage_of_Only_Changed_Lines_in_FM.csv", proj_name, "0", "normal", "XX", "Normal_Test_Run", "XX", diff_fm_with_line_numbers, changed_fm_code, "XX", "XX", unit_test_name, changed_line_numbers, str(start_time))'''
        #exit()
#exit()
        #coverage_percentage, dyn, covered_lines = run_test(cleaned_cirtable-python-wrapper,/home/ec2-user/change_aware_utg/test_analysis/projects/airtable-python-wrapper/tests/test_api_workspace.py,test_create_base,create_base,3.8461538461538463,    test_pass,"['parameter_change', 'validation', 'documentation', 'error_handling', 'logging', 'refactoring']",14.28571429
        #ode, fm_file_path, fm_name, fm_lines, unit_test_name, test_file_path, claude_result_file, proj_name, str(cot_count), "claude", str(changes_types), objective, error_type, diff_fm_with_line_numbers, changed_fm_code, "", "", org_unit_test_name, changed_line_numbers) #Here dyn is dynamic trace which will be empty
        #print(covered_lines)
    #    #exit()
    #exit()
    #df = pd.read_csv('data/Claude3-5_690_tests_with_Changed_Focal_Meth_CC_Updated.csv')
    ## Select only the desired columns
    ##selected_columns = ['proj_name','test_filename','test_method','fm_filename','fm_method']
    ## Filter the rows where 'test_pass/fail' is 'test_pass'
    #filtered_df = df[df['test_pass/fail'] == 'test_pass']
    ##print(len(filtered_df))
    ##exit()

    #selected_columns = filtered_df[['proj_name', 'test_filename', 'test_method', 'fm_method', 'coverage_percentage', 'test_pass/fail', 'change_type']]
    #
    #selected_columns.columns = ['proj_name', 'test_filename', 'test_method', 'fm_method', 'coverage_percentage_with_changed_fm', 'test_pass/fail_with_changed_fm', 'fm_change_type']
    #
    #file_path="../test_analysis/Results/1072_tests_with_Focal_Methods_with_code_coverage.csv"
    #try:
    #    df_coverage_without_change = pd.read_csv(file_path)
    #    df_coverage_without_change.info()  # Display info to understand its structure
    #except Exception as e:
    #    print(f"Error occurred while loading CSV: {str(e)}")
    #    raise  # Reraise the exception after printing for further inspection
    # 
    ##df_coverage_without_change = pd.read_csv()
    ## Merge the DataFrames based on matching proj_name, test_method_name, and Static_Analysis_Result
    #merged_df = pd.merge(selected_columns, df_coverage_without_change[['proj_name','python_file_path','test_method_name', 'Static_Analysis_Result', 'coverage_percentage']], 
    #                     left_on=['proj_name', 'test_filename', 'test_method', 'fm_method'], 
    #                     right_on=['proj_name', 'python_file_path' ,'test_method_name', 'Static_Analysis_Result'], 
    #                     how='left')

    ## Drop the unnecessary columns after the merge
    #t_formulas.py,test_to_formula,erged_df = merged_df.drop(columns=['test_method_name', 'Static_Analysis_Result', 'python_file_path'])

    #merged_df.columns = ['proj_name', 'test_filename', 'test_method', 'fm_method', 'coverage_percentage_with_changed_fm', 'test_pass/fail_with_changed_fm', 'fm_change_type', 'coverage_percentage_without_changed_in_fm']

    #print("PRINTING***=", len(merged_df))
    #print(merged_df.columns)
    ##exit()
    #
    #merged_df.to_csv('Results/Percentage_of_the_coverage_by_existing_test.csv', index=False)
    #exit()
#'''    df_search = pd.read_csv('Results/Percentage_of_the_coverage_by_existing_test.csv')
#    print('Percentage_of_the_coverage_by_existing_test=',len(df_search))
#    #exit()
#    matched_rows = []
#    #Input: Results/Coverage_of_Only_Changed_Lines_in_FM.csv
#    file_main = "Results/Coverage_of_Only_Changed_Lines_in_FM.csv"
#    df_main = pd.read_csv(file_main, on_bad_lines=bad_line_handler, engine='python')
#    print("Coverage_Only_Changes_Lines=", len(df_main))
#
#    # Iterate over each row in the main DataFrame
#    for index, row in df_main.iterrows():
#        # Extract the relevant fields for the current row
#        proj_name = row['proj_name']
#        test_filename = row['test_filename']
#        test_method = row['test_method']
#        fm_method = row['fm_method']
#        coverage_percentage_main = row['coverage_percentage']  # Keep the coverage percentage from main file
#        
#        # Search in the other CSV file for a matching row
#        matching_row = df_search[
#            (df_search['proj_name'] == proj_name) & 
#            (df_search['test_filename'] == test_filename) & 
#            (df_search['test_method'] == test_method) & 
#            (df_search['fm_method'] == fm_method)
#        ]
#        
#        # If a match is found, extract the required columns and add to the matched_rows list
#        if not matching_row.empty:
#            coverage_percentage_with_changed_fm = matching_row['coverage_percentage_with_changed_fm'].values[0]
#            coverage_percentage_without_changed_in_fm = matching_row['coverage_percentage_without_changed_in_fm'].values[0]
#
#            # Add the matched row details and coverage information to the list
#            matched_rows.append({
#                'proj_name': proj_name,
#                'test_filename': test_filename,
#                'test_method': test_method,
#                'fm_method': fm_method,
#                'coverage_percentage_with_only_changed_lines_in_fm': coverage_percentage_main,  # Keep coverage from main file
#                'coverage_percentage_with_changed_fm': coverage_percentage_with_changed_fm,
#                'coverage_percentage_without_changed_in_fm': coverage_percentage_without_changed_in_fm
#            })
##exit()
## Convert the matched rows to a DataFrame
#df_matched = pd.DataFrame(matched_rows)
#
## Save the results to a CSV file
#df_matched.to_csv('Results/coverage_percentages.csv', index=False)
#print("Matching rows with coverage information saved to 'Results/coverage_percentages.csv'")
#print(len(df_matched))
#exit()'''
#========Main Technique============
    matched_rows = []
    non_matching_rows = []
#    #Input: Results/Coverage_of_Only_Changed_Lines_in_FM.csv
    file_search = "Results/coverage_percentages.csv"
    df_search = pd.read_csv(file_search)
    df_main = pd.read_csv("Results/Claude3-5_690_tests_with_Refined_Tests_Meth_CC_with_Static_slice_with_updated_prompt_1_shanto6_after_data_clean_1.csv")
    print('df_search=',len(df_search))
    print('df_main=',len(df_main))
    
    pp_df = df_search[['proj_name','test_filename','test_method','fm_method']]
    pp_df.to_csv("Proj-Test-FM.csv", index=False)
    exit()
    # Iterate over each row in the main DataFrame
    for index, row in df_main.iterrows():
        # Extract the relevant fields for the current row
        proj_name = row['proj_name']
        test_filename = row['test_filename']
        test_method = row['test_method']
        fm_method = row['fm_method']
        coverage_percentage_static_technique = row['coverage_percentage']  # Keep the coverage percentage from main file
        print(test_method, ",", coverage_percentage_static_technique)
        
        # Search in the other CSV file for a matching row
        matching_row = df_search[
            (df_search['proj_name'] == proj_name) & 
            (df_search['test_filename'] == test_filename) & 
            (df_search['test_method'] == test_method) & 
            (df_search['fm_method'] == fm_method)
        ]
        # If no match is found, add the current row to the list of non-matching rows
        if matching_row.empty:
            non_matching_rows.append(row)


        # If a match is found, extract the required columns and add to the matched_rows list
        if not matching_row.empty:
            coverage_percentage_with_only_changed_lines_in_fm = matching_row['coverage_percentage_with_only_changed_lines_in_fm'].values[0]
            coverage_percentage_with_changed_fm = matching_row['coverage_percentage_with_changed_fm'].values[0]
            coverage_percentage_without_changed_in_fm = matching_row['coverage_percentage_without_changed_in_fm'].values[0]

            # Add the matched row details and coverage information to the list
            matched_rows.append({
                'proj_name': proj_name,
                'test_filename': test_filename,
                'test_method': test_method,
                'fm_method': fm_method,
                'coverage_percentage_static_technique': coverage_percentage_static_technique,
                'coverage_percentage_with_only_changed_lines_in_fm': coverage_percentage_with_only_changed_lines_in_fm,  # Keep coverage from main file
                'coverage_percentage_with_changed_fm': coverage_percentage_with_changed_fm,
                'coverage_percentage_without_changed_in_fm': coverage_percentage_without_changed_in_fm
            })

# Convert the non-matching rows list into a DataFrame for easy visualization
df_non_matching = pd.DataFrame(non_matching_rows)
df_non_matching.to_csv("Non-matching_Rows.csv", index=False)
# Display the non-matching rows to the user
#import ace_tools as tools; tools.display_dataframe_to_user(name="Non-matching Rows", dataframe=df_non_matching)
exit() 

# Convert the matched rows to a DataFrame
df_matched = pd.DataFrame(matched_rows)

# Save the results to a CSV file
df_matched.to_csv('Results/coverage_percentages_with_static_result.csv', index=False)
print("Matching rows with coverage information saved to 'Results/coverage_percentages_with_static_result.csv'")
exit()        
    
    #import pandas as pd
    #
    #df = pd.read_csv('Results/Percentage_of_the_coverage_by_existing_test.csv')
    #
    ## Check for the column name and ensure it's correct
    ##df.columns
    #
    ## Calculate avg, min, and max of coverage_percentage_without_changed_in_fm
    #avg_coverage = df['coverage_percentage_without_changed_in_fm'].mean()
    #min_coverage = df['coverage_percentage_without_changed_in_fm'].min()
    #max_coverage = df['coverage_percentage_without_changed_in_fm'].max()
    #
    ## Create bins for the percentage ranges 0-10%, 11-20%, etc.
    #bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    #labels = ["0-10%", "11-20%", "21-30%", "31-40%", "41-50%", "51-60%", "61-70%", "71-80%", "81-90%", "91-100%"]
    #df['coverage_range'] = pd.cut(df['coverage_percentage_without_changed_in_fm'], bins=bins, labels=labels, include_lowest=True)
    #
    ## Count the number of tests in each range
    #coverage_counts = df['coverage_range'].value_counts().sort_index()
    #
    #print(avg_coverage, min_coverage, max_coverage)
    #print(coverage_counts)
    
    
    
    
    #
    
    #df_selected = df[selected_columns]
    #selected_columns.to_csv('extracted_col.csv', index=False)
    
