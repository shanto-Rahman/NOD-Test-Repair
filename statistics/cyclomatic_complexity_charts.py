import pandas as pd
import matplotlib.pyplot as plt
import sys

data_file = sys.argv[1] 
df = pd.read_csv(data_file)

# Plot for cyclomatic complexity and line numbers
plt.figure(figsize=(14, 7))

plt.figure(figsize=(10, 6))
plt.scatter(df['line_number'], df['cyclomatic_complexity'], color='blue', alpha=0.6)
plt.title('Cyclomatic Complexity vs. Line Number')
plt.xlabel('Line Number')
plt.ylabel('Cyclomatic Complexity')
plt.grid(True)
plt.savefig('Results/cyclomatic_complexity_vs_line_numbers.png')
plt.show()

# Bar plot for cyclomatic complexity
plt.figure(figsize=(10, 12))
df.sort_values(by='cyclomatic_complexity', inplace=True)
plt.barh(df['method'], df['cyclomatic_complexity'], color='green', alpha=0.6)
plt.title('Cyclomatic Complexity of Methods')
plt.xlabel('Cyclomatic Complexity')
plt.ylabel('Method')
plt.tight_layout()
plt.savefig('Results/cyclomatic_complexity_methods.png')
plt.show()

# Scatter plot for cyclomatic complexity vs. line number
#plt.subplot(1, 2, 1)
#plt.scatter(df['line_number'], df['cyclomatic_complexity'], color='blue', alpha=0.6)
#plt.title('Cyclomatic Complexity vs. Line Number')
#plt.xlabel('Line Number')
#plt.ylabel('Cyclomatic Complexity')
#plt.grid(True)
#
## Bar plot for cyclomatic complexity
#plt.subplot(1, 2, 2)
#df.sort_values(by='cyclomatic_complexity', inplace=True)
#plt.barh(df['method'], df['cyclomatic_complexity'], color='green', alpha=0.6)
#plt.title('Cyclomatic Complexity of Methods')
#plt.xlabel('Cyclomatic Complexity')
#plt.ylabel('Method')
#plt.tight_layout()
#
## Save the plot as an image file
#plt.savefig('Results/cyclomatic_complexity_and_line_numbers.png')

#plt.show()
