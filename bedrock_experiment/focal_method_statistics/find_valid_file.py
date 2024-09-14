import re
import sys

def process_class_name(suggested_classname):
    # Split the string by dots
    parts = suggested_classname.split('.')
    
    # Check if there are multiple dots
    if len(parts) > 1:
        last_part = parts[-1]
        
        # Check if the last part starts with a capital letter
        if re.match(r'^[A-Z]', last_part):
            # If it starts with a capital letter, remove the last part
            processed_classname = '.'.join(parts[:-1])
        else:
            processed_classname = suggested_classname
    else:
        processed_classname = suggested_classname
    
    return processed_classname

if __name__ == "__main__":
    suggested_classname = sys.argv[1]
    file_name = process_class_name(suggested_classname)
    print(file_name)

