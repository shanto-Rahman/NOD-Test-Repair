#python3 match_top10_methods.py metadata/embedings/org.java_websocket.issues.Issue580Test.runNoCloseBlockingTestScenario0_qwen_embeddings.csv metadata/embedings/org.java_websocket.issues.Issue580Test.runNoCloseBlockingTestScenario0_llama_embeddings.csv -o out.csv
#!/usr/bin/env python3
import argparse
import os
from typing import List, Tuple
import pandas as pd

REQUIRED_COLS = ["Class", "Method", "Descriptor"]

def load_topk(path: str, k: int) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")
    top = df.head(k)[REQUIRED_COLS].drop_duplicates()
    top["__source__"] = os.path.basename(path)
    return top

def aggregate(csvs: List[str], k: int) -> Tuple[pd.DataFrame, dict]:
    if len(csvs) < 2:
        raise ValueError("Provide at least two CSV paths.")
    tops = [load_topk(p, k) for p in csvs]

    all_union = pd.concat(tops, ignore_index=True)
    # Unique key for matching
    all_union["__key__"] = list(zip(all_union["Class"], all_union["Method"], all_union["Descriptor"]))

    # Build presence map: for each key, which CSVs contain it
    presence = (
        all_union.groupby("__key__")["__source__"]
        .agg(lambda s: sorted(set(s)))
        .reset_index()
        .rename(columns={"__source__": "csvs_having_method"})
    )

    # Expand key back out
    presence[["Class", "Method", "Descriptor"]] = pd.DataFrame(
        presence["__key__"].tolist(), index=presence.index
    )
    presence["num_csvs_topk"] = presence["csvs_having_method"].apply(len)

    out_df = presence[
        ["Class", "Method", "Descriptor", "num_csvs_topk", "csvs_having_method"]
    ].sort_values(
        by=["num_csvs_topk", "Class", "Method", "Descriptor"],
        ascending=[False, True, True, True]
    ).reset_index(drop=True)

    # Summary stats
    N = len(csvs)
    summary = {
        "total_unique": len(out_df),
        "N": N,
        "top_k": k,
        "matched_in_all_N": int((out_df["num_csvs_topk"] == N).sum()),
        "matched_in_exactly_two": int((out_df["num_csvs_topk"] == 2).sum()),
        "frequency_table": out_df["num_csvs_topk"].value_counts().sort_index().to_dict(),
    }
    return out_df, summary

def main():
    ap = argparse.ArgumentParser(description="Match top-K methods across N CSVs for a test.")
    ap.add_argument("csv", nargs="+", help="Two or more CSV files for the test")
    ap.add_argument("-k", "--top-k", type=int, default=10, help="Top K rows to consider from each CSV (default: 10)")
    ap.add_argument("-o", "--out", required=True, help="Output CSV path for the aggregated result")
    args = ap.parse_args()

    out_df, summary = aggregate(args.csv, args.top_k)
    out_df.to_csv(args.out, index=False)

    print(f"Output written to: {args.out}")
    print(f"Top-K per CSV: {summary['top_k']}, Number of CSVs (N): {summary['N']}")
    print(f"Total unique methods in union: {summary['total_unique']}")
    print(f"Matched in all N CSVs: {summary['matched_in_all_N']}")
    print(f"Matched in exactly two CSVs: {summary['matched_in_exactly_two']}")
    print("Counts by how many CSVs contained the method (num_csvs_topk → count):")
    for n, cnt in sorted(summary["frequency_table"].items()):
        print(f"  {n} → {cnt}")

if __name__ == "__main__":
    main()

##python3 match_top10_methods.py metadata/embedings/org.java_websocket.issues.Issue580Test.runNoCloseBlockingTestScenario0_qwen_embeddings.csv metadata/embedings/org.java_websocket.issues.Issue580Test.runNoCloseBlockingTestScenario0_llama_embeddings.csv metadata/embedings/org.java_websocket.issues.Issue580Test.runNoCloseBlockingTestScenario0_llama_embeddings.csv -o out.csv
##!/usr/bin/env python3
#import argparse
#import os
#from typing import List, Tuple
#import pandas as pd
#
#REQUIRED_COLS = ["Class", "Method", "Descriptor"]
#
#def load_top10(path: str) -> pd.DataFrame:
#    df = pd.read_csv(path)
#    missing = [c for c in REQUIRED_COLS if c not in df.columns]
#    if missing:
#        raise ValueError(f"{path} is missing required columns: {missing}")
#    # Take first 10 and keep only the matching columns (dedupe within a file)
#    top = df.head(10)[REQUIRED_COLS].drop_duplicates()
#    top["__source__"] = os.path.basename(path)
#    return top
#
#def aggregate_three(csvs: List[str]) -> Tuple[pd.DataFrame, int, int]:
#    if len(csvs) != 2:
#        raise ValueError("Exactly three CSV paths are required per test.")
#    tops = [load_top10(p) for p in csvs]
#
#    # Union of all unique (Class, Method, Descriptor)
#    all_union = pd.concat(tops, ignore_index=True)
#    all_union["key"] = list(zip(all_union["Class"], all_union["Method"], all_union["Descriptor"]))
#
#    # Build presence map: for each key, set of sources containing it
#    presence = (
#        all_union.groupby("key")["__source__"]
#        .agg(lambda s: sorted(set(s)))
#        .reset_index()
#        .rename(columns={"__source__": "csvs_having_method"})
#    )
#    presence["Class"] = presence["key"].apply(lambda k: k[0])
#    presence["Method"] = presence["key"].apply(lambda k: k[1])
#    presence["Descriptor"] = presence["key"].apply(lambda k: k[2])
#    presence["num_csvs_top10"] = presence["csvs_having_method"].apply(len)
#
#    # Order columns nicely
#    out_df = presence[["Class", "Method", "Descriptor", "num_csvs_top10", "csvs_having_method"]]
#    out_df = out_df.sort_values(by=["num_csvs_top10", "Class", "Method", "Descriptor"], ascending=[False, True, True, True])
#
#    # Summary counts
#    n_all = (out_df["num_csvs_top10"] == 3).sum()
#    n_exactly_two = (out_df["num_csvs_top10"] == 2).sum()
#
#    return out_df, n_all_three, n_exactly_two
#
#def main():
#    ap = argparse.ArgumentParser(description="Match top-10 methods across three CSVs for a test.")
#    ap.add_argument("csv", nargs=2, help="Exactly three CSV files for the test")
#    ap.add_argument("-o", "--out", required=True, help="Output CSV path for the aggregated result")
#    args = ap.parse_args()
#
#    out_df, n_all_three, n_exactly_two = aggregate_three(args.csv)
#
#    # Save
#    out_df.to_csv(args.out, index=False)
#
#    # Report
#    print(f"Output written to: {args.out}")
#    print(f"Matched in all three CSVs (top-10): {n_all_three}")
#    print(f"Matched in exactly two CSVs (top-10): {n_exactly_two}")
#    print(f"Total unique (Class, Method, Descriptor) in union of top-10s: {len(out_df)}")
#
#if __name__ == "__main__":
#    main()
#
