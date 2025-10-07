#!/usr/bin/env python3
import sys, csv
from collections import OrderedDict

def main():
    import argparse
    p = argparse.ArgumentParser(description="Group by first 3 columns and sum last column if 0/1.")
    p.add_argument("input", help="Input CSV file (use - for stdin)")
    p.add_argument("-o", "--output", default="-", help="Output CSV file (default: stdout)")
    p.add_argument("--sort", action="store_true", help="Sort groups alphabetically (default: keep first-seen order)")
    args = p.parse_args()

    # open input / output
    fin = sys.stdin if args.input == "-" else open(args.input, newline="", encoding="utf-8")
    fout = sys.stdout if args.output == "-" else open(args.output, "w", newline="", encoding="utf-8")

    try:
        reader = csv.reader(fin)
        groups = OrderedDict()  # key -> dict(count, sum, has_num)

        for row in reader:
            if not row:
                continue
            # trim whitespace from all fields
            row = [c.strip() for c in row]
            if len(row) < 3:
                # skip malformed lines
                continue

            key = tuple(row[:3])  # (repo, commit, module)
            last = row[-1] if row else ""

            g = groups.get(key)
            if g is None:
                g = {"count": 0, "sum": 0, "has_num": False}
                groups[key] = g

            g["count"] += 1

            # sum only if last field is exactly 0 or 1
            if last in ("0", "1"):
                g["sum"] += int(last)
                g["has_num"] = True

        # optionally sort keys
        keys = sorted(groups.keys()) if args.sort else groups.keys()

        writer = csv.writer(fout)
        # No header, match your example: repo,commit,module,count,sum_or_NA
        for k in keys:
            g = groups[k]
            sum_field = str(g["sum"]) if g["has_num"] else "NA"
            writer.writerow([k[0], k[1], k[2], g["count"], sum_field])
    finally:
        if fin is not sys.stdin: fin.close()
        if fout is not sys.stdout: fout.close()

if __name__ == "__main__":
    main()

