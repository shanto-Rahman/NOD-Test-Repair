import sys
from modify_java_file import inject_sleep_before_line  # assuming injector.py is in the same directory
from utils import find_class_file
from pathlib import Path

def prepare_candidates(class_path, class_name):
    print("*** class_path=", class_path)
    #class_path = Path(class_path[0]) if isinstance(class_path, list) else Path(class_path)
    #class_path = Path(class_path[0])
    if isinstance(class_path, list):
        class_path = Path(class_path[0])
    else:
        class_path = Path(class_path)

    if class_path.is_dir():
        candidates = list(class_path.rglob(f"{class_name}.java"))
    elif class_path.is_file():
        candidates = [class_path]
    else:
        raise FileNotFoundError(f"{class_path} is neither file nor directory")
    return candidates


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

# Assume find_class_file returns a directory or a list of files
class_path_list = find_class_file(class_name, slug, module)
#candidates = prepare_candidates(class_path_dir, class_name)
inject_sleep_before_line(class_path_list, line_number, method_name, descriptor, code_line)
