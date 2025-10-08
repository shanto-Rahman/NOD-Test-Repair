# python3 embedding_parse.py output_found_failures_gpt2_embedding.csv
import pandas as pd
import sys
import csv

filename=sys.argv[1] #output_found_failures_gpt2_embedding.csv

df = pd.read_csv(filename)
print(len(df))
count_fail_not_found_row = 0
count_fail_found_row = 0

with open(filename, newline="") as f:
    r = csv.reader(f)
    w = csv.writer(sys.stdout)
    header = next(r)
    w.writerow(header)
    for row in r:
        # trim trailing \r in last field (Windows line endings)
        row[-1] = row[-1].rstrip('\r')
        if row[3]=='no_test_failure' and row[4]=='NA' and row[5]=='NA':
            w.writerow(row)
            count_fail_not_found_row +=1 
        else:
            #w.writerow(row)
            count_fail_found_row +=1
            #exit()

print("count_fail_not_found_row, count_fail_found_row", count_fail_not_found_row, count_fail_found_row)

#print(df["line_number"].iloc[3])
##print(df["log_file"])
#
##print(df["total_time_seconds"])
##print(df["iteration_count"])
#exit()
