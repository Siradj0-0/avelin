"""Offline regression tests: python3 -m unittest discover -s packaging/source -v."""
import hashlib
import importlib.util
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("build.py")
spec = importlib.util.spec_from_file_location("source_archive_build", SCRIPT)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class SourceArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        (self.repo / "avelin").mkdir()
        (self.repo / "avelin/__init__.py").write_text('__version__ = "0.2.0"\n')
        (self.repo / "tracked.txt").write_text("committed\n")
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")
        self.commit = self.git("rev-parse", "HEAD").strip()
        self.out1 = self.root / "one"
        self.out2 = self.root / "two"
        self.out1.mkdir()
        self.out2.mkdir()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout

    def test_exact_commit_is_reproducible_and_excludes_worktree_changes(self):
        (self.repo / "tracked.txt").write_text("modified\n")
        (self.repo / "untracked.txt").write_text("private\n")
        one, first = builder.build(self.repo, self.commit, self.out1)
        two, second = builder.build(self.repo, self.commit, self.out2)
        self.assertEqual(first, second)
        self.assertEqual(first, hashlib.sha256(one.read_bytes()).hexdigest())
        self.assertEqual(one.read_bytes(), two.read_bytes())
        with tarfile.open(one, "r:gz") as archive:
            names = archive.getnames()
            self.assertIn("avelin-0.2.0/tracked.txt", names)
            self.assertNotIn("avelin-0.2.0/untracked.txt", names)
            self.assertEqual(archive.extractfile("avelin-0.2.0/tracked.txt").read(), b"committed\n")

    def test_rejects_refs_abbreviations_and_tag_objects(self):
        self.git("tag", "-a", "v0.2.0", "-m", "fixture tag")
        tag_object = self.git("rev-parse", "v0.2.0").strip()
        for invalid in ("HEAD", self.commit[:12], self.commit.upper(), tag_object):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                builder.build(self.repo, invalid, self.out1)
        self.assertEqual(list(self.out1.iterdir()), [])

    def test_refuses_to_overwrite_output(self):
        target = self.out1 / "avelin-0.2.0.tar.gz"
        target.write_bytes(b"keep")
        with self.assertRaises(FileExistsError):
            builder.build(self.repo, self.commit, self.out1)
        self.assertEqual(target.read_bytes(), b"keep")

    def test_rejects_invalid_version_in_commit(self):
        (self.repo / "avelin/__init__.py").write_text('__version__ = "../unsafe"\n')
        self.git("add", ".")
        self.git("commit", "-qm", "bad version")
        commit = self.git("rev-parse", "HEAD").strip()
        with self.assertRaises(ValueError):
            builder.build(self.repo, commit, self.out1)
        self.assertEqual(list(self.out1.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
