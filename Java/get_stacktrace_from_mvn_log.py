import re
import sys

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

    # Write all traces to output
    with open(out_path, "w") as out:
        out.writelines(failures)


if len(sys.argv) != 3:
    print("Usage: python extract_failure_traces.py <log_file> <output_file>")
else:
    LOGFILE = sys.argv[1]
    OUTFILE = sys.argv[2]

extract_failure_traces(LOGFILE, OUTFILE)
