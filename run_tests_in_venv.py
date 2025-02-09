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
def proj_clone(proj_name, sha):
    repo_url = "https://github.com/"+proj_name
    repo_path = proj_name.split("/")[-1]
    
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
    pyproject_toml = os.path.join(project_path, "pyproject.toml")
    python_version = None

    if os.path.exists(pyproject_toml):
        try:
            import toml
            pyproject_data = toml.load(pyproject_toml)
            python_version = pyproject_data.get("project", {}).get("requires-python", "").lstrip(">=")
            if python_version:
                print(f"✅ Detected Python version from pyproject.toml: {python_version}")
        except Exception as e:
            print(f"⚠️ Error reading pyproject.toml: {e}")

    # Default to Python 3.8 if no version is found
    if not python_version:
        print("⚠️ No Python version specified, defaulting to 3.8")
        python_version = "3.8"

    # ✅ Find full path to the correct Python version
    python_executable = shutil.which(f"python{python_version}")
    
    if python_executable:
        print(f"✅ Found Python executable: {python_executable}")
        return python_executable
    else:
        print(f"❌ Python {python_version} not found! Falling back to default `python3`")
        return shutil.which("python3")


import os
import subprocess
import shutil

def create_virtual_env(project_path, python_executable):
    """Creates a virtual environment using `virtualenv` inside the project root directory."""
    
    venv_path = os.path.join(project_path, "virtualenv")  # Use "virtualenv" in project root

    print(f"📦 Creating virtual environment in: {venv_path} using {python_executable}")

    if os.path.exists(venv_path):
        print("⚠️ Virtual environment already exists. Deleting it first...")
        shutil.rmtree(venv_path)

    # Ensure `virtualenv` is installed
    try:
        subprocess.run([python_executable, "-m", "virtualenv", "--version"], check=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("⚠️ `virtualenv` not found! Installing it first...")
        subprocess.run([python_executable, "-m", "pip", "install", "--user", "virtualenv"], check=True)

    # Find `virtualenv` path
    virtualenv_bin = shutil.which("virtualenv") or os.path.expanduser("~/.local/bin/virtualenv")

    # ✅ Create virtual environment inside the project root
    try:
        subprocess.run([virtualenv_bin, venv_path], check=True)
    except subprocess.CalledProcessError:
        print("❌ Failed to create virtual environment with `virtualenv`!")
        exit(1)

    print(f"✅ Virtual environment created at: {venv_path}")
    return venv_path

import os
import subprocess
import toml

def install_dependencies(venv_path, project_path):
    """Ensure all project dependencies are installed inside the virtual environment."""
    
    python_path = os.path.join(venv_path, "bin", "python")
    pip_path = os.path.join(venv_path, "bin", "pip")

    print("📦 Ensuring `pip` is installed in the virtual environment...")

    # ✅ If pip is missing, install it manually
    if not os.path.exists(pip_path):
        print("⚠️ `pip` not found! Manually installing `pip` inside the virtual environment...")
        subprocess.run([python_path, "-m", "ensurepip"], check=True)
        subprocess.run([python_path, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=True)
    print("📦 Installing dependencies...")
    pyproject_toml = os.path.join(project_path, "pyproject.toml")

    if os.path.exists(pyproject_toml):
        with open(pyproject_toml, "r", encoding="utf-8") as f:
            pyproject_data = toml.load(f)

        dependencies = pyproject_data.get("project", {}).get("dependencies", [])

        if dependencies:
            print(f"📦 Installing dependencies from `pyproject.toml`...")
            subprocess.run([pip_path, "install"] + dependencies, check=True)

    # ✅ Check for requirements.txt
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
            print(f"📦 Installing dependencies from {req_file}...")
            subprocess.run([pip_path, "install", "-r", req_file], check=True)
            installed = True
            break

    # ✅ If no requirements.txt, try setup.py
    setup_py_path = os.path.join(project_path, "setup.py")
    if not installed and os.path.exists(setup_py_path):
        print("📦 Installing dependencies from setup.py...")
        subprocess.run([pip_path, "install", "-e", project_path], check=True)
        installed = True

    '''print("📦 Installing optional dependencies: `avwx-engine[fuzz]`...") #avwx-engine project specific
    subprocess.run([pip_path, "install", "avwx-engine[fuzz]"], check=True)
    subprocess.run([pip_path, "install", "scipy"], check=True)'''

    # ✅ Always ensure `pytest` is installed
    print("📦 Ensuring `pytest` is installed...")
    subprocess.run([pip_path, "install", "--upgrade", "pytest", "pytest-cov", "pytest-xdist", "pytest-repeat"], check=True)
    print("✅ Dependencies installed successfully!\n")

import os
import subprocess
import sys
import subprocess
import os

def run_tests(venv_path, project_path, test_name, log_dir, num_runs=1000):
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
    #pytest_command = [python_path, "-m", "pytest", "-n", str(num_parallel), "--count", str(num_runs), "--maxfail=1", test_name]
    pytest_command = [
        pytest_path,  # Path to pytest inside virtualenv
        "--maxfail=1",  # Stop after first failure
        "-n", str(num_parallel),  # Run tests in parallel
        "--count", str(10000),  # Repeat the test N times
        test_name  # The test to run
    ]


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
                log.write("=" * 50 + "\n\n")


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
    log_dir = os.path.join(script_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    input_file_name = sys.argv[1] #data/idoft_all_nod_test.csv 
    with open(input_file_name, newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            gitproj_name = row[0]
            sha = row[1]
            test_name = row[2]
            project_name = full_path_after_3 = "/".join(gitproj_name.split("/")[3:])
 
            repo, repo_path = proj_clone(project_name, sha)
            print("repo=", repo)
            #parser = argparse.ArgumentParser(description="Run tests in an isolated virtual environment per project.")
            #parser.add_argument("project_path", type=str, help="Path to the project directory")
            #args = parser.parse_args()

            #project_path = os.path.abspath(args.project_path)
            #project_name = os.path.basename(project_path)

            python_executable = detect_python_version(repo_path)
            venv_path = create_virtual_env(repo_path, python_executable)
            install_dependencies(venv_path, repo_path)
            run_tests(venv_path, repo_path, test_name, log_dir)

            #if not args.keep_venv:
            #    cleanup(venv_path)
            exit()

#
