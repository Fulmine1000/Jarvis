import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15

ApplicationWindow {
    id: root
    visible: true
    visibility: Window.Windowed
    width: 1440
    height: 780
    minimumWidth: 1360
    minimumHeight: 740
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
        x: 16; y: 66; width: 260; height: root.height - 94
        color: "#100802"; border.color: "#63340c"; border.width: 1
        Text { x: 12; y: 11; text: "SYSTEM TELEMETRY"; color: "#fff0d6"; font.pixelSize: 9; font.bold: true }
        Rectangle { x: 12; y: 29; width: parent.width - 24; height: 1; color: "#4a270b" }

        Repeater {
            model: [ ["CPU LOAD", root.cpuText], ["MEMORY", root.memoryText], ["STORAGE", root.diskText], ["NETWORK", root.networkText] ]
            Item {
                x: 14; y: 46 + index * 45; width: 220; height: 32
                Text { text: modelData[0]; color: "#d98b36"; font.pixelSize: 7; font.bold: true }
                Text { y: 12; text: modelData[1]; color: "#ffe6c2"; font.pixelSize: 12; font.bold: true }
                Rectangle { x: 120; y: 15; width: 90; height: 2; color: "#4a270b" }
                Rectangle { x: 120; y: 15; width: 90 * Math.min(1, Math.max(0.05, root.activity)); height: 2; color: "#d97716"; opacity: 0.8 }
            }
        }

        Rectangle { x: 12; y: 206; width: parent.width - 24; height: 108; color: "#1b0e05"; border.color: "#5c2e0c" }
        Text { x: 22; y: 216; text: "CORE MATRIX"; color: "#d98b36"; font.pixelSize: 8; font.bold: true }
        Repeater {
            model: [ ["KERNEL", root.kernelText], ["MEMORY", root.memoryState], ["DEVICES", root.deviceText], ["VOICE", root.voiceText] ]
            Item {
                x: 22; y: 242 + index * 20; width: 204; height: 14
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
        x: root.width - 276; y: 66; width: 260; height: root.height - 94
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
        Rectangle { x: 22; y: 305; width: 188; height: 30; color: "#100802"; border.color: "#61320d" }
        Repeater {
            model: 22
            Rectangle {
                width: 5
                height: 4 + Math.abs(Math.sin(root.t * (root.listening ? 10 : root.speaking ? 7 : 3) + index * 0.9)) * (root.listening || root.speaking ? 20 : 5)
                x: 27 + index * 8; y: 320 - height / 2; radius: 2
                color: root.speaking ? "#ffcc7a" : "#ffb347"
            }
        }
        Text { x: 22; y: 348; text: "WAKE WORD: JARVIS"; color: "#9b754f"; font.pixelSize: 8 }

        Rectangle { x: 12; y: 384; width: parent.width - 24; height: parent.height - 398; color: "#1b0e05"; border.color: "#5c2e0c" }
        Text { x: 22; y: 394; text: "LIVE EVENT STREAM"; color: "#d98b36"; font.pixelSize: 8; font.bold: true }
        Text { x: 22; y: 420; width: 204; height: parent.height - 440; text: root.eventsText; color: "#d7a66b"; font.pixelSize: 8; wrapMode: Text.Wrap; elide: Text.ElideLeft }
    }

    // Central neural reactor
    Item {
        id: core
        x: root.width / 2 - 215
        y: 96
        width: 430
        height: 430

        Rectangle { anchors.centerIn: parent; width: 382; height: 382; radius: 191; color: "transparent"; border.color: "#5c2e0c"; border.width: 1; opacity: 0.7 }
        Rectangle { anchors.centerIn: parent; width: 350; height: 350; radius: 175; color: "#1b0e05"; opacity: 0.35; border.color: "#a45c18"; border.width: 1 }
        Rectangle { anchors.centerIn: parent; width: 305; height: 305; radius: 152; color: "transparent"; border.color: "#a45c18"; border.width: 1; rotation: root.t * 6 }
        Rectangle { anchors.centerIn: parent; width: 270; height: 270; radius: 135; color: "transparent"; border.color: "#633a12"; border.width: 2; rotation: -root.t * 10 }
        Rectangle { anchors.centerIn: parent; width: 225; height: 225; radius: 112; color: "transparent"; border.color: "#ffb347"; border.width: 1; opacity: 0.65 + root.activity * 0.35; rotation: root.t * 18 }

        Repeater {
            model: 16
            Rectangle {
                width: index % 2 === 0 ? 22 : 10
                height: 2
                x: 215 + Math.cos(index * Math.PI / 8 + root.t * 0.55) * (index % 2 === 0 ? 178 : 150) - width / 2
                y: 215 + Math.sin(index * Math.PI / 8 + root.t * 0.55) * (index % 2 === 0 ? 178 : 150) - height / 2
                rotation: index * 22.5 + 90
                color: index % 4 === 0 ? "#ffb347" : "#a45c18"
                opacity: 0.8
            }
        }

        // Holographic scan plane: sweeps through the reactor like a live projection.
        Rectangle {
            anchors.centerIn: parent
            width: 218
            height: 1
            rotation: root.t * 52
            transformOrigin: Item.Center
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#00ffb347" }
                GradientStop { position: 0.48; color: "#ffe0a6" }
                GradientStop { position: 0.52; color: "#ffb347" }
                GradientStop { position: 1.0; color: "#00ffb347" }
            }
            opacity: 0.58 + root.activity * 0.25
        }

        // Three orbiting holographic markers react to the voice channel.
        Repeater {
            model: 3
            Rectangle {
                width: index === 1 ? 7 : 4
                height: width
                radius: width / 2
                x: 215 + Math.cos(root.t * (index % 2 === 0 ? 0.9 : -0.65) + index * 2.094) * (index === 1 ? 122 : 145) - width / 2
                y: 215 + Math.sin(root.t * (index % 2 === 0 ? 0.9 : -0.65) + index * 2.094) * (index === 1 ? 122 : 145) - height / 2
                color: index === 1 ? "#ffe0a6" : "#ffb347"
                opacity: 0.55 + root.activity * 0.45
            }
        }

        // Amber radial particles: the cinematic reactor shown in the reference Short.
        Repeater {
            model: 46
            Rectangle {
                width: index % 4 === 0 ? 3 : index % 3 === 0 ? 2 : 1
                height: width
                radius: width / 2
                x: 215 + Math.cos(index * 2.399 + root.t * (0.12 + (index % 5) * 0.035)) * (70 + (index * 37 % 120)) - width / 2
                y: 215 + Math.sin(index * 2.399 + root.t * (0.12 + (index % 5) * 0.035)) * (70 + (index * 37 % 120)) - height / 2
                color: index % 5 === 0 ? "#fff0d6" : "#ffb347"
                opacity: 0.28 + (Math.sin(root.t * 1.8 + index) + 1) * 0.28
            }
        }

        // Energy rings
        Rectangle {
            anchors.centerIn: parent
            width: 178 + root.activity * 20
            height: width
            radius: width / 2
            color: "#3a1c07"
            border.color: "#ff9d2e"
            border.width: 2
            opacity: 0.55
        }
        Rectangle {
            anchors.centerIn: parent
            width: 132 + root.activity * 14
            height: width
            radius: width / 2
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#63330d" }
                GradientStop { position: 0.5; color: "#d97716" }
                GradientStop { position: 1.0; color: "#100802" }
            }
            border.color: "#ffb347"
            border.width: 2
            opacity: 0.9
        }
        Rectangle {
            anchors.centerIn: parent
            width: 86 + root.activity * 10
            height: width
            radius: width / 2
            color: root.listening ? "#ffb347" : root.speaking ? "#ffcc7a" : "#ffb347"
            opacity: root.listening || root.speaking ? 0.95 : 0.72
            scale: 1.0 + Math.sin(root.t * 6) * (root.listening || root.speaking ? 0.05 : 0.015)
            Behavior on color { ColorAnimation { duration: 180 } }
        }

        // J.A.R.V.I.S. identity in the reactor center
        Text {
            anchors.centerIn: parent
            anchors.verticalCenterOffset: -1
            text: "J.A.R.V.I.S."
            color: "#fff5e5"
            font.pixelSize: 18
            font.bold: true
            style: Text.Outline
            styleColor: "#d97716"
            opacity: root.listening || root.speaking ? 1.0 : 0.94
            scale: 1.0 + Math.sin(root.t * 5) * (root.listening || root.speaking ? 0.025 : 0.008)
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 322
            text: root.listening ? "LISTENING" : root.speaking ? "SPEAKING" : "SYSTEM READY"
            color: root.listening ? "#ffb347" : root.speaking ? "#ffcc7a" : "#ffe0a6"
            font.pixelSize: 11
            font.bold: true
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 342
            text: "NEURAL PROCESSING // " + Math.round(root.activity * 100) + "%"
            color: "#d98b36"
            font.pixelSize: 7
            font.bold: true
        }
    }

    // Bottom command/response strip
    Rectangle {
        x: 286; y: root.height - 78; width: root.width - 572; height: 54
        color: "#1b0e05"
        border.color: "#63340c"
        border.width: 1
        Text { x: 12; y: 7; text: "COMMAND"; color: "#d98b36"; font.pixelSize: 7; font.bold: true }
        Text { x: 12; y: 21; width: parent.width - 24; text: root.commandText; color: "#ffe6c2"; font.pixelSize: 10; elide: Text.ElideRight }
        Rectangle { x: parent.width - 84; y: 10; width: 60; height: 3; color: "#4a270b" }
        Rectangle { x: parent.width - 84; y: 10; width: 60 * root.activity; height: 3; color: "#ffb347" }
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