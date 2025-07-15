import re
import logging
import base64
from os import path

def extract_failure_traces(log_path, out_path):
    # Pattern for exception header
    exception_start = re.compile(r'^[a-zA-Z0-9_.]+(?:Exception|Error|Failure):')
    # Pattern for stacktrace lines
    stack_line = re.compile(r'^\s+at\s')
    # Optionally, pattern for 'Caused by:', which can appear in the middle of traces
    caused_by = re.compile(r'^\s*Caused by:')

    failures = []
    in_trace = False
    trace_buf = []

    with open(log_path) as f:
        for line in f:
            if exception_start.match(line):
                # Start a new failure trace
                if trace_buf:
                    failures.append('\n'.join(trace_buf) + '\n')
                    trace_buf = []
                in_trace = True
                trace_buf.append(line.rstrip())
            elif in_trace and (stack_line.match(line) or caused_by.match(line)):
                trace_buf.append(line.rstrip())
            elif in_trace and line.strip() == "":
                # End of stacktrace
                if trace_buf:
                    failures.append('\n'.join(trace_buf) + '\n')
                    trace_buf = []
                in_trace = False
            elif in_trace and not stack_line.match(line) and not caused_by.match(line):
                # If the next line is not part of the stacktrace, end
                if trace_buf:
                    failures.append('\n'.join(trace_buf) + '\n')
                    trace_buf = []
                in_trace = False

    # If there's a trace at EOF
    if trace_buf:
        failures.append('\n'.join(trace_buf) + '\n')

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
    print("lcs match:", lcs[1])
    print(min(len(parts1), len(parts2)))
    print("lcs length:", lcs_length)
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


# Usage
# LOGFILE="baseline_10k_reruns_failing_runs_only/2-org.java_websocket.issues.Issue580Test#runNoCloseBlockingTestScenario0-878.txt"
LOGFILE = "baseline_10k_reruns_failing_runs_only/7-tachyon.client.TachyonFSTest#deleteFileTest-20.txt"
LOGFILE2 = "baseline_10k_reruns_failing_runs_only/7-tachyon.client.TachyonFSTest#deleteFileTest-38.txt"

failure_log_file="failure.log"

SLEEPY_TIMEOUT_FAIL_STR = 'SleepyTimeOut(ProbableDeadlock)'
FAILURE_THAT_COULD_NOT_BE_LOGGED = 'FAILURE_THAT_COULD_NOT_BE_LOGGED'


failure_stacktrace_isolated_tmp=extract_failure_traces(LOGFILE, failure_log_file)
failure_stacktrace_isolated_tmp2=extract_failure_traces(LOGFILE2, failure_log_file)

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

