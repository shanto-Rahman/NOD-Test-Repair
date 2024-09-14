import ast
import os
import re

class AssertVisitor(ast.NodeVisitor):
    def __init__(self):
        #print('contain_assert False')
        self.contains_assert = False

    def visit_Assert(self, node):
        #print("Direct assert statement found.")
        self.contains_assert = True

    def visit_Call(self, node):
        #print('I am from self AssertVisitor')
        # This will #print the structure and attributes of every call node
        if isinstance(node.func, ast.Attribute):
            # Print the full attribute access chain
            ##print(f"Visiting a method call: {ast.dump(node.func)}")
            method_name = node.func.attr
            # Navigate to check if this is a method called on 'self'
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'self':
                ##print(f"Method call on self: {method_name}")
                if method_name.startswith('assert'):
                    #print(f"Assertion method detected: {method_name}")
                    self.contains_assert = True
        # Ensure we continue to check all parts of the AST
        self.generic_visit(node)

def check_valid_test(node):
    ##print_ast(node)
    if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
        #debug_#print_decorators(node)
            
        if not (re.match(r'^test_', node.name) or re.search(r'_test$', node.name)):
            #print('method name not starts with the test_:',node.name)
            return False
        if any(is_fixture_decorator(decorator) for decorator in node.decorator_list):
            #print('I am from fixture branch')
        #    continue  # Skip this method if it has a pytest.fixture decorator
            return False
        ##print("HI, I am before AssertVisitor..")
        ##print(ast.dump(node, indent=4))
        assert_visitor = AssertVisitor()
        assert_visitor.visit(node)
        ##print('now going to check if assertion exists or not====')
        if assert_visitor.contains_assert:
            #print('Assert found....')
            return True
    return False

#def debug_#print_decorators(function_node):
#    for decorator in function_node.decorator_list:
#        if isinstance(decorator, ast.Call):
#            func = decorator.func
#            full_name = get_full_name(func) if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else 'Unknown'
#            #print('Decorator found:', full_name)
#        else:
#            #print('Non-call decorator found:', ast.dump(decorator))

def find_test_directory(base_path):
    # Check for 'tests' directory first
    tests_dir = os.path.join(base_path, 'tests')
    if os.path.exists(tests_dir):
        return tests_dir

    # If not found, check for 'test' directory
    test_dir = os.path.join(base_path, 'test')
    if os.path.exists(test_dir):
        return test_dir
    return None

def is_test_file(file):
    if file.endswith('.py') and (file.startswith('test_') or '_test' in file):
        return True
    else:
        return False

class AssertVisitor(ast.NodeVisitor):
    def __init__(self):
        self.contains_assert = False

    def visit_Assert(self, node):
        self.contains_assert = True

def is_fixture_decorator(decorator):
    if isinstance(decorator, ast.Call):
        func = decorator.func
        full_name = get_full_name(func)
        return full_name == 'pytest.fixture'
    elif isinstance(decorator, ast.Attribute):
        # Handle cases where the decorator is used as an attribute
        full_name = get_full_name(decorator)
        return full_name == 'pytest.fixture'
    return False

def get_full_name(node):
    """Recursively retrieves the full dotted name of an attribute or name node."""
    parts = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    parts.reverse()
    return '.'.join(parts)

def debug_print_decorators(function_node):
    #print(f"--- Inspecting function: {function_node.name} ---")
    for decorator in function_node.decorator_list:
        full_name = get_full_name(decorator)
        #print(f"Decorator found: {full_name}, is_fixture: {is_fixture_decorator(decorator)}")

