import pandas as pd
import matplotlib.pyplot as plt
import csv

# Path to the uploaded CSV file
data_file = 'Results/airtable-python-wrapper_dependency.csv'

# Read the data using csv.reader and handle irregularities
data = []
with open(data_file, newline='') as csvfile:
    reader = csv.reader(csvfile)
    headers = next(reader)
    for row in reader:
        # Handle rows with an incorrect number of columns by joining fields
        if len(row) > len(headers):
            joined_row = []
            i = 0
            while i < len(row):
                if i < len(headers) - 1:
                    if row[i].startswith('"') and not row[i].endswith('"'):
                        combined = row[i]
                        while not row[i].endswith('"'):
                            i += 1
                            combined += ',' + row[i]
                        joined_row.append(combined)
                    else:
                        joined_row.append(row[i])
                else:
                    joined_row.append(row[i])
                i += 1
            data.append(joined_row)
        else:
            data.append(row)

# Load the cleaned data into a pandas DataFrame
df = pd.DataFrame(data, columns=headers)

# Clean and convert numerical columns
df['args'] = df['args'].astype(int)
df['internal_calls'] = df['internal_calls'].astype(int)
df['external_calls'] = df['external_calls'].astype(int)
df['api_calls'] = df['api_calls'].astype(int)
df['branch_count'] = df['branch_count'].astype(int)

# Process branch types
branch_types_series = df['branch_type'].str.split('#').explode()
branch_types_counts = branch_types_series.value_counts()

# Bar chart for branch types
plt.figure(figsize=(10, 6))
branch_types_counts.plot(kind='bar', color='#66b3ff')
plt.title('Distribution of Branch Types')
plt.xlabel('Branch Type')
plt.ylabel('Count')
plt.tight_layout()

# Save the plot as an image file
plt.savefig('branch_types_distribution.png')

plt.show()

# Pie chart of the calls
calls = ['internal_calls', 'external_calls', 'api_calls']
calls_sum = df[calls].sum()

plt.figure(figsize=(7, 7))

#plt.subplot(1, 2, 1)
#calls_sum.plot(kind='pie', autopct='%1.1f%%', startangle=140, colors=['#ff9999','#66b3ff','#99ff99'])
calls_sum.plot(kind='pie', autopct='%1.1f%%', startangle=140, colors=['#ff9999','#66b3ff','#99ff99'])
plt.title('Distribution of Calls')
plt.ylabel('')
plt.savefig('distribution_of_calls.png')



# Histogram of the number of arguments, branches
plt.subplot(1, 2, 2)
df[['args', 'branch_count']].plot(kind='hist', bins=range(df[['args', 'branch_count']].max().max() + 2), alpha=0.7, edgecolor='black', subplots=True, layout=(1, 2), sharey=True, figsize=(14, 7))
plt.suptitle('Distribution of Arguments and Branches')
plt.tight_layout(rect=[0, 0.03, 1, 0.95])

# Save the plot as an image file
plt.savefig('test_data_statistics.png')

plt.show()

# Additional plot for lines, branch, number of arguments
plt.figure(figsize=(10, 6))

df[['args', 'branch_count']].plot(kind='bar', stacked=True)
plt.title('Comparison of Number of Arguments and Branches')
plt.xlabel('Index')
plt.ylabel('Count')
plt.legend(['Arguments', 'Branches'])
plt.tight_layout()

# Save the plot as an image file
plt.savefig('comparison_statistics.png')

plt.show()
