import os
import re

def inject_sleep_before_line(file_path, line_number):
    """
    Inserts 'Thread.sleep(100);' before the given line_number in the file,
    preserving the indentation of the target line.
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Get indentation of the target line
    target_line = lines[line_number - 1]
    leading_spaces = len(target_line) - len(target_line.lstrip())

    # Prepare the sleep line with correct indentation
    sleep_line = ' ' * leading_spaces + 'Thread.sleep(5000);\n'

    # Insert the sleep line before the target line
    lines.insert(line_number - 1, sleep_line)

    # Write back to file
    with open(file_path, 'w') as file:
        file.writelines(lines)

    print(f"Injected Thread.sleep(5000); before line {line_number} in {file_path}")

#def hack_into_sut(curated_change, fm_file_path, fm_name, fm_lines):
#    script_path = os.path.abspath(__file__)
#    # Get just the directory containing this script
#    script_dir = os.path.dirname(script_path)
#    #print("Script is located in:", script_dir)
#    # Read the file contents
#    with open(fm_file_path, 'r') as file:
#        lines = file.readlines()
#    # Extract start and end lines
#    fm_lines = fm_lines.strip('[]')
#    start_line, end_line = map(int, fm_lines.split('-'))
#
#    # Determine the indentation of the first line of the focal method
#    first_line = lines[start_line - 1]
#    leading_spaces = len(first_line) - len(first_line.lstrip())
#    del lines[start_line - 1:end_line]
#
#    new_code_lines = curated_change.strip().split('\n')
#    indented_new_code_lines = [' ' * leading_spaces + line for line in new_code_lines]
#    indented_new_code_lines = ['\n'] + indented_new_code_lines + ['\n']
#    # Insert the new code at the position of the deleted lines
#    for line in reversed(indented_new_code_lines):
#        lines.insert(start_line - 1, line + '\n')
#    # Calculate the new start and end lines for the inserted code
#    new_start_line = start_line
#    new_end_line = start_line + len(new_code_lines) - 1
#    # Write the modified content back to the file
#    with open(fm_file_path, 'w') as file:
#        file.writelines(lines)
#    print(new_start_line,",  end=" ,new_end_line)
#    line_range = "["+str(new_start_line)+"-"+str(new_end_line)+"]"
#    print(line_range)
#    return line_range
#