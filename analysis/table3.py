import pandas as pd
import numpy as np

# Load your CSV
df = pd.read_csv("rq2.csv")

# Define bins and labels exactly like your LaTeX table
bins = [-0.001, 0, 10, 25, 50, 75, 99, 100]  # -0.001 ensures 0 maps correctly
labels = ["0", "(0%, 10%]", "(10%, 25%]", "(25%, 50%]", "(50%, 75%]", "(75%, 99%]", "(99%, 100%]"]

df["flakerake_bucket"] = pd.cut(df["Rerun"], bins=bins, labels=labels, include_lowest=True, right=True)
df["tool_bucket"] = pd.cut(df["tool"], bins=bins, labels=labels, include_lowest=True, right=True)

# Create contingency table
table = pd.crosstab(df["tool_bucket"], df["flakerake_bucket"], dropna=False)

# Add row and column totals
table.loc["Total"] = table.sum()
table["Total"] = table.sum(axis=1)

# Print in LaTeX-like format
print(table)
# save the table to a csv
table.to_csv("table3_output.csv")
