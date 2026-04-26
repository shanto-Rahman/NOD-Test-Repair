import pandas as pd
import subprocess
import os

# Configuration
CSV_FILE = "/NOD-Test-Repair/data/test.csv"  # Ensure this matches your filename
BASE_DIR = "/NOD-Test-Repair/tdrepro/projects"
OS_NAME = os.name

def run_command(cmd, cwd=None):
    try:
        subprocess.run(cmd, shell=True, check=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {cmd}\n{e}")

def main():
    df = pd.read_csv(CSV_FILE)
    
    # Ensure project directory exists
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)

    # Group by slug to handle unique projects
    grouped = df.groupby('slug')

    for slug, group in grouped:
        project_name = slug.split('/')[-1]
        project_path = os.path.join(BASE_DIR, project_name)
        repo_url = f"https://github.com/{slug}"
        sha = group.iloc[0]['sha']

        print(f"\n" + "="*50)
        print(f"PROJECT: {slug}")
        print(f"SHA: {sha}")
        print(f"="*50)

        # Prompt user
        user_input = input(f"Do you want to run tests for {slug}? (y/n): ").lower()
        if user_input != 'y':
            print(f"Skipping {slug}...")
            continue

        # 1. Clone if doesn't exist
        if not os.path.exists(project_path):
            print(f"Cloning {repo_url}...")
            run_command(f"git clone {repo_url} {project_path}")
        
        # 2. Checkout specific SHA
        print(f"Checking out {sha}...")
        run_command(f"git checkout {sha}", cwd=project_path)

        # 3. Run associated tests
        for _, row in group.iterrows():
            module = row['module']
            test_cmd = row['test']
            
            # Determine module directory
            module_dir = project_path if module == "." else os.path.join(project_path, module)
            
            print(f"\nRunning test: {test_cmd} in module: {module}")
            
            # Maven command to run a single test method
            # Format: -Dtest=ClassName#MethodName
            run_command(f"mvn test -Dtest={test_cmd}", cwd=module_dir)

if __name__ == "__main__":
    main()