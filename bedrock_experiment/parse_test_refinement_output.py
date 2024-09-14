import os
import sys
import pandas as pd

if __name__ == "__main__":
    file_path = sys.argv[1] #Results/Claude3-5_690_tests_with_Refined_Tests_Meth_AF.csv
    df = pd.read_csv(file_path)
    repaired_results = []
    tests_that_are_not_repaired = []
    for index, row in df.iterrows():
        proj_name = row['proj_name'] 
        if proj_name.strip().startswith('#'):
            continue
        test_file_path = row['test_filename']
        unit_test_name = row['test_method']
        fm_file_path = row['fm_filename']
        fm_name = row['fm_method']
        repaired_test_code = row['repaired_test']
        changed_fm_code = row['changed_fm']
        test_status = row['test_pass/fail']
        cot = row['COT']
        if test_status == "test_pass":
            result_entry = (proj_name, fm_name, unit_test_name)

            # Append the entry to the results list
            #if result_entry not in results:
            if result_entry not in [(r[0], r[1], r[2]) for r in repaired_results]:
                repaired_results.append((proj_name, fm_name, unit_test_name, cot))

    # Extract unique `cot` values
    unique_cots = set(cot for _, _, _, cot in repaired_results)
    
    # Count occurrences of each unique `cot` value
    cot_counts = {cot: 0 for cot in unique_cots}
    
    for _, _, _, cot in repaired_results:
        cot_counts[cot] += 1

    print(f"#test passes: {len(repaired_results)}")
    # Print the count of each unique `cot` value
    #print("Count of each unique `cot` value:")
    for cot in sorted(cot_counts):
        print(f"pass@{cot}: {cot_counts[cot]} tests")

    #Dataset Parsing #Results/Claude3-5_690_tests_with_Changed_Focal_Meth_AF.csv
    print('Dataset Analysis ....')
    data_file_path = sys.argv[2] #Results/Claude3-5_690_tests_with_Changed_Focal_Meth_AF_Updated.csv
    data_df = pd.read_csv(data_file_path)
    assertion_results = []
    attribute_results = []
    for index, row in data_df.iterrows():
        proj_name = row['proj_name'] 
        if proj_name.strip().startswith('#'):
            continue
        test_file_path = row['test_filename']
        unit_test_name = row['test_method']
        fm_file_path = row['fm_filename']
        fm_name = row['fm_method']
        changed_fm_code = row['changed_fm']
        test_status = row['test_pass/fail']
        cot = row['COT']

        if test_status == "assertion_fail":
            assertion_result_entry = (proj_name, fm_name, unit_test_name)

            if assertion_result_entry not in [(r[0], r[1], r[2]) for r in assertion_results]:
                assertion_results.append((proj_name, fm_name, unit_test_name, cot))
        
        #======================================START: To get the tests list that are not repaired ================================= 
        # Check if the (proj_name, fm_name, unit_test_name) is not in repaired_results
        if not any((proj_name, fm_name, unit_test_name) == (r[0], r[1], r[2]) for r in repaired_results):
            tests_that_are_not_repaired.append(row)

        # Convert the non-matching rows into a DataFrame
    non_repaired_tests_df = pd.DataFrame(tests_that_are_not_repaired)
    print('#non repaired tests=',len(non_repaired_tests_df)) 
    # Optionally, save the non-matching rows to a new CSV file
    non_repaired_tests_df.to_csv("Results/non_repaired_tests.csv", index=False)

        #====================================== END: To get the tests list that are not repaired ================================= 

    unique_cots = set(cot for _, _, _, cot in assertion_results)
    
    # Count occurrences of each unique `cot` value
    cot_counts = {cot: 0 for cot in unique_cots}
    
    for _, _, _, cot in assertion_results:
        cot_counts[cot] += 1

    print(f"#Test assertion fail: {len(assertion_results)}")
    for cot in sorted(cot_counts):
        print(f"pass@{cot}: {cot_counts[cot]} tests")


    ###ATTRIBUTE 
    assertion_result_set = set((proj_name, fm_name, unit_test_name) for proj_name, fm_name, unit_test_name, _ in assertion_results)

    for index, row in data_df.iterrows():
        proj_name = row['proj_name'] 
        if proj_name.strip().startswith('#'):
            continue
        test_file_path = row['test_filename']
        unit_test_name = row['test_method']
        fm_file_path = row['fm_filename']
        fm_name = row['fm_method']
        changed_fm_code = row['changed_fm']
        test_status = row['test_pass/fail']
        cot = row['COT']
        if test_status == "attribute_error":
            attribute_result_entry = (proj_name, fm_name, unit_test_name)

            # Append the entry to the results list
            #if result_entry not in results:
            if attribute_result_entry not in assertion_result_set and attribute_result_entry not in [(r[0], r[1], r[2]) for r in attribute_results]:
                attribute_results.append((proj_name, fm_name, unit_test_name, cot))
                df_attribute_to_save = pd.DataFrame(attribute_results, columns=["Project Name", "Focal Method", "Unit Test Name", "COT"])
                df_attribute_to_save.to_csv("Results/attribute_error_list.csv")
    
    unique_cots = set(cot for _, _, _, cot in attribute_results)
    
    # Count occurrences of each unique `cot` value
    cot_counts = {cot: 0 for cot in unique_cots}
    
    for _, _, _, cot in attribute_results:
        cot_counts[cot] += 1

    print(f"#Test attribute error: {len(attribute_results)}")

    for cot in sorted(cot_counts):
        print(f"pass@{cot}: {cot_counts[cot]} tests")


    # Convert the results and assertion_results to sets of (proj_name, fm_name, unit_test_name)
    result_set = set((proj_name, fm_name, unit_test_name) for proj_name, fm_name, unit_test_name, _ in repaired_results)
    
    # Find the intersection of the two sets
    common_entries = result_set.intersection(assertion_result_set)
    
    # Print the number of common entries
    print(f"Number of common entries: {len(common_entries)}")


    attribute_result_set = set((proj_name, fm_name, unit_test_name) for proj_name, fm_name, unit_test_name, _ in attribute_results)
    
    # Find the intersection of the two sets
    common_entries = result_set.intersection(attribute_result_set)
    
    # Print the number of common entries
    print(f"Number of common between attribute error entries: {len(common_entries)}")


    common_entries = assertion_result_set.intersection(attribute_result_set)
    print(f"#common tests between attribute error and assertion error: {len(common_entries)}")


    #====================
    non_matching_rows = []

    data_file_path = sys.argv[3] #Results/Combined_result_of_fm_and_tests.csv
    new_df = pd.read_csv(data_file_path)
    # Compare with the new CSV file
    for index, row in new_df.iterrows():
        proj_name = row['proj_name']
        unit_test_name = row['test_method']
        fm_name = row['fm_method']
        
        # Check if the row matches any in the assertion_results
        #if not any((proj_name, fm_name, unit_test_name) == (r[0], r[1], r[2]) for r in assertion_results):
        #    non_matching_rows.append(row)
        if not any((proj_name, fm_name, unit_test_name) == (r[0], r[1], r[2]) for r in assertion_results) and not any((proj_name, fm_name, unit_test_name) == (r[0], r[1], r[2]) for r in attribute_results):
            non_matching_rows.append(row)
    # Convert the non-matching rows into a DataFrame
    non_matching_df = pd.DataFrame(non_matching_rows)
    
    # Optionally, save the non-matching rows to a new CSV file
    non_matching_df.to_csv("Results/not_assertion_error_or_attribute_errors.csv", index=False)
