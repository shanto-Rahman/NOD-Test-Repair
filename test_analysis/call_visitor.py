import ast

class CallVisitor(ast.NodeVisitor):
    def __init__(self, imports):
        self.calls = []
        self.argument_counts = []
        self.class_names = []
        self.imports = imports
        self.variable_types = {}  # Store variable types for better resolution
        self.fixture_returns = {}  # Track return values from fixtures

    def visit_Assign(self, node):
        # Handle assignments to track variable types based on class instantiation
        if isinstance(node.value, ast.Call):
            class_name = self.resolve_call_to_class_name(node.value)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.variable_types[target.id] = class_name
        self.generic_visit(node)

    def visit_Call(self, node):
        # Resolve the function or method call and determine its class/module
        func_call, class_name = self.resolve_func(node.func)
        self.calls.append(func_call)
        self.class_names.append(class_name)
        arg_count = len(node.args) + len(node.keywords)
        self.argument_counts.append(arg_count)
        self.generic_visit(node)

    def resolve_call_to_class_name(self, call):
        if isinstance(call.func, ast.Name):
            return self.imports.get(call.func.id, call.func.id)
        elif isinstance(call.func, ast.Attribute):
            return self.resolve_full_path(call.func)
        return "unknown_class"

    def resolve_func(self, node):
        func_call = "unknown_function"
        class_name = "Unknown"

        if isinstance(node, ast.Attribute):
            func_call = node.attr
            if isinstance(node.value, ast.Name) and node.value.id in self.variable_types:
                class_name = self.variable_types[node.value.id]
            else:
                class_name = self.resolve_full_path(node.value)
        elif isinstance(node, ast.Name):
            func_call = node.id
            class_name = self.imports.get(func_call, "unknown")

        return func_call, class_name

    def resolve_full_path(self, node):
        if isinstance(node, ast.Attribute):
            base_path = self.resolve_full_path(node.value)
            return f"{base_path}.{node.attr}" if base_path else node.attr
        elif isinstance(node, ast.Name):
            return self.imports.get(node.id, node.id)

    def generic_visit(self, node):
        super().generic_visit(node)



'''import ast
class CallVisitor(ast.NodeVisitor):
    def __init__(self, imports):
        self.calls = []
        self.argument_counts = []
        self.class_names = []
        self.imports = imports
        self.variable_types = {}  # Store variable types for better resolution
        self.fixture_returns = {}  # Track return values from fixtures

    def visit_FunctionDef(self, node):
        # Check if this function is a fixture
        if any(d.id == 'fixture' for d in node.decorator_list if isinstance(d, ast.Name)):
            # Process fixture to track its return type
            self.process_fixture(node)
        self.generic_visit(node)

    def process_fixture(self, node):
        # Assume the last statement in the fixture function is a return statement
        if isinstance(node.body[-1], ast.Return):
            return_expr = node.body[-1].value
            if isinstance(return_expr, ast.Call) and isinstance(return_expr.func, ast.Attribute):
                class_name = self.resolve_full_path(return_expr.func)
                self.fixture_returns[node.name] = class_name

    def visit_Call(self, node):
        # Check if this is a call in a test that uses a fixture
        func_call = ""
        class_name = ""

        if isinstance(node.func, ast.Attribute):
            func_call = node.func.attr
            if isinstance(node.func.value, ast.Name) and node.func.value.id in self.fixture_returns:
                class_name = self.fixture_returns[node.func.value.id]
            else:
                class_name = self.resolve_full_path(node.func.value)
        elif isinstance(node.func, ast.Name):
            func_call = node.func.id
            class_name = self.imports.get(func_call, "")

        self.calls.append(func_call)
        self.class_names.append(class_name)
        arg_count = len(node.args) + len(node.keywords)
        self.argument_counts.append(arg_count)
        self.generic_visit(node)

    def resolve_full_path(self, node):
        if isinstance(node, ast.Attribute):
            base_path = self.resolve_full_path(node.value)
            return f"{base_path}.{node.attr}" if base_path else node.attr
        elif isinstance(node, ast.Name):
            return self.imports.get(node.id, node.id)

    def resolve_func(self, node):
        if isinstance(node, ast.Attribute):
            return f"{self.resolve_full_path(node.value)}.{node.attr}"
        elif isinstance(node, ast.Name):
            return self.imports.get(node.id, node.id)
        return "unknown_function"'''

