import os
import sys
import ast
from collections import defaultdict

class BranchCounter(ast.NodeVisitor):
    def __init__(self):
        self.branches = 0
        self.branch_types = []

    def visit_If(self, node):
        self.branches += 1
        self.branch_types.append(self.get_branch_type(node.test))
        self.generic_visit(node)

    def visit_For(self, node):
        self.branches += 1
        self.branch_types.append('for')
        self.generic_visit(node)

    def visit_While(self, node):
        self.branches += 1
        self.branch_types.append(self.get_branch_type(node.test))
        self.generic_visit(node)

    def visit_With(self, node):
        self.branches += 1
        self.branch_types.append('with')
        self.generic_visit(node)

    def visit_Try(self, node):
        self.branches += 1
        self.branch_types.append('try')
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.branches += 1
        self.branch_types.append('except')
        self.generic_visit(node)


    def get_branch_type(self, node):
        if isinstance(node, ast.Compare):
            return 'comparison'
        elif isinstance(node, ast.BoolOp):
            return 'boolean'
        elif isinstance(node, ast.BinOp):
            return 'binary'
        elif isinstance(node, ast.Call):
            return 'function call'
        elif isinstance(node, ast.Attribute):
            return 'attribute'
        elif isinstance(node, ast.Name):
            return 'variable'
        elif isinstance(node, ast.UnaryOp):
            return 'unary'
        return 'unknown'

    def count_branches(self, code):
        tree = ast.parse(code)
        self.visit(tree)
        if not self.branch_types:
            print('*** BRANCH type not found********')
            self.branch_types.append('None')
        return self.branches, self.branch_types
                             
                             
'''class FunctionAnalyzer(ast.NodeVisitor):
    def __init__(self, file_path):
        self.file_path = file_path
        self.current_function = None
        self.dependencies =  defaultdict(lambda: {
            'internal_calls' : set(),
            'external_calls' : set(),
            'api_calls': set (),
            'arg_count': 0,  
            'arg_types': [], 
            'branch_count':  0,
            'branch_types': []
        })                   
                             
    def visit_FunctionDef(self, node):
        self.current_function = node.name
        self.dependencies[self.current_function]['arg_count'] = len(node.args.args)
        self.dependencies[self.current_function]['arg_types'] = [
            self.get_arg_type(arg) for arg in node.args.args
        ]
        self.dependencies[self.current_function]['branch_count'], self.dependencies[self.current_function]['branch_types'] = self.count_branches(node)
        self.generic_visit(node)
        self.current_function = None
    
    def get_arg_type(self, arg):
        if arg.annotation:
            return ast.dump(arg.annotation)
        return 'Unknown'


    def count_branches(self, node):
        branch_counter = BranchCounter()
        branch_counter.visit(node)
        return branch_counter.branches, branch_counter.branch_types

    def visit_Call(self, node):
        if self.current_function is None:
            self.generic_visit(node)
            return

        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            # Assuming internal call within the same file
            if func_name in self.internal_modules:
                self.dependencies[self.current_function]['internal_calls'].add(func_name)
            else:
                self.dependencies[self.current_function]['api_calls'].add(func_name)
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            value = node.func.value
            if isinstance(value, ast.Name):
                module_name = value.id
                if self.is_external_call(module_name):
                    self.dependencies[self.current_function]['api_calls'].add(f"{module_name}.{func_name}")
                else:
                    self.dependencies[self.current_function]['internal_calls'].add(func_name)
            elif isinstance(value, ast.Attribute):
                module_name = self.get_full_name(value)
                if self.is_external_call(module_name):
                    self.dependencies[self.current_function]['api_calls'].add(f"{module_name}.{func_name}")
                else:
                    self.dependencies[self.current_function]['internal_calls'].add(func_name)
        else:
            self.dependencies[self.current_function]['external_calls'].add(ast.dump(node.func))
        self.generic_visit(node)

    def get_full_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self.get_full_name(node.value) + '.' + node.attr
        return ''

    def is_external_call(self, module_name):
        return module_name not in self.internal_modules

    def analyze(self):
        with open(self.file_path, 'r') as file:
            tree = ast.parse(file.read(), filename=self.file_path)
        self.visit(tree)
        return self.dependencies'''

class FunctionAnalyzer(ast.NodeVisitor):
    def __init__(self, file_path):
        self.file_path = file_path
        self.function_definitions = set()
        self.dependencies = defaultdict(lambda: {
            'internal_calls': set(),
            'external_calls': set(),
            #'calls': set(),
            'arg_count': 0,
            'arg_types': [],
            'branch_count': 0,
            'branch_types': []
        })
        self.current_function = None

    def visit_FunctionDef(self, node):
        self.current_function = node.name
        branch_counter = BranchCounter()
        branch_counter.visit(node)
        # Ensure that the function's dictionary is properly initialized here
        self.dependencies[node.name] = {
            'arg_count': len(node.args.args),
            'arg_types': [ast.dump(arg.annotation) if arg.annotation else 'Unknown' for arg in node.args.args],
            'branch_count': branch_counter.branches,
            'branch_types': branch_counter.branch_types,
            #'calls': set(),
            'internal_calls': set(),
            'external_calls': set()
        }
        self.generic_visit(node)

    def visit_Call(self, node):
        if self.current_function:
            func_name = (node.func.id if isinstance(node.func, ast.Name) else
                         node.func.attr if isinstance(node.func, ast.Attribute) else
                         'Unknown function call')
            # Safely add calls to the current function's dependencies
            #self.dependencies[self.current_function]['calls'].add(func_name)
            # Determine if the function call is internal or external
            if func_name in self.function_definitions:
                self.dependencies[self.current_function]['internal_calls'].add(func_name)
            else:
                self.dependencies[self.current_function]['external_calls'].add(func_name)
        self.generic_visit(node)

    def analyze(self):
        with open(self.file_path, 'r') as file:
            code = file.read()
        tree = ast.parse(code)
        self.visit(tree)
        return self.dependencies


def analyze_specific_function(file_path, function_name):
    analyzer = FunctionAnalyzer(file_path)
    dependencies = analyzer.analyze()
    function_details = dependencies.get(function_name, None)
    if function_details:
        return {'function_name': function_name, 'status': 'found', 'details': function_details}
    else:
        # Similarly, ensure this is also a dictionary
        return {'function_name': function_name, 'status': 'not_found', 'message': f"Function '{function_name}' not found in {file_path}"}
    #if function_details:
    #    #print(f"Details for function '{function_name}':", function_details)
    #    return {'status': 'found', 'details': function_details}   
    #else:
    #    #print(f"Function '{function_name}' not found in {file_path}.")
    #    return {'status': 'not_found', 'message': f"Function '{function_name}' not found in {file_path}."}


#def analyze_directory(directory):
#    all_dependencies = {}
#    current_directory = os.getcwd()
#    #print(current_directory)
#    #print('directory:', directory)
#    #for root, _, files in os.walk(directory):
#    for file in os.listdir(directory):
#        if file.endswith('.py'):
#            file_path = os.path.join(directory, file)
#            #print('*****filename=', file, ", directory=",directory)
#            #file_path = os.path.join(root, file)
#            analyzer = DependencyAnalyzer(file_path, directory)
#            analyzer.analyze()
#            all_dependencies[file_path] = analyzer.dependencies
#    return all_dependencies

