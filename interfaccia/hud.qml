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
    minimumHeight: 600
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
    property bool hologramActive: false

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
        hologramActive = listening || speaking
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
        interval: 50
        running: root.visible
        repeat: true
        onTriggered: root.t += 0.05
    }

    Rectangle { anchors.fill: parent; color: "#030811" }

    // Technical grid
    Repeater {
        model: 12
        Rectangle {
            x: 0
            y: 66 + index * 48
            width: root.width
            height: 1
            color: index % 3 === 0 ? "#0b2840" : "#071b2d"
            opacity: 0.55
        }
    }
    Repeater {
        model: 10
        Rectangle {
            x: 24 + index * 98
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
            model: 14
            Rectangle {
                width: 5
                height: 18 + ((index * 17) % 58) * root.activity
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
            model: 10
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

    // Nucleo sferico 3D integrato direttamente nell'HUD Qt Quick.
    // Canvas leggero, senza browser esterno, WebGL o librerie aggiuntive.
    Item {
        id: hologram
        x: (root.width - width) / 2
        y: 70
        width: 360
        height: 390
        property real zoom: root.gestureZoom
        property real gestureTurn: root.gestureTurn

        Canvas {
            id: orbCanvas
            anchors.fill: parent
            onPaint: {
                var ctx = getContext("2d");
                var w = width, h = height;
                ctx.clearRect(0, 0, w, h);

                var active = root.hologramActive;
                var mainColor = active ? "#ffad42" : "#48fff2";
                var brightColor = active ? "#fff0cf" : "#d7ffff";
                var yaw = root.t * 0.24 + hologram.gestureTurn * Math.PI / 180.0;
                var pitch = -0.22 + Math.sin(root.t * 0.19) * 0.08;
                var radius = 82 * hologram.zoom;
                var cx = w / 2;
                var cy = 139;

                // Alone morbido e nucleo centrale: gradienti semplici, senza mesh pesanti.
                var glow = ctx.createRadialGradient(cx, cy, 3, cx, cy, radius * 1.25);
                glow.addColorStop(0.0, active ? "rgba(255,138,0,0.28)" : "rgba(0,220,255,0.20)");
                glow.addColorStop(0.55, active ? "rgba(255,138,0,0.07)" : "rgba(0,220,255,0.06)");
                glow.addColorStop(1.0, "rgba(0,0,0,0)");
                ctx.fillStyle = glow;
                ctx.beginPath();
                ctx.arc(cx, cy, radius * 1.25, 0, Math.PI * 2);
                ctx.fill();

                function project(lat, lon) {
                    var x = Math.cos(lat) * Math.cos(lon);
                    var y = Math.sin(lat);
                    var z = Math.cos(lat) * Math.sin(lon);
                    var xr = x * Math.cos(yaw) - z * Math.sin(yaw);
                    var zr = x * Math.sin(yaw) + z * Math.cos(yaw);
                    var yr = y * Math.cos(pitch) - zr * Math.sin(pitch);
                    var zz = y * Math.sin(pitch) + zr * Math.cos(pitch);
                    var perspective = 1.0 / (1.65 - zz * 0.25);
                    return [cx + xr * radius * perspective, cy - yr * radius * perspective, zz];
                }

                // Paralleli: pochi segmenti e una sola traccia per anello.
                ctx.lineWidth = 1;
                for (var li = -3; li <= 3; li++) {
                    var lat = li * Math.PI / 8;
                    ctx.beginPath();
                    for (var j = 0; j <= 36; j++) {
                        var p = project(lat, j * Math.PI * 2 / 36);
                        if (j === 0) ctx.moveTo(p[0], p[1]); else ctx.lineTo(p[0], p[1]);
                    }
                    ctx.strokeStyle = li === 0 ? mainColor : (active ? "rgba(255,173,66,0.58)" : "rgba(72,255,242,0.58)");
                    ctx.globalAlpha = li === 0 ? 0.95 : 0.64;
                    ctx.stroke();
                }

                // Meridiani: wireframe sferico leggibile, non una pila di forme geometriche.
                for (var mi = 0; mi < 10; mi++) {
                    var lon = mi * Math.PI / 10 + yaw * 0.08;
                    ctx.beginPath();
                    for (var k = 0; k <= 28; k++) {
                        var lat2 = -Math.PI / 2 + k * Math.PI / 28;
                        var p2 = project(lat2, lon);
                        if (k === 0) ctx.moveTo(p2[0], p2[1]); else ctx.lineTo(p2[0], p2[1]);
                    }
                    ctx.strokeStyle = mi % 3 === 0 ? brightColor : mainColor;
                    ctx.globalAlpha = mi % 3 === 0 ? 0.85 : 0.48;
                    ctx.stroke();
                }
                ctx.globalAlpha = 1.0;

                // Nucleo luminoso centrale e piccoli punti di riferimento.
                var core = ctx.createRadialGradient(cx - 8, cy - 10, 2, cx, cy, radius * 0.52);
                core.addColorStop(0, "#ffffff");
                core.addColorStop(0.22, brightColor);
                core.addColorStop(0.58, active ? "rgba(255,138,0,0.42)" : "rgba(0,180,230,0.35)");
                core.addColorStop(1, "rgba(0,0,0,0)");
                ctx.fillStyle = core;
                ctx.beginPath();
                ctx.arc(cx, cy, radius * 0.52, 0, Math.PI * 2);
                ctx.fill();

                for (var q = 0; q < 8; q++) {
                    var a = root.t * 0.45 + q * Math.PI / 4;
                    var px = cx + Math.cos(a) * radius * 1.12;
                    var py = cy + Math.sin(a) * radius * 1.12;
                    ctx.fillStyle = brightColor;
                    ctx.globalAlpha = 0.35 + 0.25 * Math.sin(root.t * 2 + q);
                    ctx.beginPath();
                    ctx.arc(px, py, q % 2 === 0 ? 2 : 1.3, 0, Math.PI * 2);
                    ctx.fill();
                }
                ctx.globalAlpha = 1.0;

                // Base prospettica sottile, separata dalla sfera.
                ctx.beginPath();
                ctx.ellipse(cx, 257, 112 * hologram.zoom, 20 * hologram.zoom, 0, 0, Math.PI * 2);
                ctx.strokeStyle = mainColor;
                ctx.lineWidth = 1.3;
                ctx.globalAlpha = 0.72;
                ctx.stroke();
                ctx.beginPath();
                ctx.ellipse(cx, 257, 78 * hologram.zoom, 11 * hologram.zoom, 0, 0, Math.PI * 2);
                ctx.strokeStyle = brightColor;
                ctx.globalAlpha = 0.82;
                ctx.stroke();
                ctx.globalAlpha = 1.0;

                ctx.fillStyle = "#b7ffff";
                ctx.font = "bold 9px sans-serif";
                ctx.textAlign = "center";
                ctx.fillText(root.listening ? "JARVIS CORE // LISTENING" : root.speaking ? "JARVIS CORE // ACTIVE" : "J.A.R.V.I.S. // HOLOGRAPHIC CORE", cx, 300);
                ctx.fillStyle = "#38c9f4";
                ctx.font = "8px sans-serif";
                ctx.fillText("ENERGY " + Math.round(root.activity * 100) + "%  //  " + root.gestureMode, cx, 316);
            }
        }

        // 30 FPS: animazione fluida con carico limitato anche su Mac meno recenti.
        Timer {
            interval: 33
            repeat: true
            running: root.visible
            onTriggered: orbCanvas.requestPaint()
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
        Text {
            x: 12; y: 488; width: parent.width - 24; height: 28
            text: "CORE ORB-01 // INTEGRATO NELL'HUD"
            color: "#7ce8ff"; font.pixelSize: 8; font.bold: true
            horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
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