import os
import re

def inject_sleep_before_line(file_path, line_number, method_name, descriptor, code_line):
    """
    Inserts 'Thread.sleep(100);' before the given line_number in the file,
    preserving the indentation of the target line.
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()
    print(file_path, line_number, method_name, descriptor, code_line)
    # Get indentation of the target line
    target_line = lines[line_number - 1]
    #leading_spaces = len(target_line) - len(target_line.lstrip())
    ## Prepare the sleep line with correct indentation
    ##sleep_line = ' ' * leading_spaces + 'Thread.sleep(5000);\n'
    #indent = ' ' * leading_spaces
    indent_match = re.match(r'^(\s*)', target_line)
    indent = indent_match.group(1) if indent_match else ''

    # Prepare the sleep lines with correct indentation and try-catch
    sleep_lines = [
        f"{indent}try {{\n",
        f"{indent}    Thread.sleep(5000);\n",
        f"{indent}}} catch (InterruptedException e) {{\n",
        f"{indent}    Thread.currentThread().interrupt();\n",
        f"{indent}}}\n"
    ]

    # Insert the sleep lines before the target line
    for i, sleep_line in enumerate(sleep_lines):
        lines.insert(line_number - 1 + i, sleep_line)
    # Insert the sleep line before the target line
    #lines.insert(line_number - 1, sleep_line)

    # Write back to file
    with open(file_path, 'w') as file:
        file.writelines(lines)

    print(f"Injected Thread.sleep(5000); before line {line_number} in {file_path}")
