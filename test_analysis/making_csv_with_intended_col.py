import pandas as pd
import sys

file_name = sys.argv[1] 
df = pd.read_csv(file_name)

# Prefix the 'Project' column with a hash
#df['Project'] = df['Project'].apply(lambda x: f'#{x}')
selected_columns = df[['Project', 'Repository', 'CommitId', 'TestCaseFile', 'TestCaseMethod', 'FocalMethodFile', 'FocalMethod', 'NewCommitId']]
selected_columns.rename(columns={'Project': '#Project'}, inplace=True)

selected_columns.to_csv('Results/Part_Real_Tests.csv', index=False)
