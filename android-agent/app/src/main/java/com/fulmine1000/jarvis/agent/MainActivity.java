package com.fulmine1000.jarvis.agent;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.content.Intent;
import android.view.Gravity;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.view.animation.AlphaAnimation;
import android.view.animation.LinearInterpolator;
import android.animation.ObjectAnimator;
import android.animation.AnimatorSet;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.graphics.drawable.GradientDrawable;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * HUD verticale J.A.R.V.I.S. per telefono Android.
 *
 * Non usa Tkinter, Qt o HTML Canvas: l'interfaccia è composta da View Android
 * native. La sessione resta sul telefono quando il cavo viene scollegato.
 * Quando il Mac riconnette il telefono via USB, il bridge viene riattivato;
 * pronunciando "Jarvis" mentre il cavo è collegato viene richiesta la
 * restituzione della sessione al Mac.
 */
public class MainActivity extends Activity {
    private static final int PORT = 8765;
    private static final int AUDIO_PERMISSION = 77;
    private static final String PROTOCOLLO = "JARVIS-MULTIDEVICE/2";
    private static final String PREFS = "jarvis_mobile";

    private ServerSocket serverSocket;
    private final ExecutorService executor = Executors.newCachedThreadPool();
    private final Handler main = new Handler(Looper.getMainLooper());
    private SharedPreferences prefs;

    private TextView stato;
    private TextView voce;
    private TextView risposta;
    private TextView clock;
    private TextView connessione;
    private EditText comando;
    private View reactor;
    private SpeechRecognizer speech;
    private boolean recognitionRunning = false;

    private volatile boolean sessioneAttiva;
    private volatile boolean usbCollegato;
    private volatile boolean ritornoRichiesto;
    private volatile String reverseEndpoint = "http://127.0.0.1:8766";

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        requestWindowFeatures();
        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        sessioneAttiva = prefs.getBoolean("sessione_attiva", false);
        usbCollegato = prefs.getBoolean("usb_collegato", false);
        costruisciHUD();
        avviaServer();
        avviaOrologio();
        preparaVoce();
        aggiornaHUD();
    }

    private void requestWindowFeatures() {
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setStatusBarColor(Color.rgb(2, 7, 12));
        getWindow().setNavigationBarColor(Color.rgb(2, 7, 12));
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON,
                WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
    }

    private int dp(float value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
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

    private GradientDrawable panelBackground() {
        GradientDrawable g = new GradientDrawable();
        g.setColor(Color.rgb(4, 16, 24));
        g.setStroke(dp(1), Color.rgb(10, 66, 81));
        g.setCornerRadius(dp(4));
        return g;
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
        header.setBackground(panelBackground());
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
        root.addView(telemetry, marginParams(-1, dp(116), 0, dp(10), 0, 0));
        LinearLayout metrics = new LinearLayout(this);
        metrics.setOrientation(LinearLayout.HORIZONTAL);
        telemetry.addView(metrics, new LinearLayout.LayoutParams(-1, 0, 1));
        addMetric(metrics, "CPU", "MOBILE");
        addMetric(metrics, "MEMORY", "LOCAL");
        addMetric(metrics, "LINK", "USB");

        FrameLayout reactorFrame = new FrameLayout(this);
        reactorFrame.setBackgroundColor(Color.TRANSPARENT);
        root.addView(reactorFrame, marginParams(-1, dp(330), 0, dp(8), 0, 0));
        reactor = createReactor(reactorFrame);

        LinearLayout stateCard = card("J.A.R.V.I.S. STATUS");
        root.addView(stateCard, marginParams(-1, dp(126), 0, dp(10), 0, 0));
        stato = text("SYSTEM ONLINE", 14, Color.rgb(84, 244, 255), true);
        stato.setGravity(Gravity.CENTER);
        stateCard.addView(stato, new LinearLayout.LayoutParams(-1, dp(38)));
        voce = text("STANDBY", 9, Color.rgb(183, 220, 227), true);
        voce.setGravity(Gravity.CENTER);
        stateCard.addView(voce, new LinearLayout.LayoutParams(-1, dp(25)));
        TextView local = text("CORE SESSION     " + (sessioneAttiva ? "ACTIVE" : "READY") + "\nTRANSPORT        USB / ADB\nOFFLINE MODE      READY", 8, Color.rgb(142, 191, 200), false);
        local.setGravity(Gravity.CENTER);
        stateCard.addView(local, new LinearLayout.LayoutParams(-1, 0, 1));

        LinearLayout voiceCard = card("VOICE CHANNEL");
        root.addView(voiceCard, marginParams(-1, dp(172), 0, dp(10), 0, 0));
        comando = new EditText(this);
        comando.setSingleLine(true);
        comando.setTextColor(Color.WHITE);
        comando.setHintTextColor(Color.rgb(90, 125, 135));
        comando.setHint("Scrivi un comando...");
        comando.setTextSize(14);
        comando.setPadding(dp(12), 0, dp(12), 0);
        GradientDrawable inputBg = new GradientDrawable();
        inputBg.setColor(Color.rgb(2, 16, 24));
        inputBg.setStroke(dp(1), Color.rgb(10, 60, 75));
        inputBg.setCornerRadius(dp(4));
        comando.setBackground(inputBg);
        voiceCard.addView(comando, marginParams(-1, dp(48), dp(10), dp(8), dp(10), dp(8)));

        Button invia = new Button(this);
        invia.setText("EXECUTE COMMAND");
        invia.setTextSize(10);
        invia.setTextColor(Color.rgb(231, 251, 255));
        invia.setAllCaps(false);
        invia.setOnClickListener(v -> inviaComando(comando.getText().toString()));
        voiceCard.addView(invia, marginParams(-1, dp(42), dp(10), 0, dp(10), dp(8)));

        risposta = text("Neural core standing by.", 11, Color.rgb(183, 220, 227), false);
        risposta.setGravity(Gravity.CENTER);
        voiceCard.addView(risposta, new LinearLayout.LayoutParams(-1, 0, 1));

        clock = text("--:--:--", 26, Color.rgb(231, 251, 255), true);
        clock.setGravity(Gravity.CENTER);
        root.addView(clock, marginParams(-1, dp(52), 0, dp(4), 0, 0));
        TextView footer = text("SECURITY ARMED     •     AI ENGINE READY     •     LINK LOCAL", 7, Color.rgb(79, 167, 183), true);
        footer.setGravity(Gravity.CENTER);
        root.addView(footer, new LinearLayout.LayoutParams(-1, dp(26)));

        setContentView(scroll);
    }

    private LinearLayout card(String heading) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(12), dp(8), dp(12), dp(8));
        box.setBackground(panelBackground());
        TextView h = text(heading, 8, Color.rgb(79, 167, 183), true);
        box.addView(h, new LinearLayout.LayoutParams(-1, dp(24)));
        View line = new View(this);
        line.setBackgroundColor(Color.rgb(10, 53, 65));
        box.addView(line, new LinearLayout.LayoutParams(-1, dp(1)));
        return box;
    }

    private void addMetric(LinearLayout parent, String label, String value) {
        LinearLayout cell = new LinearLayout(this);
        cell.setOrientation(LinearLayout.VERTICAL);
        cell.setGravity(Gravity.CENTER);
        TextView a = text(label, 7, Color.rgb(79, 167, 183), true);
        a.setGravity(Gravity.CENTER);
        TextView b = text(value, 11, Color.rgb(216, 247, 251), true);
        b.setGravity(Gravity.CENTER);
        cell.addView(a, new LinearLayout.LayoutParams(-1, dp(25)));
        cell.addView(b, new LinearLayout.LayoutParams(-1, 0, 1));
        parent.addView(cell, new LinearLayout.LayoutParams(0, -1, 1));
    }

    private LinearLayout.LayoutParams marginParams(int w, int h, int l, int t, int r, int b) {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(w, h);
        p.setMargins(l, t, r, b);
        return p;
    }

    private View createReactor(FrameLayout parent) {
        int size = dp(292);
        FrameLayout reactorBox = new FrameLayout(this);
        FrameLayout.LayoutParams center = new FrameLayout.LayoutParams(size, size, Gravity.CENTER);
        parent.addView(reactorBox, center);

        addRing(reactorBox, size - dp(8), Color.rgb(10, 52, 65), 1, 0);
        addRing(reactorBox, size - dp(38), Color.rgb(11, 86, 106), 1, 1);
        addRing(reactorBox, size - dp(72), Color.rgb(23, 109, 132), 1, -1);
        addRing(reactorBox, size - dp(110), Color.rgb(84, 244, 255), 2, 1);

        int coreSize = dp(132);
        TextView core = text("J.A.R.V.I.S.", 17, Color.rgb(231, 251, 255), true);
        core.setGravity(Gravity.CENTER);
        GradientDrawable coreBg = new GradientDrawable();
        coreBg.setShape(GradientDrawable.OVAL);
        coreBg.setColor(Color.rgb(3, 21, 30));
        coreBg.setStroke(dp(2), Color.rgb(53, 223, 240));
        core.setBackground(coreBg);
        FrameLayout.LayoutParams cp = new FrameLayout.LayoutParams(coreSize, coreSize, Gravity.CENTER);
        reactorBox.addView(core, cp);

        TextView sub = text("NEURAL CORE", 7, Color.rgb(79, 167, 183), true);
        sub.setGravity(Gravity.CENTER);
        FrameLayout.LayoutParams sp = new FrameLayout.LayoutParams(dp(140), dp(22), Gravity.CENTER);
        sp.topMargin = dp(92);
        reactorBox.addView(sub, sp);

        AlphaAnimation pulse = new AlphaAnimation(0.45f, 1f);
        pulse.setDuration(1100);
        pulse.setRepeatMode(AlphaAnimation.REVERSE);
        pulse.setRepeatCount(AlphaAnimation.INFINITE);
        core.startAnimation(pulse);
        return reactorBox;
    }

    private void addRing(FrameLayout parent, int size, int color, int stroke, float direction) {
        View ring = new View(this);
        GradientDrawable bg = new GradientDrawable();
        bg.setShape(GradientDrawable.OVAL);
        bg.setColor(Color.TRANSPARENT);
        bg.setStroke(dp(stroke), color);
        ring.setBackground(bg);
        FrameLayout.LayoutParams p = new FrameLayout.LayoutParams(size, size, Gravity.CENTER);
        parent.addView(ring, p);
        if (direction != 0) {
            ObjectAnimator spin = ObjectAnimator.ofFloat(ring, "rotation", 0f, direction * 360f);
            spin.setDuration(direction > 0 ? 18000 : 24000);
            spin.setRepeatCount(ObjectAnimator.INFINITE);
            spin.setInterpolator(new LinearInterpolator());
            spin.start();
        }
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
        voce.setText(usbCollegato ? "USB LINK / READY" : "OFFLINE / STANDBY");
        connessione.setText(usbCollegato ? "● USB LINK" : "● SYSTEM ONLINE");
        connessione.setTextColor(usbCollegato ? Color.rgb(84, 244, 255) : Color.rgb(40, 238, 112));
    }

    private void avviaServer() {
        executor.execute(() -> {
            try {
                serverSocket = new ServerSocket(PORT);
                while (!serverSocket.isClosed()) {
                    final Socket socket = serverSocket.accept();
                    executor.execute(() -> gestisci(socket));
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
                if (line.toLowerCase(Locale.ROOT).startsWith("content-length:")) {
                    len = Integer.parseInt(line.substring(15).trim());
                }
            }
            StringBuilder body = new StringBuilder();
            for (int i = 0; i < len; i++) { int c = in.read(); if (c < 0) break; body.append((char) c); }
            String[] parts = request.split(" ");
            String path = parts.length > 1 ? parts[1] : "/";
            String out;
            int code = 200;

            if (path.equals("/jarvis/handshake")) {
                out = "{\"ok\":true,\"protocollo\":\"" + PROTOCOLLO + "\",\"agente\":\"android\",\"versione\":\"2.0\",\"android\":\"" + safe(Build.VERSION.RELEASE) + "\",\"nome\":\"" + safe(Build.MODEL) + "\",\"vertical_hud\":true}";
            } else if (path.equals("/jarvis/sessione")) {
                sessioneAttiva = true;
                usbCollegato = true;
                ritornoRichiesto = false;
                prefs.edit().putBoolean("sessione_attiva", true).putBoolean("usb_collegato", true).apply();
                if (body.length() > 0) {
                    String endpoint = jsonValue(body.toString(), "reverse_endpoint");
                    if (endpoint != null && endpoint.length() > 0) reverseEndpoint = endpoint;
                }
                main.post(this::aggiornaHUD);
                out = "{\"ok\":true,\"sessione\":true,\"offline\":true,\"messaggio\":\"Jarvis trasferito sul telefono.\"}";
            } else if (path.equals("/jarvis/usb")) {
                String connected = jsonValue(body.toString(), "connected");
                usbCollegato = "true".equalsIgnoreCase(connected);
                prefs.edit().putBoolean("usb_collegato", usbCollegato).apply();
                main.post(this::aggiornaHUD);
                out = "{\"ok\":true,\"usb\":" + usbCollegato + "}";
            } else if (path.equals("/jarvis/ritorno_richiesto")) {
                out = "{\"ok\":true,\"requested\":" + ritornoRichiesto + "}";
            } else if (path.equals("/jarvis/ritorno")) {
                sessioneAttiva = false;
                ritornoRichiesto = false;
                prefs.edit().putBoolean("sessione_attiva", false).apply();
                main.post(() -> {
                    aggiornaHUD();
                    if (risposta != null) risposta.setText("Jarvis è tornato sul Mac.");
                });
                out = "{\"ok\":true,\"sessione\":false,\"messaggio\":\"Jarvis è tornato al Mac.\"}";
            } else if (path.equals("/jarvis/stato")) {
                out = "{\"ok\":true,\"online\":true,\"sessione\":" + sessioneAttiva + ",\"usb\":" + usbCollegato + ",\"offline\":true}";
            } else {
                code = 404;
                out = "{\"ok\":false,\"errore\":\"endpoint non trovato\"}";
            }
            rispondi(socket, code, out);
        } catch (Exception ignored) {
            try { socket.close(); } catch (Exception ignored2) {}
        }
    }

    private void rispondi(Socket socket, int code, String out) throws Exception {
        byte[] raw = out.getBytes(StandardCharsets.UTF_8);
        String status = code == 200 ? "200 OK" : "404 Not Found";
        String header = "HTTP/1.1 " + status + "\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: " + raw.length + "\r\nConnection: close\r\n\r\n";
        OutputStream os = socket.getOutputStream();
        os.write(header.getBytes(StandardCharsets.UTF_8));
        os.write(raw);
        os.flush();
        socket.close();
    }

    private void inviaComando(final String testoInput) {
        final String testo = testoInput == null ? "" : testoInput.trim();
        if (testo.length() == 0) return;
        risposta.setText("PROCESSING...");
        voce.setText("LISTENING");
        executor.execute(() -> {
            String result = null;
            if (usbCollegato) result = inviaAlMac(testo);
            if (result == null) result = comandoOffline(testo);
            final String finalResult = result;
            main.post(() -> {
                risposta.setText(finalResult);
                voce.setText(usbCollegato ? "USB LINK / READY" : "OFFLINE / STANDBY");
            });
        });
    }

    private String inviaAlMac(String testo) {
        try {
            URL url = new URL(reverseEndpoint + "/api/comando");
            HttpURLConnection c = (HttpURLConnection) url.openConnection();
            c.setConnectTimeout(1500);
            c.setReadTimeout(3000);
            c.setRequestMethod("POST");
            c.setDoOutput(true);
            c.setRequestProperty("Content-Type", "application/json; charset=utf-8");
            String body = "{\"comando\":\"" + escape(testo) + "\"}";
            c.getOutputStream().write(body.getBytes(StandardCharsets.UTF_8));
            if (c.getResponseCode() != 200) return null;
            BufferedReader r = new BufferedReader(new InputStreamReader(c.getInputStream(), StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder(); String line;
            while ((line = r.readLine()) != null) sb.append(line);
            String answer = jsonValue(sb.toString(), "risposta");
            c.disconnect();
            return answer == null ? "Comando ricevuto dal Core." : answer;
        } catch (Exception ignored) {
            return null;
        }
    }

    private String comandoOffline(String testo) {
        String c = testo.toLowerCase(Locale.ITALIAN).trim();
        if (c.startsWith("jarvis")) c = c.substring(6).trim();
        if (c.equals("jarvis")) return "Sono qui. Modalità offline attiva.";
        if (c.contains("che ore sono") || c.equals("ora")) return "Sono le " + new SimpleDateFormat("HH:mm", Locale.ITALIAN).format(new Date()) + ".";
        if (c.contains("che giorno è") || c.contains("che data è") || c.equals("data")) return "Oggi è il " + new SimpleDateFormat("dd/MM/yyyy", Locale.ITALIAN).format(new Date()) + ".";
        if (c.contains("stato sistema") || c.contains("stato")) return "Core locale operativo. Connessione USB: " + (usbCollegato ? "attiva" : "assente") + ". Modalità offline pronta.";
        if (c.contains("torna sul mac") || c.contains("ritorna sul mac") || c.contains("torna al mac")) {
            if (usbCollegato) {
                ritornoRichiesto = true;
                return "Richiesta di ritorno al Mac inviata.";
            }
            return "Il Mac non è collegato via USB. Rimango operativo sul telefono.";
        }
        return "Modalità offline: comando non disponibile localmente. Ricollegare il telefono al Mac per usare il Core completo.";
    }

    private void preparaVoce() {
        if (!SpeechRecognizer.isRecognitionAvailable(this)) return;
        speech = SpeechRecognizer.createSpeechRecognizer(this);
        speech.setRecognitionListener(new RecognitionListener() {
            @Override public void onReadyForSpeech(Bundle params) { recognitionRunning = true; main.post(() -> voce.setText("LISTENING")); }
            @Override public void onBeginningOfSpeech() { }
            @Override public void onRmsChanged(float rmsdB) { }
            @Override public void onBufferReceived(byte[] buffer) { }
            @Override public void onEndOfSpeech() { recognitionRunning = false; }
            @Override public void onError(int error) { recognitionRunning = false; main.post(() -> voce.setText(usbCollegato ? "USB LINK / READY" : "OFFLINE / STANDBY")); }
            @Override public void onResults(Bundle results) {
                recognitionRunning = false;
                ArrayList<String> values = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                if (values == null || values.isEmpty()) return;
                String spoken = values.get(0).trim();
                String normalized = spoken.toLowerCase(Locale.ITALIAN);
                if (usbCollegato && normalized.matches(".*\\bjarvis\\b.*")) {
                    ritornoRichiesto = true;
                    main.post(() -> risposta.setText("Wake word rilevata. Richiesta di ritorno al Mac."));
                    return;
                }
                inviaComando(spoken);
            }
            @Override public void onPartialResults(Bundle partialResults) { }
            @Override public void onEvent(int eventType, Bundle params) { }
        });
        if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, AUDIO_PERMISSION);
        }
    }

    private void ascolta() {
        if (speech == null) return;
        if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) return;
        Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "it-IT");
        intent.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false);
        try { speech.startListening(intent); } catch (Exception ignored) { }
    }

    private String jsonValue(String json, String key) {
        String needle = "\"" + key + "\"";
        int p = json.indexOf(needle);
        if (p < 0) return null;
        p = json.indexOf(':', p + needle.length());
        if (p < 0) return null;
        int i = p + 1;
        while (i < json.length() && Character.isWhitespace(json.charAt(i))) i++;
        if (i >= json.length()) return null;
        if (json.charAt(i) == '"') {
            i++;
            StringBuilder s = new StringBuilder();
            boolean esc = false;
            while (i < json.length()) {
                char ch = json.charAt(i++);
                if (esc) { s.append(ch); esc = false; }
                else if (ch == '\\') esc = true;
                else if (ch == '"') break;
                else s.append(ch);
            }
            return s.toString();
        }
        int e = i;
        while (e < json.length() && ",}".indexOf(json.charAt(e)) < 0) e++;
        return json.substring(i, e).trim();
    }

    private String escape(String s) { return s.replace("\\", "\\\\").replace("\"", "\\\""); }
    private String safe(String s) { return escape(s == null ? "" : s); }

    @Override
    protected void onDestroy() {
        try { if (speech != null) speech.destroy(); } catch (Exception ignored) { }
        try { if (serverSocket != null) serverSocket.close(); } catch (Exception ignored) { }
        executor.shutdownNow();
        super.onDestroy();
    }

    @Override
    protected void onResume() {
        super.onResume();
        main.postDelayed(() -> { if (sessioneAttiva && !recognitionRunning) ascolta(); }, 800);
    }
}
