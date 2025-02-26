import os
import subprocess
import shutil
import sys
import venv
import re
import csv
from git import Repo
import pytest


import toml  # Install with `pip install toml`

import shutil
import re
from tree_sitter import Parser
from tree_sitter_languages import get_language
from collections import defaultdict, deque

# Get the prebuilt Python language parser
PY_LANGUAGE = get_language("python")

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
            subprocess.run([pip_path, "install", "tree_sitter", "tree_sitter_languages", "pytest"], check=True)

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

def run_tests(venv_path, project_path, test_name, log_dir, method_lists_dir, function_trace_dir, line_trace_dir, num_runs=3000):
    """Runs the specified test using the virtual environment."""

    # Convert venv path to absolute path
    venv_path = os.path.abspath(venv_path)
    python_path = os.path.join(venv_path, "bin", "python")
    pytest_path = os.path.join(venv_path, "bin", "pytest")

    script_dir = os.path.dirname(os.path.abspath(__file__))

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

    env = os.environ.copy()
    env["PYTHONPATH"] = projects_dir

    trace_script_path = "/home/tbaral/icse25/2/NOD-Test-Repair/trace_script.py"

    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(method_lists_dir, exist_ok=True)
    os.makedirs(function_trace_dir, exist_ok=True)
    os.makedirs(line_trace_dir, exist_ok=True)

   
    # Format log filename: replace `.py` and `::` with `_`
    formatted_test_name = test_name.replace(".py", "").replace("::", "_").replace("/", "_")
    log_file = os.path.join(log_dir, f"{os.path.basename(project_path)}_{formatted_test_name}.log")
    covered_method_list_file = os.path.join(method_lists_dir, f"{os.path.basename(project_path)}_{formatted_test_name}.csv")
    function_trace_file = os.path.join(function_trace_dir, f"{os.path.basename(project_path)}_{formatted_test_name}.log")
    line_trace_file = os.path.join(line_trace_dir, f"{os.path.basename(project_path)}_{formatted_test_name}.log")
    # method_list_filename = covered_method_list_file

    # open the covered_method_list_file in write mode
    open(covered_method_list_file, "w").close()
    open(function_trace_file, "w").close()
    open(line_trace_file, "w").close()

    # I need temp function trace and line trace file
    function_trace_file_temp = os.path.join(function_trace_dir, f"{os.path.basename(project_path)}_{formatted_test_name}_temp.log")
    line_trace_file_temp = os.path.join(line_trace_dir, f"{os.path.basename(project_path)}_{formatted_test_name}_temp.log")

    function_trace_file_pass = os.path.join(function_trace_dir, f"{os.path.basename(project_path)}_{formatted_test_name}_pass.log")
    line_trace_file_pass = os.path.join(line_trace_dir, f"{os.path.basename(project_path)}_{formatted_test_name}_pass.log")

    # filenames for failure logs
    function_trace_file_fail = os.path.join(function_trace_dir, f"{os.path.basename(project_path)}_{formatted_test_name}_fail.log")
    line_trace_file_fail = os.path.join(line_trace_dir, f"{os.path.basename(project_path)}_{formatted_test_name}_fail.log")

    pytest_command = [python_path, trace_script_path, test_name, function_trace_file_temp, line_trace_file_temp, covered_method_list_file]
    
    # 🔍 Print debugging info
    print(f"Running command: {' '.join(pytest_command)}")
    print(f"Project directory: {project_path}")
    print(f"Current working directory before running pytest: {os.getcwd()}")


    with open(log_file, "w") as log:
        for i in range(1, num_runs+1):
            print(f"Running test {i}/{num_runs}...")
            try:
                result = subprocess.run(pytest_command, cwd=project_path, check=False, capture_output=True, text=True) 
                log.write(f"=== Test Run {i}/{num_runs} ===\n")
                log.write(result.stdout + "\n")
                log.write(result.stderr + "\n")

                # put the content of temp files to the final files, use append mode
                with open(function_trace_file_pass, "a") as f:
                    with open(function_trace_file_temp, "r") as f_temp:
                        f.write(f_temp.read())
                with open(line_trace_file_pass, "a") as f:
                    with open(line_trace_file_temp, "r") as f_temp:
                        f.write(f_temp.read())

                # Talank should change the logfile as it contains traces, and duplicate lines in trace. 
                # Check test results
                if "1 passed" in result.stdout:
                    test_pass += 1
                    # we want to rename the temp files to _passed ones
                    os.rename(function_trace_file_temp, function_trace_file_pass)
                    os.rename(line_trace_file_temp, line_trace_file_pass)

                if "1 failed" in result.stdout:
                    test_fail += 1
                    # we want to rename the temp files to _failed ones
                    os.rename(function_trace_file_temp, function_trace_file_fail)
                    os.rename(line_trace_file_temp, line_trace_file_fail)
                

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
    method_lists_dir = os.path.join(script_dir, "method_lists")
    method_bodies_dir = os.path.join(script_dir, "method_bodies")
    function_trace_dir = os.path.join(script_dir, "function_traces")
    line_trace_dir = os.path.join(script_dir, "line_traces")

    os.makedirs(projects_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(result_dir, exist_ok=True)

    output_file = os.path.join(result_dir, "flaky_test_results.csv")
    input_file_name = sys.argv[1] #data/idoft_all_nod_test.csv 

    with open(input_file_name, newline='', encoding='utf-8') as file, \
         open(output_file, "a", newline='', encoding='utf-8') as outfile:
        reader = csv.reader(file)
        writer = csv.writer(outfile)
        writer.writerow(["gitproj_name", "sha", "test_name", "flaky_behavior_found"])

        for row in reader:
            gitproj_name = row[0]
            sha = row[1]
            project_name = full_path_after_3 = "/".join(gitproj_name.split("/")[3:])
 
            repo, repo_path = proj_clone(project_name, sha, projects_dir)
            print("repo=", repo, project_name)
            #parser = argparse.ArgumentParser(description="Run tests in an isolated virtual environment per project.")
            #parser.add_argument("project_path", type=str, help="Path to the project directory")
            #args = parser.parse_args()

            #project_path = os.path.abspath(args.project_path)
            #project_name = os.path.basename(project_path)

            test_name = row[2]
            python_executable = detect_python_version(repo_path)
            venv_path = create_virtual_env(repo_path, python_executable)
            install_dependencies(venv_path, repo_path, project_name)
            flaky_behavior_found = run_tests(venv_path, repo_path, test_name, log_dir, method_lists_dir, function_trace_dir, line_trace_dir)
            # Write results to output file
            writer.writerow([gitproj_name, sha, test_name, flaky_behavior_found])
            outfile.flush()

            # Get the log file name for method list, using the naming convention used in run_tests
            formatted_test_name = test_name.replace(".py", "").replace("::", "_").replace("/", "_")
            log_file_generic_name = f"{os.path.basename(repo_path)}_{formatted_test_name}"

            method_list_filename = os.path.join(method_lists_dir, log_file_generic_name + ".csv")
            method_bodies_filename = os.path.join(method_bodies_dir, log_file_generic_name + ".log")
            
            os.makedirs(method_bodies_dir, exist_ok=True)

            print(f"Extracting method bodies for {method_list_filename}...")

            method_lists = [] # list of tuple (filename, method_name, level)
            with open(method_list_filename, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    current_filename, current_method_name, current_level = row[0], row[1], row[2]
                    method_lists.append((current_filename, current_method_name, current_level))

            for filename, method_name, level in method_lists:
                if filename == "filename":
                    continue

                if int(level) < 3:
                    continue

                # filter level here: eg, if level < 2 then continue so that only level 0,1,2 are considered
                method_body, start_line, end_line = extract_any_method_body(filename, method_name)
                if method_body is not None:
                    with open(method_bodies_filename, "a") as mb_file:
                        mb_file.write(f"[INFO] Method {method_name} in {filename} (lines {start_line}-{end_line}):\n")
                        mb_file.write(method_body + "\n\n")
            

            #if not args.keep_venv:
            #    cleanup(venv_path)
            #exit()

#
