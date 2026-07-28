# Deduplicate the failure logs in Results/merged_failures.csv.
#
# For every row: sanitize the stacktrace, md5 it, and keep one row per unique
# md5 per test. Also checks the invariant that no md5 is shared by two different
# tests -- if it is, the sanitized log no longer identifies the test it came from.
#
# Sanitization lives in get_similarity_score_stacktrace.py:sanitize_stacktrace.
# Edit the rules there, not here.
#
# Usage:
#   python3 dedup_failure_logs.py [--input PATH] [--output PATH]

import argparse
import ast
import csv
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SANITIZER_SRC = os.path.join(HERE, 'get_similarity_score_stacktrace.py')
DEFAULT_INPUT = os.path.join(HERE, os.pardir, 'Results', 'merged_failures.csv')

# key identifying "the same test"
TEST_KEY = ('slug', 'sha', 'module', 'test_name')


def load_sanitizer(path=SANITIZER_SRC):
    """Pull sanitize_stacktrace out of get_similarity_score_stacktrace.py.

    That module imports sentence_transformers/nltk/pandas at the top, which we
    do not need here and which are slow (or absent) on a plain box, so we lift
    just the one function definition out of the AST instead of importing the
    module.
    """
    with open(path, encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=path)

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == 'sanitize_stacktrace':
            module = ast.Module(body=[node], type_ignores=[])
            namespace = {'re': re}
            exec(compile(module, path, 'exec'), namespace)
            return namespace['sanitize_stacktrace']

    raise RuntimeError('sanitize_stacktrace not found in %s' % path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', default=os.path.normpath(DEFAULT_INPUT))
    parser.add_argument('--output', default=None,
                        help='default: <input dir>/merged_failures_deduped.csv')
    args = parser.parse_args()

    if args.output is None:
        args.output = os.path.join(os.path.dirname(os.path.abspath(args.input)),
                                   'merged_failures_deduped.csv')

    sanitize = load_sanitizer()
    csv.field_size_limit(sys.maxsize)

    seen = set()             # (test, md5) already written
    tests_by_md5 = {}        # md5 -> set of tests, for the collision check
    all_tests = set()
    total = kept = 0

    with open(args.input, newline='', encoding='utf-8') as fin, \
            open(args.output, 'w', newline='', encoding='utf-8') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()

        for row in reader:
            total += 1
            sanitized = sanitize(row['stacktrace'] or '')
            digest = hashlib.md5(sanitized.encode('utf-8')).hexdigest()
            test = tuple(row.get(col) or '' for col in TEST_KEY)

            all_tests.add(test)
            tests_by_md5.setdefault(digest, set()).add(test)

            if (test, digest) in seen:
                continue
            seen.add((test, digest))

            row['stacktrace'] = sanitized
            row['stacktrace_md5'] = digest
            writer.writerow(row)
            kept += 1

    print('rows in  : %d' % total)
    print('rows out : %d  (%s)' % (kept, args.output))
    print('distinct tests : %d' % len(all_tests))

    # no md5 should belong to more than one test
    collisions = {d: t for d, t in tests_by_md5.items() if len(t) > 1}
    if not collisions:
        print('md5 collisions across tests: NONE')
    else:
        print('md5 collisions across tests: %d' % len(collisions))
        for digest, tests in sorted(collisions.items())[:20]:
            print('  %s' % digest)
            for slug, sha, module, test_name in sorted(tests):
                print('      %s :: %s' % (slug, test_name))


if __name__ == '__main__':
    main()
