#!/usr/bin/env python3
"""Build a source-only archive from a full Git commit ID, not the working tree."""
import argparse
import ast
import gzip
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

COMMIT = re.compile(r"[0-9a-f]{40}\Z")
VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\Z")


def git(repo, *args, **kwargs):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, **kwargs)


def build(repo, commit, output_dir):
    if not COMMIT.fullmatch(commit):
        raise ValueError("commit must be a full lowercase 40-character Git SHA-1")
    # Require an actual commit object, rather than an abbreviated ref or a tag.
    resolved = git(repo, "rev-parse", "--verify", commit + "^{commit}",
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()
    if resolved != commit:
        raise ValueError("commit ID must name a commit object")
    source = git(repo, "show", commit + ":avelin/__init__.py",
                 stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    module = ast.parse(source)
    versions = [node.value.value for node in module.body
                if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "__version__"
                        for target in node.targets)
                and isinstance(node.value, ast.Constant)]
    if len(versions) != 1 or not isinstance(versions[0], str) or not VERSION.fullmatch(versions[0]):
        raise ValueError("commit must contain exactly one numeric MAJOR.MINOR.PATCH version")
    version = versions[0]
    destination = Path(output_dir) / f"avelin-{version}.tar.gz"
    # Build the tar in an anonymous temporary file before creating the output;
    # exclusive creation prevents overwriting another candidate artifact.
    with tempfile.TemporaryFile() as tar:
        git(repo, "archive", "--format=tar", f"--prefix=avelin-{version}/", commit,
            stdout=tar, stderr=subprocess.PIPE)
        tar.seek(0)
        with destination.open("xb") as raw:
            try:
                with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
                    shutil.copyfileobj(tar, compressed)
            except BaseException:
                # Remove only the partial file created exclusively by this invocation.
                raw.close()
                destination.unlink()
                raise
    digest = hashlib.sha256()
    with destination.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
            digest.update(chunk)
    return destination, digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("commit", help="full 40-character commit SHA")
    parser.add_argument("output_dir", type=Path, help="existing output directory")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        path, digest = build(args.repo, args.commit, args.output_dir)
    except (OSError, ValueError, SyntaxError, subprocess.CalledProcessError) as error:
        print(f"Source archive failed: {error}", file=sys.stderr)
        return 1
    print(f"{digest}  {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
