import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15

ApplicationWindow {
    id: root
    visible: true
    visibility: Window.Windowed
    width: 1200
    height: 680
    minimumWidth: 1100
    minimumHeight: 640
    title: "J.A.R.V.I.S. — Neural Command Interface"
    // Palette cinematografica blu/ciano ispirata all'interfaccia di J.A.R.V.I.S.
    color: "#030811"

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
    property real gestureZoom: 1.0
    property real gestureTurn: 0.0
    property string gestureMode: "GESTURE CONTROL READY"

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
        if (data.gesture_zoom !== undefined) gestureZoom = Math.max(0.72, Math.min(1.35, Number(data.gesture_zoom)))
        if (data.gesture_turn !== undefined) gestureTurn = Number(data.gesture_turn)
        gestureMode = data.gesture_mode || gestureMode
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
        interval: 33
        running: root.visible
        repeat: true
        onTriggered: root.t += 0.016
    }

    Rectangle { anchors.fill: parent; color: "#030811" }

    // Technical grid
    Repeater {
        model: 15
        Rectangle {
            x: 0
            y: 66 + index * 42
            width: root.width
            height: 1
            color: index % 3 === 0 ? "#0b2840" : "#071b2d"
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
            color: "#092037"
            opacity: 0.48
        }
    }

    // Header: separate fixed-width zones prevent text collisions at all supported sizes.
    Rectangle {
        id: header
        x: 16; y: 12; width: root.width - 32; height: 42
        color: "#071a2b"
        border.color: "#12618a"
        border.width: 1
        Rectangle { x: 0; y: parent.height - 2; width: 300; height: 2; color: "#00cfff" }
        Text {
            x: 16; width: 126; height: parent.height
            verticalAlignment: Text.AlignVCenter
            text: "J.A.R.V.I.S."; color: "#d9f8ff"
            font.pixelSize: 15; font.bold: true
            elide: Text.ElideRight
        }
        Text {
            x: 154; width: 210; height: parent.height
            verticalAlignment: Text.AlignVCenter
            text: "NEURAL COMMAND INTERFACE"; color: "#38c9f4"
            font.pixelSize: 9; font.bold: true
            elide: Text.ElideRight
        }
        Text {
            x: (parent.width - width) / 2; width: 280; height: parent.height
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            text: "●  " + root.stateText
            color: root.listening ? "#00cfff" : "#7ce8ff"
            font.pixelSize: 9; font.bold: true
            elide: Text.ElideRight
        }
        Text {
            anchors.right: parent.right; anchors.rightMargin: 16
            width: 220; height: parent.height
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
            text: "SIMONE  //  " + root.clockText
            color: "#5dbddf"; font.pixelSize: 9
            elide: Text.ElideRight
        }
    }

    // Left telemetry panel
    Rectangle {
        x: 12; y: 66; width: 220; height: root.height - 82
        color: "#061421"; border.color: "#105477"; border.width: 1
        Text { x: 12; y: 11; text: "SYSTEM TELEMETRY"; color: "#d9f8ff"; font.pixelSize: 9; font.bold: true }
        Rectangle { x: 12; y: 29; width: parent.width - 24; height: 1; color: "#0d3852" }

        Repeater {
            model: [ ["CPU LOAD", root.cpuText], ["MEMORY", root.memoryText], ["STORAGE", root.diskText], ["NETWORK", root.networkText] ]
            Item {
                x: 14; y: 46 + index * 45; width: 190; height: 32
                Text { text: modelData[0]; color: "#38c9f4"; font.pixelSize: 7; font.bold: true }
                Text { y: 12; text: modelData[1]; color: "#c8f3ff"; font.pixelSize: 12; font.bold: true }
                Rectangle { x: 108; y: 15; width: 70; height: 2; color: "#0d3852" }
                Rectangle { x: 108; y: 15; width: 70 * Math.min(1, Math.max(0.05, root.activity)); height: 2; color: "#00aee8"; opacity: 0.8 }
            }
        }

        Rectangle { x: 12; y: 206; width: parent.width - 24; height: 108; color: "#081e30"; border.color: "#12618a" }
        Text { x: 22; y: 216; text: "CORE MATRIX"; color: "#38c9f4"; font.pixelSize: 8; font.bold: true }
        Repeater {
            model: [ ["KERNEL", root.kernelText], ["MEMORY", root.memoryState], ["DEVICES", root.deviceText], ["VOICE", root.voiceText] ]
            Item {
                x: 22; y: 241 + index * 19; width: parent.width - 44; height: 14
                Text { text: modelData[0]; color: "#4287a8"; font.pixelSize: 7 }
                Text { anchors.right: parent.right; text: modelData[1]; color: index === 3 && root.listening ? "#00cfff" : "#b8eaff"; font.pixelSize: 7; font.bold: true }
            }
        }

        Rectangle { x: 12; y: 330; width: parent.width - 24; height: 120; color: "#081e30"; border.color: "#12618a" }
        Text { x: 22; y: 340; text: "ACTIVITY VECTOR"; color: "#38c9f4"; font.pixelSize: 8; font.bold: true }
        Repeater {
            model: 24
            Rectangle {
                width: 5
                height: 18 + Math.abs(Math.sin(root.t * 4.0 + index * 0.67)) * (58 * root.activity)
                x: 22 + index * 7
                y: 425 - height
                color: index % 4 === 0 ? "#00cfff" : "#00aee8"
                opacity: 0.35 + root.activity * 0.65
            }
        }
        Rectangle { x: 22; y: 425; width: parent.width - 44; height: 1; color: "#168bb8" }
        Text { x: 22; y: 470; text: "SESSION"; color: "#38c9f4"; font.pixelSize: 8; font.bold: true }
        Text { x: 22; y: 490; text: root.dateText; color: "#b8eaff"; font.pixelSize: 11 }
        Text { x: 22; y: 510; text: "SECURITY      ARMED"; color: "#7ce8ff"; font.pixelSize: 8; font.bold: true }
        Text { x: 22; y: 530; text: "AI ENGINE     READY"; color: "#00cfff"; font.pixelSize: 8; font.bold: true }
        Text { x: 22; y: 550; text: "LINK          LOCAL"; color: "#5dbddf"; font.pixelSize: 8; font.bold: true }
    }

    // Right environment panel
    Rectangle {
        x: root.width - 232; y: 66; width: 220; height: root.height - 82
        color: "#061421"; border.color: "#105477"; border.width: 1
        Text { x: 12; y: 11; text: "ENVIRONMENT / DEVICES"; color: "#d9f8ff"; font.pixelSize: 9; font.bold: true }
        Rectangle { x: 12; y: 29; width: parent.width - 24; height: 1; color: "#0d3852" }
        Text { x: 16; y: 48; text: root.clockText; color: "#d9f8ff"; font.pixelSize: 28; font.bold: true }
        Text { x: 17; y: 80; text: root.dateText; color: "#38c9f4"; font.pixelSize: 9 }

        Rectangle { x: 12; y: 108; width: parent.width - 24; height: 120; color: "#081e30"; border.color: "#12618a" }
        Text { x: 22; y: 118; text: "CONNECTED DEVICES"; color: "#38c9f4"; font.pixelSize: 8; font.bold: true }
        Repeater {
            model: [ ["COMPUTER", "ONLINE"], ["NETWORK", "ONLINE"], ["BLUETOOTH", "READY"] ]
            Item {
                x: 22; y: 145 + index * 24; width: parent.width - 34; height: 18
                Text { x: 10; text: modelData[0]; color: "#b8eaff"; font.pixelSize: 7; font.bold: true }
                Text { anchors.right: parent.right; text: modelData[1]; color: "#7ce8ff"; font.pixelSize: 7; font.bold: true }
                Rectangle { y: 17; width: parent.width; height: 1; color: "#0b3048" }
            }
        }

        Rectangle { x: 12; y: 242; width: parent.width - 24; height: 128; color: "#081e30"; border.color: "#12618a" }
        Text { x: 22; y: 252; text: "VOICE CHANNEL"; color: "#38c9f4"; font.pixelSize: 8; font.bold: true }
        Text { x: 22; y: 278; text: root.voiceDisplay(); color: root.listening ? "#00cfff" : root.speaking ? "#7ce8ff" : "#b8eaff"; font.pixelSize: 13; font.bold: true }
        Rectangle { x: 22; y: 305; width: 164; height: 30; color: "#061421"; border.color: "#105477" }
        Repeater {
            model: 18
            Rectangle {
                width: 5
                height: 4 + Math.abs(Math.sin(root.t * (root.listening ? 10 : root.speaking ? 7 : 3) + index * 0.9)) * (root.listening || root.speaking ? 20 : 5)
                x: 27 + index * 7; y: 320 - height / 2; radius: 2
                color: root.speaking ? "#7ce8ff" : "#00cfff"
            }
        }
        Text { x: 22; y: 348; text: "WAKE WORD: JARVIS"; color: "#4287a8"; font.pixelSize: 8 }

        Rectangle { x: 12; y: 384; width: parent.width - 24; height: parent.height - 398; color: "#081e30"; border.color: "#12618a" }
        Text { x: 22; y: 394; text: "LIVE EVENT STREAM"; color: "#38c9f4"; font.pixelSize: 8; font.bold: true }
        Text { x: 22; y: 420; width: 176; height: parent.height - 440; text: root.eventsText; color: "#5dbddf"; font.pixelSize: 8; wrapMode: Text.Wrap; elide: Text.ElideLeft }
    }

    // Proiettore centrale: energia verticale sospesa sopra un emettitore ellittico,
    // ispirato al reattore del riferimento video (tutto in ciano, senza sfera piena).
    Item {
        id: hologram
        x: (root.width - width) / 2
        y: 70
        width: 360
        height: 390
        property real zoom: root.gestureZoom
        property real gestureTurn: root.gestureTurn

        // Alone verticale morbido: evita il grande disco circolare dietro al nucleo.
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 8
            width: 168 * hologram.zoom
            height: 250 * hologram.zoom
            radius: width / 2
            color: "#00eaff"
            opacity: 0.07 + root.activity * 0.035
        }
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 20
            width: 126 * hologram.zoom
            height: 222 * hologram.zoom
            radius: width / 2
            color: "#5affff"
            opacity: 0.07
        }

        // Colonna di energia luminosa: ovale verticale, con nucleo bianco e
        // sottili fasce interne, non una sfera o una serie di cerchi concentrici.
        Item {
            id: energyCore
            anchors.horizontalCenter: parent.horizontalCenter
            y: 10
            width: 154 * hologram.zoom
            height: 242 * hologram.zoom
            rotation: hologram.gestureTurn

            Rectangle {
                anchors.centerIn: parent
                width: parent.width * 0.96
                height: parent.height * 0.98
                radius: width / 2
                color: "#28faff"
                opacity: 0.12 + root.activity * 0.08
            }
            Rectangle {
                anchors.centerIn: parent
                width: parent.width * 0.76
                height: parent.height * 0.92
                radius: width / 2
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#6affff" }
                    GradientStop { position: 0.18; color: "#19e9f7" }
                    GradientStop { position: 0.48; color: "#008fae" }
                    GradientStop { position: 0.76; color: "#075a7a" }
                    GradientStop { position: 1.0; color: "#8affff" }
                }
                opacity: 0.28
            }

            // Fasce luminose inclinate che danno l'effetto di energia in rotazione.
            Repeater {
                model: 7
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.width * (0.88 - index * 0.075)
                    height: parent.height * (0.78 - index * 0.075)
                    radius: width / 2
                    color: "transparent"
                    border.color: index === 3 ? "#efffff" : "#5bffff"
                    border.width: index === 3 ? 2 : 1
                    opacity: 0.25 + (6 - index) * 0.065
                    rotation: (index % 2 === 0 ? 1 : -1) * (root.t * (8 + index * 2) + index * 17)
                }
            }

            // Filamenti e particelle all'interno della proiezione.
            Repeater {
                model: 13
                Rectangle {
                    width: index % 3 === 0 ? 3 : 2
                    height: 20 + (index % 4) * 11
                    radius: width
                    x: 26 + (index * 19 % 104)
                    y: 18 + (index * 31 % 198)
                    rotation: (index % 2 === 0 ? -1 : 1) * (12 + index * 3)
                    color: index % 3 === 0 ? "#ffffff" : "#9bffff"
                    opacity: 0.22 + (Math.sin(root.t * 3 + index) + 1) * 0.22
                }
            }

            Rectangle {
                anchors.centerIn: parent
                width: parent.width * 0.42
                height: parent.height * 0.43
                radius: width / 2
                color: "#00efff"
                opacity: 0.25
            }
            Rectangle {
                anchors.centerIn: parent
                width: parent.width * 0.27
                height: parent.height * 0.28
                radius: width / 2
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#ffffff" }
                    GradientStop { position: 0.45; color: "#eaffff" }
                    GradientStop { position: 1.0; color: "#49faff" }
                }
                opacity: 0.92
            }
            Rectangle {
                anchors.centerIn: parent
                width: parent.width * 0.12
                height: parent.height * 0.13
                radius: width / 2
                color: "#ffffff"
                opacity: 1.0
            }
        }

        // Anelli prospettici della base: larghi, bassi e separati dal nucleo.
        Item {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 248
            width: 340
            height: 76
            Repeater {
                model: 5
                Rectangle {
                    anchors.centerIn: parent
                    width: parent.width - index * 25
                    height: parent.height - index * 11
                    radius: height / 2
                    color: "transparent"
                    border.color: index === 1 ? "#efffff" : "#00eaff"
                    border.width: index === 1 ? 2 : 1
                    rotation: (index % 2 === 0 ? 1 : -1) * root.t * (2 + index)
                    opacity: 0.82 - index * 0.10
                }
            }
            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                y: 36
                width: 270
                height: 2
                color: "#efffff"
                opacity: 0.72
            }
            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                y: 33
                width: 190
                height: 7
                radius: 3
                color: "#00eaff"
                opacity: 0.22 + root.activity * 0.12
            }
        }

        // Raggio di scansione e particelle circostanti, contenuti nell'area centrale.
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 16 + (Math.sin(root.t * 1.4) + 1) * 102
            width: 226
            height: 1
            color: "#e4fdff"
            opacity: 0.32 + root.activity * 0.28
        }
        Repeater {
            model: 16
            Rectangle {
                width: index % 4 === 0 ? 3 : 2
                height: width
                radius: width / 2
                x: 26 + (index * 43 % 308)
                y: 18 + (index * 37 % 300)
                color: "#9af1ff"
                opacity: 0.18 + (Math.sin(root.t * 2 + index) + 1) * 0.24
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 329
            text: root.listening ? "ARC REACTOR  //  LISTENING" : root.speaking ? "ARC REACTOR  //  ACTIVE" : "ARC REACTOR"
            color: "#b7ffff"
            font.pixelSize: 9
            font.bold: true
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 346
            text: "HOLOGRAPHIC ENERGY CORE  //  " + Math.round(root.activity * 100) + "%"
            color: "#38c9f4"
            font.pixelSize: 7
            font.bold: true
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 363
            width: parent.width
            horizontalAlignment: Text.AlignHCenter
            text: root.gestureMode
            color: "#7ce8ff"
            font.pixelSize: 7
            font.bold: true
            elide: Text.ElideRight
        }
    }

    // Widget dock: quick actions call Jarvis commands asynchronously.
    Rectangle {
        x: root.width - 232
        y: 66
        width: 220
        height: root.height - 148
        color: "#061421"
        border.color: "#105477"
        border.width: 1

        Text { x: 12; y: 10; text: "HOLOGRAPHIC WIDGETS"; color: "#d9f8ff"; font.pixelSize: 9; font.bold: true }
        Rectangle { x: 12; y: 29; width: parent.width - 24; height: 1; color: "#12618a" }

        Rectangle {
            x: 12; y: 40; width: parent.width - 24; height: 58
            color: "#081e30"; border.color: "#12618a"
            Text { x: 9; y: 7; text: "LOCAL TIME"; color: "#38c9f4"; font.pixelSize: 8; font.bold: true }
            Text { x: 9; y: 24; text: root.clockText; color: "#d9f8ff"; font.pixelSize: 16; font.bold: true }
            Text { x: 9; y: 43; text: root.dateText; color: "#5dbddf"; font.pixelSize: 8 }
        }

        Text { x: 12; y: 108; text: "WEATHER / NEWS"; color: "#38c9f4"; font.pixelSize: 8; font.bold: true }
        Button {
            x: 12; y: 126; width: 92; height: 28
            text: "METEO"
            onClicked: bridge.executeCommand("meteo")
            contentItem: Text { text: parent.text; color: "#d9f8ff"; font.pixelSize: 9; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            background: Rectangle { color: "#09273a"; border.color: "#00aee8"; radius: 2 }
        }
        Button {
            x: 112; y: 126; width: 96; height: 28
            text: "NOTIZIE"
            onClicked: bridge.executeCommand("notizie")
            contentItem: Text { text: parent.text; color: "#d9f8ff"; font.pixelSize: 9; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            background: Rectangle { color: "#09273a"; border.color: "#00aee8"; radius: 2 }
        }

        Text { x: 12; y: 164; text: "SCIENTIFIC CALCULATOR"; color: "#38c9f4"; font.pixelSize: 8; font.bold: true }
        TextField {
            id: calcInput
            x: 12; y: 182; width: parent.width - 24; height: 30
            placeholderText: "Es. (12 + 4) * 3"
            color: "#d9f8ff"; placeholderTextColor: "#4287a8"; font.pixelSize: 10
            background: Rectangle { color: "#030811"; border.color: "#12618a" }
        }
        Button {
            x: 12; y: 216; width: parent.width - 24; height: 26
            text: "CALCOLA"
            onClicked: bridge.executeCommand("calcola " + calcInput.text)
            contentItem: Text { text: parent.text; color: "#d9f8ff"; font.pixelSize: 9; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            background: Rectangle { color: "#09273a"; border.color: "#00aee8"; radius: 2 }
        }

        Text { x: 12; y: 251; text: "LOCAL NOTEPAD"; color: "#38c9f4"; font.pixelSize: 8; font.bold: true }
        TextField {
            id: noteInput
            x: 12; y: 269; width: parent.width - 24; height: 30
            placeholderText: "Scrivi una nota..."
            color: "#d9f8ff"; placeholderTextColor: "#4287a8"; font.pixelSize: 10
            background: Rectangle { color: "#030811"; border.color: "#12618a" }
        }
        Button {
            x: 12; y: 303; width: 92; height: 26
            text: "SALVA"
            onClicked: bridge.executeCommand("nota: " + noteInput.text)
            contentItem: Text { text: parent.text; color: "#d9f8ff"; font.pixelSize: 9; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            background: Rectangle { color: "#09273a"; border.color: "#00aee8"; radius: 2 }
        }
        Button {
            x: 112; y: 303; width: 96; height: 26
            text: "LEGGI"
            onClicked: bridge.executeCommand("leggi nota")
            contentItem: Text { text: parent.text; color: "#d9f8ff"; font.pixelSize: 9; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            background: Rectangle { color: "#09273a"; border.color: "#00aee8"; radius: 2 }
        }

        Text { x: 12; y: 340; text: "NETWORK DIAGNOSTICS"; color: "#38c9f4"; font.pixelSize: 8; font.bold: true }
        Button {
            x: 12; y: 358; width: parent.width - 24; height: 28
            text: "TEST VELOCITÀ"
            onClicked: bridge.executeCommand("test velocità rete")
            contentItem: Text { text: parent.text; color: "#d9f8ff"; font.pixelSize: 9; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            background: Rectangle { color: "#09273a"; border.color: "#00aee8"; radius: 2 }
        }
        Rectangle { x: 12; y: 396; width: parent.width - 24; height: 1; color: "#12618a" }
        Text { x: 12; y: 406; text: "GESTURE CONTROL"; color: "#38c9f4"; font.pixelSize: 8; font.bold: true }
        Text { x: 12; y: 424; width: parent.width - 24; text: root.gestureMode; color: "#b8eaff"; font.pixelSize: 9; wrapMode: Text.Wrap }
        Text { x: 12; y: 458; width: parent.width - 24; text: "Pinch: select  •  Swipe: rotate  •  Two hands: zoom"; color: "#4287a8"; font.pixelSize: 8; wrapMode: Text.Wrap }
        Button {
            x: 12; y: 488; width: parent.width - 24; height: 28
            text: "APRI MODELLO 3D"
            onClicked: bridge.executeCommand("apri ologramma 3d")
            contentItem: Text { text: parent.text; color: "#d9f8ff"; font.pixelSize: 9; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            background: Rectangle { color: "#09273a"; border.color: "#00aee8"; radius: 2 }
        }
    }

    // Bottom command/response strip
    Rectangle {
        x: 236; y: root.height - 68; width: root.width - 472; height: 48
        color: "#081e30"
        border.color: "#105477"
        border.width: 1
        Text { x: 12; y: 5; text: "COMMAND"; color: "#38c9f4"; font.pixelSize: 7; font.bold: true }
        Text { x: 12; y: 19; width: parent.width - 24; text: root.commandText; color: "#c8f3ff"; font.pixelSize: 10; elide: Text.ElideRight }
        Rectangle { x: parent.width - 84; y: 8; width: 60; height: 3; color: "#0d3852" }
        Rectangle { x: parent.width - 84; y: 8; width: 60 * root.activity; height: 3; color: "#00cfff" }
    }

    // Decorative corner markers
    Item {
        anchors.fill: parent
        Rectangle { x: 16; y: 12; width: 34; height: 1; color: "#00cfff" }
        Rectangle { x: 16; y: 12; width: 1; height: 34; color: "#00cfff" }
        Rectangle { x: root.width - 50; y: 12; width: 34; height: 1; color: "#00cfff" }
        Rectangle { x: root.width - 17; y: 12; width: 1; height: 34; color: "#00cfff" }
        Rectangle { x: 16; y: root.height - 13; width: 34; height: 1; color: "#00cfff" }
        Rectangle { x: 16; y: root.height - 46; width: 1; height: 34; color: "#00cfff" }
        Rectangle { x: root.width - 50; y: root.height - 13; width: 34; height: 1; color: "#00cfff" }
        Rectangle { x: root.width - 17; y: root.height - 46; width: 1; height: 34; color: "#00cfff" }
    }
}