"""Run the unittest suite, failing if discovery finds no tests."""
import sys
import unittest


def main(start_dir='tests'):
    suite = unittest.defaultTestLoader.discover(start_dir)
    if suite.countTestCases() == 0:
        print(f'No tests discovered in {start_dir!r}; failing CI.', file=sys.stderr)
        return 1
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'tests'))
