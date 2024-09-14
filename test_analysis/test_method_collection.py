
[testenv:gather_tests]
deps =
    -r requirements-test.txt
    -r requirements-dev.txt
commands =
    python -c "
import unittest

test_directory = 'projects/airtable-python-wrapper/tests'
# test_directory = 'tests'
test_loader = unittest.TestLoader()
test_suite = test_loader.discover(start_dir=test_directory)

def get_test_methods(test_suite):
    test_methods = []
    for test in test_suite:
        if isinstance(test, unittest.TestSuite):
            test_methods.extend(get_test_methods(test))
        else:
            test_methods.append(test)
    return test_methods

all_test_methods = get_test_methods(test_suite)

for test_method in all_test_methods:
    print(test_method)
"


