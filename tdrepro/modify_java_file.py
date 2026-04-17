import os
import re
from pathlib import Path

def is_method_at_line_and_code_match(file_path, line_number, method_name, code_line):
    """
    Checks whether the given code_line exists exactly at line_number
    and that line_number is inside the method body of method_name.
    """
    with open(file_path, 'r') as f:
        lines = f.readlines()

    if len(lines) < line_number:
        print("❌ Line number out of range.")
        return False

    # Check if the line content matches
    actual_line = lines[line_number - 1].strip()
    print( actual_line, " ==== ",  code_line.strip())
    #if actual_line != code_line.strip():
    #    print(f"❌ Line {line_number} does not match the expected code_line.")
    #    return False
    return True
def inject_sleep_before_line(candidates, line_number, method_name, descriptor, code_line):
    """
    Inserts 'Thread.sleep(100);' before the given line_number in the file,
    preserving the indentation of the target line.
    """
    #print("****",file_path, line_number, method_name, descriptor, code_line)
    for file_path in candidates:
        print("file_path=", file_path)
        if not Path(file_path).exists():
            print("NO FOUND ", file_path)
            continue

        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Sanity check
        if len(lines) < line_number:
            continue
 
        method_found_correctly = is_method_at_line_and_code_match(file_path, line_number, method_name, code_line) 
        if not method_found_correctly:
            continue
        else:
            print("*****method_found_correctly=", method_found_correctly)

            # Get indentation of the target line
            target_line = lines[line_number - 1]
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
            break

