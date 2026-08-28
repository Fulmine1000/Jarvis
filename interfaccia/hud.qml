import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15

ApplicationWindow {
    id: root
    visible: true
    visibility: Window.Windowed
    width: 1050
    height: 650
    minimumWidth: 980
    minimumHeight: 620
    title: "J.A.R.V.I.S. — Neural Command Interface"
    color: "#02070c"

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

    Connections {
        target: bridge
        function onStateChanged(payload) { root.setState(JSON.parse(payload)) }
        function onHideRequested() { root.visible = false }
        function onShowRequested() { root.visible = true; root.raise(); root.requestActivate() }
    }

    Timer {
        interval: 16
        running: root.visible
        repeat: true
        onTriggered: root.t += 0.016
    }

    Rectangle { anchors.fill: parent; color: "#02070c" }
    Repeater {
        model: 15
        Rectangle {
            x: 0; y: 62 + index * 42; width: root.width; height: 1
            color: index % 3 === 0 ? "#092431" : "#06151d"; opacity: 0.55
        }
    }
    Repeater {
        model: 14
        Rectangle {
            x: 24 + index * 78; y: 62; width: 1; height: root.height - 92
            color: "#061821"; opacity: 0.48
        }
    }

    Rectangle {
        x: 16; y: 12; width: root.width - 32; height: 38
        color: "#04121a"; border.color: "#0b5265"; border.width: 1
        Rectangle { x: 0; y: height - 2; width: 190; height: 2; color: "#54f4ff" }
        Text { x: 14; anchors.verticalCenter: parent.verticalCenter; text: "J.A.R.V.I.S."; color: "#e7fbff"; font.pixelSize: 15; font.bold: true }
        Text { x: 110; anchors.verticalCenter: parent.verticalCenter; text: "NEURAL COMMAND INTERFACE"; color: "#4fa7b7"; font.pixelSize: 8; font.bold: true }
        Text { anchors.centerIn: parent; text: "●  " + root.stateText; color: root.listening ? "#54f4ff" : "#28ee70"; font.pixelSize: 9; font.bold: true }
        Text { anchors.right: parent.right; anchors.rightMargin: 14; anchors.verticalCenter: parent.verticalCenter; text: "SIMONE  //  " + root.clockText; color: "#8ebfc8"; font.pixelSize: 9 }
    }

    Rectangle {
        x: 16; y: 64; width: 248; height: root.height - 92
        color: "#031018"; border.color: "#0b4251"; border.width: 1
        Text { x: 12; y: 11; text: "SYSTEM TELEMETRY"; color: "#e7fbff"; font.pixelSize: 9; font.bold: true }
        Rectangle { x: 12; y: 29; width: parent.width - 24; height: 1; color: "#0a3541" }
        Column {
            x: 14; y: 46; width: parent.width - 28; spacing: 15
            Metric { label: "CPU LOAD"; value: root.cpuText }
            Metric { label: "MEMORY"; value: root.memoryText }
            Metric { label: "STORAGE"; value: root.diskText }
            Metric { label: "NETWORK"; value: root.networkText }
        }
        Rectangle { x: 12; y: 206; width: parent.width - 24; height: 108; color: "#04151e"; border.color: "#0a3441" }
        Text { x: 22; y: 216; text: "CORE MATRIX"; color: "#4fa7b7"; font.pixelSize: 8; font.bold: true }
        Column {
            x: 22; y: 242; spacing: 11
            MatrixRow { label: "KERNEL"; value: root.kernelText }
            MatrixRow { label: "MEMORY"; value: root.memoryState }
            MatrixRow { label: "DEVICES"; value: root.deviceText }
            MatrixRow { label: "VOICE"; value: root.voiceText }
        }
        Rectangle { x: 12; y: 330; width: parent.width - 24; height: 120; color: "#04151e"; border.color: "#0a3441" }
        Text { x: 22; y: 340; text: "ACTIVITY VECTOR"; color: "#4fa7b7"; font.pixelSize: 8; font.bold: true }
        Repeater {
            model: 24
            Rectangle {
                width: 5; height: 18 + Math.abs(Math.sin(root.t * 4.0 + index * 0.67)) * (58 * root.activity)
                x: 22 + index * 8; y: 425 - height
                color: index % 4 === 0 ? "#54f4ff" : "#187da1"; opacity: 0.35 + root.activity * 0.65
                Behavior on height { NumberAnimation { duration: 80 } }
            }
        }
        Rectangle { x: 22; y: 425; width: parent.width - 44; height: 1; color: "#1b6172" }
        Text { x: 22; y: 470; text: "SESSION"; color: "#4fa7b7"; font.pixelSize: 8; font.bold: true }
        Text { x: 22; y: 490; text: root.dateText; color: "#b7dce3"; font.pixelSize: 11 }
        Text { x: 22; y: 510; text: "SECURITY      ARMED"; color: "#28ee70"; font.pixelSize: 8; font.bold: true }
        Text { x: 22; y: 530; text: "AI ENGINE     READY"; color: "#54f4ff"; font.pixelSize: 8; font.bold: true }
        Text { x: 22; y: 550; text: "LINK          LOCAL"; color: "#8ebfc8"; font.pixelSize: 8; font.bold: true }
    }

    Rectangle {
        x: root.width - 264; y: 64; width: 248; height: root.height - 92
        color: "#031018"; border.color: "#0b4251"; border.width: 1
        Text { x: 12; y: 11; text: "ENVIRONMENT / DEVICES"; color: "#e7fbff"; font.pixelSize: 9; font.bold: true }
        Rectangle { x: 12; y: 29; width: parent.width - 24; height: 1; color: "#0a3541" }
        Text { x: 16; y: 48; text: root.clockText; color: "#e7fbff"; font.pixelSize: 28; font.bold: true }
        Text { x: 17; y: 80; text: root.dateText; color: "#4fa7b7"; font.pixelSize: 9 }
        Rectangle { x: 12; y: 108; width: parent.width - 24; height: 120; color: "#04151e"; border.color: "#0a3441" }
        Text { x: 22; y: 118; text: "CONNECTED DEVICES"; color: "#4fa7b7"; font.pixelSize: 8; font.bold: true }
        DeviceRow { y: 145; label: "COMPUTER"; state: "ONLINE" }
        DeviceRow { y: 169; label: "NETWORK"; state: "ONLINE" }
        DeviceRow { y: 193; label: "BLUETOOTH"; state: "READY" }
        Rectangle { x: 12; y: 242; width: parent.width - 24; height: 128; color: "#04151e"; border.color: "#0a3441" }
        Text { x: 22; y: 252; text: "VOICE CHANNEL"; color: "#4fa7b7"; font.pixelSize: 8; font.bold: true }
        Text { x: 22; y: 278; text: root.voiceText; color: root.listening ? "#54f4ff" : "#b7dce3"; font.pixelSize: 13; font.bold: true }
        Rectangle { x: 22; y: 305; width: 188; height: 30; color: "#021018"; border.color: "#0a3c4b" }
        Repeater {
            model: 22
            Rectangle {
                width: 5
                height: 4 + Math.abs(Math.sin(root.t * (root.listening ? 10 : 3) + index * 0.9)) * (root.listening || root.speaking ? 20 : 5)
                x: 27 + index * 8; y: 320 - height / 2; radius: 2
                color: root.speaking ? "#28ee70" : "#54f4ff"
            }
        }
        Text { x: 22; y: 348; text: "WAKE WORD: JARVIS"; color: "#718f97"; font.pixelSize: 8 }
        Rectangle { x: 12; y: 384; width: parent.width - 24; height: parent.height - 398; color: "#04151e"; border.color: "#0a3441" }
        Text { x: 22; y: 394; text: "LIVE EVENT STREAM"; color: "#4fa7b7"; font.pixelSize: 8; font.bold: true }
        Text { x: 22; y: 420; width: 204; height: parent.height - 440; text: root.eventsText; color: "#8ebfc8"; font.pixelSize: 8; wrapMode: Text.Wrap; lineHeight: 1.25; elide: Text.ElideLeft }
    }

    // Central holographic reactor: the J.A.R.V.I.S. identity is integrated into the moving core.
    Item {
        id: core
        x: root.width / 2 - 215; y: 92; width: 430; height: 430

        Rectangle { anchors.centerIn: parent; width: 350; height: 350; radius: 175; color: "#03151e"; opacity: 0.35; border.color: "#0b566a"; border.width: 1 }
        Rectangle { anchors.centerIn: parent; width: 305; height: 305; radius: 152; color: "transparent"; border.color: "#176d84"; border.width: 1; rotation: root.t * 6 }
        Rectangle { anchors.centerIn: parent; width: 270; height: 270; radius: 135; color: "transparent"; border.color: "#0e4556"; border.width: 2; rotation: -root.t * 10 }
        Rectangle { anchors.centerIn: parent; width: 225; height: 225; radius: 112; color: "transparent"; border.color: "#54f4ff"; border.width: 1; opacity: 0.65 + root.activity * 0.35; rotation: root.t * 18 }

        Repeater {
            model: 16
            Rectangle {
                width: index % 2 === 0 ? 22 : 10; height: 2
                x: 215 + Math.cos(index * Math.PI / 8 + root.t * 0.55) * (index % 2 === 0 ? 178 : 150) - width / 2
                y: 215 + Math.sin(index * Math.PI / 8 + root.t * 0.55) * (index % 2 === 0 ? 178 : 150) - height / 2
                rotation: index * 22.5 + 90
                color: index % 4 === 0 ? "#54f4ff" : "#176d84"; opacity: 0.8
            }
        }

        Rectangle {
            anchors.centerIn: parent; width: 178 + root.activity * 20; height: width; radius: width / 2
            color: "#052433"; border.color: "#35dff0"; border.width: 2; opacity: 0.55
        }
        Rectangle {
            anchors.centerIn: parent; width: 132 + root.activity * 14; height: width; radius: width / 2
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#123d52" }
                GradientStop { position: 0.5; color: "#087b98" }
                GradientStop { position: 1.0; color: "#02121a" }
            }
            border.color: "#7ef8ff"; border.width: 2; opacity: 0.9
        }
        Rectangle {
            anchors.centerIn: parent; width: 86 + root.activity * 10; height: width; radius: width / 2
            color: root.listening ? "#65f9ff" : "#2bb9d3"
            opacity: root.listening || root.speaking ? 0.95 : 0.72
            scale: 1.0 + Math.sin(root.t * 6) * (root.listening || root.speaking ? 0.05 : 0.015)
            Behavior on color { ColorAnimation { duration: 180 } }
        }

        Text {
            anchors.centerIn: parent
            anchors.verticalCenterOffset: -1
            text: "J.A.R.V.I.S."
            color: "#eaffff"
            font.pixelSize: 18
            font.bold: true
            font.letterSpacing: 1.8
            style: Text.Outline
            styleColor: "#087b98"
            opacity: root.listening || root.speaking ? 1.0 : 0.94
            scale: 1.0 + Math.sin(root.t * 5) * (root.listening || root.speaking ? 0.025 : 0.008)
        }

        Text { anchors.horizontalCenter: parent.horizontalCenter; y: 322; text: root.listening ? "LISTENING" : root.speaking ? "SPEAKING" : "SYSTEM READY"; color: root.listening ? "#54f4ff" : "#b9eaf0"; font.pixelSize: 11; font.bold: true; font.letterSpacing: 2 }
        Text { anchors.horizontalCenter: parent.horizontalCenter; y: 342; text: "NEURAL PROCESSING // " + Math.round(root.activity * 100) + "%"; color: "#4fa7b7"; font.pixelSize: 7 }
    }

    Item {
        x: root.width / 2 - 205; y: 126; width: 410; height: 300
        Rectangle { x: 0; y: 0; width: 34; height: 1; color: "#54f4ff" }
        Rectangle { x: 0; y: 0; width: 1; height: 34; color: "#54f4ff" }
        Rectangle { x: width - 34; y: 0; width: 34; height: 1; color: "#54f4ff" }
        Rectangle { x: width - 1; y: 0; width: 1; height: 34; color: "#54f4ff" }
        Rectangle { x: 0; y: height - 1; width: 34; height: 1; color: "#54f4ff" }
        Rectangle { x: 0; y: height - 34; width: 1; height: 34; color: "#54f4ff" }
        Rectangle { x: width - 34; y: height - 1; width: 34; height: 1; color: "#54f4ff" }
        Rectangle { x: width - 1; y: height - 34; width: 1; height: 34; color: "#54f4ff" }
    }

    Rectangle {
        x: 286; y: root.height - 78; width: root.width - 572; height: 54
        color: "#04151e"; border.color: "#0b4251"; border.width: 1
        Text { x: 12; y: 8; text: "COMMAND"; color: "#4fa7b7"; font.pixelSize: 7; font.bold: true }
        Text { x: 12; y: 22; width: parent.width - 24; text: root.commandText; color: "#d8f7fb"; font.pixelSize: 10; elide: Text.ElideRight }
    }
}

Component {
    id: metricComponent
    Item {
        property string label: ""
        property string value: "--"
        width: 220; height: 30
        Text { x: 0; y: 0; text: label; color: "#4fa7b7"; font.pixelSize: 7; font.bold: true }
        Text { x: 0; y: 12; text: value; color: "#d8f7fb"; font.pixelSize: 12; font.bold: true }
        Rectangle { x: 120; y: 15; width: 90; height: 2; color: "#0b3340" }
    }
}

Component {
    id: matrixRowComponent
    Item {
        property string label: ""
        property string value: "--"
        width: 204; height: 12
        Text { text: label; color: "#718f97"; font.pixelSize: 7 }
        Text { anchors.right: parent.right; text: value; color: "#b7dce3"; font.pixelSize: 7; font.bold: true }
    }
}

Component {
    id: deviceRowComponent
    Item {
        property string label: ""
        property string state: "OFFLINE"
        width: 204; height: 18
        Text { x: 10; text: label; color: "#b7dce3"; font.pixelSize: 7; font.bold: true }
        Text { anchors.right: parent.right; text: state; color: "#28ee70"; font.pixelSize: 7; font.bold: true }
        Rectangle { x: 0; y: 17; width: parent.width; height: 1; color: "#092c37" }
    }
}
