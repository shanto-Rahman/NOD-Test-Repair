import os
import re

def hack_into_sut(curated_change, fm_file_path, fm_name, fm_lines):
    # Read the file contents
    with open(fm_file_path, 'r') as file:
        lines = file.readlines()

    # Extract start and end lines
    fm_lines = fm_lines.strip('[]')
    start_line, end_line = map(int, fm_lines.split('-'))

    # Determine the indentation of the first line of the focal method
    first_line = lines[start_line - 1]
    leading_spaces = len(first_line) - len(first_line.lstrip())

    # Comment out the specified lines
    #for i in range(start_line - 1, end_line):
    #    lines[i] = '# ' + lines[i]
    del lines[start_line - 1:end_line]

    new_code_lines = curated_change.strip().split('\n')
    indented_new_code_lines = [' ' * leading_spaces + line for line in new_code_lines]
    indented_new_code_lines = ['\n'] + indented_new_code_lines + ['\n']

    # Insert the new code at the position of the deleted lines
    for line in reversed(indented_new_code_lines):
        lines.insert(start_line - 1, line + '\n')

    # Calculate the new start and end lines for the inserted code
    new_start_line = start_line
    new_end_line = start_line + len(new_code_lines) - 1

    # Write the modified content back to the file
    with open(fm_file_path, 'w') as file:
        file.writelines(lines)
    print(new_start_line,",  end=" ,new_end_line)
    line_range = "["+str(new_start_line)+"-"+str(new_end_line)+"]"
    print(line_range)
    return line_range

def hack_into_test_for_cc(test_code, test_file_path, test_name, test_lines):
    # Read the file contents
    with open(test_file_path, 'r') as file:
        lines = file.readlines()

    # Extract start and end lines
    test_lines = test_lines.strip('[]')
    start_line, end_line = map(int, test_lines.split('-'))

    # Ensure start_line and end_line are within the bounds of the file
    total_lines = len(lines)

    if end_line > total_lines:
        print(f"Warning: end_line={end_line} exceeds the total number of lines in the file ({total_lines}). Adjusting end_line to {total_lines}.")
        end_line = total_lines
    
    # Determine the indentation of the first line of the focal method
    first_line = lines[start_line - 1]
    leading_spaces = len(first_line) - len(first_line.lstrip())
    print(test_file_path)
    # Comment out the specified lines
    #for i in range(start_line - 1, end_line):
    #    lines[i] = '# ' + lines[i]

    # Add the new code at the end of the commented block
    new_code_lines = test_code.strip().split('\n')
    indented_new_code_lines = [' ' * leading_spaces + line for line in new_code_lines]
    lines.insert(end_line, '\n' + '\n'.join(indented_new_code_lines) + '\n')
    #lines.insert(end_line, '\n' + '\n'.join(new_code_lines) + '\n')

    # Write the modified content back to the file
    with open(test_file_path, 'w') as file:
        file.writelines(lines)


def hack_into_test(test_code, test_file_path, test_name, test_lines):
    # Read the file contents
    with open(test_file_path, 'r') as file:
        lines = file.readlines()

    # Extract start and end lines
    test_lines = test_lines.strip('[]')
    start_line, end_line = map(int, test_lines.split('-'))

    # Ensure start_line and end_line are within the bounds of the file
    total_lines = len(lines)

    if end_line > total_lines:
        print(f"Warning: end_line={end_line} exceeds the total number of lines in the file ({total_lines}). Adjusting end_line to {total_lines}.")
        end_line = total_lines
    
    # Determine the indentation of the first line of the focal method
    first_line = lines[start_line - 1]
    leading_spaces = len(first_line) - len(first_line.lstrip())
    print(test_file_path)
    # Comment out the specified lines
    #for i in range(start_line - 1, end_line):
    #    lines[i] = '# ' + lines[i]
    # Delete the specified lines instead of commenting them out
    del lines[start_line - 1:end_line]

    # Add the new code at the end of the commented block
    new_code_lines = test_code.strip().split('\n')
    indented_new_code_lines = [' ' * leading_spaces + line for line in new_code_lines]
    
    insertion_point = start_line - 1 
    #lines.insert(insertion_point, '\n' + '\n'.join(indented_new_code_lines) + '\n')
    lines[insertion_point:insertion_point] = ['\n' + '\n'.join(indented_new_code_lines) + '\n']
    
    # Calculate the line numbers for the newly added test
    new_code_start_line = insertion_point + 1  # Line where the new code starts
    new_code_end_line = new_code_start_line + len(new_code_lines) -1  # Line where the new code ends
    
    # Write the modified content back to the file
    with open(test_file_path, 'w') as file:
        file.writelines(lines)

    return new_code_start_line, new_code_end_line
