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

    // Griglia tecnica discreta: separa le zone senza affollare la scena.
    Repeater {
        model: 10
        Rectangle {
            x: 0
            y: 72 + index * 54
            width: root.width
            height: 1
            color: index % 3 === 0 ? "#0b2840" : "#071725"
            opacity: 0.35
        }
    }

    // Header ordinato con tre zone indipendenti.
    Rectangle {
        id: header
        x: 14; y: 12; width: root.width - 28; height: 44
        color: "#071725"
        border.color: "#145477"
        border.width: 1
        Rectangle { x: 0; y: parent.height - 2; width: 260; height: 2; color: "#00cfff" }
        Text {
            x: 14; width: 132; height: parent.height
            verticalAlignment: Text.AlignVCenter
            text: "J.A.R.V.I.S."; color: "#e0faff"
            font.pixelSize: 15; font.bold: true
        }
        Text {
            x: 148; width: 200; height: parent.height
            verticalAlignment: Text.AlignVCenter
            text: "NEURAL INTERFACE"; color: "#42d8f5"
            font.pixelSize: 9; font.bold: true
        }
        Text {
            anchors.centerIn: parent
            width: 240; height: parent.height
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            text: "●  " + root.stateText
            color: "#8af4ff"; font.pixelSize: 9; font.bold: true
            elide: Text.ElideRight
        }
        Text {
            anchors.right: parent.right; anchors.rightMargin: 14
            width: 200; height: parent.height
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
            text: "SIMONE  //  " + root.clockText
            color: "#67cde8"; font.pixelSize: 9
            elide: Text.ElideRight
        }
    }

    // Colonna sinistra unica: dati di sistema raggruppati per categoria.
    Rectangle {
        id: leftPanel
        x: 14; y: 70; width: 204; height: root.height - 86
        color: "#061421"; border.color: "#124762"; border.width: 1
        Text { x: 12; y: 12; text: "SYSTEM STATUS"; color: "#e0faff"; font.pixelSize: 9; font.bold: true }
        Rectangle { x: 12; y: 31; width: parent.width - 24; height: 1; color: "#10405a" }

        Text { x: 12; y: 44; text: "TELEMETRY"; color: "#42d8f5"; font.pixelSize: 8; font.bold: true }
        Repeater {
            model: [["CPU", root.cpuText], ["MEMORY", root.memoryText], ["STORAGE", root.diskText], ["NETWORK", root.networkText]]
            Item {
                x: 12; y: 64 + index * 37; width: parent.width - 24; height: 30
                Text { text: modelData[0]; color: "#5798b2"; font.pixelSize: 7; font.bold: true }
                Text { anchors.right: parent.right; text: modelData[1]; color: "#d0f7ff"; font.pixelSize: 10; font.bold: true }
                Rectangle { y: 19; width: parent.width; height: 2; color: "#0d3045" }
                Rectangle { y: 19; width: parent.width * Math.min(1, Math.max(0.03, Number(modelData[1]) / 100 || 0.03)); height: 2; color: "#00bce8" }
            }
        }

        Rectangle { x: 12; y: 218; width: parent.width - 24; height: 1; color: "#10405a" }
        Text { x: 12; y: 230; text: "CORE MATRIX"; color: "#42d8f5"; font.pixelSize: 8; font.bold: true }
        Repeater {
            model: [["KERNEL", root.kernelText], ["MEMORY", root.memoryState], ["DEVICES", root.deviceText], ["VOICE", root.voiceText]]
            Item {
                x: 12; y: 250 + index * 22; width: parent.width - 24; height: 18
                Text { text: modelData[0]; color: "#5798b2"; font.pixelSize: 7 }
                Text {
                    anchors.right: parent.right; width: 96
                    horizontalAlignment: Text.AlignRight
                    text: modelData[1]; color: index === 3 && root.listening ? "#8af4ff" : "#c5f3ff"
                    font.pixelSize: 7; font.bold: true; elide: Text.ElideRight
                }
            }
        }

        Rectangle { x: 12; y: 348; width: parent.width - 24; height: 1; color: "#10405a" }
        Text { x: 12; y: 360; text: "VOICE CHANNEL"; color: "#42d8f5"; font.pixelSize: 8; font.bold: true }
        Text {
            x: 12; y: 381; text: root.voiceDisplay()
            color: root.listening ? "#00cfff" : root.speaking ? "#a4faff" : "#c5f3ff"
            font.pixelSize: 12; font.bold: true
        }
        Rectangle { x: 12; y: 405; width: parent.width - 24; height: 25; color: "#030d17"; border.color: "#124762" }
        Repeater {
            model: 16
            Rectangle {
                width: 4
                height: 3 + Math.abs(Math.sin(root.t * (root.listening ? 9 : root.speaking ? 7 : 2.5) + index * 0.72)) * (root.listening || root.speaking ? 16 : 3)
                x: 19 + index * 9; y: 417 - height / 2; radius: 1
                color: root.speaking ? "#a4faff" : "#00cfff"
                opacity: 0.45 + root.activity * 0.55
            }
        }
        Text { x: 12; y: 440; text: "WAKE WORD  /  HEY JARVIS"; color: "#5798b2"; font.pixelSize: 7 }

        Rectangle { x: 12; y: 463; width: parent.width - 24; height: 1; color: "#10405a" }
        Text { x: 12; y: 475; text: "SESSION"; color: "#42d8f5"; font.pixelSize: 8; font.bold: true }
        Text { x: 12; y: 494; text: root.dateText; color: "#c5f3ff"; font.pixelSize: 9 }
        Text { x: 12; y: 514; text: "SECURITY  //  ARMED"; color: "#8af4ff"; font.pixelSize: 7; font.bold: true }
        Text { x: 12; y: 534; text: "LOCAL LINK  //  ACTIVE"; color: "#67cde8"; font.pixelSize: 7; font.bold: true }
    }

    // Area centrale ampia: la sfera e' l'elemento visivo dominante.
    Item {
        id: hologram
        x: 230
        y: 70
        width: root.width - 456
        height: root.height - 86
        property real zoom: root.gestureZoom
        property real gestureTurn: root.gestureTurn

        Canvas {
            id: orbCanvas
            anchors.fill: parent
            renderTarget: Canvas.Image
            antialiasing: true

            onPaint: {
                var ctx = getContext("2d");
                var w = width, h = height;
                ctx.clearRect(0, 0, w, h);

                var active = root.hologramActive;
                var mainColor = active ? "#9cfbff" : "#35e8ff";
                var brightColor = active ? "#ffffff" : "#c8fcff";
                var dimColor = active ? "rgba(75,225,255,0.52)" : "rgba(30,170,220,0.42)";
                var cx = w / 2;
                var cy = Math.min(205, h * 0.39);
                var radius = Math.min(137, Math.max(108, (Math.min(w, h) * 0.29))) * hologram.zoom;
                var yaw = root.t * 0.22 + hologram.gestureTurn * Math.PI / 180.0;
                var pitch = -0.20 + Math.sin(root.t * 0.16) * 0.055;

                // Alone atmosferico ampio e diffuso, mantenuto leggero per GPU datate.
                var glow = ctx.createRadialGradient(cx, cy, radius * 0.12, cx, cy, radius * 1.58);
                glow.addColorStop(0.0, "rgba(0,220,255,0.19)");
                glow.addColorStop(0.48, "rgba(0,170,230,0.09)");
                glow.addColorStop(1.0, "rgba(0,0,0,0)");
                ctx.fillStyle = glow;
                ctx.beginPath(); ctx.arc(cx, cy, radius * 1.58, 0, Math.PI * 2); ctx.fill();

                function project(lat, lon) {
                    var x = Math.cos(lat) * Math.cos(lon);
                    var y = Math.sin(lat);
                    var z = Math.cos(lat) * Math.sin(lon);
                    var xr = x * Math.cos(yaw) - z * Math.sin(yaw);
                    var zr = x * Math.sin(yaw) + z * Math.cos(yaw);
                    var yr = y * Math.cos(pitch) - zr * Math.sin(pitch);
                    var zz = y * Math.sin(pitch) + zr * Math.cos(pitch);
                    var perspective = 1.0 / (1.55 - zz * 0.20);
                    return [cx + xr * radius * perspective, cy - yr * radius * perspective, zz];
                }

                // Sfera volumetrica: fasce di latitudine con profondita' e luminosita' differenziate.
                ctx.lineWidth = 1.05;
                for (var li = -5; li <= 5; li++) {
                    var lat = li * Math.PI / 12;
                    ctx.beginPath();
                    for (var j = 0; j <= 64; j++) {
                        var p = project(lat, j * Math.PI * 2 / 64);
                        if (j === 0) ctx.moveTo(p[0], p[1]); else ctx.lineTo(p[0], p[1]);
                    }
                    ctx.strokeStyle = li === 0 ? mainColor : dimColor;
                    ctx.globalAlpha = li === 0 ? 0.95 : (0.38 + 0.045 * (5 - Math.abs(li)));
                    ctx.stroke();
                }

                // Meridiani e linee guida sferiche.
                for (var mi = 0; mi < 14; mi++) {
                    var lon = mi * Math.PI / 14 + yaw * 0.08;
                    ctx.beginPath();
                    for (var k = 0; k <= 44; k++) {
                        var lat2 = -Math.PI / 2 + k * Math.PI / 44;
                        var p2 = project(lat2, lon);
                        if (k === 0) ctx.moveTo(p2[0], p2[1]); else ctx.lineTo(p2[0], p2[1]);
                    }
                    ctx.strokeStyle = mi % 3 === 0 ? brightColor : mainColor;
                    ctx.globalAlpha = mi % 3 === 0 ? 0.75 : 0.43;
                    ctx.lineWidth = mi % 3 === 0 ? 1.15 : 0.75;
                    ctx.stroke();
                }
                ctx.globalAlpha = 1.0;

                // Anelli orbitali sottili dietro la sfera.
                ctx.save();
                ctx.translate(cx, cy);
                ctx.rotate(-0.18 + Math.sin(root.t * 0.12) * 0.035);
                ctx.beginPath();
                ctx.ellipse(0, 0, radius * 1.34, radius * 0.36, 0, 0, Math.PI * 2);
                ctx.strokeStyle = "rgba(45,220,255,0.64)";
                ctx.lineWidth = 1.15;
                ctx.stroke();
                ctx.beginPath();
                ctx.ellipse(0, 0, radius * 1.47, radius * 0.43, 0, 0, Math.PI * 2);
                ctx.strokeStyle = "rgba(32,155,220,0.36)";
                ctx.lineWidth = 0.8;
                ctx.stroke();
                ctx.restore();

                // Nucleo interno sfumato, luminoso ma non opaco/nero.
                var core = ctx.createRadialGradient(cx - radius * 0.23, cy - radius * 0.27, 2, cx, cy, radius * 0.92);
                core.addColorStop(0.0, "rgba(255,255,255,0.92)");
                core.addColorStop(0.10, "rgba(170,252,255,0.52)");
                core.addColorStop(0.34, "rgba(0,195,255,0.16)");
                core.addColorStop(0.72, "rgba(0,90,170,0.045)");
                core.addColorStop(1.0, "rgba(0,0,0,0)");
                ctx.fillStyle = core;
                ctx.beginPath(); ctx.arc(cx, cy, radius * 0.92, 0, Math.PI * 2); ctx.fill();

                // Punti energetici sulla superficie, pochi e ben distribuiti.
                for (var q = 0; q < 12; q++) {
                    var a = root.t * 0.28 + q * Math.PI / 6;
                    var px = cx + Math.cos(a) * radius * 1.10;
                    var py = cy + Math.sin(a) * radius * 0.46;
                    ctx.fillStyle = brightColor;
                    ctx.globalAlpha = 0.42 + 0.28 * Math.sin(root.t * 1.8 + q);
                    ctx.beginPath(); ctx.arc(px, py, q % 3 === 0 ? 2.2 : 1.25, 0, Math.PI * 2); ctx.fill();
                }
                ctx.globalAlpha = 1.0;

                // Piattaforma olografica sotto la sfera.
                ctx.beginPath();
                ctx.ellipse(cx, cy + radius * 1.10, radius * 1.08, radius * 0.19, 0, 0, Math.PI * 2);
                ctx.strokeStyle = "rgba(53,232,255,0.76)";
                ctx.lineWidth = 1.3; ctx.stroke();
                ctx.beginPath();
                ctx.ellipse(cx, cy + radius * 1.10, radius * 0.75, radius * 0.105, 0, 0, Math.PI * 2);
                ctx.strokeStyle = "rgba(200,252,255,0.76)";
                ctx.lineWidth = 0.9; ctx.stroke();

                // Etichette allineate al centro e distanziate dal nucleo.
                ctx.textAlign = "center";
                ctx.fillStyle = "#d8fcff";
                ctx.font = "bold 10px sans-serif";
                ctx.fillText(root.listening ? "J.A.R.V.I.S.  /  LISTENING" : root.speaking ? "J.A.R.V.I.S.  /  SPEAKING" : "J.A.R.V.I.S.  /  NEURAL CORE", cx, Math.min(h - 104, cy + radius * 1.52));
                ctx.fillStyle = "#52cce8";
                ctx.font = "8px sans-serif";
                ctx.fillText("ENERGY  " + Math.round(root.activity * 100) + "%", cx, Math.min(h - 88, cy + radius * 1.52 + 17));
                ctx.fillStyle = "#2b718e";
                ctx.font = "7px sans-serif";
                ctx.fillText(root.gestureMode, cx, Math.min(h - 72, cy + radius * 1.52 + 32));
            }
        }

        // 24 FPS: piu' adatto al Mac 2010 rispetto a un ridisegno continuo a 30 FPS.
        Timer {
            interval: 42
            repeat: true
            running: root.visible
            onTriggered: orbCanvas.requestPaint()
        }
    }

    // Colonna destra: strumenti in gruppi coerenti e con spazi regolari.
    Rectangle {
        id: rightPanel
        x: root.width - 218; y: 70; width: 204; height: root.height - 86
        color: "#061421"; border.color: "#124762"; border.width: 1
        Text { x: 12; y: 12; text: "QUICK TOOLS"; color: "#e0faff"; font.pixelSize: 9; font.bold: true }
        Rectangle { x: 12; y: 31; width: parent.width - 24; height: 1; color: "#10405a" }

        Rectangle {
            x: 12; y: 43; width: parent.width - 24; height: 56
            color: "#081e30"; border.color: "#124762"
            Text { x: 9; y: 7; text: "LOCAL TIME"; color: "#42d8f5"; font.pixelSize: 7; font.bold: true }
            Text { x: 9; y: 22; text: root.clockText; color: "#e0faff"; font.pixelSize: 17; font.bold: true }
            Text { anchors.right: parent.right; anchors.rightMargin: 8; y: 29; text: root.dateText; color: "#67cde8"; font.pixelSize: 7 }
        }

        Text { x: 12; y: 112; text: "WEATHER / NEWS"; color: "#42d8f5"; font.pixelSize: 8; font.bold: true }
        Button {
            x: 12; y: 131; width: 86; height: 28; text: "METEO"
            onClicked: bridge.executeCommand("meteo")
            contentItem: Text { text: parent.text; color: "#d9f8ff"; font.pixelSize: 9; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            background: Rectangle { color: "#09273a"; border.color: "#00aee8"; radius: 2 }
        }
        Button {
            x: 104; y: 131; width: 86; height: 28; text: "NOTIZIE"
            onClicked: bridge.executeCommand("notizie")
            contentItem: Text { text: parent.text; color: "#d9f8ff"; font.pixelSize: 9; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            background: Rectangle { color: "#09273a"; border.color: "#00aee8"; radius: 2 }
        }

        Rectangle { x: 12; y: 172; width: parent.width - 24; height: 1; color: "#10405a" }
        Text { x: 12; y: 184; text: "SCIENTIFIC CALCULATOR"; color: "#42d8f5"; font.pixelSize: 8; font.bold: true }
        TextField {
            id: calcInput
            x: 12; y: 203; width: parent.width - 24; height: 30
            placeholderText: "Es. (12 + 4) * 3"
            color: "#d9f8ff"; placeholderTextColor: "#4287a8"; font.pixelSize: 10
            background: Rectangle { color: "#030811"; border.color: "#12618a" }
        }
        Button {
            x: 12; y: 238; width: parent.width - 24; height: 27; text: "CALCOLA"
            onClicked: bridge.executeCommand("calcola " + calcInput.text)
            contentItem: Text { text: parent.text; color: "#d9f8ff"; font.pixelSize: 9; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            background: Rectangle { color: "#09273a"; border.color: "#00aee8"; radius: 2 }
        }

        Text { x: 12; y: 278; text: "LOCAL NOTEPAD"; color: "#42d8f5"; font.pixelSize: 8; font.bold: true }
        TextField {
            id: noteInput
            x: 12; y: 297; width: parent.width - 24; height: 30
            placeholderText: "Scrivi una nota..."
            color: "#d9f8ff"; placeholderTextColor: "#4287a8"; font.pixelSize: 10
            background: Rectangle { color: "#030811"; border.color: "#12618a" }
        }
        Button {
            x: 12; y: 332; width: 86; height: 27; text: "SALVA"
            onClicked: bridge.executeCommand("nota: " + noteInput.text)
            contentItem: Text { text: parent.text; color: "#d9f8ff"; font.pixelSize: 9; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            background: Rectangle { color: "#09273a"; border.color: "#00aee8"; radius: 2 }
        }
        Button {
            x: 104; y: 332; width: 86; height: 27; text: "LEGGI"
            onClicked: bridge.executeCommand("leggi nota")
            contentItem: Text { text: parent.text; color: "#d9f8ff"; font.pixelSize: 9; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            background: Rectangle { color: "#09273a"; border.color: "#00aee8"; radius: 2 }
        }

        Rectangle { x: 12; y: 373; width: parent.width - 24; height: 1; color: "#10405a" }
        Text { x: 12; y: 385; text: "GESTURE CONTROL"; color: "#42d8f5"; font.pixelSize: 8; font.bold: true }
        Text { x: 12; y: 405; width: parent.width - 24; text: root.gestureMode; color: "#c5f3ff"; font.pixelSize: 8; wrapMode: Text.Wrap; elide: Text.ElideRight }
        Text { x: 12; y: 443; width: parent.width - 24; text: "Pinch: select   /   Swipe: rotate   /   Two hands: zoom"; color: "#5798b2"; font.pixelSize: 7; wrapMode: Text.Wrap }
        Rectangle { x: 12; y: 478; width: parent.width - 24; height: 1; color: "#10405a" }
        Text {
            x: 12; y: 490; width: parent.width - 24; height: 30
            text: "CORE ORB-01  /  INTEGRATED"
            color: "#8af4ff"; font.pixelSize: 8; font.bold: true
            horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        Text { x: 12; y: 530; width: parent.width - 24; text: "LOCAL SYSTEM  •  SECURE LINK"; color: "#2b718e"; font.pixelSize: 7; horizontalAlignment: Text.AlignHCenter }
    }

    // Fascia comandi dedicata, sotto la sfera e senza coprire le colonne.
    Rectangle {
        x: 230; y: root.height - 65; width: root.width - 456; height: 49
        color: "#071725"; border.color: "#124762"; border.width: 1
        Rectangle { x: 0; y: 0; width: 3; height: parent.height; color: "#00cfff" }
        Text { x: 14; y: 6; text: "LAST COMMAND"; color: "#42d8f5"; font.pixelSize: 7; font.bold: true }
        Text { x: 14; y: 22; width: parent.width - 28; text: root.commandText; color: "#d0f7ff"; font.pixelSize: 10; elide: Text.ElideRight }
        Rectangle { x: parent.width - 78; y: 8; width: 58; height: 3; color: "#0d3852" }
        Rectangle { x: parent.width - 78; y: 8; width: 58 * root.activity; height: 3; color: "#00cfff" }
    }

    // Indicatori d'angolo minimali.
    Item {
        anchors.fill: parent
        Rectangle { x: 14; y: 12; width: 30; height: 1; color: "#00cfff" }
        Rectangle { x: 14; y: 12; width: 1; height: 30; color: "#00cfff" }
        Rectangle { x: root.width - 44; y: 12; width: 30; height: 1; color: "#00cfff" }
        Rectangle { x: root.width - 15; y: 12; width: 1; height: 30; color: "#00cfff" }
        Rectangle { x: 14; y: root.height - 13; width: 30; height: 1; color: "#00cfff" }
        Rectangle { x: 14; y: root.height - 42; width: 1; height: 30; color: "#00cfff" }
        Rectangle { x: root.width - 44; y: root.height - 13; width: 30; height: 1; color: "#00cfff" }
        Rectangle { x: root.width - 15; y: root.height - 42; width: 1; height: 30; color: "#00cfff" }
    }
}
