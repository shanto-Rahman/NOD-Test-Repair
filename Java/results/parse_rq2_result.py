import csv, sys

infile = sys.argv[1] if len(sys.argv) > 1 else "input.csv"
w = csv.writer(sys.stdout)
w.writerow(["slug","commit","module","test","ones_count","zeros_count"])

with open(infile, newline="", encoding="utf-8") as f:
    r = csv.reader(f)
    for row in r:
        if not row: 
            continue
        slug, commit, module, test, flags = row[0], row[1], row[2], row[3], row[4]
        ones = sum(1 for t in flags.split(";") if t.strip()=="1")
        zeros = sum(1 for t in flags.split(";") if t.strip()=="0")
        w.writerow([slug, commit, module, test, ones, zeros])


#import csv, sys
#
#infile = sys.argv[1] if len(sys.argv) > 1 else "input.csv"
#w = csv.writer(sys.stdout)
#w.writerow(["slug","commit","module","test","iteration_count","total_time_seconds"])
#
#with open(infile, newline="", encoding="utf-8") as f:
#    r = csv.reader(f)
#    for row in r:
#        if not row: 
#            continue
#        slug, commit, module, test = row[0], row[1], row[2], row[3]
#        flags = row[4]                 # e.g., "1;1;1;...;"
#        total_time = row[5]
#        # count non-empty 0/1 tokens (trailing ';' yields empty token—ignored)
#        iteration_count = sum(1 for t in flags.split(";") if t.strip() in ("0","1"))
#        w.writerow([slug, commit, module, test, iteration_count, total_time])
#
