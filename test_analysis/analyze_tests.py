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

def get_imports(tree):
    imports = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports[n.asname if n.asname else n.name] = n.name
        elif isinstance(node, ast.ImportFrom):
            for n in node.names:
                imports[n.asname if n.asname else n.name] = f"{node.module}.{n.name}"
    return imports

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

#==========JACCARD SIMILARITY (method call with test_method name)============
def tokenize(name):
    """ Tokenize identifiers based on camel case and underscores, ignoring underscores. """
    tokens = []
    current = []
    for char in name:
        if char.isupper() or char.isdigit():
            if current:
                tokens.append(''.join(current)) #.lower())
                current = []
            current.append(char)
        elif char == '_':
            if current:
                tokens.append(''.join(current)) #.lower())
                current = []
        else:
            current.append(char)
    if current:
        tokens.append(''.join(current)) #.lower())
    return tokens

def jaccard_similarity(set1, set2):
    """ Calculate the Jaccard similarity between two sets. """
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union != 0 else 0

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

def save_function_body_for_claude_experiment(code, node, file_path):
    start_line_no, end_line_no = get_function_start_and_end_line_no(node)
    source_lines = code.splitlines()[start_line_no-1:end_line_no]
    # Create a single string from the list of lines
    function_code = "\n".join(source_lines)
    #function_block.append()
    return (file_path, node.name,function_code)

def method_name_with_call_similarities(proj_name, git_link, test_directory, outputFile):
    full_test_directory = os.path.abspath(test_directory)
    all_similarities = defaultdict(list)  # Store method name similarities for each file
    function_blocks = [] 

    count_total_tests_in_a_proj = 0
    count_api_found_for_a_test_meth = 0
    for root, _, files in os.walk(full_test_directory):
        for file in files:
            if is_test_file(file):
                temp_df = pd.DataFrame(columns=['method_name', 'function_call', 'similarity_score'])  # Temporary DataFrame
                file_path = os.path.join(root, file)
                code, tree = get_tree_from_code(file_path)
                #print(ast.dump(tree, indent=4))
                #exit()
                imports = get_imports(tree)
                #print(ast.dump(tree, indent=4))
                function_block = []
                test_method_name_list = []
                for node in ast.walk(tree):
                    if check_valid_test(node):
                        count_total_tests_in_a_proj += 1
                       # Will collect method body for the node
                        function_info = save_function_body_for_claude_experiment(code, node, file_path)
                        test_method_name = node.name
                        if test_method_name in test_method_name_list: # This check is needed because the project h2 contains the same tests twice within a few test_class
                            #print('*********Same test method found************', test_method_name)
                            continue

                        function_block.append(function_info)
                        test_method_name_list.append(test_method_name)
                        method_tokens = set(tokenize(test_method_name))
                        method_tokens.discard('test')

                        call_visitor = CallVisitor(imports)
                        call_visitor.visit(node)
                        function_calls = call_visitor.calls
                        arg_counts = call_visitor.argument_counts
                        class_names = call_visitor.class_names
                        api_call_list = []
                        highest_api_score = 0
                        best_call = None
                        # Compare method name with each function call
                        for call, class_name, arg_count in zip(function_calls, class_names, arg_counts):
                            #print('call=',call)
                            call_tokens = set(tokenize(call))
                            score = jaccard_similarity(method_tokens, call_tokens)
                            #print("score====")
                            api_call_list.append(call+"#"+str(score))
                            if score > highest_api_score:  # Only record if there's a similarity
                                highest_api_score = score
                                best_call = {
                                   'method_name': test_method_name,
                                   'function_call': call.split('.')[-1],
                                   'arg_count': arg_count,
                                   'focal_method_class_name': class_name,
                                   'similarity_score': score
                                }
                        # Concatenate new rows to the DataFrame
                        if best_call:
                            best_call['all_api_list'] =', '.join(api_call_list)
                            best_call_df = pd.DataFrame([best_call])
                            best_call_df.dropna(how='all', inplace=True)

                            if not best_call_df.empty:
                                temp_df = pd.concat([temp_df, best_call_df], ignore_index=True)
                            #temp_df = pd.concat([temp_df, pd.DataFrame([best_call])], ignore_index=True)
                
                function_blocks.extend(function_block)
                temp_df = temp_df.drop_duplicates(subset=['method_name', 'function_call', 'arg_count','focal_method_class_name', 'similarity_score'])
                all_similarities[file_path].extend(temp_df.to_dict('records'))
    save_test_method_body(proj_name, git_link, outputFile, function_blocks)
    #print(count_total_tests_in_a_proj) 
    #print(count_api_found_for_a_test_meth) 
    # Write to outputFile
    with open(outputFile, 'w', newline='') as output_file:
        writer = csv.writer(output_file)
        writer.writerow(['proj_name','git_link','file_path','test_method','function_call#arg_count','focal_method_class_name','similarity_score','all_api_list'])
        for file, data in all_similarities.items():
            for entry in data: 
                func_arg = f"{entry['function_call']}#{int(entry['arg_count'])}"
                writer.writerow([proj_name,git_link,file,entry['method_name'],func_arg,entry['focal_method_class_name'],f"{entry['similarity_score']:.4f}",entry['all_api_list']])

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
    similarity_with_api_call_outputFile = sys.argv[1] + "_focal_method_with_api_similarity.csv"
    assert_similarity_with_api_call_outputFile = sys.argv[1] + "_focal_method_with_assert_similarity.csv"
    method_name_with_call_similarities(proj_name, git_link, test_directory, similarity_with_api_call_outputFile) #Perform jaccard similarity
    #assert_args_with_call_similarities(test_directory, assert_similarity_with_api_call_outputFile)
    calculate_cyclomatic_complexity(proj_name, git_link, test_directory, complexity_outputFile)
    dependencies = analyze_directory(test_directory)
    save_dependencies_to_file(proj_name, git_link, dependencies, output_dependency_file)


if __name__ == '__main__':
    main()

