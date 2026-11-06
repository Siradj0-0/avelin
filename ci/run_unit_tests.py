"""Run the unittest suite, failing if discovery finds no tests."""
import sys
import unittest


class ProjectTestResult(unittest.TextTestResult):
    """Count whole-test skips, excluding fixture and subtest skips."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_test = None
        self.skipped_tests = 0

    def startTest(self, test):
        self.current_test = test
        super().startTest(test)

    def stopTest(self, test):
        super().stopTest(test)
        self.current_test = None

    def addSkip(self, test, reason):
        if test is self.current_test:
            self.skipped_tests += 1
        super().addSkip(test, reason)


def main(start_dir='tests'):
    suite = unittest.defaultTestLoader.discover(start_dir)
    if suite.countTestCases() == 0:
        print(f'No tests discovered in {start_dir!r}; failing CI.', file=sys.stderr)
        return 1
    result = unittest.TextTestRunner(verbosity=2, resultclass=ProjectTestResult).run(suite)
    if result.wasSuccessful() and result.testsRun == result.skipped_tests:
        print('All discovered tests were skipped; failing CI.', file=sys.stderr)
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'tests'))
