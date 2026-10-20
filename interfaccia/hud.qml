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

    // Central holographic 3D object: wireframe scan instead of the old reactor.
    Item {
        id: hologram
        x: root.width / 2 - 180
        y: 92
        width: 360
        height: 360
        property real zoom: 1.0
        property real gestureTurn: 0

        // Subtle floor projection and scan reticle.
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 286
            width: 250
            height: 1
            color: "#ffb347"
            opacity: 0.38
        }
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 294
            width: 190
            height: 1
            color: "#d97716"
            opacity: 0.22
        }

        Canvas {
            id: hologramCanvas
            anchors.fill: parent
            renderTarget: Canvas.FramebufferObject
            antialiasing: true
            onPaint: {
                var ctx = getContext("2d");
                ctx.clearRect(0, 0, width, height);
                var cx = width / 2;
                var cy = height / 2 - 12;
                var scale = 1.0 * hologram.zoom;
                var angle = root.t * 0.55 + hologram.gestureTurn;
                var points = [];
                var edges = [];
                var i, j;

                // Project a rotating 3D wireframe object with depth.
                function project(p) {
                    var x = p[0], y = p[1], z = p[2];
                    var ca = Math.cos(angle), sa = Math.sin(angle);
                    var cb = Math.cos(angle * 0.63), sb = Math.sin(angle * 0.63);
                    var rx = x * ca - z * sa;
                    var rz = x * sa + z * ca;
                    var ry = y * cb - rz * sb;
                    rz = y * sb + rz * cb;
                    var perspective = 3.6 / (3.6 + rz);
                    return [cx + rx * 92 * scale * perspective, cy + ry * 92 * scale * perspective, rz];
                }

                // A faceted scan mesh: rings plus meridians, like a scanned 3D hologram.
                var latitudes = 9;
                var longitudes = 18;
                for (i = 1; i < latitudes; i++) {
                    var lat = -Math.PI / 2 + Math.PI * i / latitudes;
                    ctx.beginPath();
                    for (j = 0; j <= 72; j++) {
                        var lon = Math.PI * 2 * j / 72;
                        var p = project([Math.cos(lat) * Math.cos(lon), Math.sin(lat), Math.cos(lat) * Math.sin(lon)]);
                        if (j === 0) ctx.moveTo(p[0], p[1]); else ctx.lineTo(p[0], p[1]);
                    }
                    ctx.strokeStyle = i % 2 === 0 ? "#ffb347" : "#9c5b1c";
                    ctx.globalAlpha = i % 2 === 0 ? 0.55 : 0.32;
                    ctx.lineWidth = i % 3 === 0 ? 1.15 : 0.65;
                    ctx.stroke();
                }
                for (i = 0; i < longitudes; i++) {
                    var lon2 = Math.PI * 2 * i / longitudes;
                    ctx.beginPath();
                    for (j = 0; j <= 72; j++) {
                        var lat2 = -Math.PI / 2 + Math.PI * j / 72;
                        var p2 = project([Math.cos(lat2) * Math.cos(lon2), Math.sin(lat2), Math.cos(lat2) * Math.sin(lon2)]);
                        if (j === 0) ctx.moveTo(p2[0], p2[1]); else ctx.lineTo(p2[0], p2[1]);
                    }
                    ctx.strokeStyle = i % 3 === 0 ? "#ffe0a6" : "#d97716";
                    ctx.globalAlpha = i % 3 === 0 ? 0.72 : 0.38;
                    ctx.lineWidth = i % 3 === 0 ? 1.1 : 0.6;
                    ctx.stroke();
                }

                // Wireframe cube corners and diagonals add a tangible 3D scan silhouette.
                var verts = [
                    [-0.72,-0.72,-0.72],[0.72,-0.72,-0.72],[0.72,0.72,-0.72],[-0.72,0.72,-0.72],
                    [-0.72,-0.72,0.72],[0.72,-0.72,0.72],[0.72,0.72,0.72],[-0.72,0.72,0.72]
                ];
                var edgePairs = [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7],[0,6],[1,7],[2,4],[3,5]];
                ctx.globalAlpha = 0.78;
                ctx.strokeStyle = "#ffe0a6";
                ctx.lineWidth = 1.15;
                for (i = 0; i < edgePairs.length; i++) {
                    var a = project(verts[edgePairs[i][0]]);
                    var b = project(verts[edgePairs[i][1]]);
                    ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
                }

                // Scan nodes and axis markers.
                ctx.globalAlpha = 0.9;
                for (i = 0; i < verts.length; i++) {
                    var v = project(verts[i]);
                    ctx.beginPath(); ctx.arc(v[0], v[1], 2.2, 0, Math.PI * 2);
                    ctx.fillStyle = "#fff0d6"; ctx.fill();
                }
                ctx.globalAlpha = 0.75;
                ctx.strokeStyle = "#ffb347";
                ctx.lineWidth = 1;
                ctx.beginPath(); ctx.moveTo(cx - 135, cy); ctx.lineTo(cx - 105, cy); ctx.moveTo(cx + 105, cy); ctx.lineTo(cx + 135, cy);
                ctx.moveTo(cx, cy - 135); ctx.lineTo(cx, cy - 105); ctx.moveTo(cx, cy + 105); ctx.lineTo(cx, cy + 135); ctx.stroke();

                // Rotating horizontal scan beam.
                var beamY = cy + Math.sin(root.t * 1.7) * 78;
                var grad = ctx.createLinearGradient(cx - 125, beamY, cx + 125, beamY);
                grad.addColorStop(0, "rgba(255,179,71,0)");
                grad.addColorStop(0.5, "rgba(255,224,166,0.8)");
                grad.addColorStop(1, "rgba(255,179,71,0)");
                ctx.strokeStyle = grad; ctx.lineWidth = 1.2; ctx.globalAlpha = 0.8;
                ctx.beginPath(); ctx.moveTo(cx - 125, beamY); ctx.lineTo(cx + 125, beamY); ctx.stroke();
                ctx.globalAlpha = 1;
            }
            Connections {
                target: root
                function onTChanged() { hologramCanvas.requestPaint() }
                function onActivityChanged() { hologramCanvas.requestPaint() }
            }
        }

        // Corner brackets frame the scanned object rather than surrounding a reactor.
        Repeater {
            model: 4
            Item {
                property real leftX: index % 2 === 0 ? 35 : 289
                property real topY: index < 2 ? 30 : 278
                x: leftX; y: topY; width: 36; height: 36
                Rectangle { x: 0; y: 0; width: 24; height: 1; color: "#ffb347"; opacity: 0.75 }
                Rectangle { x: 0; y: 0; width: 1; height: 24; color: "#ffb347"; opacity: 0.75 }
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 316
            text: root.listening ? "SCANNING // LISTENING" : root.speaking ? "HOLOGRAM LINK ACTIVE" : "3D HOLOGRAM // READY"
            color: root.listening ? "#ffcc7a" : "#ffe0a6"
            font.pixelSize: 9
            font.bold: true
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 333
            text: "LIVE MESH  //  " + Math.round(root.activity * 100) + "%"
            color: "#d98b36"
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