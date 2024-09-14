import os
from radon.visitors import ComplexityVisitor, Function
from radon.complexity import cc_visit
import sys
import ast
import re
import csv
from dependency_analysis import analyze_directory
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import difflib
from difflib import SequenceMatcher
from valid_test_find import AssertVisitor, is_fixture_decorator, get_full_name, is_test_file, find_test_directory, debug_print_decorators, check_valid_test
from save_result import save_dependencies_to_file, save_complexities_to_file, save_test_method_body
import pandas as pd
from call_visitor import CallVisitor 

def get_function_source_code(file_path, start_line_no, end_line_no):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    return ''.join(lines[start_line_no - 1:end_line_no])


def get_function_start_and_end_line_no(node):
    start_line_no = node.lineno
    # Consider decorators
    if hasattr(node, 'decorator_list') and node.decorator_list:
        start_line_no = min(start_line_no, node.decorator_list[0].lineno)

    def max_line(n):
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
        last_line = max(last_line, body_last_line)
    return start_line_no, last_line

def get_tree_from_code(code_file):
    with open(code_file, 'r') as f:
        code = f.read()
    tree = ast.parse(code)
    return code, tree

def cyclomatic_complexity(file_path):
    code, tree = get_tree_from_code(file_path)
    visitor = ComplexityVisitor.from_code(code)
    complexities = []
    for node in ast.walk(tree):
        if check_valid_test(node):
            start_line_no, end_line_no = get_function_start_and_end_line_no(node)
            complexity = next((func.complexity for func in visitor.functions if func.lineno == node.lineno), None)        
            #print(file_path, node.name, complexity, start_line_no, end_line_no)
            complexities.append((file_path, node.name, complexity, end_line_no - start_line_no, start_line_no, end_line_no))

    return complexities #, function_block

def calculate_cyclomatic_complexity(proj_name, git_link, test_directory, outputFile):
    all_cyclomatic_complexities = []
    #function_blocks = []
    full_test_directory = os.path.abspath(test_directory)
    for root, _, files in os.walk(full_test_directory):
        for file in files:
            if is_test_file(file):
                file_path = os.path.join(root, file)
                file_complexities = cyclomatic_complexity(file_path)	
                all_cyclomatic_complexities.extend(file_complexities)
                #function_blocks.extend(function_block)

    if not all_cyclomatic_complexities:
        print("No functions or methods found with cyclomatic complexity.")

    else:
        save_complexities_to_file(proj_name, git_link, all_cyclomatic_complexities, outputFile)
        print(f"\nComplexities saved to complexities.txt")
        #exit()

def main():
    current_directory = os.getcwd()
    #print(current_directory)
    test_directory = find_test_directory(current_directory)
    #print('Arg=',sys.argv[1])
    proj_name = (sys.argv[1]).split("/")[-1]
    git_link = sys.argv[2]
    #print('proj_name=',proj_name)
    output_dependency_file = sys.argv[1] +"_dependency.csv" #Other chanracteristics of the test_method
    complexity_outputFile = sys.argv[1] + "_cyclomatic_complexity.csv" #Cyclomatic complexity for test_method
    calculate_cyclomatic_complexity(proj_name, git_link, test_directory, complexity_outputFile)
    dependencies = analyze_directory(test_directory)
    save_dependencies_to_file(proj_name, git_link, dependencies, output_dependency_file)


if __name__ == '__main__':
    main()
