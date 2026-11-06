"""Check Debian staging file selection without dpkg or root."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class PackageFilesTest(unittest.TestCase):
    def run_build(self, with_dashboard):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'project'
            for directory in ('avelin', 'packaging/deb', 'assets', 'bin'):
                (root / directory).mkdir(parents=True)
            original = Path(__file__).with_name('build.sh')
            shutil.copyfile(original, root / 'packaging/deb/build.sh')
            for path, content in {
                'avelin/__init__.py': "__version__ = '0.1.0'\n",
                'avelin/app.py': '# app\n',
                'packaging/deb/launcher.py': '# launcher\n',
                'packaging/deb/avelin': '#!/bin/sh\n',
                'packaging/deb/io.github.siradj00.avelin.desktop': '[Desktop Entry]\n',
                'assets/avelin.svg': '<svg/>\n',
                'LICENSE': 'fixture\n',
            }.items():
                (root / path).write_text(content)
            if with_dashboard:
                dashboard = root / 'avelin/dashboard'
                dashboard.mkdir()
                for name in ('__init__.py', 'history.py', 'test_history.py'):
                    (dashboard / name).write_text('# fixture\n')
            dpkg = root / 'bin/dpkg-deb'
            dpkg.write_text('#!/bin/sh\nfind "$3/usr/lib/avelin/avelin" -type f | sed "s|$3||" | sort > "$MANIFEST"\n')
            dpkg.chmod(0o755)
            manifest = root / 'manifest'
            env = dict(os.environ, PATH=str(root / 'bin') + os.pathsep + os.environ['PATH'],
                       DEB_MAINTAINER='Fixture <fixture@example.invalid>', MANIFEST=str(manifest))
            subprocess.run(['sh', str(root / 'packaging/deb/build.sh'), str(root / 'out')],
                           env=env, check=True, capture_output=True, text=True)
            return manifest.read_text().splitlines()

    def test_dashboard_runtime_modules_are_included_without_tests(self):
        files = self.run_build(True)
        self.assertIn('/usr/lib/avelin/avelin/dashboard/__init__.py', files)
        self.assertIn('/usr/lib/avelin/avelin/dashboard/history.py', files)
        self.assertNotIn('/usr/lib/avelin/avelin/dashboard/test_history.py', files)

    def test_build_still_works_without_dashboard_directory(self):
        files = self.run_build(False)
        self.assertIn('/usr/lib/avelin/avelin/app.py', files)
        self.assertFalse(any('/dashboard/' in path for path in files))


if __name__ == '__main__':
    unittest.main()
