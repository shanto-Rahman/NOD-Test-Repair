import sys
from modify_java_file import inject_sleep_before_line  # assuming injector.py is in the same directory
from generating_reproducing_script import find_class_file


if len(sys.argv) != 8:
    print("Usage: python run_injection.py <file_path> <line_number> <method_name> <descriptor> <code_line>")
    sys.exit(1)

class_name = sys.argv[1]
line_number = int(sys.argv[2])
method_name = sys.argv[3]
descriptor = sys.argv[4]
code_line = sys.argv[5]
slug = sys.argv[6]
module = sys.argv[7]

class_path = find_class_file(class_name, slug, module)
#print("class_path=", class_path)
inject_sleep_before_line(class_path, line_number, method_name, descriptor, code_line)

