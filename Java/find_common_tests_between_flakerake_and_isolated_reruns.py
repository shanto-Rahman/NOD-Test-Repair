import pandas as pd

# Load test names from first CSV (one column, no header)
with open('../data/flakerake_intersection_isolatedreruns.csv', 'r') as f:
    testnames = set(line.strip() for line in f if line.strip())

    # Load second CSV
    df = pd.read_csv('results/Isolated-Result-for-flakerake.csv', header=None)

    # Check if column 3 (zero-indexed) matches any testname
    df['found'] = df[3].apply(lambda x: 'Found' if x in testnames else '')

    # Save the updated second CSV
    df.to_csv('results/Isolated-Result-for-flakerake.csv', header=False, index=False)

