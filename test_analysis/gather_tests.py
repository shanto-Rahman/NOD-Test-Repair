import unittest
import os

def check_directory_exists(directory):
    """Check if the directory exists."""
    if not os.path.exists(directory):
        print(f"Test directory '{directory}' does not exist.")
        exit(1)

def discover_tests(directory):
    """Discover all tests in the specified directory."""
    test_loader = unittest.TestLoader()
    return test_loader.discover(start_dir=directory)

def get_test_methods(test_suite):
    """Recursively collect test methods from the test suite."""
    test_methods = []
    for test in test_suite:
        if isinstance(test, unittest.TestSuite):
            test_methods.extend(get_test_methods(test))
        else:
            test_methods.append(str(test))
    return test_methods

def print_discovered_tests(test_suite):
    """Print discovered test suites for debugging."""
    #print("Discovered test suites:")
    for test in test_suite:
        print(test)

def print_test_methods(test_methods):
    """Print all test methods."""
    print(f"Total number of test methods found: {len(test_methods)}")
    for test_method in test_methods:
        print(test_method)

def check_test_files(directory):
    """Check for test files and print their contents."""
    print("Checking test files and their contents:")
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                print(f"Found test file: {file}")
                with open(os.path.join(root, file), 'r') as f:
                    print(f.read())

def main():
    test_directory = 'tests'
    check_directory_exists(test_directory)
    test_suite = discover_tests(test_directory)
    test_methods = get_test_methods(test_suite)
    #print_discovered_tests(test_suite)
    #print_test_methods(test_methods)
    check_test_files(test_directory)

if __name__ == '__main__':
    main()



#import unittest
#import os
#
#test_directory = 'tests'
#
## Check if the test directory exists
#if not os.path.exists(test_directory):
#    print(f"Test directory '{test_directory}' does not exist.")
#    exit(1)
#
## Discover all tests in the specified directory
#test_loader = unittest.TestLoader()
#test_suite = test_loader.discover(start_dir=test_directory)
#
#def get_test_methods(test_suite):
#    test_methods = []
#    for test in test_suite:
#        if isinstance(test, unittest.TestSuite):
#            test_methods.extend(get_test_methods(test))
#        else:
#            test_methods.append(str(test))
#    return test_methods
#
#all_test_methods = get_test_methods(test_suite)
#
## Print discovered test suites for debugging
#print("Discovered test suites:")
#for test in test_suite:
#    print(test)
#
## Print the number of test methods found
#print(f"Total number of test methods found: {len(all_test_methods)}")
#
## Print all test methods
#for test_method in all_test_methods:
#    print(test_method)
#
## Check for test files and their contents
#print("Checking test files and their contents:")
#for root, _, files in os.walk(test_directory):
#    for file in files:
#        if file.startswith('test_') and file.endswith('.py'):
#            print(f"Found test file: {file}")
#            with open(os.path.join(root, file), 'r') as f:
#                print(f.read())
#
#
## Print discovered test suites for debugging
#print("Discovered test suites:")
#for test in test_suite:
#    print(test)
#
## Print the number of test methods found
#print(f"Total number of test methods found: {len(all_test_methods)}")
#
## Print all test methods
#for test_method in all_test_methods:
#    print(test_method)
#
