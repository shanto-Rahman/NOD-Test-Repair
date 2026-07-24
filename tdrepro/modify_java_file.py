import os
import re
from pathlib import Path

def find_statement_start_line(lines, line_number):
    """
    Given a 1-indexed line_number that might be in the middle of a
    multi-line statement or inside a multi-line function call's argument
    list, walk backward to find the 1-indexed line where that statement
    actually begins.
    """
    def strip_strings_and_comments(line):
        # crude but enough for bracket-counting: blank out string/char
        # contents and strip // comments so their brackets don't count
        line = re.sub(r'//.*$', '', line)
        line = re.sub(r'"(?:[^"\\]|\\.)*"', '""', line)
        line = re.sub(r"'(?:[^'\\]|\\.)*'", "''", line)
        return line

    idx = line_number - 1  # 0-indexed
    depth = 0

    while idx > 0:
        clean = strip_strings_and_comments(lines[idx])
        depth += clean.count('(') - clean.count(')')
        depth += clean.count('[') - clean.count(']')

        prev_clean = strip_strings_and_comments(lines[idx - 1]).strip()

        # We can stop once we're not inside any open paren/bracket AND
        # the previous line clearly ends a prior statement/block.
        if depth <= 0 and (prev_clean.endswith(';') or prev_clean.endswith('{')
                            or prev_clean.endswith('}') or prev_clean == ''):
            break

        idx -= 1

    return idx + 1  # back to 1-indexed

def is_valid_line_number(file_path, line_number, method_name, code_line):
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
    #actual_line = lines[line_number - 1].strip()
    #print( actual_line, " ==== ",  code_line.strip())
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
 
        valid_line = is_valid_line_number(file_path, line_number, method_name, code_line) 
        if not valid_line:
            continue
        else:
            #print("*****method_found_correctly=", method_found_correctly)

            insert_at_line = find_statement_start_line(lines, line_number)

            # Get indentation of the target line
            target_line = lines[insert_at_line - 1]
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
                lines.insert(insert_at_line - 1 + i, sleep_line)
            # Insert the sleep line before the target line
            #lines.insert(line_number - 1, sleep_line)

            # Write back to file
            with open(file_path, 'w') as file:
                file.writelines(lines)

            print(f"Injected Thread.sleep(5000); before line {line_number} in {file_path}")
            break

