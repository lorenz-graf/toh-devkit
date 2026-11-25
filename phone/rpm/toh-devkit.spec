# TOH DevKit phone package: toh-i2c (CLI), toh-devkitd (session D-Bus service), the TOH DevKit app (pure QML)
# and the symbiosis config for the dev cover. Built by ../build-rpm.sh from prebuilt static Go binaries.
%global debug_package %{nil}
%global _build_id_links none
%global __os_install_post %{nil}

Name:       toh-devkit
Version:    %{tdk_version}
Release:    1
Summary:    TOH DevKit: talk to the breadboard dev cover's microcontroller
License:    BSD-3-Clause
URL:        https://github.com/lorenz-graf/toh-devkit
Requires:   symbiosis
Requires:   libsailfishapp-launcher
Requires:   nemo-qml-plugin-dbus-qt5

%description
Phone side of the TOH DevKit (breadboard dev cover for The Other Half connector):
- toh-i2c: command-line I2C transfers on the TOH bus without root
- toh-devkitd: session D-Bus service io.github.lorenz_graf.TohDevkit (started on demand)
- TOH DevKit app: switches the RP2040's LEDs
- symbiosis config for the dev cover (vendor/product 0000/0000) that allows both programs on the bus

%prep

%build

%install
S=%{_sourcedir}
install -D -m 0755 $S/toh-i2c     %{buildroot}/usr/bin/toh-i2c
install -D -m 0755 $S/toh-devkitd %{buildroot}/usr/libexec/toh-devkit/toh-devkitd
install -D -m 0644 $S/devkit.yaml %{buildroot}/usr/share/tohd-1/tohs/0000/0000/devkit.yaml
install -D -m 0644 $S/io.github.lorenz_graf.TohDevkit.service %{buildroot}/usr/share/dbus-1/services/io.github.lorenz_graf.TohDevkit.service
install -D -m 0644 $S/toh-devkit.qml     %{buildroot}/usr/share/toh-devkit/qml/toh-devkit.qml
install -D -m 0644 $S/toh-devkit.desktop %{buildroot}/usr/share/applications/toh-devkit.desktop
for s in 86 108 128 172; do
  install -D -m 0644 $S/icons/${s}x${s}/toh-devkit.png %{buildroot}/usr/share/icons/hicolor/${s}x${s}/apps/toh-devkit.png
done

%post
# A toh-devkitd still running from the previous version keeps its deleted binary, and symbiosis refuses deleted
# executables (AccessDenied). Stop it; D-Bus activation starts the new one on the next call.
p=$(pidof toh-devkitd) && kill $p || :
# symbiosis reads the config on attach: take the cover off and put it back on after installing

%preun
if [ "$1" = 0 ]; then
  p=$(pidof toh-devkitd) && kill $p || :
fi

%files
/usr/bin/toh-i2c
%dir /usr/libexec/toh-devkit
/usr/libexec/toh-devkit/toh-devkitd
%dir /usr/share/tohd-1/tohs/0000
%dir /usr/share/tohd-1/tohs/0000/0000
/usr/share/tohd-1/tohs/0000/0000/devkit.yaml
/usr/share/dbus-1/services/io.github.lorenz_graf.TohDevkit.service
%dir /usr/share/toh-devkit
%dir /usr/share/toh-devkit/qml
/usr/share/toh-devkit/qml/toh-devkit.qml
/usr/share/applications/toh-devkit.desktop
/usr/share/icons/hicolor/86x86/apps/toh-devkit.png
/usr/share/icons/hicolor/108x108/apps/toh-devkit.png
/usr/share/icons/hicolor/128x128/apps/toh-devkit.png
/usr/share/icons/hicolor/172x172/apps/toh-devkit.png
