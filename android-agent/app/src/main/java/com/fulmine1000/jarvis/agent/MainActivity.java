package com.fulmine1000.jarvis.agent;

import android.Manifest;
import android.app.Activity;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.Window;
import android.view.WindowManager;
import android.widget.*;
import android.graphics.drawable.GradientDrawable;

import org.json.JSONObject;
import org.vosk.Model;
import org.vosk.Recognizer;

import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.*;

public class MainActivity extends Activity {
    private static final int PORT = 8765;
    private static final int AUDIO_PERMISSION = 77;
    private static final String PROTOCOLLO = "JARVIS-MULTIDEVICE/3";
    private static final String PREFS = "jarvis_mobile";

    private final ExecutorService executor = Executors.newCachedThreadPool();
    private final Handler main = new Handler(Looper.getMainLooper());
    private SharedPreferences prefs;

    private TextView stato, voce, risposta, clock, connessione, voskStatus;
    private EditText comando;

    private ServerSocket serverSocket;
    private volatile boolean serverRunning;
    private volatile boolean sessioneAttiva;
    private volatile boolean usbCollegato;
    private volatile boolean ritornoRichiesto;
    private volatile String reverseEndpoint = "http://127.0.0.1:8766";

    private volatile boolean voiceRunning;
    private volatile boolean voiceStopping;
    private AudioRecord audioRecord;
    private Thread voiceThread;
    private Model voskModel;
    private Recognizer voskRecognizer;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setStatusBarColor(Color.rgb(2, 7, 12));
        getWindow().setNavigationBarColor(Color.rgb(2, 7, 12));
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON,
                WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        sessioneAttiva = prefs.getBoolean("sessione_attiva", false);
        usbCollegato = prefs.getBoolean("usb_collegato", false);

        costruisciHUD();
        avviaServer();
        avviaOrologio();
        richiediMicrofono();
        aggiornaHUD();
    }

    private int dp(float v) {
        return (int) (v * getResources().getDisplayMetrics().density + 0.5f);
    }

    private TextView text(String value, float size, int color, boolean bold) {
        TextView v = new TextView(this);
        v.setText(value);
        v.setTextSize(size);
        v.setTextColor(color);
        v.setGravity(Gravity.CENTER_VERTICAL);
        v.setTypeface(Typeface.create("sans", bold ? Typeface.BOLD : Typeface.NORMAL));
        return v;
    }

    private GradientDrawable panel() {
        GradientDrawable g = new GradientDrawable();
        g.setColor(Color.rgb(4, 16, 24));
        g.setStroke(dp(1), Color.rgb(10, 66, 81));
        g.setCornerRadius(dp(4));
        return g;
    }

    private LinearLayout.LayoutParams margins(int w, int h, int l, int t, int r, int b) {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(w, h);
        p.setMargins(l, t, r, b);
        return p;
    }

    private LinearLayout card(String title) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(12), dp(8), dp(12), dp(8));
        box.setBackground(panel());
        TextView h = text(title, 8, Color.rgb(79, 167, 183), true);
        box.addView(h, new LinearLayout.LayoutParams(-1, dp(24)));
        TextView line = new TextView(this);
        line.setBackgroundColor(Color.rgb(10, 53, 65));
        box.addView(line, new LinearLayout.LayoutParams(-1, dp(1)));
        return box;
    }

    private void costruisciHUD() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.rgb(2, 7, 12));

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(12), dp(10), dp(12), dp(18));
        scroll.addView(root, new ScrollView.LayoutParams(-1, -1));

        LinearLayout header = new LinearLayout(this);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(12), 0, dp(12), 0);
        header.setBackground(panel());
        root.addView(header, new LinearLayout.LayoutParams(-1, dp(52)));

        TextView title = text("J.A.R.V.I.S.", 17, Color.rgb(231, 251, 255), true);
        header.addView(title, new LinearLayout.LayoutParams(0, -1, 1));
        TextView mode = text("MOBILE NEURAL INTERFACE", 8, Color.rgb(79, 167, 183), true);
        mode.setGravity(Gravity.CENTER);
        header.addView(mode, new LinearLayout.LayoutParams(0, -1, 1));
        connessione = text("● SYSTEM ONLINE", 8, Color.rgb(40, 238, 112), true);
        connessione.setGravity(Gravity.RIGHT | Gravity.CENTER_VERTICAL);
        header.addView(connessione, new LinearLayout.LayoutParams(0, -1, 1));

        LinearLayout telemetry = card("SYSTEM TELEMETRY");
        root.addView(telemetry, margins(-1, dp(116), 0, dp(10), 0, 0));
        LinearLayout metrics = new LinearLayout(this);
        metrics.setOrientation(LinearLayout.HORIZONTAL);
        telemetry.addView(metrics, new LinearLayout.LayoutParams(-1, 0, 1));
        metric(metrics, "CPU", "MOBILE");
        metric(metrics, "MEMORY", "LOCAL");
        metric(metrics, "LINK", "USB");

        LinearLayout reactor = card("NEURAL CORE");
        root.addView(reactor, margins(-1, dp(210), 0, dp(8), 0, dp(10)));
        TextView core = text("J.A.R.V.I.S.", 24, Color.rgb(231, 251, 255), true);
        core.setGravity(Gravity.CENTER);
        GradientDrawable coreBg = new GradientDrawable();
        coreBg.setShape(GradientDrawable.OVAL);
        coreBg.setColor(Color.rgb(3, 21, 30));
        coreBg.setStroke(dp(2), Color.rgb(53, 223, 240));
        core.setBackground(coreBg);
        reactor.addView(core, new LinearLayout.LayoutParams(-1, dp(120)));
        TextView sub = text("OFFLINE VOSK CORE", 8, Color.rgb(79, 167, 183), true);
        sub.setGravity(Gravity.CENTER);
        reactor.addView(sub, new LinearLayout.LayoutParams(-1, dp(30)));
        voskStatus = text("VOSK: INITIALIZING", 8, Color.rgb(142, 191, 200), true);
        voskStatus.setGravity(Gravity.CENTER);
        reactor.addView(voskStatus, new LinearLayout.LayoutParams(-1, 0, 1));

        LinearLayout statusCard = card("J.A.R.V.I.S. STATUS");
        root.addView(statusCard, margins(-1, dp(145), 0, 0, 0, dp(10)));
        stato = text("SYSTEM ONLINE", 14, Color.rgb(84, 244, 255), true);
        stato.setGravity(Gravity.CENTER);
        statusCard.addView(stato, new LinearLayout.LayoutParams(-1, dp(38)));
        voce = text("OFFLINE / STANDBY", 9, Color.rgb(183, 220, 227), true);
        voce.setGravity(Gravity.CENTER);
        statusCard.addView(voce, new LinearLayout.LayoutParams(-1, dp(25)));
        TextView local = text("CORE SESSION     " + (sessioneAttiva ? "ACTIVE" : "READY") +
                "\nTRANSPORT        USB / ADB\nOFFLINE MODE      VOSK READY", 8, Color.rgb(142, 191, 200), false);
        local.setGravity(Gravity.CENTER);
        statusCard.addView(local, new LinearLayout.LayoutParams(-1, 0, 1));

        LinearLayout voiceCard = card("VOICE CHANNEL");
        root.addView(voiceCard, margins(-1, dp(180), 0, 0, 0, dp(10)));
        comando = new EditText(this);
        comando.setSingleLine(true);
        comando.setTextColor(Color.WHITE);
        comando.setHintTextColor(Color.rgb(90, 125, 135));
        comando.setHint("Scrivi un comando...");
        comando.setTextSize(14);
        comando.setPadding(dp(12), 0, dp(12), 0);
        GradientDrawable input = new GradientDrawable();
        input.setColor(Color.rgb(2, 16, 24));
        input.setStroke(dp(1), Color.rgb(10, 60, 75));
        input.setCornerRadius(dp(4));
        comando.setBackground(input);
        voiceCard.addView(comando, margins(-1, dp(48), dp(10), dp(8), dp(10), dp(8)));

        Button send = new Button(this);
        send.setText("EXECUTE COMMAND");
        send.setTextSize(10);
        send.setTextColor(Color.rgb(231, 251, 255));
        send.setAllCaps(false);
        send.setOnClickListener(v -> inviaComando(comando.getText().toString()));
        voiceCard.addView(send, margins(-1, dp(42), dp(10), 0, dp(10), dp(8)));

        risposta = text("Neural core standing by.", 11, Color.rgb(183, 220, 227), false);
        risposta.setGravity(Gravity.CENTER);
        voiceCard.addView(risposta, new LinearLayout.LayoutParams(-1, 0, 1));

        clock = text("--:--:--", 26, Color.rgb(231, 251, 255), true);
        clock.setGravity(Gravity.CENTER);
        root.addView(clock, margins(-1, dp(52), 0, dp(4), 0, 0));

        TextView footer = text("SECURITY ARMED     •     VOSK OFFLINE AI     •     USB / ADB LINK", 7, Color.rgb(79, 167, 183), true);
        footer.setGravity(Gravity.CENTER);
        root.addView(footer, new LinearLayout.LayoutParams(-1, dp(26)));
        setContentView(scroll);
    }

    private void metric(LinearLayout parent, String a, String b) {
        LinearLayout c = new LinearLayout(this);
        c.setOrientation(LinearLayout.VERTICAL);
        c.setGravity(Gravity.CENTER);
        TextView x = text(a, 7, Color.rgb(79, 167, 183), true);
        x.setGravity(Gravity.CENTER);
        TextView y = text(b, 11, Color.rgb(216, 247, 251), true);
        y.setGravity(Gravity.CENTER);
        c.addView(x, new LinearLayout.LayoutParams(-1, dp(25)));
        c.addView(y, new LinearLayout.LayoutParams(-1, 0, 1));
        parent.addView(c, new LinearLayout.LayoutParams(0, -1, 1));
    }

    private void avviaOrologio() {
        main.post(new Runnable() {
            @Override public void run() {
                if (clock != null) clock.setText(new SimpleDateFormat("HH:mm:ss", Locale.ITALIAN).format(new Date()));
                main.postDelayed(this, 1000);
            }
        });
    }

    private void aggiornaHUD() {
        if (stato == null) return;
        stato.setText(sessioneAttiva ? "SESSION ACTIVE" : "SYSTEM ONLINE");
        connessione.setText(usbCollegato ? "● USB LINK" : "● SYSTEM ONLINE");
        connessione.setTextColor(usbCollegato ? Color.rgb(84, 244, 255) : Color.rgb(40, 238, 112));
        if (!voiceRunning) voce.setText(usbCollegato ? "USB LINK / READY" : "OFFLINE / STANDBY");
    }

    private void avviaServer() {
        executor.execute(() -> {
            try {
                serverSocket = new ServerSocket(PORT);
                serverRunning = true;
                while (serverRunning && !serverSocket.isClosed()) {
                    Socket s = serverSocket.accept();
                    executor.execute(() -> gestisci(s));
                }
            } catch (Exception e) {
                main.post(() -> { if (stato != null) stato.setText("SERVER ERROR"); });
            }
        });
    }

    private void gestisci(Socket socket) {
        try {
            BufferedReader in = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
            String request = in.readLine();
            if (request == null) { socket.close(); return; }
            String line; int len = 0;
            while ((line = in.readLine()) != null && !line.isEmpty()) {
                if (line.toLowerCase(Locale.ROOT).startsWith("content-length:"))
                    len = Integer.parseInt(line.substring(15).trim());
            }
            StringBuilder body = new StringBuilder();
            for (int i = 0; i < len; i++) { int c = in.read(); if (c < 0) break; body.append((char)c); }
            String[] parts = request.split(" ");
            String path = parts.length > 1 ? parts[1] : "/";
            int code = 200;
            String out;

            if (path.equals("/jarvis/handshake")) {
                JSONObject o = new JSONObject();
                o.put("ok", true); o.put("protocollo", PROTOCOLLO); o.put("agente", "android");
                o.put("versione", "3.0"); o.put("android", Build.VERSION.RELEASE);
                o.put("nome", Build.MODEL); o.put("vertical_hud", true); o.put("vosk", true);
                out = o.toString();
            } else if (path.equals("/jarvis/sessione")) {
                sessioneAttiva = true; usbCollegato = true; ritornoRichiesto = false;
                prefs.edit().putBoolean("sessione_attiva", true).putBoolean("usb_collegato", true).apply();
                String ep = jsonValue(body.toString(), "reverse_endpoint");
                if (ep != null && !ep.isEmpty()) reverseEndpoint = ep;
                main.post(this::aggiornaHUD);
                avviaVoskSePossibile();
                out = "{\"ok\":true,\"sessione\":true,\"offline\":true,\"vosk\":true,\"messaggio\":\"Jarvis trasferito sul telefono.\"}";
            } else if (path.equals("/jarvis/usb")) {
                String connected = jsonValue(body.toString(), "connected");
                usbCollegato = "true".equalsIgnoreCase(connected);
                prefs.edit().putBoolean("usb_collegato", usbCollegato).apply();
                main.post(this::aggiornaHUD);
                out = "{\"ok\":true,\"usb\":" + usbCollegato + "}";
            } else if (path.equals("/jarvis/ritorno_richiesto")) {
                out = "{\"ok\":true,\"requested\":" + ritornoRichiesto + "}";
            } else if (path.equals("/jarvis/ritorno")) {
                sessioneAttiva = false; ritornoRichiesto = false;
                prefs.edit().putBoolean("sessione_attiva", false).apply();
                main.post(() -> { aggiornaHUD(); if (risposta != null) risposta.setText("Jarvis è tornato sul Mac."); });
                out = "{\"ok\":true,\"sessione\":false,\"messaggio\":\"Jarvis è tornato al Mac.\"}";
            } else if (path.equals("/jarvis/stato")) {
                out = "{\"ok\":true,\"online\":true,\"sessione\":" + sessioneAttiva +
                        ",\"usb\":" + usbCollegato + ",\"offline\":true,\"vosk\":" + (voskModel != null) + "}";
            } else if (path.equals("/api/comando")) {
                String cmd = jsonValue(body.toString(), "comando");
                String answer = comandoOffline(cmd == null ? "" : cmd);
                out = new JSONObject().put("ok", true).put("risposta", answer).toString();
            } else {
                code = 404;
                out = "{\"ok\":false,\"errore\":\"endpoint non trovato\"}";
            }
            rispondi(socket, code, out);
        } catch (Exception ignored) {
            try { socket.close(); } catch (Exception ignored2) {}
        }
    }

    private void rispondi(Socket s, int code, String out) throws Exception {
        byte[] raw = out.getBytes(StandardCharsets.UTF_8);
        String status = code == 200 ? "200 OK" : "404 Not Found";
        String h = "HTTP/1.1 " + status + "\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: " + raw.length + "\r\nConnection: close\r\n\r\n";
        OutputStream os = s.getOutputStream();
        os.write(h.getBytes(StandardCharsets.UTF_8)); os.write(raw); os.flush(); s.close();
    }

    private void inviaComando(String input) {
        final String testo = input == null ? "" : input.trim();
        if (testo.isEmpty()) return;
        risposta.setText("PROCESSING...");
        executor.execute(() -> {
            String result = usbCollegato ? inviaAlMac(testo) : null;
            if (result == null) result = comandoOffline(testo);
            String r = result;
            main.post(() -> { risposta.setText(r); aggiornaHUD(); });
        });
    }

    private String inviaAlMac(String testo) {
        try {
            URL url = new URL(reverseEndpoint + "/api/comando");
            HttpURLConnection c = (HttpURLConnection) url.openConnection();
            c.setConnectTimeout(1500); c.setReadTimeout(3000);
            c.setRequestMethod("POST"); c.setDoOutput(true);
            c.setRequestProperty("Content-Type", "application/json; charset=utf-8");
            c.getOutputStream().write(new JSONObject().put("comando", testo).toString().getBytes(StandardCharsets.UTF_8));
            if (c.getResponseCode() != 200) return null;
            BufferedReader r = new BufferedReader(new InputStreamReader(c.getInputStream(), StandardCharsets.UTF_8));
            StringBuilder b = new StringBuilder(); String l;
            while ((l = r.readLine()) != null) b.append(l);
            String ans = jsonValue(b.toString(), "risposta");
            c.disconnect();
            return ans == null ? "Comando ricevuto dal Core." : ans;
        } catch (Exception e) { return null; }
    }

    private String comandoOffline(String testo) {
        String c = testo.toLowerCase(Locale.ITALIAN).trim();
        if (c.equals("jarvis") || c.equals("hey jarvis") || c.equals("ehi jarvis"))
            return "Sono qui. Modalità offline attiva.";
        if (c.startsWith("jarvis ")) c = c.substring(7).trim();
        if (c.contains("che ore sono") || c.equals("ora"))
            return "Sono le " + new SimpleDateFormat("HH:mm", Locale.ITALIAN).format(new Date()) + ".";
        if (c.contains("che giorno è") || c.contains("che data è") || c.equals("data"))
            return "Oggi è il " + new SimpleDateFormat("dd/MM/yyyy", Locale.ITALIAN).format(new Date()) + ".";
        if (c.contains("stato sistema") || c.equals("stato"))
            return "Core locale operativo. USB: " + (usbCollegato ? "attiva" : "assente") + ". Vosk: " + (voskModel != null ? "attivo" : "non pronto") + ".";
        if (c.contains("torna sul mac") || c.contains("ritorna sul mac") || c.contains("torna al mac")) {
            if (usbCollegato) { ritornoRichiesto = true; return "Richiesta di ritorno al Mac inviata."; }
            return "Il Mac non è collegato via USB. Rimango operativo sul telefono.";
        }
        return "Modalità offline: comando non disponibile localmente.";
    }

    private void richiediMicrofono() {
        if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED)
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, AUDIO_PERMISSION);
        else avviaVoskSePossibile();
    }

    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == AUDIO_PERMISSION && grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED)
            avviaVoskSePossibile();
        else if (voskStatus != null) voskStatus.setText("VOSK: MICROPHONE PERMISSION REQUIRED");
    }

    private void avviaVoskSePossibile() {
        if (!sessioneAttiva || voiceRunning) return;
        if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) return;
        executor.execute(() -> {
            try {
                if (voskModel == null) {
                    main.post(() -> { if (voskStatus != null) voskStatus.setText("VOSK: LOADING MODEL"); });
                    File modelDir = new File(getFilesDir(), "vosk-model-small-it-0.22");
                    if (!modelDir.exists()) copyAssetTree("vosk-model-small-it-0.22", modelDir);
                    voskModel = new Model(modelDir.getAbsolutePath());
                }
                main.post(() -> { if (voskStatus != null) voskStatus.setText("VOSK: OFFLINE READY"); });
                startVoiceLoop();
            } catch (Exception e) {
                main.post(() -> { if (voskStatus != null) voskStatus.setText("VOSK ERROR: " + e.getClass().getSimpleName()); });
            }
        });
    }

    private void startVoiceLoop() {
        if (voiceRunning) return;
        voiceThread = new Thread(() -> {
            voiceRunning = true; voiceStopping = false;
            int min = AudioRecord.getMinBufferSize(16000, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT);
            if (min <= 0) min = 4096;
            int bufferSize = Math.max(min * 2, 8192);
            try {
                audioRecord = new AudioRecord(MediaRecorder.AudioSource.MIC, 16000,
                        AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT, bufferSize);
                voskRecognizer = new Recognizer(voskModel, 16000.0f);
                audioRecord.startRecording();
                main.post(() -> voce.setText("LISTENING / VOSK OFFLINE"));
                byte[] buffer = new byte[bufferSize];
                while (!voiceStopping && sessioneAttiva) {
                    int n = audioRecord.read(buffer, 0, buffer.length);
                    if (n <= 0) continue;
                    if (voskRecognizer.acceptWaveForm(buffer, n)) {
                        String result = voskRecognizer.getResult();
                        String text = jsonValue(result, "text");
                        if (text != null && !text.trim().isEmpty()) processSpeech(text.trim());
                    }
                }
            } catch (Exception e) {
                main.post(() -> { if (voskStatus != null) voskStatus.setText("VOSK AUDIO ERROR"); });
            } finally {
                voiceRunning = false;
                try { if (audioRecord != null) audioRecord.stop(); } catch (Exception ignored) {}
                try { if (audioRecord != null) audioRecord.release(); } catch (Exception ignored) {}
                audioRecord = null;
                try { if (voskRecognizer != null) voskRecognizer.close(); } catch (Exception ignored) {}
                voskRecognizer = null;
                main.post(this::aggiornaHUD);
            }
        }, "Jarvis-Vosk");
        voiceThread.start();
    }

    private void processSpeech(String spoken) {
        String normalized = spoken.toLowerCase(Locale.ITALIAN).trim();
        if (normalized.contains("jarvis")) {
            if (usbCollegato) {
                ritornoRichiesto = true;
                main.post(() -> risposta.setText("Wake word rilevata. Richiesta di ritorno al Mac."));
                return;
            }
            if (normalized.equals("jarvis") || normalized.equals("hey jarvis") || normalized.equals("ehi jarvis")) {
                main.post(() -> risposta.setText("Sono qui. Modalità offline attiva."));
                return;
            }
        }
        inviaComando(spoken);
    }

    private void stopVoiceLoop() {
        voiceStopping = true;
        try { if (audioRecord != null) audioRecord.stop(); } catch (Exception ignored) {}
        if (voiceThread != null) {
            try { voiceThread.join(500); } catch (Exception ignored) {}
        }
    }

    private void copyAssetTree(String assetPath, File out) throws IOException {
        String[] children = getAssets().list(assetPath);
        if (children == null || children.length == 0) {
            File parent = out.getParentFile();
            if (parent != null && !parent.exists()) parent.mkdirs();
            InputStream in = getAssets().open(assetPath);
            FileOutputStream fos = new FileOutputStream(out);
            byte[] b = new byte[8192]; int n;
            while ((n = in.read(b)) > 0) fos.write(b, 0, n);
            in.close(); fos.close();
            return;
        }
        if (!out.exists() && !out.mkdirs()) throw new IOException("Cannot create " + out);
        for (String child : children) copyAssetTree(assetPath + "/" + child, new File(out, child));
    }

    private String jsonValue(String json, String key) {
        if (json == null) return null;
        try {
            JSONObject o = new JSONObject(json);
            if (o.has(key)) return o.optString(key, null);
        } catch (Exception ignored) {}
        return null;
    }

    @Override protected void onResume() {
        super.onResume();
        if (sessioneAttiva) main.postDelayed(this::avviaVoskSePossibile, 500);
    }

    @Override protected void onDestroy() {
        stopVoiceLoop();
        serverRunning = false;
        try { if (serverSocket != null) serverSocket.close(); } catch (Exception ignored) {}
        try { if (voskModel != null) voskModel.close(); } catch (Exception ignored) {}
        executor.shutdownNow();
        super.onDestroy();
    }
}
