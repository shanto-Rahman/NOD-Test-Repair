# input get_similarity_score_stacktrace.py <file1_path> <file2_path>
# Output: similarity_exception_line,similarity_stacktrace,similarity_failure_message
# note that we are only considering the similarity_exception_line for comparing with flakerake's isolated rerun failures

import re
import os
from sentence_transformers import SentenceTransformer, util, SimilarityFunction
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
import sys
import pandas as pd



def extract_failure_traces(log_path):
    exception_start = re.compile(r'^[a-zA-Z0-9_.]+(?:Exception|Error|Failure)\b')
    stack_line = re.compile(r'^\s+at\s')
    caused_by = re.compile(r'^\s*Caused by:')
    failed_test_line = re.compile(r'^\s*Failed tests:\s*$')
    failed_test_entry = re.compile(r'^\s{2,}.*\):')
    compact_failed_test_entry = re.compile(r'^\s*Failed tests:\s+(.*\):.*)')

    stacktrace = None
    exception_line = None
    failure_message = None
    trace_buf = []
    in_trace = False
    in_failed_summary = False
    summary_failures = []

    with open(log_path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip()

            # Handle one-line summary
            m = compact_failed_test_entry.match(line)
            if m:
                summary_failures.append(m.group(1).strip())
                continue

            # Handle indented summary
            if failed_test_line.match(line):
                in_failed_summary = True
                continue
            elif in_failed_summary:
                if failed_test_entry.match(line):
                    summary_failures.append(line.strip())
                elif line.strip() == "":
                    in_failed_summary = False

            # Stacktrace detection
            if exception_start.match(line):
                if not exception_line:
                    exception_line = line
                in_trace = True
                trace_buf = [line]
            elif in_trace and (stack_line.match(line) or caused_by.match(line)):
                trace_buf.append(line)
            elif in_trace and line.strip() == "":
                if trace_buf and not stacktrace:
                    stacktrace = '\n'.join(trace_buf)
                trace_buf = []
                in_trace = False
            elif in_trace:
                if trace_buf and not stacktrace:
                    stacktrace = '\n'.join(trace_buf)
                trace_buf = []
                in_trace = False

    if trace_buf and not stacktrace:
        stacktrace = '\n'.join(trace_buf)

    if summary_failures:
        failure_message = '\n'.join(summary_failures)

    return stacktrace, exception_line, failure_message



def sanitize_stacktrace(failure_stacktrace_isolated):
    failure_stacktrace_isolated = [line.replace('\n', ' ') for line in failure_stacktrace_isolated]
    failure_stacktrace_isolated = [line.replace('\t', '') for line in failure_stacktrace_isolated]
    failure_stacktrace_isolated = [line.replace('at ', '') for line in failure_stacktrace_isolated]
    # if edu.gmu.swe.flaky.sleepy.runner.SleepyTestRunner.main in line, then remove that line
    failure_stacktrace_isolated = [line for line in failure_stacktrace_isolated if 'edu.gmu.swe.flaky.sleepy.runner.SleepyTestRunner.main' not in line]
    failure_stacktrace_isolated = ' '.join(failure_stacktrace_isolated)
    failure_stacktrace_isolated = re.sub(r'\s+', ' ', failure_stacktrace_isolated)
    return failure_stacktrace_isolated



def match_bleu(failure1, failure2):
    """
    Compare two failure traces using case-insensitive BLEU score
    with add-one smoothing (method1), up to 4-grams with equal weights.
    """
    weights = (0.25, 0.25, 0.25, 0.25)
    smoothing = SmoothingFunction().method1

    # Case-insensitive, whitespace tokenized
    reference = [failure2.lower().split()]
    prediction = failure1.lower().split()

    score = sentence_bleu(reference, prediction, weights=weights, smoothing_function=smoothing)
    return score




def semantic_similarity_score(failure1, failure2):
    # if any of the inputs are None, return None
    if failure1 is None or failure2 is None:
        return None
    
    if pd.isna(failure1) or pd.isna(failure2):
        return 0.0

    if not isinstance(failure1, str) or not isinstance(failure2, str):
        return 0.0

    failure1 = failure1.strip()
    failure2 = failure2.strip()

    if not failure1 or not failure2:
        return 0.0

    model = SentenceTransformer('sentence-transformers/stsb-roberta-large')
    model.similarity_fn_name = SimilarityFunction.COSINE

    print(failure1)
    print(failure2)

    # Use raw strings
    failure1 = failure1.lower()
    failure2 = failure2.lower()

    embedding1 = model.encode(failure1, convert_to_tensor=True)
    embedding2 = model.encode(failure2, convert_to_tensor=True)

    similarity = util.cos_sim(embedding1, embedding2).item()  # Convert tensor to float

    return similarity



# file1="/scratch/tbaral/ase26/nod-rr/baseline_10k_reruns_failing_runs_only/104-org.java_websocket.issues.Issue713Test#testIssue-230.txt"
# file2="/scratch/tbaral/ase26/nod-rr/baseline_10k_reruns_failing_runs_only/104-org.java_websocket.issues.Issue713Test#testIssue-442.txt"

file1 = sys.argv[1]
file2 = sys.argv[2]


stacktrace1, exception_line1, failure_message1 = extract_failure_traces(file1)
stacktrace2, exception_line2, failure_message2 = extract_failure_traces(file2)

# Sanitize stacktraces
if stacktrace1 is not None:
    stacktrace1 = sanitize_stacktrace(stacktrace1)
if stacktrace2 is not None:
    stacktrace2 = sanitize_stacktrace(stacktrace2)
if exception_line1 is not None:
    exception_line1 = sanitize_stacktrace(exception_line1)
if exception_line2 is not None:
    exception_line2 = sanitize_stacktrace(exception_line2)
if failure_message1 is not None:
    failure_message1 = sanitize_stacktrace(failure_message1)
if failure_message2 is not None:
    failure_message2 = sanitize_stacktrace(failure_message2)

similarity_stacktrace = semantic_similarity_score(stacktrace1, stacktrace2)
similarity_exception = semantic_similarity_score(exception_line1, exception_line2)
similarity_failure_message = semantic_similarity_score(failure_message1, failure_message2)

# if any of the value is not None then save the .4f value
if similarity_stacktrace is not None:
    similarity_stacktrace = f"{similarity_stacktrace:.4f}"
else:
    similarity_stacktrace = "None"
if similarity_exception is not None:
    similarity_exception = f"{similarity_exception:.4f}"
else:
    similarity_exception = "None"
if similarity_failure_message is not None:
    similarity_failure_message = f"{similarity_failure_message:.4f}"
else:
    similarity_failure_message = "None"

print(f"{similarity_exception},{similarity_stacktrace},{similarity_failure_message}")
