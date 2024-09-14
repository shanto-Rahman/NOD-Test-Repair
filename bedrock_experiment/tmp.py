import pandas as pd
#df = pd.read_csv("Results/From-Shiqi/Claude3-5_690_tests_with_Refined_Tests_Meth_CC_with_Dynamic_slice_with_updated_prompt_1_node5_after_data_clean.csv")
#
##print(df['test_status'])
## Filter rows where 'test_pass/fail' is 'test_pass'
#filtered_df = df[df['diff_fm'] == 'test_pass']
##print("df_len=", len(filtered_df))
#
## Extract the 'coverage_percentage' and 'COT' columns
#result_df = filtered_df[['diff_fm', 'changed_fm', 'change_type']]
#
## Save the extracted data to a new CSV (optional)
#result_df.to_csv('extracted_data.csv', index=False)
#
## Print the filtered result (optional)
#print(result_df)
#df = pd.read_csv("Results/From-Shiqi/Claude3-5_690_tests_with_Refined_Tests_Meth_CC_with_Static_slice_with_updated_prompt_1_shanto6_after_data_clean_with_time_1.csv")
#
#filtered_df = df[df['test_pass/fail'] == 'test_pass']
##print("df_len=", len(filtered_df))
#
## Extract the 'coverage_percentage' and 'COT' columns
#result_df = filtered_df[['test_pass/fail', 'coverage_percentage', 'COT']]
#
## Save the extracted data to a new CSV (optional)
#result_df.to_csv('extracted_data.csv', index=False)
#
## Print the filtered result (optional)
#print(result_df)
df = pd.read_csv("Results/Claude3-5_690_tests_with_Refined_Tests_Meth_AF_with_NA_slice.csv")
#filtered_df = df[df['test_pass/fail'] == 'test_pass']
#print("df_len=", len(filtered_df))

# Extract the 'coverage_percentage' and 'COT' columns
result_df = df[['change_type']]

# Save the extracted data to a new CSV (optional)
result_df.to_csv('extracted_data.csv', index=False)

# Print the filtered result (optional)
print(result_df)
