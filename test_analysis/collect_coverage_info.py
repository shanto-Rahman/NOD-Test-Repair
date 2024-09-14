import json
import ast
import sys
import os
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

def find_covered_methods_xml(source_file, file_coverage_data, fm):
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
            total_lines = end_line - start_line + 1  # Total lines in the method
            for i, line in enumerate(code_lines[start_line-1:end_line+1]):
                is_exec, in_multiline_string = is_executable_line(line, in_multiline_string)
                if is_exec:
                    executable_lines.append(start_line + i)
            lines_covered = [line for line in executable_lines if line in file_coverage_data]
            total_executable_lines = len(executable_lines)  # Total executable lines in the method
            
            number_of_lines_covered = len(lines_covered)
            if total_executable_lines > 0:  # Avoid division by zero
                coverage_percentage = (number_of_lines_covered / total_executable_lines) * 100
            else:
                coverage_percentage = 0

            if lines_covered:
                return lines_covered, coverage_percentage


    return [], 0

def collect_files_xml(coverage_file_path, focal_meth):
    # Parse the XML file
    tree = ET.parse(coverage_file_path)
    root = tree.getroot()  # Get the root of the XML document

    for package in root.findall(".//package"):
        for class_element in package.findall(".//class"):
            filename = class_element.get('filename')
            #print('filename from python=',filename)
            file_coverage_data = {int(line.get('number')) for line in class_element.findall(".//line") if int(line.get('hits')) > 0}
            
            covered_methods, coverage_percentage = find_covered_methods_xml(filename, file_coverage_data, focal_meth)
            if covered_methods:
                #print(f"Methods covered in {filename}: {covered_methods}")
                return filename, covered_methods, coverage_percentage

if __name__ == '__main__':
    focal_meth = sys.argv[1]
    coverage_file_path = 'coverage.xml'
    if not os.path.exists(coverage_file_path):
        print(f"Error: The file '{coverage_file_path}' does not exist. So, not doing anything more.")
        sys.exit(1)  # Exit the script with a non-zero error code to indicate an error

    file_name, lines_covered, coverage_percentage = collect_files_xml(coverage_file_path, focal_meth)
    
    print(f"{file_name}#{lines_covered}#{coverage_percentage}")
