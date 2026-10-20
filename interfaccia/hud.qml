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

    // Proiettore centrale ispirato al riferimento: reattore verticale sospeso
    // sopra una piattaforma di anelli ellittici prospettici.
    Item {
        id: hologram
        x: (root.width - width) / 2
        y: 72
        width: 360
        height: 390
        property real zoom: 1.0
        property real gestureTurn: 0

        // Luce volumetrica dietro la proiezione.
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 30
            width: 188
            height: 220
            radius: width / 2
            color: "#00eaff"
            opacity: 0.10 + root.activity * 0.05
        }
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 42
            width: 150
            height: 190
            radius: width / 2
            color: "#72ffff"
            opacity: 0.09
        }

        // Reattore sospeso: forma ovale verticale con bordo luminoso e nucleo
        // bianco molto intenso, non una palla né un cilindro pieno.
        Item {
            id: energyCore
            anchors.horizontalCenter: parent.horizontalCenter
            y: 28
            width: 164
            height: 222
            rotation: hologram.gestureTurn

            Rectangle {
                anchors.centerIn: parent
                width: 150
                height: 210
                radius: width / 2
                color: "#00eaff"
                opacity: 0.16 + root.activity * 0.08
            }
            Rectangle {
                anchors.centerIn: parent
                width: 132
                height: 194
                radius: width / 2
                color: "transparent"
                border.color: "#4effff"
                border.width: 3
                opacity: 0.82
            }
            Rectangle {
                anchors.centerIn: parent
                width: 112
                height: 174
                radius: width / 2
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#26faff" }
                    GradientStop { position: 0.22; color: "#0adce9" }
                    GradientStop { position: 0.50; color: "#087b9b" }
                    GradientStop { position: 0.78; color: "#0acfe0" }
                    GradientStop { position: 1.0; color: "#a1ffff" }
                }
                opacity: 0.42
            }

            // Anelli interni separati: la rotazione dà profondità senza riempire
            // tutta la forma con cerchi sovrapposti.
            Repeater {
                model: 5
                Rectangle {
                    anchors.centerIn: parent
                    width: 102 - index * 13
                    height: 158 - index * 21
                    radius: width / 2
                    color: "transparent"
                    border.color: index === 2 ? "#ffffff" : "#9affff"
                    border.width: index === 2 ? 2 : 1
                    opacity: 0.55 + (4 - index) * 0.08
                    rotation: root.t * (index % 2 === 0 ? 9 : -12) + index * 18
                }
            }

            // Piccoli settori tecnici lungo il perimetro dell'ellisse.
            Repeater {
                model: 24
                Item {
                    anchors.fill: parent
                    rotation: index * 15 + root.t * 3
                    Rectangle {
                        anchors.horizontalCenter: parent.horizontalCenter
                        y: 12
                        width: index % 3 === 0 ? 3 : 1
                        height: index % 3 === 0 ? 12 : 6
                        color: index % 3 === 0 ? "#ffffff" : "#8cffff"
                        opacity: 0.85
                    }
                }
            }

            // Centro ottico brillante con alone.
            Rectangle {
                anchors.centerIn: parent
                width: 78
                height: 92
                radius: width / 2
                color: "#00f4ff"
                opacity: 0.38
            }
            Rectangle {
                anchors.centerIn: parent
                width: 52
                height: 66
                radius: width / 2
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#ffffff" }
                    GradientStop { position: 0.45; color: "#f5ffff" }
                    GradientStop { position: 1.0; color: "#72ffff" }
                }
                opacity: 0.98
            }
            Rectangle {
                anchors.centerIn: parent
                width: 25
                height: 34
                radius: width / 2
                color: "#ffffff"
            }
        }

        // Raggi sottili tra il nucleo sospeso e la base di proiezione.
        Repeater {
            model: 9
            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                y: 230 + index * 2
                width: 1
                height: 18
                color: "#7affff"
                opacity: 0.22 - index * 0.015
            }
        }

        // Base piatta e larga, vista in prospettiva: è l'elemento chiave
        // del riferimento video, con due anelli ciano molto luminosi.
        Item {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 248
            width: 352
            height: 88
            Repeater {
                model: 6
                Rectangle {
                    anchors.centerIn: parent
                    width: 346 - index * 26
                    height: 72 - index * 10
                    radius: height / 2
                    color: "transparent"
                    border.color: index === 1 ? "#dfffff" : "#00efff"
                    border.width: index === 1 ? 3 : 1
                    rotation: (index % 2 === 0 ? 1 : -1) * root.t * (1.5 + index)
                    opacity: 0.95 - index * 0.11
                }
            }
            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                y: 34
                width: 320
                height: 3
                color: "#eaffff"
                opacity: 0.85
            }
            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                y: 30
                width: 240
                height: 10
                radius: 5
                color: "#00eaff"
                opacity: 0.22 + root.activity * 0.18
            }
            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                y: 44
                width: 210
                height: 1
                color: "#7affff"
                opacity: 0.65
            }
        }

        // Scansione verticale e particelle luminose.
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 32 + (Math.sin(root.t * 1.4) + 1) * 91
            width: 220
            height: 1
            color: "#efffff"
            opacity: 0.45 + root.activity * 0.3
        }
        Repeater {
            model: 18
            Rectangle {
                width: index % 4 === 0 ? 3 : 2
                height: width
                radius: width / 2
                x: 20 + (index * 43 % 320)
                y: 24 + (index * 37 % 310)
                color: "#b5ffff"
                opacity: 0.18 + (Math.sin(root.t * 2.2 + index) + 1) * 0.25
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 342
            text: root.listening ? "ARC REACTOR  //  LISTENING" : root.speaking ? "ARC REACTOR  //  ACTIVE" : "ARC REACTOR"
            color: "#b7ffff"
            font.pixelSize: 9
            font.bold: true
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 358
            text: "HOLOGRAPHIC PROJECTION  //  " + Math.round(root.activity * 100) + "%"
            color: "#38c9f4"
            font.pixelSize: 7
            font.bold: true
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