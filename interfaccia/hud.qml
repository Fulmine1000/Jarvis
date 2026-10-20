import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15

ApplicationWindow {
    id: root
    visible: true
    visibility: Window.Windowed
    width: 1280
    height: 700
    minimumWidth: 1180
    minimumHeight: 650
    title: "J.A.R.V.I.S. — Neural Command Interface"
    // Palette cinematografica ambra/arancio: niente pannelli blu/ciano residui.
    color: "#070503"

    property real t: 0
    property string stateText: "SYSTEM ONLINE"
    property string commandText: "Awaiting command..."
    property string responseText: "Neural core standing by."
    property string clockText: "--:--:--"
    property string dateText: "----/--/--"
    property string cpuText: "--"
    property string memoryText: "--"
    property string diskText: "--"
    property string networkText: "--"
    property string voiceText: "STANDBY"
    property string memoryState: "ONLINE"
    property string deviceText: "5 / 5"
    property string kernelText: "OPERATIONAL"
    property string eventsText: ""
    property bool listening: false
    property bool speaking: false
    property real activity: 0.18

    function setState(data) {
        if (!data) return
        stateText = data.state || stateText
        commandText = data.command || commandText
        responseText = data.response || responseText
        clockText = data.clock || clockText
        dateText = data.date || dateText
        cpuText = data.cpu || cpuText
        memoryText = data.memory || memoryText
        diskText = data.disk || diskText
        networkText = data.network || networkText
        voiceText = data.voice || voiceText
        memoryState = data.memory_state || memoryState
        deviceText = data.devices || deviceText
        kernelText = data.kernel || kernelText
        eventsText = data.events || eventsText
        listening = !!data.listening
        speaking = !!data.speaking
        activity = Math.max(0.08, Math.min(1.0, Number(data.activity || 0.18)))
    }

    function voiceDisplay() {
        if (root.speaking) return "SPEAKING"
        if (root.listening) return "LISTENING"
        return "STANDBY"
    }

    Connections {
        target: bridge
        function onStateChanged(payload) {
            try { root.setState(JSON.parse(payload)) } catch (e) {}
        }
        function onHideRequested() { root.visible = false }
        function onShowRequested() {
            root.visible = true
            root.raise()
            root.requestActivate()
        }
    }

    Timer {
        interval: 16
        running: root.visible
        repeat: true
        onTriggered: root.t += 0.016
    }

    Rectangle { anchors.fill: parent; color: "#070503" }

    // Technical grid
    Repeater {
        model: 15
        Rectangle {
            x: 0
            y: 66 + index * 42
            width: root.width
            height: 1
            color: index % 3 === 0 ? "#35200d" : "#1d1007"
            opacity: 0.55
        }
    }
    Repeater {
        model: 14
        Rectangle {
            x: 24 + index * 78
            y: 66
            width: 1
            height: root.height - 92
            color: "#241306"
            opacity: 0.48
        }
    }

    // Header: separate fixed-width zones prevent text collisions at all supported sizes.
    Rectangle {
        id: header
        x: 16; y: 12; width: root.width - 32; height: 42
        color: "#1a0d04"
        border.color: "#7a3c0b"
        border.width: 1
        Rectangle { x: 0; y: parent.height - 2; width: 300; height: 2; color: "#ffb347" }
        Text {
            x: 16; width: 126; height: parent.height
            verticalAlignment: Text.AlignVCenter
            text: "J.A.R.V.I.S."; color: "#fff0d6"
            font.pixelSize: 15; font.bold: true
            elide: Text.ElideRight
        }
        Text {
            x: 154; width: 270; height: parent.height
            verticalAlignment: Text.AlignVCenter
            text: "NEURAL COMMAND INTERFACE"; color: "#d98b36"
            font.pixelSize: 9; font.bold: true
            elide: Text.ElideRight
        }
        Text {
            x: (parent.width - width) / 2; width: 280; height: parent.height
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            text: "●  " + root.stateText
            color: root.listening ? "#ffb347" : "#ffcc7a"
            font.pixelSize: 9; font.bold: true
            elide: Text.ElideRight
        }
        Text {
            anchors.right: parent.right; anchors.rightMargin: 16
            width: 220; height: parent.height
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
            text: "SIMONE  //  " + root.clockText
            color: "#d7a66b"; font.pixelSize: 9
            elide: Text.ElideRight
        }
    }

    // Left telemetry panel
    Rectangle {
        x: 12; y: 66; width: 220; height: root.height - 82
        color: "#100802"; border.color: "#63340c"; border.width: 1
        Text { x: 12; y: 11; text: "SYSTEM TELEMETRY"; color: "#fff0d6"; font.pixelSize: 9; font.bold: true }
        Rectangle { x: 12; y: 29; width: parent.width - 24; height: 1; color: "#4a270b" }

        Repeater {
            model: [ ["CPU LOAD", root.cpuText], ["MEMORY", root.memoryText], ["STORAGE", root.diskText], ["NETWORK", root.networkText] ]
            Item {
                x: 14; y: 46 + index * 45; width: 190; height: 32
                Text { text: modelData[0]; color: "#d98b36"; font.pixelSize: 7; font.bold: true }
                Text { y: 12; text: modelData[1]; color: "#ffe6c2"; font.pixelSize: 12; font.bold: true }
                Rectangle { x: 108; y: 15; width: 70; height: 2; color: "#4a270b" }
                Rectangle { x: 108; y: 15; width: 70 * Math.min(1, Math.max(0.05, root.activity)); height: 2; color: "#d97716"; opacity: 0.8 }
            }
        }

        Rectangle { x: 12; y: 206; width: parent.width - 24; height: 108; color: "#1b0e05"; border.color: "#5c2e0c" }
        Text { x: 22; y: 216; text: "CORE MATRIX"; color: "#d98b36"; font.pixelSize: 8; font.bold: true }
        Repeater {
            model: [ ["KERNEL", root.kernelText], ["MEMORY", root.memoryState], ["DEVICES", root.deviceText], ["VOICE", root.voiceText] ]
            Item {
                x: 22; y: 242 + index * 20; width: 176; height: 14
                Text { text: modelData[0]; color: "#9b754f"; font.pixelSize: 7 }
                Text { anchors.right: parent.right; text: modelData[1]; color: index === 3 && root.listening ? "#ffb347" : "#f4d7ac"; font.pixelSize: 7; font.bold: true }
            }
        }

        Rectangle { x: 12; y: 330; width: parent.width - 24; height: 120; color: "#1b0e05"; border.color: "#5c2e0c" }
        Text { x: 22; y: 340; text: "ACTIVITY VECTOR"; color: "#d98b36"; font.pixelSize: 8; font.bold: true }
        Repeater {
            model: 24
            Rectangle {
                width: 5
                height: 18 + Math.abs(Math.sin(root.t * 4.0 + index * 0.67)) * (58 * root.activity)
                x: 22 + index * 8
                y: 425 - height
                color: index % 4 === 0 ? "#ffb347" : "#d97716"
                opacity: 0.35 + root.activity * 0.65
            }
        }
        Rectangle { x: 22; y: 425; width: parent.width - 44; height: 1; color: "#a45c18" }
        Text { x: 22; y: 470; text: "SESSION"; color: "#d98b36"; font.pixelSize: 8; font.bold: true }
        Text { x: 22; y: 490; text: root.dateText; color: "#f4d7ac"; font.pixelSize: 11 }
        Text { x: 22; y: 510; text: "SECURITY      ARMED"; color: "#ffcc7a"; font.pixelSize: 8; font.bold: true }
        Text { x: 22; y: 530; text: "AI ENGINE     READY"; color: "#ffb347"; font.pixelSize: 8; font.bold: true }
        Text { x: 22; y: 550; text: "LINK          LOCAL"; color: "#d7a66b"; font.pixelSize: 8; font.bold: true }
    }

    // Right environment panel
    Rectangle {
        x: root.width - 232; y: 66; width: 220; height: root.height - 82
        color: "#100802"; border.color: "#63340c"; border.width: 1
        Text { x: 12; y: 11; text: "ENVIRONMENT / DEVICES"; color: "#fff0d6"; font.pixelSize: 9; font.bold: true }
        Rectangle { x: 12; y: 29; width: parent.width - 24; height: 1; color: "#4a270b" }
        Text { x: 16; y: 48; text: root.clockText; color: "#fff0d6"; font.pixelSize: 28; font.bold: true }
        Text { x: 17; y: 80; text: root.dateText; color: "#d98b36"; font.pixelSize: 9 }

        Rectangle { x: 12; y: 108; width: parent.width - 24; height: 120; color: "#1b0e05"; border.color: "#5c2e0c" }
        Text { x: 22; y: 118; text: "CONNECTED DEVICES"; color: "#d98b36"; font.pixelSize: 8; font.bold: true }
        Repeater {
            model: [ ["COMPUTER", "ONLINE"], ["NETWORK", "ONLINE"], ["BLUETOOTH", "READY"] ]
            Item {
                x: 22; y: 145 + index * 24; width: 204; height: 18
                Text { x: 10; text: modelData[0]; color: "#f4d7ac"; font.pixelSize: 7; font.bold: true }
                Text { anchors.right: parent.right; text: modelData[1]; color: "#ffcc7a"; font.pixelSize: 7; font.bold: true }
                Rectangle { y: 17; width: parent.width; height: 1; color: "#3b210d" }
            }
        }

        Rectangle { x: 12; y: 242; width: parent.width - 24; height: 128; color: "#1b0e05"; border.color: "#5c2e0c" }
        Text { x: 22; y: 252; text: "VOICE CHANNEL"; color: "#d98b36"; font.pixelSize: 8; font.bold: true }
        Text { x: 22; y: 278; text: root.voiceDisplay(); color: root.listening ? "#ffb347" : root.speaking ? "#ffcc7a" : "#f4d7ac"; font.pixelSize: 13; font.bold: true }
        Rectangle { x: 22; y: 305; width: 164; height: 30; color: "#100802"; border.color: "#61320d" }
        Repeater {
            model: 18
            Rectangle {
                width: 5
                height: 4 + Math.abs(Math.sin(root.t * (root.listening ? 10 : root.speaking ? 7 : 3) + index * 0.9)) * (root.listening || root.speaking ? 20 : 5)
                x: 27 + index * 7; y: 320 - height / 2; radius: 2
                color: root.speaking ? "#ffcc7a" : "#ffb347"
            }
        }
        Text { x: 22; y: 348; text: "WAKE WORD: JARVIS"; color: "#9b754f"; font.pixelSize: 8 }

        Rectangle { x: 12; y: 384; width: parent.width - 24; height: parent.height - 398; color: "#1b0e05"; border.color: "#5c2e0c" }
        Text { x: 22; y: 394; text: "LIVE EVENT STREAM"; color: "#d98b36"; font.pixelSize: 8; font.bold: true }
        Text { x: 22; y: 420; width: 176; height: parent.height - 440; text: root.eventsText; color: "#d7a66b"; font.pixelSize: 8; wrapMode: Text.Wrap; elide: Text.ElideLeft }
    }

    // Central hologram matched to the Instagram reference: amber/orange arc-reactor
    // projection floating above luminous elliptical emitter rings.
    Item {
        id: hologram
        x: root.width / 2 - 180
        y: 86
        width: 360
        height: 360
        property real zoom: 1.0
        property real gestureTurn: 0

        // Atmospheric amber/orange glow behind the projected object.
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 35
            width: 248 * hologram.zoom
            height: 248 * hologram.zoom
            radius: width / 2
            color: "#3d1b05"
            opacity: 0.22 + root.activity * 0.12
        }
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 50
            width: 214 * hologram.zoom
            height: 214 * hologram.zoom
            radius: width / 2
            color: "transparent"
            border.color: "#ff9a24"
            border.width: 2
            opacity: 0.38 + root.activity * 0.22
        }

        // Main floating arc-reactor disc, drawn as a luminous amber/orange technical hologram.
        Item {
            id: reactor
            anchors.horizontalCenter: parent.horizontalCenter
            y: 56
            width: 190 * hologram.zoom
            height: 190 * hologram.zoom
            rotation: root.t * 5 + hologram.gestureTurn
            Rectangle {
                anchors.centerIn: parent
                width: parent.width
                height: parent.height
                radius: width / 2
                color: "#06373d"
                opacity: 0.42
                border.color: "#ff9a24"
                border.width: 2
            }
            Rectangle {
                anchors.centerIn: parent
                width: parent.width - 18
                height: parent.height - 18
                radius: width / 2
                color: "transparent"
                border.color: "#ffd08a"
                border.width: 3
                opacity: 0.94
            }
            Rectangle {
                anchors.centerIn: parent
                width: parent.width - 36
                height: parent.height - 36
                radius: width / 2
                color: "transparent"
                border.color: "#e87512"
                border.width: 1
                opacity: 0.9
            }
            Rectangle {
                anchors.centerIn: parent
                width: parent.width - 66
                height: parent.height - 66
                radius: width / 2
                color: "transparent"
                border.color: "#ffb347"
                border.width: 2
                opacity: 0.8
            }
            Repeater {
                model: 12
                Rectangle {
                    width: 5
                    height: 25
                    radius: 2
                    x: reactor.width / 2 - width / 2
                    y: 10
                    transformOrigin: Item.Bottom
                    rotation: index * 30
                    color: index % 3 === 0 ? "#fff0d6" : "#ff9a24"
                    opacity: 0.9
                }
            }
            Repeater {
                model: 24
                Rectangle {
                    width: index % 3 === 0 ? 3 : 1
                    height: index % 3 === 0 ? 10 : 6
                    x: reactor.width / 2 - width / 2
                    y: 2
                    transformOrigin: Item.Bottom
                    rotation: index * 15
                    color: "#ffd9a0"
                    opacity: 0.75
                }
            }
            Rectangle {
                anchors.centerIn: parent
                width: 54
                height: 54
                radius: 27
                color: "#ffd9a0"
                opacity: 0.96
            }
            Rectangle {
                anchors.centerIn: parent
                width: 34
                height: 34
                radius: 17
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#fff4e6" }
                    GradientStop { position: 0.5; color: "#ffbf66" }
                    GradientStop { position: 1.0; color: "#d96508" }
                }
                opacity: 1.0
            }
        }

        // Scanning sweep across the reactor, with a subtle animated pulse.
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 56 + (Math.sin(root.t * 1.8) + 1) * 75
            width: 205 * hologram.zoom
            height: 2
            color: "#ffe0ad"
            opacity: 0.55 + root.activity * 0.35
        }

        // Amber/orange elliptical projection platform, matching the floating hologram in the video.
        Item {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 238
            width: 310 * hologram.zoom
            height: 90
            Repeater {
                model: 4
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.width - index * 25
                    height: parent.height - index * 15
                    radius: height / 2
                    color: "transparent"
                    border.color: index === 1 ? "#ffb347" : "#ff9a24"
                    border.width: index === 1 ? 3 : 1
                    opacity: (0.82 - index * 0.13) + root.activity * 0.1
                }
            }
            Rectangle {
                anchors.centerIn: parent
                width: parent.width - 26
                height: 2
                color: "#ffe0ad"
                opacity: 0.45
            }
        }

        // Fine particles rise from the emitter to the object.
        Repeater {
            model: 24
            Rectangle {
                width: index % 4 === 0 ? 3 : 2
                height: width
                radius: width / 2
                x: 70 + (index * 47 % 220)
                y: 170 + (index * 29 % 75)
                color: "#ffcc7a"
                opacity: 0.22 + (Math.sin(root.t * 2 + index) + 1) * 0.28
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 326
            text: root.listening ? "HOLOGRAM SCAN // ACTIVE" : root.speaking ? "ARC REACTOR // LINKED" : "3D HOLOGRAM // READY"
            color: "#ffcc7a"
            font.pixelSize: 9
            font.bold: true
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 342
            text: "LIVE PROJECTION  //  " + Math.round(root.activity * 100) + "%"
            color: "#d97716"
            font.pixelSize: 7
            font.bold: true
        }
    }

    // Bottom command/response strip
    Rectangle {
        x: 236; y: root.height - 68; width: root.width - 472; height: 48
        color: "#1b0e05"
        border.color: "#63340c"
        border.width: 1
        Text { x: 12; y: 5; text: "COMMAND"; color: "#d98b36"; font.pixelSize: 7; font.bold: true }
        Text { x: 12; y: 19; width: parent.width - 24; text: root.commandText; color: "#ffe6c2"; font.pixelSize: 10; elide: Text.ElideRight }
        Rectangle { x: parent.width - 84; y: 8; width: 60; height: 3; color: "#4a270b" }
        Rectangle { x: parent.width - 84; y: 8; width: 60 * root.activity; height: 3; color: "#ffb347" }
    }

    // Decorative corner markers
    Item {
        anchors.fill: parent
        Rectangle { x: 16; y: 12; width: 34; height: 1; color: "#ffb347" }
        Rectangle { x: 16; y: 12; width: 1; height: 34; color: "#ffb347" }
        Rectangle { x: root.width - 50; y: 12; width: 34; height: 1; color: "#ffb347" }
        Rectangle { x: root.width - 17; y: 12; width: 1; height: 34; color: "#ffb347" }
        Rectangle { x: 16; y: root.height - 13; width: 34; height: 1; color: "#ffb347" }
        Rectangle { x: 16; y: root.height - 46; width: 1; height: 34; color: "#ffb347" }
        Rectangle { x: root.width - 50; y: root.height - 13; width: 34; height: 1; color: "#ffb347" }
        Rectangle { x: root.width - 17; y: root.height - 46; width: 1; height: 34; color: "#ffb347" }
    }
}