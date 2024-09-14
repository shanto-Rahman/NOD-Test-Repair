import json
import ast
import sys
import os
import xml.etree.ElementTree as ET
import xml.dom.minidom
import re


# Function to create a new XML element with text content
def create_element_with_text(tag, text):
    element = ET.Element(tag)
    element.text = text
    return element

# Function to parse Python file and get method line ranges
def get_methods_line_ranges(filepath):
    with open(filepath, "r") as file:
        tree = ast.parse(file.read(), filename=filepath)

    methods = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):  # Checks for function definitions
            method_start = node.lineno
            method_end = getattr(node, 'end_lineno', node.body[-1].lineno if node.body else method_start)
            #method_end = node.body[-1].lineno if node.body else method_start
            methods[node.name] = (method_start, method_end)
    
    return methods

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
            file_coverage_data = {int(line.get('number')) for line in class_element.findall(".//line")}
            
            covered_methods, coverage_percentage = find_covered_methods_xml(filename, file_coverage_data, focal_meth)
            if covered_methods:
                #print(f"Methods covered in {filename}: {covered_methods}")
                return filename, covered_methods, coverage_percentage

def collect_only_the_methods_that_are_called_from_fm(traces_output, focal_meth, focal_file):
    root = ET.fromstring(traces_output)
    # Find the focal method
    file_name = None
    focal_method_element = None
    for filename_element in root.findall("filename"):
        #print('** I am filename_element***')
        file_name = filename_element.get("name")
        #if filename_element.get("name") == focal_file:
        if focal_file.endswith(file_name):
            #print('** I am filename_element***')
            for method_element in filename_element.findall("method"):
                if method_element.get("name") == focal_meth:
                    focal_method_element = method_element
                    print('** focal method matched found **', focal_method_element)
                    break
            if focal_method_element:
                break

    # Extract the method body text
    focal_method_body = focal_method_element.find("method_body").text
    
    try:
        #called_methods = set(re.findall(r'\b\w+\(', focal_method_body))
        called_methods = set(re.findall(r'\b(\w+)\(', focal_method_body))
        print(f"called_methods: {called_methods}")
    except Exception as e:
        print(f"An error occurred during regex matching: {e}")

    # Create a new root element for the output XML
    new_root = ET.Element("traces")

    # Add the focal method to the new XML structure
    new_filename_element = ET.SubElement(new_root, "filename", name=file_name)
    new_focal_method_element = ET.SubElement(new_filename_element, "method", name=focal_meth)
    new_focal_method_body_element = ET.SubElement(new_focal_method_element, "method_body")
    new_focal_method_body_element.text = focal_method_body

    # Find and add the methods called by the focal method
    for method_name in called_methods:
        print("I am within called_methods ===", method_name)
        method_found = False
        for method_element in filename_element.findall("method"):
            if method_element.get("name") == method_name:
                new_method_element = ET.SubElement(new_filename_element, "method", name=method_name)
                method_body = method_element.find("method_body").text
                new_method_body_element = ET.SubElement(new_method_element, "method_body")
                new_method_body_element.text = method_body
                method_found = True
                break
        if not method_found:
            print(f"Method '{method_name}' called by '{focal_meth}' not found in file '{focal_file}'.")

    # Convert the ElementTree to a string
    new_traces_output = ET.tostring(new_root, encoding='unicode', method='xml')
    return new_traces_output

if __name__ == '__main__':
    focal_meth = sys.argv[1] # bases
    focal_file = sys.argv[2] # /home/ec2-user/change_aware_utg/test_analysis/projects/airtable-python-wrapper/pyairtable/api/api.py
    coverage_file_path = 'coverage.xml'
    if not os.path.exists(coverage_file_path):
        print(f"Error: The file '{coverage_file_path}' does not exist. So, not doing anything more.")
        sys.exit(1)  # Exit the script with a non-zero error code to indicate an error
    # Load and parse the XML file
    tree = ET.parse(coverage_file_path)
    coverage_root = tree.getroot()
    # Initialize a dictionary to store the results
    output_data = {} 
    traces = ET.Element("traces")

    for package in coverage_root.findall(".//package"):
        package_name = package.get("name")
        for cls in package.findall(".//class"):
            class_name = cls.get("name")
            filename = cls.get("filename")
            line_rate = cls.get("line-rate")
            branch_rate = cls.get("branch-rate")
            complexity = cls.get("complexity")
    
            # Find all executed lines within the class
             # Debug output
            #print(f"Processing class: {class_name} in package: {package_name} from file: {filename}")
            executed_lines = []
            for line in cls.findall(".//line"):
                line_number = int(line.get("number"))
                hits = int(line.get("hits"))
                #if hits and int(hits) > 0:  # Only consider lines that were executed
                executed_lines.append(line_number)
            # Debug output
            #print(f"Total executed lines: {len(executed_lines)} for file {filename}")
            if executed_lines:
                #print(f"Executed Lines: {', '.join(executed_lines)}")
                # Convert each line number to a string for joining
                executed_lines_str = ', '.join(map(str, executed_lines))
                #print(f"Executed Lines: {executed_lines_str}")
                # Now map these lines to methods
                methods_line_ranges = get_methods_line_ranges(filename)
                lines_outside_methods = set(executed_lines)
                with open(filename, 'r') as f:
                    lines = f.readlines()
                filename_element = ET.Element("filename", name=filename)
                has_methods = False
                for method_name, (start_line, end_line) in methods_line_ranges.items():
                    print('method_name, start_line, end_line=', method_name, start_line, end_line)
                    relevant_lines = [line for line in executed_lines if start_line <= line <= end_line]
                    # Debug output
                    #print(f"Method {method_name} has {len(relevant_lines)} relevant lines")
        
                    # Exclude method if only its definition is executed (or nothing is executed)
                    if relevant_lines and len(relevant_lines) > 1:
                        method_element = ET.SubElement(filename_element, "method", name=method_name)
                        method_body = ''.join([lines[line-1] for line in relevant_lines if line in lines_outside_methods])

                        # Append a newline before the method body text for proper indentation in the final XML
                        method_body = "\n" + method_body

                        # Create the method body element with the preserved method body text
                        method_body_element = create_element_with_text("method_body", method_body)
                        method_element.append(method_body_element)
                        has_methods = True 
  
                        # Remove each line in relevant_lines from lines_outside_methods
                        for line in relevant_lines:
                            lines_outside_methods.discard(line)  # discard is safer as it does not raise an error if the element is not found
                
                # Only add the filename element if it contains at least one method
                if has_methods:
                    traces.append(filename_element)
    # Convert the ElementTree to a string
    xml_str = ET.tostring(traces, encoding='unicode')
    # Manually prettify the XML output by adding an appropriate newline
    traces_output = xml_str.replace('><', '>\n<') 
    #print(traces_output)
    new_traces_output = collect_only_the_methods_that_are_called_from_fm(traces_output, focal_meth, focal_file)
    print(new_traces_output)
