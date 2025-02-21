import tree_sitter
from tree_sitter import Language, Parser
import re

# Load the Python grammar for Tree-sitter
#PY_LANGUAGE = Language("tree-sitter-python.so", "python")
from tree_sitter_languages import get_language

# Get the prebuilt Python language parser
PY_LANGUAGE = get_language("python")

def extract_test_function(file_path, test_name):
    """Extracts the test function's code, including decorators, and handles class-based test methods."""
    parser = Parser()
    parser.set_language(PY_LANGUAGE)

    #Remove parameterized values (e.g., [float32_cpu-fixed_assets-max_weight=0.5])
    test_name_clean = re.sub(r"\[.*\]", "", test_name)

    print(f"Searching for test function: {test_name_clean}")

    # Read the test file
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()
        lines = code.splitlines()

    # Parse with Tree-Sitter
    tree = parser.parse(bytes(code, "utf8"))
    root_node = tree.root_node

    # Split class and function names if the test is inside a class
    if "::" in test_name_clean:
        class_name, function_name = test_name_clean.split("::", 1)
    else:
        class_name, function_name = None, test_name_clean

    def find_function(node, current_class=None):
        """Recursively search for function inside a class or globally."""
        for child in node.children:
            if child.type == "class_definition":
                class_node_name = child.child_by_field_name("name")
                if class_node_name:
                    class_node_name = class_node_name.text.decode("utf-8")
                    print(f"Found class: {class_node_name}")

                #Enter class only if it's the correct one
                if class_name and class_node_name == class_name:
                    print(f"Entering class '{class_node_name}' body")
                    class_body = child.child_by_field_name("body")
                    if class_body:
                        return find_function(class_body, current_class=class_node_name)

            elif child.type in ("function_definition", "decorated_definition"):
                print(f"Found potential function node: {child.type}")

                # Extract function name
                func_name = child.child_by_field_name("name")
                if func_name:
                    func_name = func_name.text.decode("utf-8")
                    print(f"Found function: {func_name}")

                #Ensure it's the correct function and the correct class
                if func_name == function_name and (current_class == class_name or class_name is None):
                    start_line = child.start_point[0] + 1
                    end_line = child.end_point[0] + 1

                    #Collect decorators (always check previous siblings)
                    decorators = []
                    prev_node = child.prev_named_sibling  # Check previous sibling node
                    while prev_node and prev_node.type == "decorator":
                        decorator_line = lines[prev_node.start_point[0]]
                        decorators.insert(0, decorator_line)  # Insert at the beginning to keep order
                        prev_node = prev_node.prev_named_sibling  # Move to the previous node

                    #Adjust start_line to include decorators
                    if decorators:
                        start_line = prev_node.start_point[0] + 1 if prev_node else child.start_point[0] + 1

                    #Extract function body (including decorators)
                    func_code_lines = lines[start_line-1:end_line]
                    func_code = "\n".join(decorators + func_code_lines)

                    if current_class:
                        print(f"Found method '{function_name}' inside class '{current_class}' at lines {start_line}-{end_line}")
                    else:
                        print(f"Found function '{function_name}' at lines {start_line}-{end_line}")

                    return func_code, start_line, end_line

            # Recursively search inside blocks (e.g., class or module)
            if child.type in ("module", "class_definition", "decorated_definition", "block"):
                result = find_function(child, current_class=current_class)
                if result:
                    return result

        return None

    return find_function(root_node) or (None, None, None)

