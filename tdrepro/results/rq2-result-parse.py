input_filename = "RQ2-Result-Final.csv"
output_filename = "RQ2-Result-PerRowCounts.csv"

with open(input_filename, "r") as infile, open(output_filename, "w") as outfile:
    for line in infile:
        parts = line.strip().split(",")
        if len(parts) < 5:
            continue
        binary_str = parts[4].strip(";")
        count_ones = binary_str.split(";").count("1")

        # Write the original line + count to output
        outfile.write(f"{line.strip()},{count_ones}\n")

#count = 0
#with open(input_filename, "r") as f:
#    for line in f:
#        parts = line.strip().split(",")
#        if len(parts) < 5:
#            continue
#        binary_str = parts[4].strip(";")  # Get the 5th column and remove trailing semicolon
#        ones = binary_str.split(";").count("1")
#        count += ones
#
#        print("Total number of 1s in the last column:", count)
#        exit()

