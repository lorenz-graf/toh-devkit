#!/bin/sh
# Builds ../build/toh-devkit-<version>-<release>.aarch64.rpm (Go binaries cross-compiled, app is pure QML).
# Needs go, python3 + Pillow (icon), rpmbuild (Arch: pacman -S rpm-tools). Sailfish has rpm 4.16, so the package is
# written in rpm v4 format with a gzip payload.
set -eu
cd "$(dirname "$0")"
VERSION=0.1.0

OUT=$(cd .. && pwd)/build
TOP=$OUT/rpm
rm -rf "$TOP" && mkdir -p "$TOP/SOURCES"
for c in toh-i2c toh-devkitd; do
  CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build -trimpath -ldflags="-s -w" -o "$TOP/SOURCES/$c" ./cmd/$c
done
python3 app/make_icon.py "$TOP/SOURCES/icons" >/dev/null
cp devkit.yaml app/toh-devkit.qml app/toh-devkit.desktop app/io.github.lorenz_graf.TohDevkit.service "$TOP/SOURCES/"

rpmbuild -bb --quiet --target aarch64-unknown-linux \
    --define "_topdir $TOP" \
    --define "tdk_version $VERSION" \
    --define "_binary_payload w9.gzdio" \
    --define "_rpmformat 4" \
    rpm/toh-devkit.spec
rm -f "$OUT"/toh-devkit-*.rpm
mv "$TOP"/RPMS/aarch64/*.rpm "$OUT/"
rm -rf "$TOP"
echo "built: $(ls "$OUT"/toh-devkit-*.rpm)"
