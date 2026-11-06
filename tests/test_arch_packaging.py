"""Exercise the Arch recipe's staging only, without makepkg or a host install."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / 'packaging/arch/PKGBUILD'
COMMIT = 'f9fa6a3a69902f1aab9f62a37df953ffa786d4b7'


class ArchRecipeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='avelin arch ')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.srcdir = self.base / 'source dir'
        self.pkgdir = self.base / 'package dir'
        self.source = self.srcdir / f'avelin-{COMMIT}'
        for part in ('avelin', 'assets', 'packaging/deb'):
            shutil.copytree(ROOT / part, self.source / part,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        shutil.copy2(ROOT / 'LICENSE', self.source / 'LICENSE')

    def stage(self):
        script = 'set -e; source "$1"; package'
        return subprocess.run(['bash', '-c', script, 'bash', str(RECIPE)],
                              env={**os.environ, 'srcdir': str(self.srcdir),
                                   'pkgdir': str(self.pkgdir)},
                              text=True, capture_output=True)

    def test_recipe_syntax_and_integrity_metadata(self):
        subprocess.run(['bash', '-n', str(RECIPE)], check=True)
        result = subprocess.run(
            ['bash', '-c', 'source "$1"; printf "%s\\n" "$pkgname" "$pkgver" "${arch[0]}" "${source[0]}" "${sha256sums[0]}" "${depends[@]}"',
             'bash', str(RECIPE)], check=True, text=True, capture_output=True)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[:3], ['avelin-experimental', '0.1.0.r9.gf9fa6a3', 'any'])
        self.assertIn(COMMIT, lines[3])
        self.assertEqual(lines[4], '2e1e573d473da451cfa48082227fc745e60f62a49a1814d8e9ac034bb4961ef8')
        self.assertEqual(set(lines[5:]), {'python>=3.10', 'python-gobject', 'python-cairo', 'gtk4', 'glib2'})

    def test_staging_contains_exact_application_and_desktop_assets(self):
        result = self.stage()
        self.assertEqual(result.returncode, 0, result.stderr)
        files = {str(p.relative_to(self.pkgdir)) for p in self.pkgdir.rglob('*') if p.is_file()}
        expected = {f'usr/lib/avelin/avelin/{p.name}' for p in (self.source / 'avelin').glob('*.py')}
        expected |= {'usr/lib/avelin/launcher.py', 'usr/bin/avelin',
                     'usr/share/applications/io.github.siradj00.avelin.desktop',
                     'usr/share/icons/hicolor/scalable/apps/io.github.siradj00.avelin.svg',
                     'usr/share/licenses/avelin-experimental/LICENSE'}
        self.assertEqual(files, expected)
        for source in (self.source / 'avelin').glob('*.py'):
            self.assertEqual((self.pkgdir / 'usr/lib/avelin/avelin' / source.name).read_bytes(), source.read_bytes())
        launcher = self.pkgdir / 'usr/bin/avelin'
        self.assertEqual(launcher.read_bytes(), (self.source / 'packaging/deb/avelin').read_bytes())
        self.assertEqual(launcher.stat().st_mode & 0o777, 0o755)
        desktop = (self.pkgdir / 'usr/share/applications/io.github.siradj00.avelin.desktop').read_text()
        self.assertIn('\nExec=avelin\n', desktop)
        self.assertIn('\nIcon=io.github.siradj00.avelin\n', desktop)
        self.assertEqual((self.pkgdir / 'usr/share/licenses/avelin-experimental/LICENSE').read_bytes(),
                         (self.source / 'LICENSE').read_bytes())

    def test_missing_required_source_fails_staging(self):
        (self.source / 'assets/avelin.svg').unlink()
        self.assertNotEqual(self.stage().returncode, 0)

    def test_isolated_launcher_logic_does_not_import_from_cwd_or_pythonpath(self):
        self.assertEqual(self.stage().returncode, 0)
        # Relocate the launcher's single fixed package path for this staging-only test.
        private = self.pkgdir / 'usr/lib/avelin'
        original = (private / 'launcher.py').read_text()
        self.assertEqual(original.count("'/usr/lib/avelin'"), 1)
        test_launcher = self.base / 'launcher.py'
        test_launcher.write_text(original.replace("'/usr/lib/avelin'", repr(str(private))))
        (private / 'avelin/__main__.py').write_text('print("PRIVATE")\n')
        hostile = self.base / 'hostile'
        (hostile / 'avelin').mkdir(parents=True)
        (hostile / 'avelin/__init__.py').write_text('raise RuntimeError("wrong package")\n')
        result = subprocess.run([sys.executable, '-IB', str(test_launcher)], cwd=hostile,
                                env={**os.environ, 'PYTHONPATH': str(hostile)},
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'PRIVATE')


if __name__ == '__main__':
    unittest.main()
