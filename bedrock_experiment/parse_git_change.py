import subprocess
import difflib
import os
import re

#def get_file_content_at_commit(commit, file_path, project_dir):
#    try:
#        result = subprocess.run(
#            ['git', 'show', f'{commit}:{file_path}'], 
#            cwd=project_dir, 
#            check=True, 
#            stdout=subprocess.PIPE, 
#            stderr=subprocess.PIPE, 
#            text=True
#        )
#        return result.stdout.splitlines()
#    except subprocess.CalledProcessError as e:
#        print(f"Error getting file content at {commit}: {e}")
#        return None
#
#def get_working_file_content(file_path, project_dir):
#    full_path = os.path.join(project_dir, file_path)
#    print(f"Trying to read file at: {full_path}")  # Debugging line
#    try:
#        with open(full_path, 'r') as file:
#            return file.readlines()
#    except FileNotFoundError:
#        print(f"File {full_path} not found in working directory.")
#        return None

def get_file_content_at_commit(commit, file_path, project_dir):
    try:
        result = subprocess.run(
            ['git', 'show', f'{commit}:{file_path}'], 
            cwd=project_dir, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        return result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        print(f"Error getting file content at {commit}: {e}")
        return None

def get_working_file_content(file_path, project_dir):
    full_path = os.path.join(project_dir, file_path)
    print(f"Trying to read file at: {full_path}")  # Debugging line
    try:
        with open(full_path, 'r') as file:
            return file.readlines()
    except FileNotFoundError:
        print(f"File {full_path} not found in working directory.")
        return None

def normalize_whitespace(lines):
    return [' '.join(line.split()) for line in lines]

#def get_diff(file_path, project_dir):

def get_relative_path(project_name, full_path):
    # Find the index where the project name starts in the full path
    start_index = full_path.find(project_name)
    if start_index == -1:
        raise ValueError(f"Project name '{project_name}' not found in the full path '{full_path}'")
    
    # Extract the relative path
    relative_path = full_path[start_index + len(project_name) + 1:]  # +1 to skip the trailing '/'
    return relative_path



#import difflib
#import re
#
#def collect_git_diff(full_file_path, project_dir, proj_name):
#    file_path = get_relative_path(proj_name, full_file_path)
#    print('file_path=', file_path)
#    print('project_dir=', project_dir)
#    
#    # Get file content at HEAD
#    head_content = get_file_content_at_commit('HEAD', file_path, project_dir)
#    
#    # Get file content in working directory
#    working_content = get_working_file_content(file_path, project_dir)
#    
#    if head_content is None or working_content is None:
#        return None, None, None
#    
#    # Normalize whitespace
#    head_content_normalized = normalize_whitespace(head_content)
#    working_content_normalized = normalize_whitespace(working_content)
#    
#    # Generate unified diff with normalized content
#    diff = difflib.unified_diff(
#        head_content_normalized,
#        working_content_normalized, 
#        fromfile=f'{file_path} (HEAD)', 
#        tofile=f'{file_path} (working directory)',
#        lineterm='',
#        n=1  # Number of context lines
#    )
#    # Convert the diff generator to a list so it can be iterated multiple times
#    diff_lines = list(diff)
#
#    # Now join the diff lines to create the final diff result
#    diff_result = '\n'.join(diff_lines)
#
#    # Prepare to capture changed line numbers and generate the diff with line numbers
#    changed_line_numbers = []
#    diff_with_line_numbers = []  # List to store diff lines with line numbers
#
#    # Regex to capture changed line numbers from diff header
#    line_number_pattern = re.compile(r'^@@ -\d+,\d+ \+(\d+),(\d+) @@')
#
#    # Read the working file to check for empty/commented lines
#    with open(full_file_path, 'r') as file:
#        working_lines = file.readlines()
#
#    in_multiline_comment = False
#    current_line_number = None
#
#    for line in diff_lines:
#        match = line_number_pattern.match(line)
#        if match:
#            start_line = int(match.group(1))
#            num_lines = int(match.group(2))
#            current_line_number = start_line
#        elif line.startswith('+') and not line.startswith('+++'):
#            # This line was added, so add its line number
#            if current_line_number and current_line_number <= len(working_lines):
#                stripped_line = working_lines[current_line_number - 1].strip()
#               
#                # Check for multi-line string start/end
#                if '"""' in stripped_line or "'''" in stripped_line:
#                    in_multiline_comment = not in_multiline_comment
#                    continue
#
#                # Exclude non-executable lines
#                if (not in_multiline_comment and stripped_line and
#                    not stripped_line.startswith("#") and
#                    not stripped_line.startswith("def ") and
#                    stripped_line != "else:"):
#                    changed_line_numbers.append(current_line_number)
#
#                # Append to diff_with_line_numbers as well
#                diff_with_line_numbers.append(f'{current_line_number}: {stripped_line}')
#                current_line_number += 1
#
#        elif line.startswith('-') or line.startswith(' '):
#            # Do not increment line number for removed or context lines
#            continue
#        else:
#            if current_line_number:
#                current_line_number += 1
#
#    # Return all results
#    print(','.join(map(str, changed_line_numbers)))
#    print('\n'.join(diff_with_line_numbers))
#    exit()
#    return  diff_result, ','.join(map(str, changed_line_numbers)), '\n'.join(diff_with_line_numbers)


def collect_git_diff(full_file_path, project_dir, proj_name):
    file_path = get_relative_path(proj_name, full_file_path)
    print('file_path=', file_path)
    print('project_dir=', project_dir)
    # Get file content at HEAD
    head_content = get_file_content_at_commit('HEAD', file_path, project_dir)
    # Get file content in working directory
    working_content = get_working_file_content(file_path, project_dir)
    if head_content is None or working_content is None:
        return None 

    # Normalize whitespace
    head_content_normalized = normalize_whitespace(head_content)
    working_content_normalized = normalize_whitespace(working_content)
    # Generate unified diff with normalized content
    diff = difflib.unified_diff(
        head_content_normalized, 
        working_content_normalized, 
        fromfile=f'{file_path} (HEAD)', 
        tofile=f'{file_path} (working directory)',
        lineterm='',
        n=1  # Number of context lines
    )

    # Convert diff generator to a list so it can be used multiple times
    #diff_lines = list(diff)
    diff_result = '\n'.join(diff)

    diff_lines = list(difflib.unified_diff(
            head_content_normalized,
            working_content_normalized,
            lineterm='',
            n=1
        ))  # Convert the diff generator to a list
    
    changed_line_numbers = []
    diff_with_line_numbers = []  # List to store diff lines with line numbers
    
    # Regex to capture changed line numbers from diff header
    line_number_pattern = re.compile(r'^@@ -\d+,\d+ \+(\d+),(\d+) @@')
    
    # Read the working file to check for empty/commented lines
    with open(full_file_path, 'r') as file:
        working_lines = file.readlines()
    
    current_line_number = None
    for line in diff_lines:
        match = line_number_pattern.match(line)
        if match:
            start_line = int(match.group(1))
            num_lines = int(match.group(2))
            current_line_number = start_line
    
        elif line.startswith('+') and not line.startswith('+++'):
            # This line was added, so add its line number
            if current_line_number and current_line_number <= len(working_lines):
                stripped_line = working_lines[current_line_number - 1].strip()

                # Check for multi-line string start/end
                if stripped_line.startswith('"""') or stripped_line.startswith("'''"):
                    current_line_number += 1
                    continue
                
                # Skip non-executable lines
                if (stripped_line and 
                    not stripped_line.startswith("#") and  # Ignore comments
                    not stripped_line.startswith("def ") and  # Ignore function definitions
                    stripped_line != "else:" and  # Ignore else branch
                    not stripped_line == "" and
                    not stripped_line.startswith("while")):
                
                    # Record the line number and append the line with line number to the diff_with_line_numbers
                    changed_line_numbers.append(current_line_number)
                    diff_with_line_numbers.append(f'{current_line_number}: {stripped_line}')
                current_line_number += 1
    
        elif line.startswith('-') or line.startswith(' '):
            continue
        else:
            if current_line_number:
                current_line_number += 1



    #print('diff_result=', diff_result)
    print("Final changed_line_numbers:", ','.join(map(str, changed_line_numbers)))
    #print("diff_with_line_numbers=", '\n'.join(diff_with_line_numbers))
    #exit()
    return  diff_result, ','.join(map(str, changed_line_numbers)) , '\n'.join(diff_with_line_numbers)
