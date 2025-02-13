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
                        print(f"✅ Detected Python version from pyproject.toml: {python_version}") 
        except Exception as e:
            print(f"⚠️ Error reading pyproject.toml: {e}")

    # Default to Python 3.8 if no version is found
    if not python_version:
        print("⚠️ No Python version specified, defaulting to 3.8")
        python_version = "3.8"

    # ✅ Find full path to the correct Python version
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
        print(f"✅ Found Python executable: {python_executable}")
    else:
        print(f"❌ Python {python_version} not found! Please ensure it is installed.")
    
    return python_executable

import os
import subprocess
import shutil

def create_virtual_env(project_path, python_executable):
    """Creates a virtual environment using `virtualenv` inside the project root directory."""
    
    venv_path = os.path.join(project_path, "virtualenv")  # Use "virtualenv" in project root

    print(f"📦 Creating virtual environment in: {venv_path} using {python_executable}")
    #exit()

    if os.path.exists(venv_path):
        print("⚠️ Virtual environment already exists. Deleting it first...")
        shutil.rmtree(venv_path)

    # Ensure `virtualenv` is installed
    try:
        subprocess.run([python_executable, "-m", "virtualenv", "--version"], check=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("⚠️ `virtualenv` not found! Installing it first...")
        subprocess.run([python_executable, "-m", "pip", "install", "--user", "virtualenv"], check=True)

    # Create virtual environment with the specified Python executable
    try:
        subprocess.run([python_executable, "-m", "virtualenv", venv_path, "--python", python_executable], check=True)
        print(f"✅ Virtual environment created at: {venv_path}")
    except subprocess.CalledProcessError:
        print("❌ Failed to create virtual environment with `virtualenv`!")
        exit(1)

    return venv_path


#def create_virtual_env(project_path, python_executable):
#    """Creates a virtual environment using `virtualenv` inside the project root directory."""
#    
#    venv_path = os.path.join(project_path, "virtualenv")  # Use "virtualenv" in project root
#
#    print(f"📦 Creating virtual environment in: {venv_path} using {python_executable}")
#
#    if os.path.exists(venv_path):
#        print("⚠️ Virtual environment already exists. Deleting it first...")
#        shutil.rmtree(venv_path)
#
#    # Ensure `virtualenv` is installed
#    try:
#        subprocess.run([python_executable, "-m", "virtualenv", "--version"], check=True, stdout=subprocess.PIPE)
#    except subprocess.CalledProcessError:
#        print("⚠️ `virtualenv` not found! Installing it first...")
#        subprocess.run([python_executable, "-m", "pip", "install", "--user", "virtualenv"], check=True)
#
#    # Find `virtualenv` path
#    virtualenv_bin = shutil.which("virtualenv") or os.path.expanduser("~/.local/bin/virtualenv")
#
#    # ✅ Create virtual environment inside the project root
#    try:
#        subprocess.run([virtualenv_bin, venv_path], check=True)
#    except subprocess.CalledProcessError:
#        print("❌ Failed to create virtual environment with `virtualenv`!")
#        exit(1)
#
#    print(f"✅ Virtual environment created at: {venv_path}")
#    return venv_path

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
    print("📦 Installing dependencies...")
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
                print("📦 Installing coco-agent in editable mode due to special requirements...")
                setup_py_path = os.path.join(project_path, "setup.py")
                subprocess.run([pip_path, "install", "-e", project_path], check=True)
                installed = True
                break
            else:
                print(f"📦 Installing dependencies from {req_file}...")
                subprocess.run([pip_path, "install", "-r", req_file], check=True)
                installed = True
                break

    # If no requirements.txt or special conditions matched, try setup.py (for editable mode installation)
    if not installed:
        setup_py_path = os.path.join(project_path, "setup.py")
        if os.path.exists(setup_py_path):
            print("📦 Installing project in editable mode from setup.py...")
            subprocess.run([pip_path, "install", "-e", project_path], check=True)

    # Ensure test dependencies are always installed
    print("📦 Ensuring `pytest` and related dependencies are installed...")
    subprocess.run([pip_path, "install", "--upgrade", "pytest", "pytest-cov", "pytest-xdist", "pytest-repeat", "toml"], check=True)

    print("✅ Dependencies installed successfully!\n")


def install_dependencies(venv_path, project_path, project_name):
    """Ensure all project dependencies are installed inside the virtual environment."""
    
    python_path = os.path.join(venv_path, "bin", "python")
    pip_path = os.path.join(venv_path, "bin", "pip")

    print("📦 Ensuring `pip` is installed in the virtual environment...")

    # ✅ Ensure pip, setuptools, and wheel are up-to-date
    #subprocess.run([python_path, "-m", "ensurepip"], check=True)
    # ✅ Run ensurepip only if it exists
    try:
        subprocess.run([python_path, "-m", "ensurepip"], check=True)
    except subprocess.CalledProcessError:
        print("⚠️ `ensurepip` is missing. Skipping...")
        # ✅ Manually install pip when `ensurepip` is not available
        get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
        get_pip_path = os.path.join(venv_path, "get-pip.py")

        # ✅ Download get-pip.py
        subprocess.run(["curl", "-o", get_pip_path, get_pip_url], check=True)

        # ✅ Run get-pip.py inside the virtual environment
        subprocess.run([python_path, get_pip_path], check=True)

        # ✅ Cleanup
        os.remove(get_pip_path)
    subprocess.run([python_path, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=True)

    print("📦 Installing dependencies...")
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

        except Exception as e:
            print(f"Error processing `pyproject.toml`: {e}")
        print("proj_name=", project_name)
        # Special handling for the opentelemetry project
    if project_name.lower() == "microsoft/opentelemetry-azure-monitor-python":
        print("📦 Special handling for opentelemetry project...")
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


    #else:
    #    print("No `pyproject.toml` found at the project path.") 

    # ✅ Check for requirements.txt
    install_requirements(python_path, project_path, pip_path, project_name)
    '''requirements_files = [
        os.path.join(project_path, "requirements.txt"),
        os.path.join(project_path, "requirements-dev.txt"),
        os.path.join(project_path, "requirements_test.txt"),
        os.path.join(project_path, "dev-requirements.txt"),
        os.path.join(project_path, "test-requirements.txt"),
    ]

    installed = False
    for req_file in requirements_files:
        if os.path.exists(req_file):
            print(f"📦 Installing dependencies from {req_file}...")
            subprocess.run([pip_path, "install", "-r", req_file], check=True)
            installed = True
            break

    # ✅ If no requirements.txt, try setup.py (for editable mode installation)
    setup_py_path = os.path.join(project_path, "setup.py")
    if not installed and os.path.exists(setup_py_path):
        print("📦 Installing project in editable mode from setup.py...")
        subprocess.run([pip_path, "install", "-e", project_path], check=True)

    # ✅ Always ensure test dependencies are installed
    print("📦 Ensuring `pytest` and related dependencies are installed...")
    subprocess.run([pip_path, "install", "--upgrade", "pytest", "pytest-cov", "pytest-xdist", "pytest-repeat", "toml"], check=True)

    print("✅ Dependencies installed successfully!\n")'''

#def install_dependencies(venv_path, project_path, project_name):
#    """Ensure all project dependencies are installed inside the virtual environment."""
#    
#    python_path = os.path.join(venv_path, "bin", "python")
#    pip_path = os.path.join(venv_path, "bin", "pip")
#
#    print("📦 Ensuring `pip` is installed in the virtual environment...")
#
#    # ✅ If pip is missing, install it manually
#    if not os.path.exists(pip_path):
#        print("⚠️ `pip` not found! Manually installing `pip` inside the virtual environment...")
#        subprocess.run([python_path, "-m", "ensurepip"], check=True)
#        subprocess.run([python_path, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=True)
#    print("📦 Installing dependencies...")
#    pyproject_toml = os.path.join(project_path, "pyproject.toml")
#
#    if os.path.exists(pyproject_toml):
#        with open(pyproject_toml, "r", encoding="utf-8") as f:
#            pyproject_data = toml.load(f)
#
#        dependencies = pyproject_data.get("project", {}).get("dependencies", [])
#
#        if dependencies:
#            print(f"📦 Installing dependencies from `pyproject.toml`...")
#            subprocess.run([pip_path, "install"] + dependencies, check=True)
#
#    # ✅ Check for requirements.txt
#    requirements_files = [
#        os.path.join(project_path, "requirements.txt"),
#        os.path.join(project_path, "requirements-dev.txt"),
#        os.path.join(project_path, "requirements_test.txt"),
#        os.path.join(project_path, "dev-requirements.txt"),
#        os.path.join(project_path, "test-requirements.txt"),
#    ]
#
#    installed = False
#    for req_file in requirements_files:
#        if os.path.exists(req_file):
#            print(f"📦 Installing dependencies from {req_file}...")
#            subprocess.run([pip_path, "install", "-r", req_file], check=True)
#            installed = True
#            break
#
#    # ✅ If no requirements.txt, try setup.py
#    setup_py_path = os.path.join(project_path, "setup.py")
#    if not installed and os.path.exists(setup_py_path):
#        print("📦 Installing dependencies from setup.py...")
#        subprocess.run([pip_path, "install", "-e", project_path], check=True)
#        installed = True
#
#    '''print("📦 Installing optional dependencies: `avwx-engine[fuzz]`...") #avwx-engine project specific
#    subprocess.run([pip_path, "install", "avwx-engine[fuzz]"], check=True)
#    subprocess.run([pip_path, "install", "scipy"], check=True)'''
#
#    # ✅ Always ensure `pytest` is installed
#    print("📦 Ensuring `pytest` is installed...")
#    subprocess.run([pip_path, "install", "--upgrade", "pytest", "pytest-cov", "pytest-xdist", "pytest-repeat"], check=True)
#    if project_name.lower() == "airbnb/artificial-adversary":
#        print(project_name.lower())
#        print("📦 Airbnb project detected! Installing NLTK & TextBlob...")
#        subprocess.run([pip_path, "install", "textblob", "nltk"], check=True)
#
#        print("📦 Downloading required NLTK corpora...")
#        subprocess.run([python_path, "-c", "import nltk; nltk.download('punkt')"], check=True)
#        subprocess.run([python_path, "-c", "import nltk; nltk.download('averaged_perceptron_tagger')"], check=True)
#        #exit()
#    elif project_name.lower() == "2franix/rpi-controls": 
#        print("install dep")
#        subprocess.run([pip_path, "install", "importlib_metadata"], check=True)
#
#
#    print("✅ Dependencies installed successfully!\n")

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
        print(f"❌ ERROR: Python binary not found in virtualenv: {python_path}")
        print(f"🔍 Current working directory: {os.getcwd()}")  # Print current directory
        return

    if not os.path.exists(pytest_path):
        print(f"❌ ERROR: pytest not found in virtualenv: {pytest_path}")
        print(f"🔍 Current working directory: {os.getcwd()}")  # Print current directory
        return

    # Convert project path to absolute path
    project_path = os.path.abspath(project_path)
    num_parallel = 200
    test_pass=0
    test_fail=0
    pytest_command = [python_path, "-m", "pytest", test_name]
    #pytest_command = [
    #    pytest_path,  # Path to pytest inside virtualenv
    #    "--maxfail=1",  # Stop after first failure
    #    "-n", str(num_parallel),  # Run tests in parallel
    #    "--count", str(10000),  # Repeat the test N times
    #    test_name  # The test to run
    #]


    # 🔍 Print debugging info
    print(f"🚀 Running command: {' '.join(pytest_command)}")
    print(f"📂 Project directory: {project_path}")
    print(f"🔍 Current working directory before running pytest: {os.getcwd()}")
    # Format log filename: replace `.py` and `::` with `_`
    formatted_test_name = test_name.replace(".py", "").replace("::", "_").replace("/", "_")
    log_file = os.path.join(log_dir, f"{os.path.basename(project_path)}_{formatted_test_name}.log")

    with open(log_file, "w") as log:
        for i in range(1, num_runs+1):
            print(f"🔄 Running test {i}/{num_runs}...")
            try:
                result = subprocess.run(pytest_command, cwd=project_path, check=False, capture_output=True, text=True) 
                log.write(f"=== Test Run {i}/{num_runs} ===\n")
                log.write(result.stdout + "\n")
                log.write(result.stderr + "\n")
                # Check test results
                if "1 passed" in result.stdout:
                    test_pass += 1
                if "1 failed" in result.stdout:
                    test_fail += 1

                # Stop if at least one test passes and one fails
                if test_pass > 0 and test_fail > 0:
                    print("🚨 Flaky test detected! Stopping execution.")
                    return True # flaky test detected

            except Exception as e:
                print(f"❌ ERROR: An unexpected exception occurred.\n{e}")
                print(f"🔍 Current working directory after failure: {os.getcwd()}")

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
            flaky_behavior_found = run_tests(venv_path, repo_path, test_name, log_dir)
            # Write results to output file
            writer.writerow([gitproj_name, sha, test_name, flaky_behavior_found])
            outfile.flush()

            #if not args.keep_venv:
            #    cleanup(venv_path)
            #exit()

#
