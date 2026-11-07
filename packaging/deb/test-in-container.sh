#!/bin/sh
# Run as root in a disposable Debian/Ubuntu container with network access.
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends dpkg-dev python3 desktop-file-utils appstream xvfb xauth
# A deliberately non-deliverable contact, only for disposable CI test packages.
export DEB_MAINTAINER='Avelin CI <ci@example.invalid>'
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT HUP INT TERM
sh "$root/packaging/deb/build.sh" "$out"
set -- "$out"/*.deb
[ "$#" -eq 1 ] && [ -f "$1" ]
deb=$1
[ "$(dpkg-deb -f "$deb" Package)" = avelin ]
[ "$(dpkg-deb -f "$deb" Architecture)" = all ]
dpkg-deb -f "$deb" Depends | grep -F 'python3-gi-cairo'
dpkg-deb -c "$deb"
# Create an explicitly synthetic older-version package from the candidate. This
# exercises package-manager upgrade mechanics, not a real historic release.
version=$(dpkg-deb -f "$deb" Version)
old_version='0~agent8-test'
dpkg --compare-versions "$old_version" lt "$version"
old_stage="$out/old-stage"
old_deb="$out/synthetic-old.deb"
dpkg-deb --raw-extract "$deb" "$old_stage"
sed -i "s/^Version: .*/Version: $old_version/" "$old_stage/DEBIAN/control"
dpkg-deb --root-owner-group --build "$old_stage" "$old_deb"
[ "$(dpkg-deb -f "$old_deb" Version)" = "$old_version" ]
sha256sum "$deb" > "$out/candidate.sha256"
# Both installs resolve dependencies through APT inside this disposable container.
apt-get install -y --no-install-recommends "$old_deb"
[ "$(dpkg-query -W -f='${Version}' avelin)" = "$old_version" ]
apt-get install -y --no-install-recommends "$deb"
[ "$(dpkg-query -W -f='${Version}' avelin)" = "$version" ]
sha256sum -c "$out/candidate.sha256"
dpkg-query -W -f='${Status}\n' avelin | grep -Fx 'install ok installed'
desktop-file-validate /usr/share/applications/io.github.siradj00.avelin.desktop
python3 "$root/packaging/deb/test_metainfo.py"
test -f /usr/share/metainfo/io.github.siradj00.avelin.metainfo.xml
appstreamcli validate /usr/share/metainfo/io.github.siradj00.avelin.metainfo.xml
test -f /usr/share/icons/hicolor/scalable/apps/io.github.siradj00.avelin.svg
cd /tmp
# Isolated Python and an unrelated cwd ensure this is the installed copy.
xvfb-run -a /usr/bin/python3 -IB "$root/packaging/deb/smoke_installed.py"
# The installed launcher must remain alive long enough to open the GTK app.
set +e
timeout 8s xvfb-run -a /usr/bin/avelin > "$out/launcher.log" 2>&1
result=$?
set -e
cat "$out/launcher.log"
[ "$result" -eq 124 ] || { echo "Launcher exited unexpectedly: $result" >&2; exit 1; }
apt-get remove -y avelin
! dpkg-query -W -f='${Status}\n' avelin 2>/dev/null | grep -q 'install ok installed'
test ! -e /usr/bin/avelin
test ! -e /usr/lib/avelin/launcher.py
test ! -e /usr/share/applications/io.github.siradj00.avelin.desktop
test ! -e /usr/share/icons/hicolor/scalable/apps/io.github.siradj00.avelin.svg
test ! -e /usr/share/metainfo/io.github.siradj00.avelin.metainfo.xml
