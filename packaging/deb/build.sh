#!/bin/sh
# Build an experimental, architecture-independent binary package; no release upload.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
out=${1:-"$root/dist/deb"}
: "${DEB_MAINTAINER:?Set DEB_MAINTAINER to a real name and contact email}"
case "$DEB_MAINTAINER" in *'
'*|'') echo 'Invalid DEB_MAINTAINER' >&2; exit 1;; esac
command -v dpkg-deb >/dev/null || { echo 'dpkg-deb is required' >&2; exit 1; }
version=$(python3 - "$root/avelin/__init__.py" <<'PY'
import ast, re, sys
module = ast.parse(open(sys.argv[1], encoding='utf-8').read())
values = [n.value.value for n in module.body if isinstance(n, ast.Assign)
          and any(isinstance(t, ast.Name) and t.id == '__version__' for t in n.targets)
          and isinstance(n.value, ast.Constant)]
if len(values) != 1 or not isinstance(values[0], str) or not re.fullmatch(r'\d+\.\d+\.\d+', values[0]):
    raise SystemExit('Expected one numeric MAJOR.MINOR.PATCH __version__')
print(values[0] + '~dev1')
PY
)
stage=$(mktemp -d)
chmod 0755 "$stage"
trap 'rm -rf "$stage"' EXIT HUP INT TERM
install -d -m 0755 "$stage/DEBIAN" "$stage/usr/bin" "$stage/usr/lib/avelin/avelin" \
  "$stage/usr/share/applications" "$stage/usr/share/metainfo" "$stage/usr/share/icons/hicolor/scalable/apps" "$stage/usr/share/doc/avelin"
install -m 0644 "$root"/avelin/*.py "$stage/usr/lib/avelin/avelin/"
# The dashboard is optional on branches preceding its extraction.
if [ -d "$root/avelin/dashboard" ]; then
  install -d -m 0755 "$stage/usr/lib/avelin/avelin/dashboard"
  for source in "$root"/avelin/dashboard/*.py; do
    case "${source##*/}" in test_*) continue ;; esac
    [ -f "$source" ] || continue
    install -m 0644 "$source" "$stage/usr/lib/avelin/avelin/dashboard/"
  done
fi
install -m 0644 "$root/packaging/deb/launcher.py" "$stage/usr/lib/avelin/launcher.py"
install -m 0755 "$root/packaging/deb/avelin" "$stage/usr/bin/avelin"
install -m 0644 "$root/packaging/deb/io.github.siradj00.avelin.desktop" "$stage/usr/share/applications/"
install -m 0644 "$root/packaging/deb/io.github.siradj00.avelin.metainfo.xml" "$stage/usr/share/metainfo/"
install -m 0644 "$root/assets/avelin.svg" "$stage/usr/share/icons/hicolor/scalable/apps/io.github.siradj00.avelin.svg"
install -m 0644 "$root/LICENSE" "$stage/usr/share/doc/avelin/copyright"
cat > "$stage/DEBIAN/control" <<CONTROL
Package: avelin
Version: $version
Section: utils
Priority: optional
Architecture: all
Maintainer: $DEB_MAINTAINER
Depends: python3 (>= 3.10), python3-gi, python3-gi-cairo, python3-cairo, gir1.2-gtk-4.0, libglib2.0-bin
Suggests: pciutils, power-profiles-daemon
Homepage: https://github.com/Siradj0-0/avelin
Description: GTK system information and settings companion
 Avelin is an experimental desktop application for inspecting a Linux system
 and making selected, confirmed changes to user settings.
CONTROL
mkdir -p "$out"
dpkg-deb --root-owner-group --build "$stage" "$out/avelin_${version}_all.deb"
