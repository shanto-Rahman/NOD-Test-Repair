import pandas as pd

# Function to filter rows where COT == 0
def filter_cot_zero(df):
    return df[df['COT'] == 0]

# Load the three CSV files into DataFrames
df1 = pd.read_csv('repaired_results_NA.csv')
df2 = pd.read_csv('repaired_results_Static.csv')
df3 = pd.read_csv('repaired_results_Dynamic.csv')


# Apply the filter to each DataFrame to only include rows with COT == 0
df1 = filter_cot_zero(df1)
df2 = filter_cot_zero(df2)
df3 = filter_cot_zero(df3)

# Find rows in df3 that are not in df1
unique_in_df3_vs_df1 = pd.merge(df3, df1, on=['proj_name', 'fm_name', 'unit_test_name'], how='left', indicator=True)
unique_in_df3_vs_df1 = unique_in_df3_vs_df1[unique_in_df3_vs_df1['_merge'] == 'left_only']
unique_in_df3_vs_df1 = unique_in_df3_vs_df1.drop(columns='_merge')

# Find rows in df3 that are not in df2
unique_in_df3_vs_df2 = pd.merge(df3, df2, on=['proj_name', 'fm_name', 'unit_test_name'], how='left', indicator=True)
unique_in_df3_vs_df2 = unique_in_df3_vs_df2[unique_in_df3_vs_df2['_merge'] == 'left_only']
unique_in_df3_vs_df2 = unique_in_df3_vs_df2.drop(columns='_merge')

# Find rows in df3 that are unique compared to both df1 and df2
unique_in_df3 = pd.merge(unique_in_df3_vs_df1, unique_in_df3_vs_df2, on=['proj_name', 'fm_name', 'unit_test_name'])

# Save the unique rows to a CSV file
unique_in_df3.to_csv('unique_in_dynamic.csv', index=False)

# Print the number of unique rows in df3 that are not in df1 or df2
print(f"Number of unique rows in dynamic slice that are not in df1 or df2: {len(unique_in_df3)}")
# Find rows in df1 that are not in df2
unique_in_df1_vs_df2 = pd.merge(df1, df2, on=['proj_name', 'fm_name', 'unit_test_name'], how='left', indicator=True)
unique_in_df1_vs_df2 = unique_in_df1_vs_df2[unique_in_df1_vs_df2['_merge'] == 'left_only']
unique_in_df1_vs_df2 = unique_in_df1_vs_df2.drop(columns='_merge')

# Find rows in df1 that are not in df3
unique_in_df1_vs_df3 = pd.merge(df1, df3, on=['proj_name', 'fm_name', 'unit_test_name'], how='left', indicator=True)
unique_in_df1_vs_df3 = unique_in_df1_vs_df3[unique_in_df1_vs_df3['_merge'] == 'left_only']
unique_in_df1_vs_df3 = unique_in_df1_vs_df3.drop(columns='_merge')

# Find rows in df1 that are unique compared to both df2 and df3
unique_in_df1 = pd.merge(unique_in_df1_vs_df2, unique_in_df1_vs_df3, on=['proj_name', 'fm_name', 'unit_test_name'])

# Save the unique rows to a CSV file
unique_in_df1.to_csv('unique_in_df1.csv', index=False)
print(f"Number of unique rows in without_any_slice that are not in df3 or df2: {len(unique_in_df1)}")

# 2. Unique rows in df2 that are not in df1 and df3
# Find rows in df2 that are not in df1
unique_in_df2_vs_df1 = pd.merge(df2, df1, on=['proj_name', 'fm_name', 'unit_test_name'], how='left', indicator=True)
unique_in_df2_vs_df1 = unique_in_df2_vs_df1[unique_in_df2_vs_df1['_merge'] == 'left_only']
unique_in_df2_vs_df1 = unique_in_df2_vs_df1.drop(columns='_merge')

# Find rows in df2 that are not in df3
unique_in_df2_vs_df3 = pd.merge(df2, df3, on=['proj_name', 'fm_name', 'unit_test_name'], how='left', indicator=True)
unique_in_df2_vs_df3 = unique_in_df2_vs_df3[unique_in_df2_vs_df3['_merge'] == 'left_only']
unique_in_df2_vs_df3 = unique_in_df2_vs_df3.drop(columns='_merge')

# Find rows in df2 that are unique compared to both df1 and df3
unique_in_df2 = pd.merge(unique_in_df2_vs_df1, unique_in_df2_vs_df3, on=['proj_name', 'fm_name', 'unit_test_name'])

# Save the unique rows to a CSV file
unique_in_df2.to_csv('unique_in_df2.csv', index=False)
print(f"Number of unique rows in static slice that are not in df1 or df3: {len(unique_in_df2)}")

# Concatenate the DataFrames
combined_df = pd.concat([df1, df2, df3])
# Drop duplicates based on 'proj_name', 'fm_name', 'unit_test_name' to get unique tests
unique_tests_df = combined_df.drop_duplicates(subset=['proj_name', 'fm_name', 'unit_test_name'])
# Count the number of unique tests
total_unique_tests = len(unique_tests_df)
# Save the unique tests to a CSV file if needed
unique_tests_df.to_csv('total_unique_tests.csv', index=False)

# Print the number of unique tests
print(f"Total unique tests that are fixed across all three CSVs: {total_unique_tests}")

# Merge df1 and df2 on 'proj_name', 'fm_name', 'unit_test_name'
common_df1_df2 = pd.merge(df1, df2, on=['proj_name', 'fm_name', 'unit_test_name'])

# Merge the result with df3 to find rows common across all three DataFrames
common_all = pd.merge(common_df1_df2, df3, on=['proj_name', 'fm_name', 'unit_test_name'])

# Count the number of common rows
total_common_tests = len(common_all)

# Save the common rows to a CSV file if needed
common_all.to_csv('common_across_all.csv', index=False)

# Print the number of common tests
print(f"Number of tests common across all three CSVs: {total_common_tests}")
exit()

# Concatenate the DataFrames for easy comparison
combined_df = pd.concat([df1, df2, df3])
common_rows = pd.merge(pd.merge(df1, df2, on=['proj_name', 'fm_name', 'unit_test_name']), df3, on=['proj_name', 'fm_name', 'unit_test_name'])
# Save the common rows to a CSV file
common_rows.to_csv('common_rows.csv', index=False)

# Print the number of common rows
print(f"Number of common rows: {len(common_rows)}")

# Find the unique rows in each DataFrame
# Unique to df1
unique_to_df1 = pd.concat([df1, common_rows]).drop_duplicates(keep=False)

# Unique to df2
unique_to_df2 = pd.concat([df2, common_rows]).drop_duplicates(keep=False)

# Unique to df3
unique_to_df3 = pd.concat([df3, common_rows]).drop_duplicates(keep=False)

# Save the unique rows to separate CSV files
unique_to_df1.to_csv('unique_to_file1.csv', index=False)
unique_to_df2.to_csv('unique_to_file2.csv', index=False)
unique_to_df3.to_csv('unique_to_file3.csv', index=False)

# Print the number of unique rows in each file
print(f"Number of unique rows in file1: {len(unique_to_df1)}")
print(f"Number of unique rows in file2: {len(unique_to_df2)}")
print(f"Number of unique rows in file3: {len(unique_to_df3)}")

# Find common rows between file1 and file2, and between file1 and file3
common_rows_file1_file2 = pd.merge(unique_to_df1, unique_to_df2, on=['proj_name', 'fm_name', 'unit_test_name'])
common_rows_file1_file3 = pd.merge(unique_to_df1, unique_to_df3, on=['proj_name', 'fm_name', 'unit_test_name'])

# Calculate the number of different rows
diff_rows_file1_file2 = len(unique_to_df1) - len(common_rows_file1_file2)
diff_rows_file1_file3 = len(unique_to_df1) - len(common_rows_file1_file3)

# Output the results
print(f"Number of rows in file1 different from file2: {diff_rows_file1_file2}")
print(f"Number of rows in file1 different from file3: {diff_rows_file1_file3}")


## Drop duplicates to find unique rows across all DataFrames
#unique_rows = combined_df.drop_duplicates(keep=False)
#
## Find the common rows by using the groupby method and filtering
#common_rows = combined_df[combined_df.duplicated(keep=False)]
#
## Optional: Save the results to CSV files
#unique_rows.to_csv('unique_rows.csv', index=False)
#common_rows.to_csv('common_rows.csv', index=False)
#
#print("Unique rows have been saved to 'unique_rows.csv'.")
#print("Common rows have been saved to 'common_rows.csv'.")
