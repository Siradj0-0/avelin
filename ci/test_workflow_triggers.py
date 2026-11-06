"""Guard the merge-queue event used by required test checks."""
import re
import unittest
from pathlib import Path


def trigger_names(text):
    """Read the simple block-style trigger list used by our workflow."""
    block = re.search(r'(?m)^on:[ \t]*\n((?:(?:[ \t]+[^\n]*|[ \t]*)\n)*)', text)
    if block is None:
        return set()
    return set(re.findall(r'(?m)^  ([A-Za-z_][A-Za-z0-9_]*):[ \t]*(?:#.*)?$', block.group(1)))


class WorkflowTriggerTests(unittest.TestCase):
    def test_tests_workflow_runs_for_merge_queue(self):
        workflow = Path(__file__).resolve().parents[1] / '.github/workflows/test.yml'
        self.assertIn('merge_group', trigger_names(workflow.read_text(encoding='utf-8')))

    def test_job_named_merge_group_is_not_a_trigger(self):
        workflow = 'on:\n  pull_request:\njobs:\n  merge_group:\n    runs-on: ubuntu-latest\n'
        self.assertNotIn('merge_group', trigger_names(workflow))


if __name__ == '__main__':
    unittest.main()
