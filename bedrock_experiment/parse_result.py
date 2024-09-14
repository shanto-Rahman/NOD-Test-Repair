import pandas as pd
import os
import sys

file_name = sys.argv[1]
df = pd.read_csv(file_name)
print(df.head())
aggregated_data = df.groupby('#proj_name').agg(
    total_rows = pd.NamedAgg(column='#proj_name', aggfunc='size'),  # Count the total rows per project
    API_found_by_jaccard = pd.NamedAgg(column='Static_Analysis_Result', aggfunc=lambda x: x.notna().sum())  # Count non-empty Static_Analysis_Result entries
)

# Reset the index to make 'proj_name' a column again
aggregated_data.reset_index(inplace=True)
# Calculate the percentage of APIs found by Jaccard
aggregated_data['API_found_percentage'] = (aggregated_data['API_found_by_jaccard'] / aggregated_data['total_rows']) * 100

# Construct the desired output format
aggregated_data['output'] = aggregated_data.apply(
    lambda row: f"proj_name={row['#proj_name']},API_found_by_jaccard={row['API_found_by_jaccard']},total_rows={row['total_rows']},API_found_percentage={row['API_found_percentage']:.2f}%",
    axis=1
)


# Print or save the output
print(aggregated_data['output'])

# Optionally, if you want to save this to a file:
aggregated_data.to_csv('Results/output_summary.csv', index=False, columns=['#proj_name', 'API_found_by_jaccard', 'total_rows', 'API_found_percentage'])

