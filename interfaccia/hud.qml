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

    // Proiezione centrale disegnata come un unico apparato luminoso,
    // evitando la pila di forme indipendenti della versione precedente.
    Item {
        id: hologram
        x: (root.width - width) / 2
        y: 72
        width: 360
        height: 390
        property real zoom: 1.0
        property real gestureTurn: 0

        Canvas {
            id: hologramCanvas
            anchors.fill: parent
            renderTarget: Canvas.FramebufferObject
            antialiasing: true

            Connections {
                target: root
                function onTChanged() { hologramCanvas.requestPaint() }
                function onActivityChanged() { hologramCanvas.requestPaint() }
                function onListeningChanged() { hologramCanvas.requestPaint() }
                function onSpeakingChanged() { hologramCanvas.requestPaint() }
            }

            onPaint: {
                var ctx = getContext("2d");
                ctx.reset();
                ctx.clearRect(0, 0, width, height);

                var cx = width / 2;
                var pulse = 0.82 + 0.18 * Math.sin(root.t * 2.0);
                var active = root.listening || root.speaking;
                var glow = active ? 1.0 : 0.72 + root.activity * 0.28;

                // Luce diffusa unica: il bagliore avvolge il reattore invece
                // di leggere come una sagoma piena aggiunta sullo sfondo.
                var haze = ctx.createRadialGradient(cx, 139, 8, cx, 145, 148);
                haze.addColorStop(0, "rgba(29,255,255," + (0.18 * glow) + ")");
                haze.addColorStop(0.45, "rgba(0,190,240,0.10)");
                haze.addColorStop(1, "rgba(0,120,190,0)");
                ctx.fillStyle = haze;
                ctx.fillRect(35, 8, 290, 292);

                // Campo verticale del reattore: una sola silhouette continua,
                // con bordo vivo e luce interna sfumata.
                ctx.save();
                ctx.translate(cx, 132);
                ctx.rotate(Math.sin(root.t * 0.24) * 0.025);
                ctx.shadowColor = "#00eaff";
                ctx.shadowBlur = 24 * pulse;
                var shell = ctx.createLinearGradient(-72, 0, 72, 0);
                shell.addColorStop(0, "rgba(0,255,255,0.08)");
                shell.addColorStop(0.22, "rgba(20,220,255,0.28)");
                shell.addColorStop(0.5, "rgba(215,255,255,0.72)");
                shell.addColorStop(0.78, "rgba(15,205,255,0.25)");
                shell.addColorStop(1, "rgba(0,255,255,0.06)");
                ctx.beginPath();
                ctx.ellipse(0, 0, 66, 101, 0, 0, Math.PI * 2);
                ctx.fillStyle = shell;
                ctx.fill();
                ctx.shadowBlur = 0;
                ctx.lineWidth = 1.6;
                ctx.strokeStyle = "rgba(125,255,255,0.95)";
                ctx.stroke();

                // Due curve laterali e archi interrotti costruiscono profondità
                // e un aspetto da tecnologia volumetrica, non da bersaglio.
                for (var side = -1; side <= 1; side += 2) {
                    ctx.beginPath();
                    ctx.moveTo(side * 48, -76);
                    ctx.bezierCurveTo(side * 18, -43, side * 23, 31, side * 49, 77);
                    ctx.strokeStyle = "rgba(180,255,255,0.78)";
                    ctx.lineWidth = 1.4;
                    ctx.stroke();
                }

                for (var ring = 0; ring < 3; ring++) {
                    ctx.beginPath();
                    ctx.ellipse(0, 0, 51 - ring * 10, 79 - ring * 16,
                                root.t * (ring % 2 ? -0.16 : 0.12), 0.24 + ring * 0.18,
                                Math.PI * 1.83 + ring * 0.22);
                    ctx.strokeStyle = ring === 1
                        ? "rgba(238,255,255,0.88)"
                        : "rgba(67,245,255," + (0.7 - ring * 0.12) + ")";
                    ctx.lineWidth = ring === 1 ? 2.0 : 1.1;
                    ctx.stroke();
                }

                // Nucleo luminoso: alone morbido e cuore bianco con riflesso ciano.
                var coreGlow = ctx.createRadialGradient(0, 0, 2, 0, 0, 49);
                coreGlow.addColorStop(0, "rgba(255,255,255,0.98)");
                coreGlow.addColorStop(0.22, "rgba(226,255,255,0.9)");
                coreGlow.addColorStop(0.48, "rgba(0,247,255,0.48)");
                coreGlow.addColorStop(1, "rgba(0,225,255,0)");
                ctx.fillStyle = coreGlow;
                ctx.beginPath();
                ctx.ellipse(0, 0, 37, 48, 0, 0, Math.PI * 2);
                ctx.fill();
                ctx.shadowColor = "#eaffff";
                ctx.shadowBlur = 15 * pulse;
                ctx.beginPath();
                ctx.ellipse(0, 0, 17, 25, 0, 0, Math.PI * 2);
                ctx.fillStyle = "rgba(255,255,255,0.94)";
                ctx.fill();
                ctx.shadowBlur = 0;

                // Tracce luminose brevi attorno al nucleo, disposte sul profilo.
                for (var i = 0; i < 20; i++) {
                    var a = (Math.PI * 2 * i / 20) + root.t * 0.18;
                    var rx = 57, ry = 88;
                    var x1 = Math.cos(a) * rx;
                    var y1 = Math.sin(a) * ry;
                    var x2 = Math.cos(a) * (rx + (i % 4 === 0 ? 10 : 4));
                    var y2 = Math.sin(a) * (ry + (i % 4 === 0 ? 10 : 4));
                    ctx.beginPath();
                    ctx.moveTo(x1, y1);
                    ctx.lineTo(x2, y2);
                    ctx.strokeStyle = i % 4 === 0
                        ? "rgba(255,255,255,0.95)" : "rgba(91,245,255,0.65)";
                    ctx.lineWidth = i % 4 === 0 ? 1.6 : 0.8;
                    ctx.stroke();
                }
                ctx.restore();

                // Fasci di luce convergono verso la piattaforma, lasciando
                // un piccolo spazio visibile sotto il reattore sospeso.
                ctx.save();
                ctx.globalAlpha = 0.26 + 0.12 * pulse;
                ctx.strokeStyle = "#7effff";
                ctx.lineWidth = 1;
                for (var beam = -4; beam <= 4; beam++) {
                    ctx.beginPath();
                    ctx.moveTo(cx + beam * 12, 236);
                    ctx.lineTo(cx + beam * 19, 268);
                    ctx.stroke();
                }
                ctx.restore();

                // Piattaforma proiettante in prospettiva: ellissi schiacciate,
                // segmenti interrotti e luce radente come un solo disco olografico.
                var floorGlow = ctx.createRadialGradient(cx, 286, 12, cx, 286, 172);
                floorGlow.addColorStop(0, "rgba(37,255,255,0.30)");
                floorGlow.addColorStop(0.55, "rgba(0,200,255,0.12)");
                floorGlow.addColorStop(1, "rgba(0,150,230,0)");
                ctx.fillStyle = floorGlow;
                ctx.beginPath();
                ctx.ellipse(cx, 286, 171, 37, 0, 0, Math.PI * 2);
                ctx.fill();

                ctx.shadowColor = "#00eaff";
                ctx.shadowBlur = 17 * pulse;
                ctx.lineWidth = 2;
                ctx.strokeStyle = "rgba(79,250,255,0.96)";
                ctx.beginPath();
                ctx.ellipse(cx, 282, 164, 28, 0, 0, Math.PI * 2);
                ctx.stroke();
                ctx.shadowBlur = 0;

                ctx.lineWidth = 1.3;
                ctx.strokeStyle = "rgba(219,255,255,0.94)";
                ctx.beginPath();
                ctx.ellipse(cx, 283, 132, 19, 0, 0.08, Math.PI * 0.92);
                ctx.stroke();
                ctx.strokeStyle = "rgba(45,225,255,0.76)";
                ctx.beginPath();
                ctx.ellipse(cx, 285, 148, 24, 0, Math.PI * 1.05, Math.PI * 1.95);
                ctx.stroke();

                ctx.lineWidth = 1;
                ctx.strokeStyle = "rgba(0,210,255,0.76)";
                ctx.beginPath();
                ctx.ellipse(cx, 291, 112, 13, 0, 0, Math.PI * 2);
                ctx.stroke();

                // Tacche sulla superficie seguono la prospettiva della base.
                for (var mark = 0; mark < 32; mark++) {
                    var angle = Math.PI * 2 * mark / 32;
                    var px = cx + Math.cos(angle) * 151;
                    var py = 282 + Math.sin(angle) * 24;
                    ctx.beginPath();
                    ctx.moveTo(px, py);
                    ctx.lineTo(cx + Math.cos(angle) * 158, 282 + Math.sin(angle) * 27);
                    ctx.strokeStyle = mark % 4 === 0
                        ? "rgba(230,255,255,0.95)" : "rgba(49,220,255,0.52)";
                    ctx.lineWidth = mark % 4 === 0 ? 1.3 : 0.7;
                    ctx.stroke();
                }

                // Particelle contenute nel campo di proiezione.
                for (var p = 0; p < 16; p++) {
                    var pxp = 48 + ((p * 47 + Math.sin(root.t + p) * 7) % 264);
                    var pyp = 35 + ((p * 31 + root.t * (p % 2 ? 5 : -3) + 280) % 210);
                    var alpha = 0.22 + (0.5 + 0.5 * Math.sin(root.t * 2 + p)) * 0.58;
                    ctx.fillStyle = "rgba(185,255,255," + alpha + ")";
                    ctx.fillRect(pxp, pyp, p % 5 === 0 ? 2 : 1, p % 5 === 0 ? 2 : 1);
                }
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 328
            text: root.listening ? "HOLOGRAPHIC CORE  //  LISTENING"
                  : root.speaking ? "HOLOGRAPHIC CORE  //  ACTIVE"
                  : "HOLOGRAPHIC CORE"
            color: "#b7ffff"
            font.pixelSize: 9
            font.bold: true
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 345
            text: "PROJECTION FIELD  //  " + Math.round(root.activity * 100) + "%"
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