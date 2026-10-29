import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15

ApplicationWindow {
    id: root
    visible: true
    visibility: Window.Windowed
    width: 1440
    height: 810
    minimumWidth: 1100
    minimumHeight: 650
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

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#020711" }
            GradientStop { position: 0.52; color: "#041326" }
            GradientStop { position: 1.0; color: "#020711" }
        }
    }

    // Bagliore laterale leggero, senza modificare il renderer della sfera.
    Rectangle {
        x: 0; y: 76; width: root.width; height: root.height - 150
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#092d4a" }
            GradientStop { position: 0.24; color: "#030b17" }
            GradientStop { position: 0.76; color: "#030b17" }
            GradientStop { position: 1.0; color: "#092d4a" }
        }
        opacity: 0.28
    }

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
        color: "#071a2c"
        border.color: "#00aee8"
        border.width: 1
        Rectangle { x: 0; y: 0; width: parent.width * 0.30; height: 3; color: "#42eaff" }
        Rectangle { x: parent.width * 0.67; y: parent.height - 3; width: parent.width * 0.33; height: 3; color: "#00cfff" }
        Rectangle { x: 10; y: 8; width: 22; height: 2; color: "#00cfff"; rotation: -35 }
        Rectangle { x: parent.width - 31; y: parent.height - 10; width: 22; height: 2; color: "#00cfff"; rotation: -35 }
        Text {
            x: 24; width: 130; height: parent.height
            verticalAlignment: Text.AlignVCenter
            text: "‹‹   J.A.R.V.I.S."; color: "#e0faff"
            font.pixelSize: 14; font.bold: true
        }
        Text {
            anchors.centerIn: parent
            width: Math.min(500, parent.width * 0.48); height: parent.height
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            text: "J.A.R.V.I.S. — NEURAL COMMAND INTERFACE"
            color: "#b9f8ff"; font.pixelSize: 12; font.bold: true
            elide: Text.ElideRight
        }
        Text {
            anchors.right: parent.right; anchors.rightMargin: 18
            width: 220; height: parent.height
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
            text: "SIMONE  //  " + root.clockText + "   ››"
            color: "#67eaff"; font.pixelSize: 10; font.bold: true
            elide: Text.ElideRight
        }
    }

    // Indicatore di stato centrale, sopra il nucleo.
    Rectangle {
        x: (root.width - 230) / 2; y: 105; width: 230; height: 28
        color: "#061a2a"; border.color: "#087aa7"; border.width: 1
        Rectangle { x: 12; y: 10; width: 8; height: 8; radius: 4; color: root.speaking ? "#ffffff" : root.listening ? "#55f7ff" : "#00eaff" }
        Text { anchors.fill: parent; anchors.leftMargin: 28; anchors.rightMargin: 8; verticalAlignment: Text.AlignVCenter; text: root.stateText; color: "#b9f8ff"; font.pixelSize: 10; font.bold: true; elide: Text.ElideRight }
    }

    // Pannello laterale sinistro in stile reference.
    Rectangle {
        id: leftPanel
        x: 22; y: root.height * 0.405; width: 265; height: 190
        color: "#040d19"; border.color: "#00cfff"; border.width: 1
        Rectangle { x: 0; y: 0; width: 90; height: 3; color: "#00eaff" }
        Rectangle { x: 0; y: 0; width: 3; height: 30; color: "#00eaff" }
        Rectangle { x: 0; y: parent.height - 3; width: 56; height: 3; color: "#00eaff" }
        Rectangle { x: parent.width - 3; y: parent.height - 30; width: 3; height: 30; color: "#087aa7" }
        Rectangle { x: 0; y: 0; width: 3; height: 45; color: "#00cfff" }
        Text { x: 16; y: 14; text: "STATO SISTEMA"; color: "#00dfff"; font.pixelSize: 15; font.bold: true }
        Rectangle { x: 16; y: 42; width: parent.width - 32; height: 1; color: "#087aa7" }
        Text { x: 16; y: 56; text: "MEMORIA"; color: "#62b8d5"; font.pixelSize: 9; font.bold: true }
        Text { x: parent.width - 116; y: 55; width: 98; horizontalAlignment: Text.AlignRight; text: root.memoryState; color: "#b9f8ff"; font.pixelSize: 10; font.bold: true; elide: Text.ElideRight }
        Rectangle { x: 16; y: 75; width: parent.width - 32; height: 3; color: "#102a3c" }
        Rectangle { x: 16; y: 75; width: (parent.width - 32) * 0.82; height: 3; color: "#00cfff" }
        Text { x: 16; y: 88; text: "RETE"; color: "#62b8d5"; font.pixelSize: 9; font.bold: true }
        Text { x: 80; y: 87; width: parent.width - 98; text: root.networkText; color: "#8ceeff"; font.pixelSize: 10; elide: Text.ElideRight }
        Text { x: 16; y: 111; text: "DISPOSITIVI"; color: "#62b8d5"; font.pixelSize: 9; font.bold: true }
        Text { x: 105; y: 110; width: parent.width - 122; text: root.deviceText; color: "#8ceeff"; font.pixelSize: 10; elide: Text.ElideRight }
        Text { x: 16; y: 135; text: "CPU"; color: "#62b8d5"; font.pixelSize: 9; font.bold: true }
        Text { x: 58; y: 134; text: root.cpuText; color: "#8ceeff"; font.pixelSize: 10 }
        Text { x: 124; y: 135; text: "RAM"; color: "#62b8d5"; font.pixelSize: 9; font.bold: true }
        Text { x: 166; y: 134; width: parent.width - 180; text: root.memoryText; color: "#8ceeff"; font.pixelSize: 10; elide: Text.ElideRight }
        Text { x: 16; y: 159; text: "KERNEL"; color: "#62b8d5"; font.pixelSize: 9; font.bold: true }
        Text { x: 76; y: 158; width: parent.width - 92; text: root.kernelText; color: "#56cde9"; font.pixelSize: 10; elide: Text.ElideRight }
    }

    // Meteo e accesso ai comandi in alto a sinistra.
    Rectangle {
        x: 22; y: 98; width: 310; height: 112
        color: "#050f1d"; border.color: "#00cfff"; border.width: 1
        Rectangle { x: 0; y: 0; width: 76; height: 3; color: "#00eaff" }
        Text { x: 16; y: 12; text: "METEO  /  AMBIENTE"; color: "#00dfff"; font.pixelSize: 12; font.bold: true }
        Text { x: 16; y: 39; text: "DATI IN ATTESA DI RICHIESTA"; color: "#8ceeff"; font.pixelSize: 9; font.bold: true }
        Text { x: 16; y: 56; text: "Chiedi a Jarvis le condizioni locali"; color: "#62b8d5"; font.pixelSize: 10 }
        Button {
            x: 16; y: 68; width: 88; height: 28; text: "METEO"
            onClicked: bridge.executeCommand("meteo")
            contentItem: Text { text: parent.text; color: "#d9f8ff"; font.pixelSize: 10; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            background: Rectangle { color: "#08263d"; border.color: "#00cfff"; radius: 2 }
        }
        Button {
            x: 112; y: 68; width: 100; height: 28; text: "NOTIZIE"
            onClicked: bridge.executeCommand("notizie")
            contentItem: Text { text: parent.text; color: "#d9f8ff"; font.pixelSize: 10; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
            background: Rectangle { color: "#08263d"; border.color: "#00cfff"; radius: 2 }
        }
    }

    // Orologio in alto a destra.
    Rectangle {
        x: root.width - 287; y: 98; width: 265; height: 112
        color: "#050f1d"; border.color: "#00cfff"; border.width: 1
        Rectangle { x: parent.width - 76; y: 0; width: 76; height: 3; color: "#00eaff" }
        Rectangle { x: 18; y: 32; width: 42; height: 42; radius: 21; color: "transparent"; border.color: "#00cfff"; border.width: 2 }
        Rectangle { x: 38; y: 39; width: 2; height: 14; color: "#00eaff"; transform: Rotation { origin.x: 1; origin.y: 14; angle: 0 } }
        Rectangle { x: 38; y: 51; width: 13; height: 2; color: "#00eaff" }
        Text { x: 76; y: 12; text: "ORA"; color: "#00dfff"; font.pixelSize: 13; font.bold: true }
        Text { x: 76; y: 34; text: root.clockText; color: "#e0faff"; font.pixelSize: 24; font.bold: true }
        Text { x: 76; y: 75; text: root.dateText; color: "#67cde8"; font.pixelSize: 11 }
    }

    // Area centrale ampia: la sfera e' l'elemento visivo dominante.
    Item {
        id: hologram
        x: 332
        y: 145
        width: root.width - 664
        height: root.height - 290
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
                var cy = h * 0.48;
                var radius = Math.min(260, Math.max(200, (Math.min(w, h) * 0.47))) * hologram.zoom;
                var yaw = root.t * 0.22 + hologram.gestureTurn * Math.PI / 180.0;
                var pitch = -0.20 + Math.sin(root.t * 0.16) * 0.055;

                // Alone atmosferico ampio e diffuso, mantenuto leggero per GPU datate.
                var glow = ctx.createRadialGradient(cx, cy, radius * 0.12, cx, cy, radius * 1.58);
                glow.addColorStop(0.0, "rgba(0,235,255,0.25)");
                glow.addColorStop(0.42, "rgba(0,185,255,0.13)");
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

                // Alone volumetrico molto leggero dietro la nuvola, non una sfera piena.
                var pulse = 1.0 + 0.025 * Math.sin(root.t * 1.4);
                var aura = ctx.createRadialGradient(
                    cx - radius * 0.22, cy - radius * 0.27, radius * 0.04,
                    cx, cy, radius * 1.05 * pulse
                );
                aura.addColorStop(0.0, "rgba(65,235,255,0.15)");
                aura.addColorStop(0.48, "rgba(0,170,255,0.075)");
                aura.addColorStop(0.82, "rgba(0,110,210,0.025)");
                aura.addColorStop(1.0, "rgba(0,0,0,0)");
                ctx.fillStyle = aura;
                ctx.beginPath();
                ctx.arc(cx, cy, radius * 1.05 * pulse, 0, Math.PI * 2);
                ctx.fill();

                // Sfera 3D a punti: spirale di Fibonacci per una distribuzione uniforme.
                // Il numero resta moderato per mantenere fluido il MacBook Pro meno recente.
                var pointCount = 760;
                var goldenAngle = Math.PI * (3.0 - Math.sqrt(5.0));
                var points = [];
                for (var pi = 0; pi < pointCount; pi++) {
                    var ny = 1.0 - 2.0 * (pi + 0.5) / pointCount;
                    var latP = Math.asin(ny);
                    var lonP = pi * goldenAngle;
                    var p3 = project(latP, lonP);
                    points.push({ x: p3[0], y: p3[1], z: p3[2], id: pi });
                }

                // Prima il retro, poi la superficie frontale: la profondità risulta più credibile.
                points.sort(function(a, b) { return a.z - b.z; });
                for (var pj = 0; pj < points.length; pj++) {
                    var point = points[pj];
                    var depth = point.z;
                    var front = Math.max(0.0, depth);
                    var back = Math.max(0.0, -depth);
                    var dotSize = 1.10 + (depth + 1.0) * 0.95;
                    var alpha = depth >= 0.0
                        ? 0.42 + front * 0.48
                        : 0.035 + (1.0 - back) * 0.075;

                    ctx.globalAlpha = alpha;
                    ctx.fillStyle = depth > 0.48 ? "#d8fdff" : "#38dcff";
                    ctx.beginPath();
                    ctx.arc(point.x, point.y, dotSize, 0, Math.PI * 2);
                    ctx.fill();

                    // Pochi punti frontali hanno un alone sottile, come impulsi energetici.
                    if (depth > 0.78 && point.id % 19 === 0) {
                        ctx.globalAlpha = 0.14;
                        ctx.fillStyle = "#63f4ff";
                        ctx.beginPath();
                        ctx.arc(point.x, point.y, dotSize * 2.15, 0, Math.PI * 2);
                        ctx.fill();
                    }
                }
                ctx.globalAlpha = 1.0;

                // Nessun contorno geometrico pesante: la silhouette nasce dai punti stessi.

                // Nessuna piattaforma ellittica: il nucleo resta una sfera di punti pulita.

                // Etichette del nucleo: sempre sotto la sfera, mai sovrapposte ai punti.
                // Il layout riserva una fascia inferiore dedicata per le tre righe.
                ctx.textAlign = "center";
                var labelY = Math.min(h - 48, cy + radius * 1.43);
                ctx.fillStyle = "#d8fcff";
                ctx.font = "bold 10px sans-serif";
                ctx.fillText(root.listening ? "J.A.R.V.I.S.  /  LISTENING" : root.speaking ? "J.A.R.V.I.S.  /  SPEAKING" : "J.A.R.V.I.S.  /  NEURAL CORE", cx, labelY);
                ctx.fillStyle = "#52cce8";
                ctx.font = "8px sans-serif";
                ctx.fillText("ENERGY  " + Math.round(root.activity * 100) + "%", cx, labelY + 15);
                ctx.fillStyle = "#2b718e";
                ctx.font = "7px sans-serif";
                ctx.fillText(root.gestureMode, cx, labelY + 29);
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

    // Dispositivi sulla destra.
    Rectangle {
        id: rightPanel
        x: root.width - 287; y: root.height * 0.405; width: 265; height: 190
        color: "#040d19"; border.color: "#00cfff"; border.width: 1
        Rectangle { x: parent.width - 90; y: 0; width: 90; height: 3; color: "#00eaff" }
        Rectangle { x: parent.width - 3; y: 0; width: 3; height: 30; color: "#00eaff" }
        Rectangle { x: parent.width - 56; y: parent.height - 3; width: 56; height: 3; color: "#00eaff" }
        Rectangle { x: 0; y: parent.height - 30; width: 3; height: 30; color: "#087aa7" }
        Rectangle { x: parent.width - 3; y: 0; width: 3; height: 45; color: "#00cfff" }
        Text { x: 16; y: 14; width: parent.width - 32; text: "DISPOSITIVI"; color: "#00dfff"; font.pixelSize: 15; font.bold: true; horizontalAlignment: Text.AlignRight }
        Rectangle { x: 16; y: 42; width: parent.width - 32; height: 1; color: "#087aa7" }
        Text { x: 20; y: 59; text: "▣   •  Computer"; color: "#8ceeff"; font.pixelSize: 12 }
        Text { x: 20; y: 91; text: "⌘   •  Rete"; color: "#8ceeff"; font.pixelSize: 12 }
        Text { x: 20; y: 123; text: "ᛒ   •  Bluetooth"; color: "#8ceeff"; font.pixelSize: 12 }
        Text { x: 20; y: 155; text: "⌂   •  Smart Home"; color: "#8ceeff"; font.pixelSize: 12 }
    }

    // Stato della voce in basso a sinistra.
    Rectangle {
        x: 22; y: root.height - 124; width: 330; height: 92
        color: "#050f1d"; border.color: "#00cfff"; border.width: 1
        Rectangle { x: 0; y: 0; width: 80; height: 3; color: "#00eaff" }
        Text { x: 16; y: 10; text: "ULTIMA RISPOSTA"; color: "#62b8d5"; font.pixelSize: 9; font.bold: true }
        Text { x: 16; y: 29; width: parent.width - 30; text: root.responseText; color: "#d9f8ff"; font.pixelSize: 11; elide: Text.ElideRight }
        Rectangle { x: 16; y: 57; width: 6; height: 6; radius: 3; color: root.speaking ? "#ffffff" : root.listening ? "#00eaff" : "#16718e" }
        Text { x: 29; y: 53; text: "VOICE  /  " + root.voiceDisplay(); color: "#00dfff"; font.pixelSize: 9; font.bold: true }
    }

    // Modalità assistente in basso a destra.
    Rectangle {
        x: root.width - 352; y: root.height - 124; width: 330; height: 92
        color: "#050f1d"; border.color: "#00cfff"; border.width: 1
        Rectangle { x: parent.width - 80; y: 0; width: 80; height: 3; color: "#00eaff" }
        Text { x: 14; y: 10; width: parent.width - 28; text: "MODALITÀ"; color: "#00dfff"; font.pixelSize: 13; font.bold: true; horizontalAlignment: Text.AlignRight }
        Text { x: 14; y: 36; width: parent.width - 28; text: root.speaking ? "Assistente in risposta" : root.listening ? "In ascolto" : "Assistente attivo"; color: "#d9f8ff"; font.pixelSize: 12; horizontalAlignment: Text.AlignRight }
        Text { x: 14; y: 64; width: parent.width - 28; text: root.gestureMode; color: "#56cde9"; font.pixelSize: 9; horizontalAlignment: Text.AlignRight; elide: Text.ElideRight }
    }

    // Fascia comandi dedicata, sotto la sfera e senza coprire le colonne.
    Rectangle {
        x: 375; y: root.height - 58; width: root.width - 750; height: 38
        color: "#071a2c"; border.color: "#00cfff"; border.width: 1
        Rectangle { x: 0; y: 0; width: 4; height: parent.height; color: "#00e5ff" }
        Rectangle { x: 0; y: 0; width: parent.width * 0.24; height: 2; color: "#00e5ff" }
        Rectangle { x: parent.width * 0.76; y: parent.height - 2; width: parent.width * 0.24; height: 2; color: "#00e5ff" }
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
