import configparser
import os

def update_tox_ini():
    # Path to your tox.ini file
    tox_ini_path = 'tox.ini'
    
    # Read the contents of the file
    with open(tox_ini_path, 'r') as file:
        lines = file.readlines()
    
    # Variables to track if we are in the correct section
    in_testenv = False
    added_deps = False
    added_commands = False
    new_lines = [] 

    # Process each line
    for i in range(len(lines)):
        if lines[i].strip() == '[testenv]':
            in_testenv = True
            append_index = len(new_lines)


        if in_testenv and lines[i].strip().startswith('[') and lines[i].strip() != '[testenv]':
            in_testenv = False
            if not added_deps:
                #print('not found deps ***')
                new_lines.insert(append_index + 1, 'deps =\n    pytest-cov\n    pytest-json-report\n')
                added_deps = True
            if not added_commands:
                #print('FROM COMMAND INSERT**')
                new_lines.insert(append_index + 1, 'commands =\n    python -m pytest --cov --cov-report=xml --json-report-file=testreport/report.json {posargs:-m \'not integration\'}\n')
                added_commands = True
        new_lines.append(lines[i])

        if in_testenv:
            if (lines[i].strip().startswith('deps =') or  lines[i].strip().startswith('deps=')) and not added_deps:
                new_lines.append('    pytest-cov\n    pytest-json-report\n')
                added_deps = True
                #print('found deps ***')
            
            if (lines[i].strip().startswith('commands =') or lines[i].strip().startswith('commands=')) and not added_commands:
                #print('I am in the commands***', lines[i], ',i=',i)
                #print(new_lines)
                new_lines.append('   python -m pytest --cov --cov-report=xml --json-report-file=testreport/report.json {posargs:-m \'not integration\'}\n')
                #print(new_lines)
                added_commands = True
       
    # In case the file ends without another section starting after [testenv]
    if in_testenv:
        if not added_deps:
            new_lines.append('deps =\n    pytest-cov\n    pytest-json-report\n')
        if not added_commands:
            new_lines.append('commands =\n    python -m pytest --cov --cov-report=xml --json-report-file=testreport/report.json {posargs:-m \'not integration\'}\n')

    # Write the changes back to the file
    with open(tox_ini_path, 'w') as file:
        file.writelines(new_lines)

    print("tox.ini updated successfully.")

if __name__ == '__main__':
    update_tox_ini()

