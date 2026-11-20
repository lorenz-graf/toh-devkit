// TOH DevKit app: controls the RP2040's LEDs through toh-devkitd (session D-Bus, started on demand).
// Pure QML, run by sailfish-qml (no compiled code).
import QtQuick 2.0
import Sailfish.Silica 1.0
import Nemo.DBus 2.0

ApplicationWindow {
    id: app
    property string status: "Connecting…"
    property bool connected: false
    // RGB LED colour as hue / saturation (colour field) and value (brightness slider), each 0-1
    property real hue: 0
    property real sat: 0
    property real val: 0
    readonly property color rgbColor: Qt.hsva(hue, sat, val, 1)

    function rgbToHsv(r, g, b) {
        r /= 255; g /= 255; b /= 255
        var max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min, h = 0
        if (d > 0) {
            if (max === r) h = ((g - b) / d) % 6
            else if (max === g) h = (b - r) / d + 2
            else h = (r - g) / d + 4
            h /= 6
            if (h < 0) h += 1
        }
        return { h: h, s: max === 0 ? 0 : d / max, v: max }
    }
    onRgbColorChanged: if (!page.loading) sendRgb.restart()

    DBusInterface {
        id: devkit
        bus: DBus.SessionBus
        service: "io.github.lorenz_graf.TohDevkit"
        path: "/io/github/lorenz_graf/TohDevkit"
        iface: "io.github.lorenz_graf.TohDevkit"
    }

    function fail(err) {
        app.connected = false
        var s = String(err)
        app.status = s.indexOf("NotAttached") >= 0 || s.indexOf("borrow") >= 0
                ? "Cover not attached" : "No answer from the board"
    }

    function refresh() {
        devkit.typedCall("Info", [], function(info) {
            var first = !app.connected
            app.status = info
            app.connected = true
            if (first) loadState()
        }, fail)
    }

    function loadState() {
        devkit.typedCall("GetState", [], function(s) {
            page.loading = true
            var c = rgbToHsv(s[0], s[1], s[2])
            if (c.v > 0) { app.hue = c.h; app.sat = c.s }   // keep the marker where it was when the LED is off
            app.val = c.v
            page.led.value = s[3]
            page.loading = false
        }, fail)
    }

    Timer {   // keep the status current while the app is open
        interval: 3000; repeat: true; triggeredOnStart: true
        running: Qt.application.state === Qt.ApplicationActive
        onTriggered: app.refresh()
    }

    // Slider changes are sent at most every 60 ms (one bus borrow per call)
    Timer {
        id: sendRgb; interval: 60
        onTriggered: devkit.typedCall("SetRgb", [
            { type: "i", value: Math.round(app.rgbColor.r * 255) },
            { type: "i", value: Math.round(app.rgbColor.g * 255) },
            { type: "i", value: Math.round(app.rgbColor.b * 255) }], function() {}, app.fail)
    }
    Timer {
        id: sendLed; interval: 60
        onTriggered: devkit.typedCall("SetLed", [{ type: "i", value: Math.round(page.led.value) }],
                                      function() {}, app.fail)
    }

    initialPage: Page {
        id: page
        property bool loading: false
        property alias led: led

        SilicaFlickable {
            anchors.fill: parent
            contentHeight: col.height + Theme.paddingLarge

            Column {
                id: col
                width: parent.width

                PageHeader { title: "TOH DevKit" }

                Label {
                    x: Theme.horizontalPageMargin
                    width: parent.width - 2 * x
                    text: app.status
                    color: app.connected ? Theme.highlightColor : Theme.secondaryHighlightColor
                    wrapMode: Text.Wrap
                }

                SectionHeader { text: "LED on GP14" }
                TextSwitch {
                    text: "On"
                    enabled: app.connected
                    checked: led.value > 0
                    automaticCheck: false
                    onClicked: led.value = led.value > 0 ? 0 : 255
                }
                Slider {
                    id: led
                    width: parent.width
                    enabled: app.connected
                    label: "Brightness"
                    minimumValue: 0; maximumValue: 255; stepSize: 1
                    valueText: Math.round(value)
                    onValueChanged: if (!page.loading) sendLed.restart()
                }

                SectionHeader { text: "RGB LED" }
                Item {
                    id: field
                    x: Theme.horizontalPageMargin
                    width: parent.width - 2 * x
                    height: width * 0.6
                    opacity: app.connected ? 1 : 0.4

                    Rectangle {   // hue, left to right (a vertical gradient turned by -90 degrees)
                        anchors.centerIn: parent
                        width: parent.height; height: parent.width
                        rotation: -90
                        gradient: Gradient {
                            GradientStop { position: 0.0;   color: "#ff0000" }
                            GradientStop { position: 0.167; color: "#ffff00" }
                            GradientStop { position: 0.333; color: "#00ff00" }
                            GradientStop { position: 0.5;   color: "#00ffff" }
                            GradientStop { position: 0.667; color: "#0000ff" }
                            GradientStop { position: 0.833; color: "#ff00ff" }
                            GradientStop { position: 1.0;   color: "#ff0000" }
                        }
                    }
                    Rectangle {   // saturation: full at the top, white at the bottom
                        anchors.fill: parent
                        gradient: Gradient {
                            GradientStop { position: 0.0; color: "#00ffffff" }
                            GradientStop { position: 1.0; color: "#ffffffff" }
                        }
                    }
                    Rectangle {   // marker
                        width: Theme.paddingLarge * 2; height: width; radius: width / 2
                        x: app.hue * field.width - width / 2
                        y: (1 - app.sat) * field.height - height / 2
                        color: Qt.hsva(app.hue, app.sat, 1, 1)
                        border.color: "white"; border.width: 3
                        Rectangle {
                            anchors.fill: parent; anchors.margins: 3; radius: width / 2
                            color: "transparent"; border.color: "black"; border.width: 1
                        }
                    }
                    MouseArea {
                        anchors.fill: parent
                        enabled: app.connected
                        preventStealing: true   // dragging here must not scroll the page
                        function pick(mx, my) {
                            app.hue = Math.max(0, Math.min(1, mx / width))
                            app.sat = Math.max(0, Math.min(1, 1 - my / height))
                            if (app.val === 0) app.val = 0.5   // picking a colour while off: switch on at half
                        }
                        onPressed: pick(mouse.x, mouse.y)
                        onPositionChanged: pick(mouse.x, mouse.y)
                    }
                }
                Slider {
                    width: parent.width; enabled: app.connected
                    label: "Brightness"
                    minimumValue: 0; maximumValue: 100; stepSize: 1
                    value: Math.round(app.val * 100)
                    id: brightness
                    valueText: Math.round(value) + " %"
                    onValueChanged: if (Math.round(app.val * 100) !== Math.round(value)) app.val = value / 100
                    // a dragged Silica slider drops its value binding, so follow app.val by hand
                    Connections {
                        target: app
                        onValChanged: if (Math.round(brightness.value) !== Math.round(app.val * 100))
                                          brightness.value = app.val * 100
                    }
                }
                Button {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "All off"
                    enabled: app.connected
                    onClicked: { app.val = 0; led.value = 0 }
                }
            }
            VerticalScrollDecorator {}
        }
    }

    cover: CoverBackground {
        Column {
            anchors.centerIn: parent
            width: parent.width - 2 * Theme.paddingLarge
            spacing: Theme.paddingMedium
            Label {
                width: parent.width; horizontalAlignment: Text.AlignHCenter
                text: "TOH DevKit"
            }
            Label {
                width: parent.width; horizontalAlignment: Text.AlignHCenter
                text: app.status
                font.pixelSize: Theme.fontSizeExtraSmall
                color: Theme.secondaryColor
                wrapMode: Text.Wrap
            }
        }
    }
}
