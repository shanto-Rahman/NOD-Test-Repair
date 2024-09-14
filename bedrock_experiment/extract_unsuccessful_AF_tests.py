import pandas as pd
import sys
from io import StringIO


def check_substring_in_file(file_path, substring):
    # Open the file in read mode
    with open(file_path, 'r', encoding='utf-8') as file:
        # Read the file content
        file_content = file.read()
        
        # Check if the substring is in the file content
        if substring in file_content:
            return True
        else:
            return False
def collect_line_fm_and_test(proj_name, test_method, fm, count):
    df_data = pd.read_csv("Results/Combined_result_of_fm_and_tests.csv")
    # Define the columns to match
    #columns_to_match = ['proj_name', 'test_filename', 'test_method', 'fm_filename', 'fm_method']
    columns_to_match = ['proj_name', 'test_method', 'fm_method']
    
    matched_rows = df_data[
        (df_data['proj_name'] == proj_name) &
        (df_data['test_method'] == test_method) &
        (df_data['fm_method'] == fm)
    ]
    if not matched_rows.empty:
        count += 1
        return matched_rows, count
    else:
        print('Matched rows found')
        return "NA"

    #if all(col in df_criteria.columns for col in columns_to_match) and all(col in df_data.columns for col in columns_to_match):
    #    filtered_df = df_data[df_data[columns_to_match].apply(tuple, axis=1).isin(
    #        df_criteria[columns_to_match].apply(tuple, axis=1)
    #    )]    
    #    print("Filtered Rows from the Second CSV:")
    #    print(filtered_df)
    #
    #    output_path = 'Results/filtered_results.csv'
    #    filtered_df.to_csv(output_path, index=False)
    #else:
    #    print("Ensure both DataFrames contain the specified columns.")

def to_search_for_duplicate(file_name):
    df = pd.read_csv(file_name)
    columns_to_match = ['proj_name','test_file_path', 'test_method_name', 'fm']
    duplicates = df[df.duplicated(subset=columns_to_match, keep=False)]
    # Select only the specified columns from the duplicates
    duplicates_selected_columns = duplicates[columns_to_match]
    
    duplicates_selected_columns.to_csv("Results/duplicate_selected_col.csv", index=False)
    # Save these duplicate rows to a new CSV file, preserving all instances
    #duplicates.to_csv('Results/duplicate.csv', index=False)

columns_to_compare = ['proj_name', 'test_file_path', 'test_method_name', 'fm']
def collect_test_that_have_assertion_error(file_name):
    
    to_search_for_duplicate(file_name)
    df = pd.read_csv("Results/Claude_690_tests_with_Changed_Focal_Meth_AF.csv")
    assertion_error_tests = df[df['test_pass/fail'] == 'assertion_fail']
     
    assertion_error_tests_selected = assertion_error_tests[columns_to_compare].drop_duplicates(subset=columns_to_compare, keep='first')
    assertion_error_tests_selected.to_csv('All_ASSERT_ERROR_TESTS.csv', index=False)
    
    no_assertion_error_tests = df[df['test_pass/fail'].isna()]
    assertion_error_tests[columns_to_compare].to_csv('Results/assertion_fail_rows.csv', index=False) #The tests whose assertion error happened
    no_assertion_error_tests.to_csv('Results/No_assertion_fail_rows.csv', index=False)
    return len(assertion_error_tests), len(no_assertion_error_tests)

def collect_fixed_tests_assertion_error(filename): 
    #to_search_for_duplicate(filename)

    df = pd.read_csv(filename)
    df_passed_tests = df[df['test_pass/fail'] == 'test_pass'] # Coming from Refined_test_AF.csv 
    df_passed_tests_selected = df_passed_tests[columns_to_compare].drop_duplicates(subset=columns_to_compare, keep='first')
    print('passed tests len=', len(df_passed_tests_selected))
    df_passed_tests_selected.to_csv('Results/Passed_Assertion_Tests.csv', index=False)
    #to_search_for_duplicate('Results/Passed_Assertion_Tests.csv')
    
    df_original_assertion_fail = pd.read_csv('Results/assertion_fail_rows.csv') #This one is coming from the file that made the test error due to the changes   
    df_still_failed_assertion_tests = df[df['test_pass/fail'].isna()] #Results/Claude_690_tests_with_Refined_Tests_Meth_AF.csv


    not_found_test_fix_rows = pd.merge(df_original_assertion_fail, df_still_failed_assertion_tests, on=columns_to_compare, how='inner') #Aim is to look for the common tests and fm accross the files
    test_error_rows = not_found_test_fix_rows[columns_to_compare].drop_duplicates(subset=columns_to_compare, keep='first')
    print('test errors len=', len(test_error_rows))
    test_error_rows.to_csv('Results/intersected_assertion_fail_rows.csv', index=False) # total test error (#test_pass+#test_error = assertion_fail_rows.csv)
    #exit() 
    not_found_test_fix_rows = pd.merge(test_error_rows, df_passed_tests_selected, on=columns_to_compare, how='inner') #Aim is to look for the common tests and fm accross the files
    print('#not found test fix=', len(not_found_test_fix_rows))
    #not_found_test_fix_rows.to_csv('tmp1.csv', index=False)
    #exit()
    not_found_test_fix_rows.to_csv("Results/Failed_To_Fix_Assertion_Error_Tests.csv", index=False) #not fixed
    #to_search_for_duplicate('Results/Failed_To_Fix_Assertion_Error_Tests.csv')
    return len(df_passed_tests), len(not_found_test_fix_rows)

if __name__ == "__main__": 
    #1. How many have assertion errors?
    count_assertion_error, no_assertion_error = collect_test_that_have_assertion_error("Results/Claude_690_tests_with_Changed_Focal_Meth_AF.csv") #Input: Results/Claude_690_tests_with_Changed_Focal_Meth_AF.csv 
    print("assertion_error_tests=",count_assertion_error,", count no_assertion_error=",no_assertion_error)

    #2. How many assertion errors are fixed?
    count_fixed_assertion_error, count_still_assertion_error_tests = collect_fixed_tests_assertion_error("Results/Claude_690_tests_with_Refined_Tests_Meth_AF.csv")
    print( "count_fixed_assertion_error=", count_fixed_assertion_error,",count_still_assertion_error_tests=", count_still_assertion_error_tests)
    exit() 

    ##Results/Claude_690_tests_with_Refined_Tests_Meth_AF.csv

    df_not_assert_error_file = pd.read_csv("Results/not-find-assertion-error.csv") 
    matched_rows_csv = "Results/AttributeErrors.csv"
    count = 0
    for index, row in df_not_assert_error_file.iterrows():
        proj_name = row['proj_name']
        fm = row['fm_method']
        test_method = row['test_method']
        new_search_key = proj_name+"_"+test_method +"_" + fm +"_" 
        csv_with_a_specific_type = sys.argv[1] #csv that contains all attribute error for example (find by searching into the log file) 
        #extract_unsuccessful_AF_tests
        
        if check_substring_in_file(csv_with_a_specific_type, new_search_key):
            #print('find search key', new_search_key)
            matched_row, count = collect_line_fm_and_test(proj_name, test_method, fm, count)
            matched_row.to_csv(matched_rows_csv, mode='a', index=False, header=not bool(index))
 
            print(count)
    #exit() 
    
    
