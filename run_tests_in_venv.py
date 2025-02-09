import os
import subprocess
import shutil
import sys
import venv
import re
import csv

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

import subprocess
import shutil
import os
import sys

def create_virtual_env(project_name, project_path, python_executable):
    """Creates a virtual environment using `virtualenv` for the project."""
    venv_path = os.path.join(project_path, f"{project_name}_venv")

    print(f"📦 Creating virtual environment in: {venv_path} using {python_executable}")

    if os.path.exists(venv_path):
        print("⚠️ Virtual environment already exists. Deleting it first...")
        shutil.rmtree(venv_path)

    # ✅ Ensure `virtualenv` is installed
    try:
        subprocess.run([python_executable, "-m", "virtualenv", "--version"], check=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("⚠️ `virtualenv` not found! Installing it first...")
        subprocess.run([python_executable, "-m", "pip", "install", "--user", "virtualenv"], check=True)

    # ✅ Find the correct `virtualenv` path
    virtualenv_bin = shutil.which("virtualenv") or os.path.expanduser("~/.local/bin/virtualenv")
    
    # ✅ Create virtual environment
    try:
        subprocess.run([virtualenv_bin, venv_path], check=True)
    except subprocess.CalledProcessError:
        print("❌ Failed to create virtual environment with `virtualenv`!")
        sys.exit(1)

    print(f"✅ Virtual environment created at: {venv_path}")
    return venv_path

#import subprocess
#import shutil
#import sys
#
#def create_virtual_env(project_name, project_path, python_executable):
#    """Creates a virtual environment using `virtualenv` for the project."""
#    venv_path = os.path.join(project_path, f"{project_name}_venv")
#
#    print(f"📦 Creating virtual environment in: {venv_path} using {python_executable}")
#
#    if os.path.exists(venv_path):
#        print("⚠️ Virtual environment already exists. Deleting it first...")
#        shutil.rmtree(venv_path)
#
#    # ✅ Check if `pip` is installed
#    try:
#        subprocess.run([python_executable, "-m", "ensurepip", "--default-pip"], check=True)
#        print("✅ ensurepip found!")
#    except subprocess.CalledProcessError:
#        print("⚠️ `ensurepip` is missing! Trying to install manually...")
#        subprocess.run(["sudo", "apt", "install", "-y", "python3.10-venv"], check=False)  # Safe fallback
#        try:
#            subprocess.run([python_executable, "-m", "ensurepip", "--default-pip"], check=True)
#        except subprocess.CalledProcessError:
#            print("❌ `ensurepip` is still missing! Cannot proceed.")
#            sys.exit(1)
#
#    # ✅ Upgrade `pip`
#    try:
#        subprocess.run([python_executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=True)
#        print("✅ pip installed successfully!")
#    except subprocess.CalledProcessError:
#        print("❌ Failed to install `pip`! Check your Python installation.")
#        sys.exit(1)
#
#    # ✅ Install `virtualenv` if missing
#    try:
#        subprocess.run([python_executable, "-m", "pip", "install", "--user", "virtualenv"], check=True)
#        print("✅ virtualenv installed successfully!")
#    except subprocess.CalledProcessError:
#        print("❌ Failed to install `virtualenv`!")
#        sys.exit(1)
#
#    # ✅ Create the virtual environment
#    try:
#        subprocess.run([python_executable, "-m", "virtualenv", venv_path], check=True)
#    except subprocess.CalledProcessError:
#        print("❌ Failed to create virtual environment with `virtualenv`!")
#        sys.exit(1)
#
#    print(f"✅ Virtual environment created at: {venv_path}")
#    return venv_path

#import subprocess
#import shutil
#
#def create_virtual_env(project_name, project_path, python_executable):
#    """Creates a virtual environment using `virtualenv` for the project."""
#    venv_path = os.path.join(project_path, f"{project_name}_venv")
#
#    print(f"📦 Creating virtual environment in: {venv_path} using {python_executable}")
#
#    if os.path.exists(venv_path):
#        print("⚠️ Virtual environment already exists. Deleting it first...")
#        shutil.rmtree(venv_path)
#
#    # ✅ Ensure `pip` is installed before proceeding
#    try:
#        subprocess.run([python_executable, "-m", "ensurepip", "--default-pip"], check=True)
#        subprocess.run([python_executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=True)
#        print("✅ pip installed successfully!")
#    except subprocess.CalledProcessError:
#        print("❌ Failed to install `pip`! Check your Python installation.")
#        exit(1)
#
#    # ✅ Install `virtualenv` if missing
#    try:
#        subprocess.run([python_executable, "-m", "pip", "install", "--user", "virtualenv"], check=True)
#        print("✅ virtualenv installed successfully!")
#    except subprocess.CalledProcessError:
#        print("❌ Failed to install `virtualenv`!")
#        exit(1)
#
#    # ✅ Create the virtual environment
#    try:
#        subprocess.run([python_executable, "-m", "virtualenv", venv_path], check=True)
#    except subprocess.CalledProcessError:
#        print("❌ Failed to create virtual environment with `virtualenv`!")
#        exit(1)
#
#    print(f"✅ Virtual environment created at: {venv_path}")
#    return venv_path
#
#def create_virtual_env(project_name, project_path, python_executable):
#    """Creates a virtual environment using `virtualenv` for the project."""
#    venv_path = os.path.join(project_path, f"{project_name}_venv")
#
#    print(f"📦 Creating virtual environment in: {venv_path} using {python_executable}")
#
#    if os.path.exists(venv_path):
#        print("⚠️ Virtual environment already exists. Deleting it first...")
#        shutil.rmtree(venv_path)
#
#    # ✅ Ensure virtualenv is installed
#    try:
#        subprocess.run([python_executable, "-m", "virtualenv", "--version"], check=True, stdout=subprocess.PIPE)
#    except subprocess.CalledProcessError:
#        print("⚠️ `virtualenv` not found! Installing it first...")
#        subprocess.run([python_executable, "-m", "pip", "install", "--user", "virtualenv"], check=True)
#
#    # ✅ Use `virtualenv` to create the environment
#    try:
#        subprocess.run([python_executable, "-m", "virtualenv", venv_path], check=True)
#    except subprocess.CalledProcessError:
#        print("❌ Failed to create virtual environment with `virtualenv`!")
#        exit(1)
#
#    print(f"✅ Virtual environment created at: {venv_path}")
#    return venv_path

#def create_virtual_env(project_name, project_path, python_executable):
#    """Creates a virtual environment using `virtualenv` for the project."""
#    venv_path = os.path.join(project_path, f"{project_name}_venv")
#
#    print(f"📦 Creating virtual environment in: {venv_path} using {python_executable}")
#
#    if os.path.exists(venv_path):
#        print("⚠️ Virtual environment already exists. Deleting it first...")
#        shutil.rmtree(venv_path)
#
#    # ✅ Use the correct Python executable
#    try:
#        subprocess.run([python_executable, "-m", "virtualenv", venv_path], check=True)
#    except subprocess.CalledProcessError:
#        print("❌ Failed to create virtual environment with `virtualenv`!")
#        exit(1)
#
#    print(f"✅ Virtual environment created at: {venv_path}")
#    return venv_path

#def install_dependencies(venv_path, project_path):
#    """Install project dependencies inside the virtual environment."""
#    
#    pip_path = os.path.join(venv_path, "bin", "pip") if os.name != "nt" else os.path.join(venv_path, "Scripts", "pip.exe")
#
#    print("📦 Ensuring `pip` is installed in the virtual environment...")
#
#    # ✅ If pip is missing, install it manually
#    if not os.path.exists(pip_path):
#        print("⚠️ `pip` not found! Manually installing `pip` inside the virtual environment...")
#        python_path = os.path.join(venv_path, "bin", "python") if os.name != "nt" else os.path.join(venv_path, "Scripts", "python.exe")
#        subprocess.run([python_path, "-m", "ensurepip"], check=True)
#        subprocess.run([python_path, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=True)
#
#    print("📦 Installing dependencies...")
#
#    # ✅ Check if pyproject.toml uses Poetry
#    pyproject_toml = os.path.join(project_path, "pyproject.toml")
#    if os.path.exists(pyproject_toml):
#        with open(pyproject_toml, "r", encoding="utf-8") as f:
#            pyproject_content = f.read()
#
#        if "[tool.poetry]" in pyproject_content:
#            print("📦 Detected valid `pyproject.toml`, installing dependencies with Poetry...")
#            subprocess.run([pip_path, "install", "poetry"], check=True)
#            subprocess.run(["poetry", "install"], cwd=project_path, check=True)
#            print("✅ Installed dependencies using Poetry!")
#            return
#
#    # ✅ Check for requirements.txt or setup.py
#    requirements_files = [
#        os.path.join(project_path, "requirements.txt"),
#        os.path.join(project_path, "requirements-dev.txt"),
#        os.path.join(project_path, "requirements_test.txt"),
#        os.path.join(project_path, "dev-requirements.txt"),
##        os.path.join(project_path, "test-requirements.txt"),
##    ]
##
##    installed = False
##    for req_file in requirements_files:
##        if os.path.exists(req_file):
##            print(f"📦 Installing dependencies from {req_file}...")
##            subprocess.run([pip_path, "install", "-r", req_file], check=True)
##            installed = True
##            break
##
##    # ✅ If no requirements.txt, try setup.py
##    setup_py_path = os.path.join(project_path, "setup.py")
##    if not installed and os.path.exists(setup_py_path):
##        print("📦 Installing dependencies from setup.py...")
##        subprocess.run([pip_path, "install", "-e", project_path], check=True)
##        installed = True
##
##    # ✅ If neither requirements.txt nor setup.py, install pytest manually
##    if not installed:
##        print("⚠️ No `requirements.txt` or `setup.py` found. Installing `pytest` manually.")
##        subprocess.run([pip_path, "install", "pytest"], check=True)
##
##    print("✅ Dependencies installed successfully!\n")
##
#import os
#import subprocess
#
#def install_dependencies(venv_path, project_path):
#    """Install project dependencies inside the virtual environment."""
#    pip_path = os.path.join(venv_path, "bin", "pip") if os.name != "nt" else os.path.join(venv_path, "Scripts", "pip.exe")
#
#    print("📦 Ensuring `pip` is installed in the virtual environment...")
#
#    # ✅ If pip is missing, install it manually
#    if not os.path.exists(pip_path):
#        print("⚠️ `pip` not found! Manually installing `pip` inside the virtual environment...")
#        python_path = os.path.join(venv_path, "bin", "python") if os.name != "nt" else os.path.join(venv_path, "Scripts", "python.exe")
#        subprocess.run([python_path, "-m", "ensurepip"], check=True)
#        subprocess.run([python_path, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=True)
#
#    print("📦 Installing dependencies...")
#
#    # ✅ Check if pyproject.toml exists
#    pyproject_toml = os.path.join(project_path, "pyproject.toml")
#    if os.path.exists(pyproject_toml):
#        with open(pyproject_toml, "r", encoding="utf-8") as f:
#            pyproject_content = f.read()
#
#        # ✅ If `pytest` configuration exists, ensure pytest-cov is installed
#        if "[tool.pytest.ini_options]" in pyproject_content:
#            print("📦 Detected pytest config in `pyproject.toml`, ensuring `pytest-cov` is installed...")
#            subprocess.run([pip_path, "install", "pytest", "pytest-cov"], check=True)
#
#    # ✅ Check for requirements.txt or setup.py
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
#    # ✅ If neither requirements.txt nor setup.py, install pytest manually
#    if not installed:
#        print("⚠️ No `requirements.txt` or `setup.py` found. Installing `pytest` manually.")
#        subprocess.run([pip_path, "install", "pytest", "pytest-cov"], check=True)
#
#    print("✅ Dependencies installed successfully!\n")

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

    print("📦 Installing optional dependencies: `avwx-engine[fuzz]`...") #avwx-engine project specific
    subprocess.run([pip_path, "install", "avwx-engine[fuzz]"], check=True)
    subprocess.run([pip_path, "install", "scipy"], check=True)

    # ✅ If neither `requirements.txt` nor `setup.py`, manually install missing packages
    if not installed:
        print("⚠️ No `requirements.txt` or `setup.py` found. Installing `pytest` manually.")
        subprocess.run([pip_path, "install", "pytest", "pytest-cov"], check=True)

    print("✅ Dependencies installed successfully!\n")


import os
import subprocess
import sys

def run_tests(venv_path, project_path):
    """Runs all tests using the virtual environment created with `virtualenv`."""
    test_dir = os.path.join(project_path, "tests")

    if not os.path.exists(test_dir):
        print(f"⚠️ No test directory found in {project_path}")
        return

    test_files = [f for f in os.listdir(test_dir) if f.startswith("test_") and f.endswith(".py")]
    if not test_files:
        print("⚠️ No test files found!")
        return

    print("\n🚀 Running tests:")
    python_path = os.path.join(venv_path, "bin", "python") if sys.platform != "win32" else os.path.join(venv_path, "Scripts", "python.exe")

    for test_file in test_files:
        test_path = os.path.join(test_dir, test_file)
        print(f"🔹 Running {test_file}...")

        pytest_command = [
            python_path, "-m", "pytest", test_path
        ]

        # ✅ Run pytest using the correct virtualenv Python
        subprocess.run(pytest_command, check=False)


def cleanup(venv_path):
    """Deletes the virtual environment."""
    if os.path.exists(venv_path):
        shutil.rmtree(venv_path)
        print(f"Deleted virtual environment: {venv_path}")

if __name__ == "__main__":
    import argparse
    input_file_name = sys.argv[1] #data/idoft_all_nod_test.csv 
    with open(input_file_name, newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            gitproj_name = row[0]
            sha = row[1]
            test_name = row[2]
            proj_name = gitproj_name.split("/")[3]
 
            proj_clone(proj_name, sha)
            parser = argparse.ArgumentParser(description="Run tests in an isolated virtual environment per project.")
            parser.add_argument("project_path", type=str, help="Path to the project directory")
            args = parser.parse_args()

            project_path = os.path.abspath(args.project_path)
            project_name = os.path.basename(project_path)

            python_executable = detect_python_version(project_path)
            venv_path = create_virtual_env(project_name, project_path, python_executable)
            install_dependencies(venv_path, project_path)
            run_tests(venv_path, project_path)
            exit()

#    #if not args.keep_venv:
#    #    cleanup(venv_path)
#
