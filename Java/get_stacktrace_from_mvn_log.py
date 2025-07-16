import re
import logging
import base64
from os import path
import hashlib
import pandas as pd

def extract_failure_traces(log_path):
    exception_start = re.compile(r'^[a-zA-Z0-9_.]+(?:Exception|Error|Failure):')
    stack_line = re.compile(r'^\s+at\s')
    caused_by = re.compile(r'^\s*Caused by:')
    failed_test_line = re.compile(r'^\s*Failed tests:\s*$')
    failed_test_entry = re.compile(r'^\s{2,}.*\):')  # Indented failure line
    compact_failed_test_entry = re.compile(r'^\s*Failed tests:\s+(.*\):.*)')  # One-line form

    failures = []
    in_trace = False
    trace_buf = []
    found_stacktrace = False
    summary_failures = []
    in_failed_summary = False

    with open(log_path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip()

            # Handle one-line summary format
            m = compact_failed_test_entry.match(line)
            if m:
                summary_failures.append(m.group(1).strip())
                continue

            # Handle start of indented summary section
            if failed_test_line.match(line):
                in_failed_summary = True
                continue
            elif in_failed_summary:
                if failed_test_entry.match(line):
                    summary_failures.append(line.strip())
                elif line.strip() == "":
                    in_failed_summary = False  # end of section

            # Stacktrace block detection
            if exception_start.match(line):
                if trace_buf:
                    failures.append('\n'.join(trace_buf))
                    trace_buf = []
                in_trace = True
                found_stacktrace = True
                trace_buf.append(line)
            elif in_trace and (stack_line.match(line) or caused_by.match(line)):
                trace_buf.append(line)
            elif in_trace and line.strip() == "":
                if trace_buf:
                    failures.append('\n'.join(trace_buf))
                    trace_buf = []
                in_trace = False
            elif in_trace:
                # non-stack line ends the block
                if trace_buf:
                    failures.append('\n'.join(trace_buf))
                    trace_buf = []
                in_trace = False

    if trace_buf:
        failures.append('\n'.join(trace_buf))

    # Only add summary-style failures if no stack traces found
    if not found_stacktrace:
        failures.extend(summary_failures)

    return failures


def get_failure_str(failure_file):
    # Note: this refers to the failure.log file which is used by each run.
    # This function returns the most recent failure.

    if not path.exists(failure_file):
        return "NoFail"
    with open(failure_file, "r") as failure_file:
        failure_str = failure_file.read()
        # logging.debug("Failure from " + test_method)
        logging.debug(failure_str)

        if failure_str == SLEEPY_TIMEOUT_FAIL_STR or failure_str == FAILURE_THAT_COULD_NOT_BE_LOGGED:
            # Since the generator will remove the sleepy timeout string (does not match a package prefix)
            # We need to return it now.
            return failure_str

        failure_str_parts = failure_str.partition('\n')

        failure_exception_line = failure_str_parts[0]
        failure_exception_line = replace_number_by_x(failure_exception_line)
        
        failure_rest = failure_str_parts[2]

        failure_rest = remove_bottom_trace_parts(failure_rest)

        failure_rest_base64 = flake_rake_base64_encode(failure_rest)
        failure_str = f'{failure_exception_line}FlakeRakeB64StackTrace={failure_rest_base64}'

        # Handle if we dont find anything.
        if failure_str.strip() == "":
            failure_str = "NoFail"
    return failure_str


def flake_rake_base64_encode(arg):
    return base64.b64encode(arg.encode('ascii')).decode('ascii')


def flake_rake_base64_decode(arg):
    return base64.b64decode(arg.encode('ascii')).decode('ascii')



def remove_bottom_trace_parts(partial_log):
    """
    Remove the trace parts from the bottom of the stack trace. We need to remove the parts
    after the line that contains "at org.junit.runners.ParentRunner.run(ParentRunner.java"
    """
    for line in partial_log.splitlines():
        if "at org.junit.runners.ParentRunner.run(ParentRunner.java" in line:
            # return partial_log.splitlines()[:i+1], but we need to convert it to string, \n
            # return '\n'.join(partial_log.splitlines()[:i+1])
            return '\n'.join(partial_log.splitlines()[:partial_log.splitlines().index(line) + 1])

    return partial_log


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

    def lcs(s1, s2):
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
def stacktrace_similarity_score(stacktrace1: str, stacktrace2: str) -> float:
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
    # print("lcs match:", lcs[1])
    # print(min(len(parts1), len(parts2)))
    # print("lcs length:", lcs_length)
    score = lcs_length / min(len(parts1), len(parts2))
    # score = (len(top_matches) + len(bottom_matches)) / (2 * total_compared) if total_compared > 0 else 0.0
    return score


def sanitize_stacktrace(failure_stacktrace_isolated):
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



def get_unique_failures_idoft_remaining(output_file):
    idoft = "data/idoft_remaining.csv"
    # basepath_failed_logs = "../baseline_10k_reruns_failing_runs_only"
    basepath_failed_logs = "/scratch/tbaral/ase26/nod-rr/run_10k/NOD-Test-Repair/Java/rerun-logs_remaining"

    idoft_dataset = pd.read_csv(idoft) #ID,Project-Name,SHA,Module,Test-Name,"#Total-fail(Out of 10,000 runs)",#Uniq-Failure,flaky,Time,Time to get the first failure,# Test failed by 100 runs,Failure Run Id

    # filter the dataset to include those where "flaky" column is 1
    idoft_dataset = idoft_dataset[idoft_dataset['flaky'] == 1]

    for index, row in idoft_dataset.iterrows():
        project_name = row['Project-Name']
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


        for failure_run_id in failure_run_ids:
            failure_log_file = path.join(basepath_failed_logs, f"{test_id}-{test_name}-{failure_run_id}.txt")
            if path.exists(failure_log_file):
                found = False
                failure_str = extract_failure_traces(failure_log_file)
                failure_str = sanitize_stacktrace(failure_str)

                # if failure_str is empty, we skip it
                if not failure_str:
                    # retry with the next run id, may be we mistakenly put one run id instead of the other
                    failure_run_id_tmp = str(int(failure_run_id) + 1)
                    failure_log_file = path.join(basepath_failed_logs, f"{test_id}-{test_name}-{failure_run_id_tmp}.txt")
                    if path.exists(failure_log_file):
                        failure_str = extract_failure_traces(failure_log_file)
                        failure_str = sanitize_stacktrace(failure_str)
                    if not failure_str:
                        # look for failure run_id -1
                        failure_run_id_tmp = str(int(failure_run_id_tmp) - 1)
                        failure_log_file = path.join(basepath_failed_logs, f"{test_id}-{test_name}-{failure_run_id_tmp}.txt")
                        if path.exists(failure_log_file):
                            failure_str = extract_failure_traces(failure_log_file)
                            failure_str = sanitize_stacktrace(failure_str)
                        if not failure_str:
                            test_ids_with_issues.add(test_id)
                            # print(f"Skipping {test_name} ({test_id}) because failure_str is empty and no next run found.")
                            continue

                # if unique_failure_list is empty, add the first failure. It should be a list of tuples, (failure_str, [failure_run_id])
                if not unique_failure_list:
                    unique_failure_list.append((failure_str, [failure_run_id]))
                    # print(f"First failure for {test_name} ({test_id}): {failure_str}")
                else:
                    # Check if the failure_str is already in the list
                    for i, (existing_failure_str, run_ids) in enumerate(unique_failure_list):
                        # check similarity score
                        score = stacktrace_similarity_score(existing_failure_str, failure_str)
                        if score > 0.9:  # You can adjust the threshold as needed
                            found = True
                            run_ids.append(failure_run_id)
                            unique_failure_list[i] = (existing_failure_str, run_ids)
                            break
                    if not found:
                        unique_failure_list.append((failure_str, [failure_run_id]))

            else:
                print(f"Failure log file {failure_log_file} does not exist.")

        # now we save a new row for each unique failure
        # if unique_failure_list is empty, we skip it
        if not unique_failure_list:
            print(f"Skipping {test_name} ({test_id}) because no unique failures found.")
            continue

        for unique_failure_str, run_ids in unique_failure_list:
            run_ids_str = ';'.join(run_ids)
            first_run_id = run_ids[0]
            stacktrace_md5 = get_md5_from_stacktrace(unique_failure_str)
            count_run_ids = len(run_ids)
            slug = project_name
            with open(output_file, "a") as f:
                f.write(f'{test_id},{slug},{sha},{module},{test_name},{first_run_id},{stacktrace_md5},"{unique_failure_str}",{run_ids_str},{count_run_ids}\n')



def get_unique_failures_idoft(output_file):
    idoft = "data/idoft_69.csv"
    # basepath_failed_logs = "../baseline_10k_reruns_failing_runs_only"
    basepath_failed_logs = "/scratch/tbaral/ase26/nod-rr/run_10k/NOD-Test-Repair/Java/rerun-logs_first69"

    idoft_dataset = pd.read_csv(idoft) #ID,Project-Name,SHA,Module,Test-Name,"#Total-fail(Out of 10,000 runs)",#Uniq-Failure,flaky,Time,Time to get the first failure,# Test failed by 100 runs,Failure Run Id

    # filter the dataset to include those where "flaky" column is 1
    idoft_dataset = idoft_dataset[idoft_dataset['flaky'] == 1]

    for index, row in idoft_dataset.iterrows():
        project_name = row['Project-Name']
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


        for failure_run_id in failure_run_ids:
            failure_log_file = path.join(basepath_failed_logs, f"{test_id}-{test_name}-{failure_run_id}.txt")
            if path.exists(failure_log_file):
                found = False
                failure_str = extract_failure_traces(failure_log_file)
                failure_str = sanitize_stacktrace(failure_str)

                # if failure_str is empty, we skip it
                if not failure_str:
                    # retry with the next run id, may be we mistakenly put one run id instead of the other
                    failure_run_id_tmp = str(int(failure_run_id) + 1)
                    failure_log_file = path.join(basepath_failed_logs, f"{test_id}-{test_name}-{failure_run_id_tmp}.txt")

                    if path.exists(failure_log_file):
                        failure_str = extract_failure_traces(failure_log_file)
                        failure_str = sanitize_stacktrace(failure_str)
                    
                    if not failure_str:
                        # print(f"Skipping {test_name} ({test_id}) because failure_str is empty and no next run found.")
                        # look for failure run_id -1
                        failure_run_id_tmp = str(int(failure_run_id) - 1)
                        failure_log_file = path.join(basepath_failed_logs, f"{test_id}-{test_name}-{failure_run_id_tmp}.txt")
                        if path.exists(failure_log_file):
                            failure_str = extract_failure_traces(failure_log_file)
                            failure_str = sanitize_stacktrace(failure_str)
                        if not failure_str:
                            test_ids_with_issues.add(test_id)
                            continue

                # if unique_failure_list is empty, add the first failure. It should be a list of tuples, (failure_str, [failure_run_id])
                if not unique_failure_list:
                    unique_failure_list.append((failure_str, [failure_run_id]))
                    # print(f"First failure for {test_name} ({test_id}): {failure_str}")
                else:
                    # Check if the failure_str is already in the list
                    for i, (existing_failure_str, run_ids) in enumerate(unique_failure_list):
                        # check similarity score
                        score = stacktrace_similarity_score(existing_failure_str, failure_str)
                        if score > 0.9:  # You can adjust the threshold as needed
                            found = True
                            run_ids.append(failure_run_id)
                            unique_failure_list[i] = (existing_failure_str, run_ids)
                            break
                    if not found:
                        unique_failure_list.append((failure_str, [failure_run_id]))

            else:
                print(f"Failure log file {failure_log_file} does not exist.")

        # now we save a new row for each unique failure
        # if unique_failure_list is empty, we skip it
        if not unique_failure_list:
            print(f"Skipping {test_name} ({test_id}) because no unique failures found.")
            continue

        for unique_failure_str, run_ids in unique_failure_list:
            run_ids_str = ';'.join(run_ids)
            first_run_id = run_ids[0]
            stacktrace_md5 = get_md5_from_stacktrace(unique_failure_str)
            count_run_ids = len(run_ids)
            slug = project_name
            with open(output_file, "a") as f:
                f.write(f'{test_id},{slug},{sha},{module},{test_name},{first_run_id},{stacktrace_md5},"{unique_failure_str}",{run_ids_str},{count_run_ids}\n')



# create a set of test ids that have issues
test_ids_with_issues = set()


if __name__ == "__main__":
    output_file = "data/idoft_unique_failures_all.csv"
    with open(output_file, "w") as f:
        f.write("ID,slug,sha,module,test_name,run_id,stacktrace_md5,stacktrace,all_run_ids,count_run_ids\n")
    get_unique_failures_idoft(output_file)
    get_unique_failures_idoft_remaining(output_file)

    # print test ids with issues
    if test_ids_with_issues:
        print("Test ids with issues:")
        for test_id in test_ids_with_issues:
            print(test_id)

exit(0)


file="/scratch/tbaral/ase26/nod-rr/run_10k/NOD-Test-Repair/Java/rerun-logs_first69/13-org.java_websocket.issues.Issue580Test#runNoCloseBlockingTestScenario4-2228.txt"
failure_stacktrace= extract_failure_traces(file)
failure_stacktrace = sanitize_stacktrace(failure_stacktrace)
print(f"Failure stacktrace: {failure_stacktrace}")



# Example usage
LOGFILE = "baseline_10k_reruns_failing_runs_only/7-tachyon.client.TachyonFSTest#deleteFileTest-20.txt"
LOGFILE2 = "baseline_10k_reruns_failing_runs_only/7-tachyon.client.TachyonFSTest#deleteFileTest-38.txt"

failure_log_file="failure.log"

SLEEPY_TIMEOUT_FAIL_STR = 'SleepyTimeOut(ProbableDeadlock)'
FAILURE_THAT_COULD_NOT_BE_LOGGED = 'FAILURE_THAT_COULD_NOT_BE_LOGGED'


failure_stacktrace_isolated_tmp=extract_failure_traces(LOGFILE)
failure_stacktrace_isolated_tmp2=extract_failure_traces(LOGFILE2)

failure_stacktrace_isolated = sanitize_stacktrace(failure_stacktrace_isolated_tmp)
failure_stacktrace_isolated2 = sanitize_stacktrace(failure_stacktrace_isolated_tmp2)

print(f"Failure stacktrace isolated: {failure_stacktrace_isolated}")
print(f"Failure stacktrace isolated2: {failure_stacktrace_isolated2}")

# failure_stacktrace_flakerake_file = "internal/flakerake_log.log"
# with open(failure_stacktrace_flakerake_file, "r") as f:
#     failure_stacktrace_flakerake = f.read().strip().splitlines()

# failure_stacktrace_flakerake = sanitize_stacktrace(failure_stacktrace_flakerake)

score = stacktrace_similarity_score(failure_stacktrace_isolated, failure_stacktrace_isolated2)
print(f"Similarity score: {score:.2f}")
