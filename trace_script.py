import sys
import runpy
import linecache
import pytest

call_stack = []
initial_depth = None  # To store the base depth

# Read arguments
if len(sys.argv) < 2:
    print("Usage: python -m trace_script <script.py> [ftrace.log]")
    sys.exit(1)

script_name = sys.argv[1]
ftracefile = sys.argv[2] if len(sys.argv) > 2 else "ftrace.log"
linetracefile = sys.argv[3] if len(sys.argv) > 3 else "linetrace.log"
method_lists = sys.argv[4] if len(sys.argv) > 4 else "method_lists.log"

def trace_calls(frame, event, arg):
    global initial_depth

    filename = frame.f_code.co_filename
    func_name = frame.f_code.co_name
    # modulename = frame.f_globals["__name__"]
    lineno = frame.f_lineno  # Get the current line number

    # Ignore system files
    if "/lib/python3" in filename or "<" in filename:
        return

    # Retrieve the actual source code line
    code_line = linecache.getline(filename, lineno).strip()

    with open(linetracefile, "a") as linetrace_out:
        linetrace_out.write(f"filename: {filename}, funcname: {func_name}, line {lineno}: {code_line}\n")

    if event == "call":
        if initial_depth is None:
            initial_depth = len(call_stack)  # Set initial depth on first function call

        level = len(call_stack) - initial_depth  # Normalize depth
        call_stack.append(func_name)

        # Print function call details
        with open(ftracefile, "a") as ftrace_out:
            ftrace_out.write(f"filename: {filename}, funcname: {func_name}, level: {level}\n")
        
        with open(method_lists, "a") as method_lists_out:
            method_lists_out.write(f"{filename},{func_name},{level}\n")

    elif event == "return":
        if call_stack:
            call_stack.pop()

    return trace_calls

# Clear previous logs
open(ftracefile, "w").close()
open(linetracefile, "w").close()

with open(method_lists, "w") as method_lists_out:
    method_lists_out.write("filename,method,level\n")

print(f"TALANK Tracing {script_name}...")

sys.settrace(trace_calls)

# Run the target script while keeping tracing enabled
# runpy.run_path(script_name, run_name="__main__")

# test_function = sys.argv[1]  # Example: "tests/test_keras.py::test_fit_sgd"

# Run pytest with the specified test function
pytest.main(["-s", script_name])


sys.settrace(None)  # Disable tracing after execution
