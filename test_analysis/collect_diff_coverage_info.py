import difflib
import ast
import os
import sys
import xml.etree.ElementTree as ET

def is_executable_line(line, in_multiline_string):
    """Check if a line is not a comment, blank, or within a multiline string."""
    stripped_line = line.strip()

    # Check if we are currently in a multiline string
    if in_multiline_string:
        # Check if this line closes the multiline string
        if '"""' in stripped_line and stripped_line.count('"""') % 2 != 0:
            return False, not in_multiline_string
        return False, in_multiline_string

    # Handling for single-line comments or empty lines
    if stripped_line.startswith("#") or stripped_line == "":
        return False, False

    # Check for start or end of a multiline string
    if stripped_line.startswith('"""') and stripped_line.endswith('"""') and len(stripped_line) > 3:
        # It's a single-line multiline string, ignore
        return False, False
    elif '"""' in stripped_line:
        # Multiline string starts or ends here
        return False, not in_multiline_string

    return True, False

def find_covered_methods_xml(source_file, file_coverage_data, fm, changed_lines_in_diff_fm):
    with open(source_file, 'r') as file:
        #code = file.read()
        code_lines = file.readlines()
    #tree = ast.parse(code, filename=source_file)   
    tree = ast.parse(''.join(code_lines), filename=source_file)
    method_coverage = {}
    in_multiline_string = False
    executable_lines = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == fm:
            start_line = node.lineno
            end_line = max(getattr(n, 'lineno', start_line) for n in ast.walk(node))
            # Determine which changed lines are within this method's range
            relevant_changed_lines = [line for line in changed_lines_in_diff_fm if start_line <= line <= end_line]

            # Check if all relevant changed lines are covered
            covered_changed_lines = [line for line in relevant_changed_lines if line in file_coverage_data]
            all_lines_covered = len(covered_changed_lines) == len(relevant_changed_lines)

            coverage_percentage = (len(covered_changed_lines) / len(relevant_changed_lines) * 100) if relevant_changed_lines else 0

            return covered_changed_lines, coverage_percentage, all_lines_covered

    return [], 0, False


def collect_files_xml(coverage_file_path, focal_meth, changed_lines_in_diff_fm):
    # Parse the XML file
    tree = ET.parse(coverage_file_path)
    root = tree.getroot()  # Get the root of the XML document

    for package in root.findall(".//package"):
        for class_element in package.findall(".//class"):
            filename = class_element.get('filename')
            #print('filename from python=',filename)
            file_coverage_data = {int(line.get('number')) for line in class_element.findall(".//line") if int(line.get('hits')) > 0}
            
            covered_methods, coverage_percentage, all_lines_covered = find_covered_methods_xml(filename, file_coverage_data, focal_meth, changed_lines_in_diff_fm)
            if covered_methods:
                #print(f"Methods covered in {filename}: {covered_methods}")
                return filename, covered_methods, coverage_percentage, all_lines_covered
    
    # Default return if no matching file is found
    return None, [], 0, False



if __name__ == '__main__':
    focal_meth_name = sys.argv[1]
    #changed_focal_method = sys.argv[2]
    #diff_fm = sys.argv[3]
    #changed_lines_in_diff_fm = sys.argv[2]
    changed_lines_in_diff_fm = [int(x) for x in sys.argv[2].split(',')]
    coverage_file_path = 'coverage.xml'
    #print('diff_fm=', diff_fm)
    #print('changed_fm=', changed_focal_method)
    
    if not os.path.exists(coverage_file_path):
        print(f"Error: The file '{coverage_file_path}' does not exist. So, not doing anything more.")
        sys.exit(1)
    
    file_name, lines_covered, coverage_percentage, all_lines_covered = collect_files_xml(coverage_file_path, focal_meth_name, changed_lines_in_diff_fm)
    
    print(f"{file_name}#{lines_covered}#{coverage_percentage}")

    #changed_lines = parse_git_diff(diff_fm)
    ## Collect the coverage data and compare it with the changed lines
    #file_name, lines_covered, coverage_percentage = collect_files_xml(
    #    coverage_file_path, changed_lines
    #)

    #if file_name:
    #    print(f"{file_name}#{lines_covered}#{coverage_percentage}")
    #else:
    #    print("No coverage information found for the changed lines.")
