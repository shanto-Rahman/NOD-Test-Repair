import os
from radon.visitors import ComplexityVisitor, Function
from radon.complexity import cc_visit
import sys
import ast
import re
import csv
from dependency_analysis import analyze_specific_function
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import difflib
from difflib import SequenceMatcher
#from valid_test_find import AssertVisitor, is_fixture_decorator, get_full_name, is_test_file, find_test_directory, debug_print_decorators, check_valid_test
#from valid_test_find import is_test_file
from save_result import save_dependencies_to_file, save_complexities_to_file, save_test_method_body
import pandas as pd
from pathlib import Path
#from call_visitor import CallVisitor 

os.environ['BASE_DIR'] = '/mnt/efs/people/urshanto/change_aware_utg'

def get_function_source_code(file_path, start_line_no, end_line_no):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    return ''.join(lines[start_line_no - 1:end_line_no])

def get_function_start_and_end_line_no(node):
     #NEED to debug
    start_line_no = node.lineno

    # Consider decorators
    if hasattr(node, 'decorator_list') and node.decorator_list:
        start_line_no = min(start_line_no, node.decorator_list[0].lineno)
    def max_line(n):
        if hasattr(n, 'end_lineno'):
            max_lineno = n.end_lineno
        else:
            max_lineno = n.lineno if hasattr(n, 'lineno') else -1
        for child in ast.iter_child_nodes(n):
            child_max = max_line(child)
            max_lineno = max(max_lineno, child_max)
        return max_lineno

    # Check the body of the function
    last_line = max_line(node)

    '''def max_line(n):
        max_lineno = n.lineno if hasattr(n, 'lineno') else -1
        for child in ast.iter_child_nodes(n):
            child_max = max_line(child)
            max_lineno = max(max_lineno, child_max)
        return max_lineno

    # Start with the last line of the function definition itself
    last_line = node.lineno

    # Check the body of the function
    if hasattr(node, 'body'):
        body_last_line = max((max_line(n) for n in node.body), default=last_line)
        last_line = max(last_line, body_last_line)'''
    return start_line_no, last_line

def get_tree_from_code(code_file):
    with open(code_file, 'r') as f:
        code = f.read()
    tree = ast.parse(code)
    return code, tree

def write_results_to_csv(result, output_filename, project_name, fm_filename, test_name, test_filename):
    write_header = not os.path.exists(output_filename)
    with open(output_filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        # Write the header if the file is new
        if write_header:
            writer.writerow(['Proj_name', 'fm_File_name', 'test_File_name', 'test_name', 'fm_method', 'args', 'types', 'internal_calls', 'external_calls', 'api_calls', 'branch_count', 'branch_type'])
        
        if result['status'] == 'found':
            details = result['details']
            # Ensure all parts are available, or provide defaults
            writer.writerow([
                project_name,  # Example project name
                fm_filename,  # Example file name
                test_filename,
                test_name,
                result['function_name'],
                details.get('arg_count', '0'),
                '#'.join(details.get('arg_types', [])),
                len(details.get('internal_calls', [])),
                len(details.get('external_calls', [])),
                len(details.get('api_calls', [])),
                details.get('branch_count', '0'),
                ','.join(details.get('branch_types', ['None']))
            ])

def cyclomatic_complexity(file_path, method_name, proj_name, test_name, test_filename, fm_first_covered_line):
    print('file_path=',file_path)
    code, tree = get_tree_from_code(file_path)
    visitor = ComplexityVisitor.from_code(code)
    complexities = []
    fm_found = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == method_name:  # Check for function definitions
            #print(method_name)
            fm_function_details = analyze_specific_function(file_path, method_name)       
            #exit()
            complexity_visitor = ComplexityVisitor()
            complexity_visitor.visit(node)  # Recalculate just for this node
            complexity = complexity_visitor.complexity
            start_line_no, end_line_no = get_function_start_and_end_line_no(node)
            if (int(fm_first_covered_line) - int(start_line_no)) <= 10 and not fm_found: 
                print('HI=',int(start_line_no), int(fm_first_covered_line))
                print('complexity from complexity visitor=', complexity, ", fm_found=", fm_found)
                fm_found=True
                complexities.append((file_path, node.name, complexity, end_line_no - start_line_no, start_line_no, end_line_no))
                print(fm_function_details['status'])
                write_results_to_csv(fm_function_details, "Results/properties_of_fm.csv", proj_name, file_path, test_name, test_filename)
                print(f"Function: {method_name}, Complexity: {complexity}, Lines: {end_line_no - start_line_no}")
        else:
            continue
    return complexities

def calculate_cyclomatic_complexity(proj_name, directory, fm_filepath_and_name, fm, outputFile, test_name, test_filename, fm_first_covered_line):
    all_cyclomatic_complexities = []
    fm_file_name = fm_filepath_and_name.split('/')[-1]
    fm_file_path = Path(fm_filepath_and_name)
    fm_directory_path = fm_file_path.parent
    proj_dir = directory+proj_name
    print('proj_dir=',proj_dir)
    print('directory-path=',fm_directory_path)

    BASE_DIR = os.getenv('BASE_DIR')    
    # Use BASE_DIR to build other paths
    project_path = os.path.join(BASE_DIR, directory)
    print("Base Directory is set to:", BASE_DIR, project_path)    
    sut_path = project_path+"/"+proj_name+"/" +str(fm_directory_path)
    fm_full_directory = os.path.abspath(sut_path)
    print('fm_full_dir=',fm_full_directory)
    result_found = False
    for root, _, files in os.walk(fm_full_directory):
        if not result_found:
            for file in files: #file=pyairtable/api/enterprise.py
                #print(file)
                if file == fm_file_name: #and is_file(file):
                    fm_file_path = os.path.join(root, file)
                    file_complexities = cyclomatic_complexity(fm_file_path, fm, proj_name, test_name, test_filename, fm_first_covered_line) #method_name="info"
                    if file_complexities:
                        #print(fm_file_path,"****========")
                        result_found = True
                        all_cyclomatic_complexities.extend(file_complexities)
                        break
                    #function_blocks.extend(function_block)

    if not all_cyclomatic_complexities:
        print(proj_name, ",No functions or methods found with cyclomatic complexity.")

    else:
        save_complexities_to_file(proj_name, all_cyclomatic_complexities, outputFile, test_name, test_filename)
        print(f"\nComplexities saved to complexities.txt")
        #exit()

def main():
    #current_directory = os.getcwd()
    #print(current_directory)
    directory = "test_analysis/projects/" #find_test_directory(current_directory)
    proj_name = sys.argv[1] #billiard
    #within_proj_dir = sys.argv[2] #billiard
    fm_filepath_and_name = sys.argv[2] #billiard/util.py
    fm = sys.argv[3] #get_pdeathsig
    test_name = sys.argv[4]
    test_filename = sys.argv[5]
    fm_first_covered_line = sys.argv[6]
    #print('proj_name=',proj_name)
    output_dependency_file = sys.argv[1] +"_dependency.csv" #Other chanracteristics of the test_method
    complexity_outputFile = "Results/"+sys.argv[1] + "_cyclomatic_complexity.csv" #Cyclomatic complexity for test_method
    calculate_cyclomatic_complexity(proj_name, directory, fm_filepath_and_name, fm, complexity_outputFile, test_name, test_filename, fm_first_covered_line)
    #dependencies = analyze_directory(test_directory)
    #save_dependencies_to_file(proj_name, git_link, dependencies, output_dependency_file)


if __name__ == '__main__':
    main()
