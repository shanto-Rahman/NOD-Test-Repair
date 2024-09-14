import time
import subprocess
import re
import csv
import ast
import os
from bs4 import BeautifulSoup
import html

def get_function_code(filename, function_name): # For test code, because test method should be uniq
    """Extracts and returns the complete source code of a function from a given Python file."""
    with open(filename, "r") as source:
        tree = ast.parse(source.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return ast.unparse(node)  # For Python 3.9+
    return None  # Return None if the function is not found


def get_function_code_fm(filename, function_name, fm_lines):
    """Extracts and returns the complete source code of a function from a given Python file."""
    with open(filename, "r") as source:
        tree = ast.parse(source.read())
    print(fm_lines)
    fm_start_line, fm_end_line = map(int, fm_lines.strip('[]').split('-'))
    
    # Print the extracted numbers
    print("Start:", fm_start_line)
    print("End:", fm_end_line)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            # Get the start and end lines of the function node
            function_start_line = node.lineno
            function_end_line = max(getattr(n, 'lineno', function_start_line) for n in ast.walk(node))

            # Check if the function lines match the fm_lines range
            if fm_start_line <= function_start_line <= fm_end_line and fm_start_line <= function_end_line <= fm_end_line:
                return ast.unparse(node)
    return None  # Return None if the function is not found


def check_llm_response_for_cc(response, response_loc): #generation task
    if response.find('</root>') == -1:
        return "root_not_found", [], []
   
    if response_loc == "test_meth":
        if  response.find('</generated_test_method>') == -1:
            print('generated_test_method not found')
            return "incomplete_test_fm", [], []
    
    # Extract the XML part only
    xml_start = response.find('<root>')
    xml_end = response.find('</root>') + len('</root>')
    xml_content = response[xml_start:xml_end]
    # Strip any leading/trailing whitespace from the response
    xml_content = xml_content.strip()
 
    #Now going to check if <changed_focal_method> exists or not
    soup = BeautifulSoup(xml_content, 'html.parser')
    # Initialize variables
    #changed_response_method_content = ""
    tag_names = []
    unit_test_name = ""
    if response_loc == "test_meth":
        changed_response_method_content = "incomplete_repaired_test"
        changed_response_method_element = soup.find('generated_test_method')
        if not changed_response_method_element:
            print("generated new test method ***")
            changed_response_method_element = soup.find('new_test_method')
        changes_type = soup.find('modification_type')
        generated_unit_test_element = soup.find('generated_test_name')
    # Extract the content of the method
    if changed_response_method_element:
        changed_response_method_content = changed_response_method_element.get_text(strip=True)
    if generated_unit_test_element:
        unit_test_name = generated_unit_test_element.get_text()
    # Extract changes_type content
    if changes_type:
        tag_names = [change.name for change in changes_type.find_all()]
    print('tag_names=',tag_names)
    return changed_response_method_content, tag_names, unit_test_name



def check_llm_response(response, response_loc):
    if response.find('</root>') == -1:
        return "root_not_found", []
   
    if response_loc == "fm" and response.find('</changed_focal_method>') == -1:
        return "incomplete_changed_fm", []
    if response_loc == "test_meth":
        if  response.find('</repaired_test_method>') == -1 and  response.find('</new_test_method>') == -1:
            print('repaired_test_method not found')
            return "incomplete_test_fm", []
    
    # Extract the XML part only
    xml_start = response.find('<root>')
    xml_end = response.find('</root>') + len('</root>')
    xml_content = response[xml_start:xml_end]
    # Strip any leading/trailing whitespace from the response
    xml_content = xml_content.strip()
 
    #Now going to check if <changed_focal_method> exists or not
    soup = BeautifulSoup(xml_content, 'html.parser')
    # Initialize variables
    #changed_response_method_content = ""
    tag_names = []

    # Find the correct method and changes_type based on response_loc
    if response_loc == "fm":
        changed_response_method_content = "incomplete_changed_fm"
        changed_response_method_element = soup.find('changed_focal_method')
        changes_type = soup.find('changes_type')
    elif response_loc == "test_meth":
        changed_response_method_content = "incomplete_repaired_test"
        changed_response_method_element = soup.find('repaired_test_method')
        if not changed_response_method_element:
            print("generated new test method ***")
            changed_response_method_element = soup.find('new_test_method')
        changes_type = soup.find('modification_type')
    # Extract the content of the method
    if changed_response_method_element:
        changed_response_method_content = changed_response_method_element.get_text(strip=True)
    
    # Extract changes_type content
    if changes_type:
        tag_names = [change.name for change in changes_type.find_all()]
    print('tag_names=',tag_names)
    return changed_response_method_content, tag_names


def run_test_for_real_example(proj_name, fm_file_path, fm_name, unit_test_name, test_file_path, old_commit, new_commit,  objective="Real_data_find"):
    try:
        script_name = "./run_tests.sh"
        if objective == "Real_data_find":
            result = subprocess.run([script_name, proj_name, fm_name, unit_test_name, test_file_path, old_commit, new_commit, fm_file_path], check=True, text=True, capture_output=True)
            print("test_run result, Script output:", result.stdout)

    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running the script: {e}")
        print("Error output:", e.stderr)
    except FileNotFoundError as e:
        print(f"Script file not found: {e}")
    except PermissionError as e:
        print(f"Permission error: {e}")

def run_test(response, fm_file_path, fm_name, fm_lines, unit_test_name, test_file_path, outputFile, proj_name, chain_count_cc, llm_name, changes_types, objective, error_type="", diff_fm="", changed_fm="", diff_test="", dynamic_trace_found="", org_unit_test_name="", changed_line_numbers="", start_time=""): 
    try:
        if objective == "Refine_AF" or objective == "Refine_CC" or objective == "Normal_Test_Run":
            script_name = "./run_test_to_repair.sh"
            if dynamic_trace_found == "":
                dynamic_trace_found = "Dyn-trace-NA"
            else:
                dynamic_trace_found = "Dyn-trace-Found"

            result = subprocess.run([script_name, proj_name, fm_name, unit_test_name, test_file_path, response, objective, outputFile, chain_count_cc, llm_name, changes_types, fm_file_path, objective, diff_fm, changed_fm, diff_test, error_type, dynamic_trace_found, org_unit_test_name, changed_line_numbers, start_time], check=True, text=True, capture_output=True)

        elif objective == "Reproduce-AF" or objective == "AF" or objective == "CC" or objective == "Reproduce_CC" :
            script_name = "./run_test_after_adding_change_in_fm.sh"
            result = subprocess.run([script_name, proj_name, fm_name, unit_test_name, test_file_path, response, outputFile, chain_count_cc, llm_name, changes_types, fm_file_path, objective], check=True, text=True, capture_output=True)
        # Print the initial script output for debugging
        print('start_time=',start_time)
        print("test_run result, Script output:", result.stdout)
        
        dynamic_trace = ""
        if objective == "Reproduce-AF" or objective == "Reproduce_CC":
            # Decode any HTML entities back to their original characters
            decoded_output = html.unescape(result.stdout)
             
            # Extract the content between <traces> and </traces> tags
            match = re.search(r"<traces>([\s\S]*?)</traces>", decoded_output)

            if match:
                dynamic_trace = match.group(1)  # Extract the entire <traces> block including the tags

        coverage_percentage_match = re.search(r"coverage_percentage:\s*([0-9]+(?:\.[0-9]+)?)", result.stdout)
        covered_lines_match = re.search(r"covered_lines:\s*\[([0-9,\s]+)\]", result.stdout)
        
        covered_lines = []
        if covered_lines_match:
            covered_lines_str = covered_lines_match.group(1)
            covered_lines = [int(x.strip()) for x in covered_lines_str.split(',')]
            print('coverage_percentage=',covered_lines)
        if coverage_percentage_match:
            coverage_percentage = float(coverage_percentage_match.group(1))
            print('coverage_percentage=',coverage_percentage)
            #exit()
            return coverage_percentage, dynamic_trace, covered_lines
        else:
            return "", dynamic_trace, covered_lines #"coverage_reduce"
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running the script: {e}")
        print("Error output:", e.stderr)
    except FileNotFoundError as e:
        print(f"Script file not found: {e}")
    except PermissionError as e:
        print(f"Permission error: {e}") 

def parse_test_log(file_path):
    results = {
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "skipped": 0
    }

    # Regular expressions to match log entries
    pass_pattern = re.compile(r'PASSED|SUCCESS|passed|success')
    fail_pattern = re.compile(r'FAILED|FAILURE|failed|Failure')
    error_pattern = re.compile(r'ERROR|EXCEPTION|Error')
    skip_pattern = re.compile(r'SKIPPED|skipped')

    try:
        with open(file_path, 'r') as file:
            for line in file:
                if pass_pattern.search(line):
                    results["passed"] += 1
                elif fail_pattern.search(line):
                    results["failed"] += 1
                elif error_pattern.search(line):
                    results["errors"] += 1
                elif skip_pattern.search(line):
                    results["skipped"] += 1

    except FileNotFoundError:
        print(f"Error: The file {file_path} does not exist.")
        return None

    return results

def parse_log_for_assertion_errors(file_path):
    results = {
        "assertion_errors": 0,
        "failed": 0,
        "errors": 0,
        "syntax_errors": 0,
        "passed": 0,
        "skipped": 0
    }

    # Regular expressions to match log entries
    syntax_error_pattern = re.compile(r'SyntaxError')
    assertion_error_pattern = re.compile(r'AssertionError')
    fail_pattern = re.compile(r'FAILED|FAILURE|failed|Failure')
    error_pattern = re.compile(r'ERROR|EXCEPTION|Error')
    pass_pattern = re.compile(r'PASSED|SUCCESS|passed|success')
    skip_pattern = re.compile(r'SKIPPED|skipped')

    try:
        with open(file_path, 'r') as file:
            for line in file:
                if syntax_error_pattern.search(line): 
                    results["syntax_errors"] += 1
                elif assertion_error_pattern.search(line):
                    results["assertion_errors"] += 1
                elif fail_pattern.search(line):
                    results["failed"] += 1
                elif error_pattern.search(line):
                    results["errors"] += 1
                elif pass_pattern.search(line):
                    results["passed"] += 1
                elif skip_pattern.search(line):
                    results["skipped"] += 1


    except FileNotFoundError:
        print(f"Error: The file {file_path} does not exist.")
        return None

    return results


def extract_failure_reasons(log_content):
    print("****Log_content=", log_content)
    lines = log_content.split('\n')
    
    # Filter out lines that start with '.pkg' or 'py39'
    filtered_lines = [line for line in lines if not line.startswith('.pkg') and not line.startswith('py39')]
    
    # Join the filtered lines back into a single string
    filtered_log_content = '\n'.join(filtered_lines)
    
    # Regular expression to match the failure reason
    failure_reason_pattern = re.compile(r'(ImportError while loading conftest.*|E\s+File ".*", line \d+.*\nE\s+.*\nE\s+\^\nE\s+SyntaxError: .*|FAIL code \d+.*)')
    
    # Find all matches in the filtered log content
    matches = failure_reason_pattern.findall(filtered_log_content)
    
    # Join all matches to form the failure reason
    failure_reason = "\n".join(matches)   
    
    return failure_reason

def git_stash(repo_dir):
    try:
        # Navigate to the repository directory
        subprocess.run(['git', '-C', repo_dir, 'stash'], check=True)
        print(f"Changes stashed successfully in repository at {repo_dir}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while stashing changes: {e}")


def fail_to_generate_test(proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, aim, csv_file_path, chain_count_cc, dynamic_trace, covered_percentage, count_selected_tests_that_covers_all_tests, covered_lines_set, elapsed_time):
    git_stash("../test_analysis/projects/"+proj_name)
    if covered_percentage == "100.0":
        covered_lines_str = ','.join(map(str, covered_lines_set))
        data = [[proj_name,test_file_path,unit_test_name,fm_file_path,fm_name,"NA",covered_lines_str,"100.0","test_pass","NA",aim,[],"DYN",chain_count_cc,count_selected_tests_that_covers_all_tests,elapsed_time]]
    else:
        data = [[proj_name,test_file_path,unit_test_name,fm_file_path,fm_name,"NA","NA",covered_percentage,"NA",aim,[],"DYN",chain_count_cc,count_selected_tests_that_covers_all_tests,elapsed_time]] #covered_percentage kichu ekta howa manei ekta test pass
    with open(csv_file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data) 

def fail_to_refine_test(proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, aim, csv_file_path, chain_count_cc, dynamic_trace, elapsed_time):
    git_stash("../test_analysis/projects/"+proj_name)
    if dynamic_trace == "":
        data = [[proj_name,test_file_path,unit_test_name,fm_file_path,fm_name,"NA","NA","NA","NA","NA","NA","NA",aim,[],"Dyn-trace-NA",chain_count_cc,elapsed_time]]
    else:
        data = [[proj_name,test_file_path,unit_test_name,fm_file_path,fm_name,"NA","NA","NA","NA","NA","NA","NA",aim,[],"Dyn-trace-Found",chain_count_cc,elapsed_time]]
    with open(csv_file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data) 

def fail_to_get_changed_fm(proj_name, test_file_path, unit_test_name, fm_file_path, fm_name, aim, csv_file_path, chain_count_cc):
    data = [[proj_name,test_file_path,unit_test_name,fm_file_path,fm_name,"NA","NA","NA","NA",aim,chain_count_cc]]
    #csv_file_path = "Results/690_tests_with_Focal_Methods.csv" 
    # Write data to the CSV file
    with open(csv_file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data) 

def read_log_file(log_file_path, objective):
    with open(log_file_path, 'r') as file:
        log_content = file.read()
    if objective == "CC" or objective == "Reproduce_CC": 
        test_results = parse_test_log(log_file_path) 
    elif objective == "AF" or objective == "Refine_AF" or objective == "Refine_CC" or objective == "Normal_Test_Run":
        test_results = parse_log_for_assertion_errors(log_file_path)
    return log_content, test_results
