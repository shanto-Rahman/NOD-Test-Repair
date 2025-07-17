import re
import logging
import base64
from os import path
import hashlib
import pandas as pd
from sentence_transformers import SentenceTransformer, util, SimilarityFunction


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

    return exception_line,stacktrace, failure_message



def replace_number_by_x(line):
    """
    Replace all numbers in the line with 'X'
    :param line: the line to replace numbers in
    :return: the line with numbers replaced by 'X'
    """
    return re.sub(r'\d+', 'X', line)


def compare_stack_traces(a_parts, b_parts):
    """

    :param a_parts:
    :param b_parts:
    :return: top_trace_matching_parts, bottom_trace_matching_parts
    """

    def compare_stack_traces_tops():
        collector = []
        for a_part, b_part in zip(a_parts, b_parts):
            if a_part == b_part:
                collector.append(a_part)
            else:
                break
        return collector

    # def lcs(s1, s2):
    #     matrix = [[[] for x in range(len(s2))] for x in range(len(s1))]
    #     for i in range(len(s1)):
    #         for j in range(len(s2)):
    #             if s1[i] == s2[j]:
    #                 if i == 0 or j == 0:
    #                     matrix[i][j] = list(s1[i])
    #                 else:
    #                     matrix[i][j] = matrix[i - 1][j - 1] + list(s1[i])
    #             else:
    #                 matrix[i][j] = max(matrix[i - 1][j], matrix[i][j - 1], key=len)

    #     cs = matrix[-1][-1]

    #     return len(cs), cs

    def lcs(s1, s2): # This function gets LCS in terms of String
        # print("Computing LCS for stack traces")
        # print("s1:", s1)
        # print("s2:", s2)
        matrix = [[[] for x in range(len(s2))] for x in range(len(s1))]
        for i in range(len(s1)):
            for j in range(len(s2)):
                if s1[i] == s2[j]:
                    if i == 0 or j == 0:
                        matrix[i][j] = [s1[i]]   # FIX: Use [s1[i]] instead of list(s1[i])
                    else:
                        matrix[i][j] = matrix[i - 1][j - 1] + [s1[i]]
                else:
                    matrix[i][j] = max(matrix[i - 1][j], matrix[i][j - 1], key=len)
        cs = matrix[-1][-1]
        return len(cs), cs

    lcs_out = lcs(a_parts, b_parts)
    # print(lcs_out)
    top_parts_in_common = compare_stack_traces_tops()
    a_parts.reverse()
    b_parts.reverse()
    bottom_parts_in_common = compare_stack_traces_tops()
    return tuple([top_parts_in_common, bottom_parts_in_common, lcs_out])



# You need to have compare_stack_traces.compare_stack_traces available!
def stacktrace_similarity_score_lcs(stacktrace1: str, stacktrace2: str) -> float:
    """
    Compute similarity score between two stacktrace strings.
    Returns a float between 0 and 1.
    """
    parts1 = stacktrace1.split(' ')
    parts2 = stacktrace2.split(' ')

    # remove empty parts
    parts1 = [part for part in parts1 if part.strip()]
    parts2 = [part for part in parts2 if part.strip()]

    top_matches, bottom_matches, lcs = compare_stack_traces(parts1, parts2)
    # Similarity as in original code: (top + bottom) / (2 * total compared)
    total_compared = len(parts2)
    lcs_length = len(lcs[1])  # lcs[1] contains the longest common subsequence. The problem is that lcs counts characters not strings. And len(parts1) and len(parts2) count strings.
    score = lcs_length / min(len(parts1), len(parts2))
    return score



def semantic_similarity_score(failure1, failure2):
    # if any of the inputs are None, return None
    if failure1 is None or failure2 is None:
        return None

    model = SentenceTransformer('sentence-transformers/stsb-roberta-large')
    model.similarity_fn_name = SimilarityFunction.COSINE

    # Use raw strings
    failure1 = failure1.lower()
    failure2 = failure2.lower()

    embedding1 = model.encode(failure1, convert_to_tensor=True)
    embedding2 = model.encode(failure2, convert_to_tensor=True)

    similarity = util.cos_sim(embedding1, embedding2).item()  # Convert tensor to float

    return similarity


def sanitize_stacktrace(failure_stacktrace_isolated):
    if failure_stacktrace_isolated is None:
        return None

    if isinstance(failure_stacktrace_isolated, str):
        failure_stacktrace_isolated = failure_stacktrace_isolated.split('\n')


    failure_stacktrace_isolated = [line.replace('\n', ' ') for line in failure_stacktrace_isolated]
    failure_stacktrace_isolated = [line.replace('\t', '') for line in failure_stacktrace_isolated]
    failure_stacktrace_isolated = [line.replace('at ', '') for line in failure_stacktrace_isolated]
    # if edu.gmu.swe.flaky.sleepy.runner.SleepyTestRunner.main in line, then remove that line
    failure_stacktrace_isolated = [line for line in failure_stacktrace_isolated if 'edu.gmu.swe.flaky.sleepy.runner.SleepyTestRunner.main' not in line]
    failure_stacktrace_isolated = ' '.join(failure_stacktrace_isolated)
    failure_stacktrace_isolated = re.sub(r'\s+', ' ', failure_stacktrace_isolated)
    return failure_stacktrace_isolated



def get_md5_from_stacktrace(stacktrace):
    """
    Get the MD5 hash of the stacktrace.
    :param stacktrace: the stacktrace to hash  
    :return: the MD5 hash of the stacktrace
    """
    md5_hash = hashlib.md5()
    md5_hash.update(stacktrace.encode('utf-8'))
    return md5_hash.hexdigest()




def get_unique_failures(data_source, dataset_path, basepath_failed_logs, output_file):
    global failure_index
    dataset = pd.read_csv(dataset_path) #ID,Project-Name,SHA,Module,Test-Name,"#Total-fail(Out of 10,000 runs)",#Uniq-Failure,flaky,Time,Time to get the first failure,# Test failed by 100 runs,Failure Run Id

    # filter the dataset to include those where "flaky" column is 1
    dataset = dataset[dataset['flaky'] == 1]

    for index, row in dataset.iterrows():
        test_id = row['ID']
        test_name = row['Test-Name']
        project_name = row['Project-Name']
        slug = row['Project-Name']
        sha = row['SHA']
        module = row['Module']
        total_fail = row['#Total-fail(Out of 10,000 runs)']
        unique_fail = row['#Uniq-Failure']
        flaky = row['flaky']
        time = row['Time']
        time_to_first_failure = row['Time to get the first failure']
        num_test_failed_by_100_runs = row['# Test failed by 100 runs']
        failure_run_ids = row['Failure Run Id']


        unique_failure_list = []
        test_id = row['ID']
        test_name = row['Test-Name']
        failure_run_ids = row['Failure Run Id'].split(';')

        failure_run_ids = [run_id for run_id in failure_run_ids if run_id.strip()]

        for failure_run_id in failure_run_ids:
            failure_log_file = path.join(basepath_failed_logs, f"{test_id}-{test_name}-{failure_run_id}.txt")
            if path.exists(failure_log_file):
                found = False
                exception_line, failure_stacktrace, failure_message = extract_failure_traces(failure_log_file)
                
                

                exception_line = sanitize_stacktrace(exception_line)
                failure_stacktrace = sanitize_stacktrace(failure_stacktrace)
                failure_message = sanitize_stacktrace(failure_message)

            

                # if failure_str is empty, we skip it
                if not exception_line and not failure_stacktrace and not failure_message:
                    # retry with the next run id, may be we mistakenly put one run id instead of the other
                    failure_run_id_tmp = str(int(failure_run_id) + 1)
                    failure_log_file = path.join(basepath_failed_logs, f"{test_id}-{test_name}-{failure_run_id_tmp}.txt")
                    
                    if path.exists(failure_log_file):
                        exception_line, failure_stacktrace, failure_message = extract_failure_traces(failure_log_file)
                        
                        exception_line = sanitize_stacktrace(exception_line)
                        failure_stacktrace = sanitize_stacktrace(failure_stacktrace)
                        failure_message = sanitize_stacktrace(failure_message)
                        
                    if not exception_line and not failure_stacktrace and not failure_message:
                        # look for failure run_id -1
                        failure_run_id_tmp = str(int(failure_run_id) - 1)
                        failure_log_file = path.join(basepath_failed_logs, f"{test_id}-{test_name}-{failure_run_id_tmp}.txt")
                        
                        if path.exists(failure_log_file):
                            exception_line, failure_stacktrace, failure_message = extract_failure_traces(failure_log_file)
                            
                            exception_line = sanitize_stacktrace(exception_line)
                            failure_stacktrace = sanitize_stacktrace(failure_stacktrace)
                            failure_message = sanitize_stacktrace(failure_message)

                        if not exception_line and not failure_stacktrace and not failure_message:
                            test_ids_with_issues.add(test_id)
                            continue
                # test
                if not exception_line and not failure_stacktrace and not failure_message:
                    print(f"Skipping {test_name} ({test_id}) because failure log file {failure_log_file} does not contain valid failure information.")
                    test_ids_with_issues.add(test_id)
                    continue

                # if unique_failure_list is empty, add the first failure. It should be a list of tuples, (failure_str, [failure_run_id])
                if not unique_failure_list:
                    unique_failure_list.append((exception_line, failure_stacktrace, failure_message, [failure_run_id]))

                else:
                    # Check if the failure_str is already in the list
                    for i, (existing_exception_line, existing_failure_stacktrace, existing_failure_message, run_ids) in enumerate(unique_failure_list):
                        # check similarity score
                        score_exception_line = semantic_similarity_score(existing_exception_line, exception_line)
                        score_failure_stacktrace = semantic_similarity_score(existing_failure_stacktrace, failure_stacktrace)
                        score_failure_message = semantic_similarity_score(existing_failure_message, failure_message)


                        if score_exception_line is not None:
                            score_exception_line = round(score_exception_line, 4)
                        if score_failure_stacktrace is not None:
                            score_failure_stacktrace = round(score_failure_stacktrace, 4)
                        if score_failure_message is not None:
                            score_failure_message = round(score_failure_message, 4)


                        print(score_failure_stacktrace)
                        if score_failure_stacktrace is not None:
                            if score_failure_stacktrace > 0.9:  # You can adjust the threshold as needed
                                found = True
                                run_ids.append(failure_run_id)
                                unique_failure_list[i] = (existing_exception_line, existing_failure_stacktrace, existing_failure_message, run_ids)
                                break
                        else:
                            if score_failure_message is not None:
                                if score_failure_message > 0.9:  # You can adjust the threshold as needed
                                    found = True
                                    run_ids.append(failure_run_id)
                                    unique_failure_list[i] = (existing_exception_line, existing_failure_stacktrace, existing_failure_message, run_ids)
                      
                        if not found:
                            unique_failure_list.append((exception_line, failure_stacktrace, failure_message, [failure_run_id]))

            else:
                print(f"Failure log file {failure_log_file} does not exist.")

        if not unique_failure_list:
            print(f"Skipping {test_name} ({test_id}) because no unique failures found.")
            continue


        for exception_line, failure_stacktrace, failure_message, run_ids in unique_failure_list:
            run_ids_str = ';'.join(run_ids)
            frequency_of_failure = len(run_ids)
            first_run_id = run_ids[0]
            stacktrace_md5 = get_md5_from_stacktrace(failure_stacktrace)
            failure_exceptioin_line = exception_line
            failure_stacktrace = failure_stacktrace
            failure_message = failure_message
            with open(output_file, "a") as f:
                f.write(f'{failure_index},{test_id},{data_source},{slug},{sha},{module},{test_name},{first_run_id},{stacktrace_md5},"{failure_exceptioin_line}","{failure_stacktrace}","{failure_message}",{frequency_of_failure},{run_ids_str}\n')
                failure_index += 1


# create a set of test ids that have issues
test_ids_with_issues = set()
global failure_index
failure_index = 1

if __name__ == "__main__":
    output_file = "data/idoft_unique_failures_all_dataset.csv"
    with open(output_file, "w") as f:
        # f.write("ID,slug,sha,module,test_name,run_id,stacktrace_md5,stacktrace,all_run_ids,count_run_ids\n")
        f.write("failure_ID,test_ID,data_source,slug,sha,module,test_name,first_run_id,stacktrace_md5,failure_exception_line,failure_stacktrace,failure_message,frequency_of_failure,run_ids\n")
    # get_unique_failures_idoft(output_file)
    # get_unique_failures_idoft_remaining(output_file)
    # get_unique_failures_flakerake(output_file)

    get_unique_failures("idoft", "data/idoft_69.csv", "/scratch/tbaral/ase26/nod-rr/run_10k/NOD-Test-Repair/Java/rerun-logs_first69", output_file)
    get_unique_failures("idoft", "data/idoft_remaining.csv", "/scratch/tbaral/ase26/nod-rr/run_10k/NOD-Test-Repair/Java/rerun-logs_remaining", output_file)
    get_unique_failures("flakerake", "data/flakerake_129.csv", "/scratch/tbaral/ase26/nod-rr/baseline_10k_reruns_flakerake_dataset", output_file)

    # print test ids with issues
    if test_ids_with_issues:
        print("Test ids with issues:")
        for test_id in test_ids_with_issues:
            print(test_id)


