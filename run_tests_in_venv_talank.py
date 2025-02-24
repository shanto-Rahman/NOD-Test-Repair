import os
import subprocess
import shutil
import sys
import venv
import re
import csv
from git import Repo


import toml  # Install with `pip install toml`

import shutil
import re
from tree_sitter import Parser
from tree_sitter_languages import get_language
from collections import defaultdict, deque

# Get the prebuilt Python language parser
PY_LANGUAGE = get_language("python")


def reorder_function_levels(log_file, function_levels):
    """
    Reorder the function_levels dictionary based on the order of function definitions in the log_file.

    Args:
        log_file (str): Path to the log file containing function definitions.
        function_levels (dict): Dictionary with composite keys (filename, modulename, funcname) and their levels as values.

    Returns:
        dict: Reordered dictionary matching the sequence in the log file.
    """
    # Read the log file and extract function definitions
    with open(log_file, 'r') as file:
        log_lines = file.readlines()

    # Initialize a list to hold the ordered function identifiers
    ordered_functions = []

    # Flag to start capturing function definitions
    capture = False

    # Regular expression to match function definition lines
    func_def_pattern = re.compile(
        r'filename:\s*(?P<filename>[^,]+),\s*modulename:\s*(?P<modulename>[^,]+),\s*funcname:\s*(?P<funcname>[^\s]+)'
    )

    def find_level(filename, modulename, funcname):
        # from the dictionary function_levels, if the object has filename, modulename, funcname, return the level
        for item in function_levels:
            if item['filename'] == filename and item['modulename'] == modulename and item['funcname'] == funcname:
                return item['level']
        return None

    
    filename_method = []

    for line in log_lines:
        if line.strip() == "functions called:":
            capture = True
            continue
        if capture:
            # if line.strip() == "":
            #     break  # End of function definitions section

            # Match the line against the function definition pattern
            match = func_def_pattern.search(line)
            if match:
                # Extract filename, modulename, and funcname
                filename = match.group('filename').strip()
                modulename = match.group('modulename').strip()
                funcname = match.group('funcname').strip()
                level = find_level(filename, modulename, funcname)

                # if level is None:
                #     # print(f"Function {funcname} not found in the trace output.")
                #     continue

                if "/lib/python3" in filename:
                    continue
                if "<" in filename:
                    continue

                temp_dict = {
                    'filename': filename,
                    'modulename': modulename,
                    'funcname': funcname,
                    'level': level
                }

                # append the filename and method name to the filename_method list, as a tuple
                filename_method.append((filename, funcname))

                ordered_functions.append(temp_dict)

    return ordered_functions, filename_method


def parse_trackcalls_output(log_file):
    """
    Parses the output of `python -m trace --trackcalls` to determine function call levels.

    Args:
        log_file (str): Path to the log file containing the trace output.

    Returns:
        list of dict: A list where each dict contains 'filename', 'modulename', 'funcname', and 'level'.
    """
    with open(log_file, 'r') as f:
        lines = f.readlines()

    call_graph = defaultdict(list)
    function_files = {}
    current_file = None

    # Regular expressions to match lines
    file_header_re = re.compile(r'^\*\*\* (.+) \*\*\*$')
    call_re = re.compile(r'^\s*(\S+) -> (\S+)$')

    for line in lines:
        file_header_match = file_header_re.match(line)
        call_match = call_re.match(line)

        if file_header_match:
            current_file = file_header_match.group(1)
        elif call_match and current_file:
            caller = call_match.group(1)
            callee = call_match.group(2)
            call_graph[caller].append(callee)
            function_files[caller] = current_file
            function_files[callee] = current_file

    # Determine levels using BFS
    levels = {}
    queue = deque()

    # Initialize the queue with top-level module functions
    for func in call_graph:
        if '.<module>' in func:
            queue.append((func, 0))
            levels[func] = 0

    while queue:
        current_func, current_level = queue.popleft()
        for callee in call_graph[current_func]:
            if callee not in levels:  # Avoid revisiting
                levels[callee] = current_level + 1
                queue.append((callee, current_level + 1))

    # Prepare the result
    result = []
    for func, level in levels.items():
        filename = function_files.get(func, 'Unknown')
        modulename, funcname = func.rsplit('.', 1)
        result.append({
            'filename': filename,
            'modulename': modulename,
            'funcname': funcname,
            'level': level
        })

    return result



def run_trace_func_level(venv_path, project_name, fully_qualified_test_name):
    def filter_function_names(line):
        # Filter out the function names from the trace output
        # if line contains one of the following, then return None otherwite return the line
        # 1. lib/python3.8/site-packages/
        # 2. /usr/lib/python3.8/
        # 3. filename: <string>, modulename: <string>,
        # 4. filename: <frozen importlib._bootstrap_external>,

        if "filename: /usr/lib/" in line:
            return None
        if "filename: <string>" in line:
            return None
        if "filename: <frozen" in line:
            return None
        if "filename: <__array_function__" in line:
            return None
        if "/virtualenv/lib/python3.8/site-packages/" in line:
            return None
        # if "level: None" in line:
        #     return None
        return line

    if "/" in project_name:
        project_name = project_name.split("/")[1]

    print(f"Running test with trace to get function trace and levels: {fully_qualified_test_name}")
    print(f"Project name: {project_name}")

    venv_path = os.path.abspath(venv_path)
    python_path = os.path.join(venv_path, "bin", "python")
    pytest_path = os.path.join(venv_path, "bin", "pytest")


    std_lib = os.path.dirname(os.__file__)

    python_code = (
        "import site; "
        "s = site.getsitepackages(); "
        "print(s[0])"
    )

    site_packages_command = [python_path, "-c", python_code]

    site_packages_result = subprocess.run(
        site_packages_command,
        check=True,
        capture_output=True,
        text=True
    )

    site_packages = site_packages_result.stdout.strip()
    ignore_dirs = f"{std_lib}{os.pathsep}{site_packages}"

    script_dir = os.path.dirname(os.path.abspath(__file__))
    projects_dir = os.path.join(script_dir, "projects", project_name)
    
    log_dir = os.path.join(script_dir, "logs_traces")
    method_bodies_dir = os.path.join(script_dir, "method_bodies")
    formatted_test_name = fully_qualified_test_name.replace(".py", "").replace("::", "_").replace("/", "_")
    formatted_test_name = f"{project_name}_{formatted_test_name}"

    trace_file_path_temp = f"{log_dir}/{formatted_test_name}_temp.log"
    trace_file_path_wo_duplicate_lines = f"{log_dir}/{formatted_test_name}.log"
    method_bodies_filename = f"{method_bodies_dir}/{formatted_test_name}.log"

    # relative_trace_file_path = f"logs_traces/{formatted_test_name}.log"
    listfunc_trace = f"traces_listfunc/{formatted_test_name}.log"
    trackcalls_trace = f"trace_trackcalls/{formatted_test_name}.log"
    level_trace = f"level_traces/{formatted_test_name}.log"

    os.makedirs(log_dir, exist_ok=True)
    os.makedirs("traces_listfunc", exist_ok=True)
    os.makedirs("trace_trackcalls", exist_ok=True)
    os.makedirs("level_traces", exist_ok=True)
    os.makedirs(method_bodies_dir, exist_ok=True)


    trace_command_listfunc = [python_path,  "-m", "trace", "--listfuncs", f"--ignore-dir={ignore_dirs}", pytest_path, "-s", fully_qualified_test_name]
    trace_command_trackcalls = [python_path,  "-m", "trace", "--trackcalls", f"--ignore-dir={ignore_dirs}", pytest_path, "-s", fully_qualified_test_name]
    
    env = os.environ.copy()
    #  reset env["PYTHONPATH"] = projects_dir
    env["PYTHONPATH"] = projects_dir

    # run the trace command just like we run the test command
    with open(listfunc_trace, "w") as log:
        result = subprocess.run(trace_command_listfunc, cwd=projects_dir, check=False, capture_output=True, text=True)
        log.write(result.stdout + "\n")
        log.write(result.stderr + "\n")

    with open(trackcalls_trace, "w") as log:
        result = subprocess.run(trace_command_trackcalls, cwd=projects_dir, check=False, capture_output=True, text=True)
        log.write(result.stdout + "\n")
        log.write(result.stderr + "\n")

    # Now that we have two tracefiles,
    function_levels = parse_trackcalls_output(trackcalls_trace)
    ordered_functions, filename_method = reorder_function_levels(listfunc_trace, function_levels)

    with open(level_trace, "w") as f:
        for func in ordered_functions:
            line = f"filename: {func['filename']}, modulename: {func['modulename']}, funcname: {func['funcname']}, level: {func['level']}\n"
            # line = filter_function_names(line)
            if line is not None:
                f.write(line)
            # f.write(f"filename: {func['filename']}, modulename: {func['modulename']}, funcname: {func['funcname']}, level: {func['level']}\n")

    
    # clear the method_bodies file before writing to it
    with open(method_bodies_filename, "w") as f:
        f.write("")

    # get method bodies for each of the filename_method
    for filename, method in filename_method:
        if method == "<module>":
            continue

        exclude_file_path_content = ["site-packages", "/usr/lib/"]

        if any(exclude_file_path in filename for exclude_file_path in exclude_file_path_content):
            continue
        
        method_body, start_line, end_line = extract_any_method_body(filename, method)
        if method_body is not None:
            with open(method_bodies_filename, "a") as mb_file:
                # mb_file.write(f"[INFO] Method {method_name[1]} in {method_name[0]} (lines {method_body[1]}-{method_body[2]}):\n")
                mb_file.write(f"[INFO] Method {method} in {filename} (lines {start_line}-{end_line}):\n")
                mb_file.write(method_body + "\n\n")

    return level_trace

def extract_any_method_body(file_path, qualified_method_name):
    """
    Extracts the source code of a function or method from a Python file,
    given its fully qualified name.
    
    Parameters:
      file_path (str): Path to the Python source file.
      qualified_method_name (str): The fully qualified function/method name.
                                   For methods, use "ClassName.method_name";
                                   for top-level functions, use "function_name".
    
    Returns:
      tuple: (method_source, start_line, end_line) where method_source is the
             extracted source code (including decorators) and start_line/end_line
             indicate where the definition occurs in the file (1-indexed).
             If the method is not found, returns (None, None, None).
    """
    print("file_path=", file_path)
    print("qualified_method_name=", qualified_method_name)


    # Read the file content
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()
    lines = code.splitlines()
    
    # Initialize the parser and parse the source code.
    parser = Parser()
    parser.set_language(PY_LANGUAGE)
    tree = parser.parse(bytes(code, "utf8"))
    root_node = tree.root_node
    
    # Determine if a class is specified. We assume that if there is a dot,
    # then the part before the dot is the class name.
    if "." in qualified_method_name:
        class_name, function_name = qualified_method_name.split(".", 1)
    else:
        class_name = None
        function_name = qualified_method_name

    def find_function(node, current_class=None):
        """
        Recursively searches the AST node for the function definition.
        """
        for child in node.children:
            if child.type == "class_definition":
                # Get the class name from the AST node.
                class_node = child.child_by_field_name("name")
                if class_node:
                    child_class_name = class_node.text.decode("utf-8")
                    # If we're looking for a method in a specific class, descend only when matched.
                    if class_name and child_class_name == class_name:
                        class_body = child.child_by_field_name("body")
                        if class_body:
                            result = find_function(class_body, current_class=child_class_name)
                            if result:
                                return result
            elif child.type in ("function_definition", "decorated_definition"):
                func_node = child.child_by_field_name("name")
                if func_node:
                    func_name = func_node.text.decode("utf-8")
                    # Ensure we have the correct function (and correct class if applicable)
                    if func_name == function_name and (class_name is None or current_class == class_name):
                        # Determine the start and end lines (1-indexed)
                        start_line = child.start_point[0] + 1
                        end_line = child.end_point[0] + 1
                        
                        # Collect decorators (if any) from previous siblings.
                        decorators = []
                        prev_node = child.prev_named_sibling
                        while prev_node and prev_node.type == "decorator":
                            decorators.insert(0, lines[prev_node.start_point[0]])
                            prev_node = prev_node.prev_named_sibling
                        if decorators:
                            # Adjust start_line to include decorators.
                            start_line = decorators[0].strip() and child.start_point[0] + 1 or start_line
                        
                        # Extract the function's code lines.
                        func_code_lines = lines[start_line - 1:end_line]
                        method_source = "\n".join(decorators + func_code_lines)
                        return method_source, start_line, end_line
            # Recursively search in child nodes if the type is one of these.
            if child.type in ("module", "class_definition", "decorated_definition", "block"):
                result = find_function(child, current_class=current_class)
                if result:
                    return result
        return None

    return find_function(root_node) or (None, None, None)


def get_all_covered_methods_names(venv_path, project_name, fully_qualified_test_name, log_file_name):
    # First runs the command like the following, just as we run in run_with_trace function
    # /home/tbaral/icse25/NOD-Test-Repair/projects/vizkg/virtualenv/bin/python -m coverage run --source /home/tbaral/icse25/NOD-Test-Repair/projects/vizkg /home/tbaral/icse25/NOD-Test-Repair/projects/vizkg/virtualenv/bin/pytest -s tests/dataIdentification_test.py::VizKGTestCase::test_column_dataframe
    # Then we get the function coverage list using the following command
    # coverage report --functions | grep "function" | awk '{ sub(/%/,"",$NF); if ($NF > 0) print $1, $2, $3 }'
    # The output of the above command is like the following:
        # VizKG/utils/util.py: function __convert_dtypes
        # VizKG/utils/util.py: function set_chart
        # VizKG/utils/util.py: function set_dataframe
        # VizKG/visualize.py: function VizKG.__init__
        # tests/dataIdentification_test.py: function VizKGTestCase.setUp
    # we need to return this output as a list.

    if "/" in project_name:
        project_name = project_name.split("/")[1]

    venv_path = os.path.abspath(venv_path)
    python_path = os.path.join(venv_path, "bin", "python")
    pytest_path = os.path.join(venv_path, "bin", "pytest")
    coverage_path = os.path.join(venv_path, "bin", "coverage")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    projects_dir = os.path.join(script_dir, "projects", project_name)

    os.system(f"{python_path} -m pip install git+https://github.com/nedbat/coveragepy@f10c455b7c8fd26352de#egg=coverage==0.0")

    coverage_command=[python_path, "-m", "coverage", "run", f"--source={projects_dir}", pytest_path, "-s", fully_qualified_test_name]
    coverage_report_command = ["coverage", "report", "--functions", "|", "grep", "function", "|", "awk", "'{ sub(/%/,\"\",$NF); if ($NF > 0) print $1, $2, $3 }'"]
    
    os.makedirs("func_coverage", exist_ok=True)

    temo_coverage_file = f"func_coverage/{log_file_name}.log"
    
    # run the coverage command
    print("Running coverage command:")

    subprocess.run(coverage_command, cwd=projects_dir)

    # get the function coverage list
    with open(temo_coverage_file, "w") as fnull:
        result = subprocess.run(
                'coverage report --functions | grep function | awk \'{ sub(/%/,"",$NF); if ($NF > 0) print $1, $2, $3 }\'',
                shell=True,
                cwd=projects_dir,
                capture_output=True,
                text=True
            )

        if result.returncode != 0:
            print(f"Error running coverage report command: {result.stderr}")
            return []
        
        with open(temo_coverage_file, "w") as f:
            f.write(result.stdout)
    
    with open(temo_coverage_file, "r") as f:
        lines = f.readlines()
        print("lines=", lines)
        files = [line.split(":")[0] for line in lines]
        functions = [line.split(":")[1].strip() for line in lines]
        # remove the word "function" from the functions list
        functions = [function.replace("function", "").strip() for function in functions]

        print("files=", files)
        print("functions=", functions)
    
        fully_qualified_file = [f"{projects_dir}/{file}" for file in files]
        return list(zip(fully_qualified_file, functions))


def run_test_with_trace(venv_path, project_name, fully_qualified_test_name, trace_level="method"):
    def remove_unnecessary_lines(input_file, output_file):
        # from the trace output, remove everything before the line:
        # ========= short test summary info ========

        with open(input_file, "r") as infile:
            lines = infile.readlines()
            start = 0
            for i, line in enumerate(lines):
                if "=== short test summary info ===" in line:
                    start = i
                    break
            with open(output_file, "w") as outfile:
                outfile.writelines(lines[start:])


    def filter_function_names(line):
        # Filter out the function names from the trace output
        # if line contains one of the following, then return None otherwite return the line
        # 1. lib/python3.8/site-packages/
        # 2. /usr/lib/python3.8/
        # 3. filename: <string>, modulename: <string>,
        # 4. filename: <frozen importlib._bootstrap_external>,

        if "lib/python3.8/site-packages/" in line:
            return None
        if "/usr/lib/python3.8/" in line:
            return None
        if "filename: <string>, modulename: <string>," in line:
            return None
        if "filename: <frozen importlib." in line:
            return None
        if ", funcname: <module>" in line:
            return None
        return line


    if "/" in project_name:
        project_name = project_name.split("/")[1]

    print(f"Running test with trace: {fully_qualified_test_name}")
    print(f"Project name: {project_name}")

    def sanitize_trace_line(line):
        # Remove the leading spaces and the newline character
        return re.sub(r"^\w+(\.\w+)?\(\d+\):\s", "", line)


    # Process the traces to remove the duplicate lines
    def process_trace(input_file, output_file):
        if not os.path.exists(input_file):
                print(f"Input file {input_file} does not exist")
                return
        
        with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
                previous_line = None
                count = 1
                for line in infile:
                    line = sanitize_trace_line(line)
                    if line == previous_line:
                        count += 1
                    else:
                        if previous_line is not None:
                            if count > 1:
                                outfile.write(f"{previous_line.strip()} (executed {count} consecutive times)\n")
                            else:
                                outfile.write(previous_line)
                        previous_line = line
                        count = 1
            # Write the last line
                if previous_line is not None:
                    if count > 1:
                        outfile.write(f"{previous_line.strip()} (executed {count} consecutive times)\n")
                    else:
                        outfile.write(previous_line)
            
    venv_path = os.path.abspath(venv_path)
    python_path = os.path.join(venv_path, "bin", "python")
    pytest_path = os.path.join(venv_path, "bin", "pytest")


    std_lib = os.path.dirname(os.__file__)

    python_code = (
        "import site; "
        "s = site.getsitepackages(); "
        "print(s[0])"
    )

    site_packages_command = [python_path, "-c", python_code]

    site_packages_result = subprocess.run(
        site_packages_command,
        check=True,
        capture_output=True,
        text=True
    )

    site_packages = site_packages_result.stdout.strip()
    ignore_dirs = f"{std_lib}{os.pathsep}{site_packages}"

    script_dir = os.path.dirname(os.path.abspath(__file__))
    projects_dir = os.path.join(script_dir, "projects", project_name)
    log_dir = os.path.join(script_dir, "logs_traces")

    formatted_test_name = fully_qualified_test_name.replace(".py", "").replace("::", "_").replace("/", "_")
    formatted_test_name = f"{project_name}_{formatted_test_name}"

    trace_file_path_temp = f"{log_dir}/{formatted_test_name}_temp.log"
    trace_file_path_wo_duplicate_lines = f"{log_dir}/{formatted_test_name}.log"

    relative_trace_file_path = f"logs_traces/{formatted_test_name}.log"

    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(result_dir, exist_ok=True)

    trace_command = [python_path,  "-m", "trace", "--trace", f"--ignore-dir={ignore_dirs}", pytest_path, "-s", fully_qualified_test_name]
    env = os.environ.copy()
    #  reset env["PYTHONPATH"] = projects_dir
    env["PYTHONPATH"] = projects_dir

    print("current working directory=", projects_dir)

    # run the trace command just like we run the test command
    with open(trace_file_path_temp, "w") as log:
        result = subprocess.run(trace_command, cwd=projects_dir, check=False, capture_output=True, text=True)
        log.write(result.stdout + "\n")
        log.write(result.stderr + "\n")

    # process the trace file to remove duplicate lines
    process_trace(trace_file_path_temp, trace_file_path_wo_duplicate_lines)
    # remove the temporary trace file
    os.remove(trace_file_path_temp)
    return relative_trace_file_path


# ---------------- Step 1: Clone the GitHub Repository ----------------
def proj_clone(proj_name, sha, projects_dir):
    repo_url = "https://github.com/"+proj_name
    repo_name = proj_name.split("/")[-1]
    repo_path = os.path.join(projects_dir, repo_name)  # Clone inside projects directory
    
    if not os.path.exists(repo_path):
        print("Cloning repository...")
        Repo.clone_from(repo_url, repo_path)
    
    repo = Repo(repo_path)
    try:
        repo.git.checkout(sha)
        print(f"Successfully checked out commit")
    except Exception as e:
        print(f"Failed to checkout commit")
        exit(1)
    return repo, repo_path

def detect_python_version(project_path):
    """Detects the required Python version and returns the full executable path."""
    pyproject_toml_path = os.path.join(project_path, "pyproject.toml")
    python_version = None

    if os.path.exists(pyproject_toml_path):
        try:
            with open(pyproject_toml_path, "r", encoding="utf-8") as file:
                pyproject_data = toml.load(file)
                requires_python = pyproject_data.get("tool", {}).get("poetry", {}).get("dependencies", {}).get("python")
                #python_version = pyproject_data.get("project", {}).get("requires-python", "").lstrip(">=")
                if requires_python:
                    # Extracting the minimum version requirement from the version specifier
                    match = re.search(r'>=([\d\.]+)', requires_python)
                    if match:
                        python_version = match.group(1)
                        print(f"Detected Python version from pyproject.toml: {python_version}") 
        except Exception as e:
            print(f"Error reading pyproject.toml: {e}")

    # Default to Python 3.8 if no version is found
    if not python_version:
        print("No Python version specified, defaulting to 3.8")
        python_version = "3.8"

    #python_executable = shutil.which(f"python{python_version}")
    #python_version = "3.8"
    '''if python_version == "3.7": 
        activation_command = f"source activate py_37"
    elif python_version == "3.9":
        activation_command = f"source activate py_39"
    os.system(activation_command)'''
    print('version=', python_version)
    python_executable = shutil.which(f"python{python_version}") #or shutil.which("python3")
    
    if python_executable:
        print(f"Found Python executable: {python_executable}")
    else:
        print(f"Python {python_version} not found! Please ensure it is installed.")
    
    return python_executable

import os
import subprocess
import shutil

def create_virtual_env(project_path, python_executable):
    """Creates a virtual environment using `virtualenv` inside the project root directory."""
    
    venv_path = os.path.join(project_path, "virtualenv")  # Use "virtualenv" in project root

    print(f"Creating virtual environment in: {venv_path} using {python_executable}")
    #exit()

    if os.path.exists(venv_path):
        # return venv_path
        print("Virtual environment already exists. Deleting it first...")
        # return venv_path
        shutil.rmtree(venv_path)

    # Ensure `virtualenv` is installed
    try:
        print("Checking if `virtualenv` is installed...")
        print("python_executable=", python_executable)
        subprocess.run([python_executable, "-m", "virtualenv", "--version"], check=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("`virtualenv` not found! Installing it first...")
        subprocess.run([python_executable, "-m", "pip", "install", "--user", "virtualenv"], check=True)

    # Create virtual environment with the specified Python executable
    try:
        subprocess.run([python_executable, "-m", "virtualenv", venv_path, "--python", python_executable], check=True)
        print(f"Virtual environment created at: {venv_path}")
    except subprocess.CalledProcessError:
        print("Failed to create virtual environment with `virtualenv`!")
        exit(1)

    return venv_path


import os
import subprocess
import toml

def convert_poetry_version_to_pip(version):
    """
    Convert Poetry version specifiers to pip-compatible version specifiers.
    Example: '^1.22.3' -> '>=1.22.3,<2.0.0'
    """
    #autoresearch/autora, this if else were needed when it was autoresearch/autora project
    if isinstance(version, dict):
        if 'version' in version:
            version = version['version']
        else:
            return None 

    if version.startswith("^"):
        major_version = version[1:].split(".")[0]
        next_major_version = str(int(major_version) + 1)
        return f">={version[1:]},<{next_major_version}.0.0"
    else:
        return version

def install_requirements(python_path, project_path, pip_path, project_name):
    print("Installing dependencies...")
    requirements_files = [
        os.path.join(project_path, "requirements.txt"),
        os.path.join(project_path, "requirements-dev.txt"),
        os.path.join(project_path, "requirements_test.txt"),
        os.path.join(project_path, "dev-requirements.txt"),
        os.path.join(project_path, "test-requirements.txt"),
    ]

    installed = False
    for req_file in requirements_files:
        if os.path.exists(req_file):
            if project_name == "connectedcompany/coco-agent" and req_file.endswith("requirements.txt"):
                # Special handling for coco-agent with dot in requirements.txt
                print("Installing coco-agent in editable mode due to special requirements...")
                setup_py_path = os.path.join(project_path, "setup.py")
                subprocess.run([pip_path, "install", "-e", project_path], check=True)
                installed = True
                break
            else:
                print(f"Installing dependencies from {req_file}...")
                subprocess.run([pip_path, "install", "-r", req_file], check=True)
                installed = True
                break

    # If no requirements.txt or special conditions matched, try setup.py (for editable mode installation)
    if not installed:
        setup_py_path = os.path.join(project_path, "setup.py")
        if os.path.exists(setup_py_path):
            print("Installing project in editable mode from setup.py...")
            subprocess.run([pip_path, "install", "-e", project_path], check=True)

    # Ensure test dependencies are always installed
    print("Ensuring `pytest` and related dependencies are installed...")
    subprocess.run([pip_path, "install", "--upgrade", "pytest", "pytest-cov", "pytest-xdist", "pytest-repeat", "toml"], check=True)

    print("Dependencies installed successfully!\n")


def install_dependencies(venv_path, project_path, project_name):
    """Ensure all project dependencies are installed inside the virtual environment."""
    
    python_path = os.path.join(venv_path, "bin", "python")
    pip_path = os.path.join(venv_path, "bin", "pip")

    print("Ensuring `pip` is installed in the virtual environment...")

    try:
        subprocess.run([python_path, "-m", "ensurepip"], check=True)
    except subprocess.CalledProcessError:
        print("`ensurepip` is missing. Skipping...")
        get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
        get_pip_path = os.path.join(venv_path, "get-pip.py")

        subprocess.run(["curl", "-o", get_pip_path, get_pip_url], check=True)

        subprocess.run([python_path, get_pip_path], check=True)

        os.remove(get_pip_path)
    subprocess.run([python_path, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=True)

    print("Installing dependencies...")
    pyproject_toml_path = os.path.join(project_path, "pyproject.toml")

    if os.path.exists(pyproject_toml_path):
        try:
            with open(pyproject_toml_path, "r", encoding="utf-8") as file:
                pyproject_data = toml.load(file)
            
            # Initialize dependencies
            dependencies = []

            # Check if the project uses Poetry
            if "poetry" in pyproject_data.get("tool", {}):
                print("****SHANTO poetry found")
                print("pyproject_data=",pyproject_data)
                poetry_data = pyproject_data["tool"]["poetry"]
                dependencies = {k: convert_poetry_version_to_pip(v) for k, v in poetry_data.get("dependencies", {}).items() if k != "python"}
                print('I AM dependencies=',dependencies)

            # Check if the project uses Flit
            elif "flit" in pyproject_data.get("tool", {}):
                flit_data = pyproject_data["tool"]["flit"]["metadata"]
                dependencies = [convert_poetry_version_to_pip(dep) for dep in flit_data.get("requires", [])]

            # Install dependencies if any
            if dependencies:
                print("****SHANTO")
                print(f"Installing: {', '.join(dependencies)}")
                subprocess.run([pip_path, "install"] + list(dependencies), check=True)


            else:
                print("No dependencies listed in `pyproject.toml`.")

            print("Installing tree_sitter and tree_sitter_languages...")
            subprocess.run([pip_path, "install", "tree_sitter", "tree_sitter_languages"], check=True)

        except Exception as e:
            print(f"Error processing `pyproject.toml`: {e}")
        print("proj_name=", project_name)
        # Special handling for the opentelemetry project
    if project_name.lower() == "microsoft/opentelemetry-azure-monitor-python":
        print("Special handling for opentelemetry project...")
        subprocess.run([pip_path, "install", "opentelemetry-api", "opentelemetry-sdk"], check=True)
    elif project_name.lower() == "nschloe/pipdate":
        subprocess.run([pip_path, "install", "pipdate", "matplotlib"], check=True) 
    elif project_name.lower() == "mondeja/pgdoc-datatype-parser":
        print("I AM HERE ,")
        subprocess.run([pip_path, "install", "--upgrade", "setuptools"], check=True)
        subprocess.run([python_path, "-c", "import pkg_resources"], check=True)
    elif project_name.lower() == "radeklat/issue-watcher":
        subprocess.run([pip_path, "install", "issue_watcher"], check=True) 

    elif project_name.lower() == "ratan-lab/sumo":
        #print("I AM SUMO")
        #subprocess.run([pip_path, "install", "sumo"], check=True) 
        subprocess.run([pip_path, "install", "sumo"], check=True)
        # Example: subprocess.run([pip_path, "install", "sumo-subpackage"], check=True)
    elif project_name.lower() == "serfend/sgtlibc":
        subprocess.run([pip_path, "install", "attrs"], check=True)
    elif project_name.lower() == "experimaestro/experimaestro-python":
        subprocess.run([pip_path, "install", "experimaestro"], check=True)
    elif project_name.lower() == "jenesuispasdave/authenticator":
        subprocess.run([pip_path, "install", "authenticator"], check=True)
    elif project_name.lower() == "clementchadebec/pyraug":
        subprocess.run([pip_path, "install", "pyraug"], check=True)
    elif project_name.lower() == "stas-prokopiev/local_simple_database":
        subprocess.run([pip_path, "install", "local_simple_database"], check=True)
    elif project_name.lower() == "sagecontinuum/sage-data-client":
        subprocess.run([pip_path, "install", "sage_data_client"], check=True)

    install_requirements(python_path, project_path, pip_path, project_name)


import os
import subprocess
import sys
import subprocess
import os

def run_tests(venv_path, project_path, test_name, log_dir, num_runs=1):
    """Runs the specified test using the virtual environment."""

    # Convert venv path to absolute path
    venv_path = os.path.abspath(venv_path)
    python_path = os.path.join(venv_path, "bin", "python")
    pytest_path = os.path.join(venv_path, "bin", "pytest")

    # Check if virtual environment files exist
    if not os.path.exists(python_path):
        print(f"ERROR: Python binary not found in virtualenv: {python_path}")
        print(f"Current working directory: {os.getcwd()}")  # Print current directory
        return

    if not os.path.exists(pytest_path):
        print(f"ERROR: pytest not found in virtualenv: {pytest_path}")
        print(f"Current working directory: {os.getcwd()}")  # Print current directory
        return

    # Convert project path to absolute path
    project_path = os.path.abspath(project_path)
    num_parallel = 200
    test_pass=0
    test_fail=0
    pytest_command = [python_path, "-m", "pytest", test_name] # Talank need to change this to run with trace
    #pytest_command = [
    #    pytest_path,  # Path to pytest inside virtualenv
    #    "--maxfail=1",  # Stop after first failure
    #    "-n", str(num_parallel),  # Run tests in parallel
    #    "--count", str(10000),  # Repeat the test N times
    #    test_name  # The test to run
    #]


    # 🔍 Print debugging info
    print(f"Running command: {' '.join(pytest_command)}")
    print(f"Project directory: {project_path}")
    print(f"Current working directory before running pytest: {os.getcwd()}")
    # Format log filename: replace `.py` and `::` with `_`
    formatted_test_name = test_name.replace(".py", "").replace("::", "_").replace("/", "_")
    log_file = os.path.join(log_dir, f"{os.path.basename(project_path)}_{formatted_test_name}.log")

    with open(log_file, "w") as log:
        for i in range(1, num_runs+1):
            print(f"Running test {i}/{num_runs}...")
            try:
                result = subprocess.run(pytest_command, cwd=project_path, check=False, capture_output=True, text=True) 
                log.write(f"=== Test Run {i}/{num_runs} ===\n")
                log.write(result.stdout + "\n")
                log.write(result.stderr + "\n")
                # Talank should change the logfile as it contains traces, and duplicate lines in trace. 
                # Check test results
                if "1 passed" in result.stdout:
                    test_pass += 1
                if "1 failed" in result.stdout:
                    test_fail += 1

                # Stop if at least one test passes and one fails
                if test_pass > 0 and test_fail > 0:
                    print("Flaky test detected! Stopping execution.")
                    return True # flaky test detected

            except Exception as e:
                print(f"ERROR: An unexpected exception occurred.\n{e}")
                print(f"Current working directory after failure: {os.getcwd()}")

def cleanup(venv_path):
    """Deletes the virtual environment."""
    if os.path.exists(venv_path):
        shutil.rmtree(venv_path)
        print(f"Deleted virtual environment: {venv_path}")

if __name__ == "__main__":
    import argparse
    script_dir = os.path.dirname(os.path.abspath(__file__))
    projects_dir = os.path.join(script_dir, "projects")
    log_dir = os.path.join(script_dir, "logs")
    result_dir = os.path.join(script_dir, "results")

    os.makedirs(projects_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(result_dir, exist_ok=True)

    output_file = os.path.join(result_dir, "trace_files.csv")
    input_file_name = sys.argv[1] #data/idoft_all_nod_test.csv 

    with open(input_file_name, newline='', encoding='utf-8') as file, \
         open(output_file, "a", newline='', encoding='utf-8') as outfile:
        reader = csv.reader(file)
        writer = csv.writer(outfile)
        writer.writerow(["gitproj_name", "sha", "test_name", "trace_file_path"])

        for row in reader:
            gitproj_name = row[0]
            sha = row[1]
            project_name = full_path_after_3 = "/".join(gitproj_name.split("/")[3:])
 
            repo, repo_path = proj_clone(project_name, sha, projects_dir)
            print("repo=", repo, project_name)

            test_name = row[2]
            python_executable = detect_python_version(repo_path)
            venv_path = create_virtual_env(repo_path, python_executable)
            install_dependencies(venv_path, repo_path, project_name)

            # trace_log_file_path = run_test_with_trace(venv_path, project_name, test_name)
            trace_log_file_path = run_trace_func_level(venv_path, project_name, test_name)
            # Write results to output file
            writer.writerow([gitproj_name, sha, test_name, trace_log_file_path])
            trace_log_filename = os.path.basename(trace_log_file_path)
            # remove extension from the trace_log_filename
            trace_log_filename = trace_log_filename.split(".")[0]
            # os.makedirs("method_bodies", exist_ok=True)
            # method_names = get_all_covered_methods_names(venv_path, project_name, test_name, trace_log_filename)
            # print("method_names=", method_names)
            # with open("method_bodies/"+trace_log_filename, "w") as mb_file:
            #     for method_name in method_names:
            #         method_body= extract_any_method_body(method_name[0], method_name[1])
            #         if method_body[0] is not None:
            #             mb_file.write(f"[INFO] Method {method_name[1]} in {method_name[0]} (lines {method_body[1]}-{method_body[2]}):\n")
            #             mb_file.write(method_body[0] + "\n\n")

            outfile.flush()

            #if not args.keep_venv:
            #    cleanup(venv_path)
            #exit()

#
