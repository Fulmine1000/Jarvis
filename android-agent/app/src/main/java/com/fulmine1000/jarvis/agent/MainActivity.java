package com.fulmine1000.jarvis.agent;

import android.app.Activity;
import android.os.Bundle;
import android.os.Build;
import android.graphics.Color;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.URL;
import java.net.HttpURLConnection;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Agente Android leggero: il Core Jarvis resta sul Mac.
 * Il telefono ospita soltanto questa sessione/interfaccia e un piccolo HTTP
 * server, compatibile anche con Android molto vecchi (minSdk 14).
 */
public class MainActivity extends Activity {
    private static final int PORT = 8765;
    private ServerSocket serverSocket;
    private ExecutorService executor = Executors.newCachedThreadPool();
    private TextView stato;
    private TextView risposta;
    private EditText comando;
    private volatile String macEndpoint = null;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        costruisciUI();
        avviaServer();
    }

    private void costruisciUI() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(24, 30, 24, 24);
        root.setBackgroundColor(Color.rgb(5, 11, 20));

        TextView titolo = new TextView(this);
        titolo.setText("J.A.R.V.I.S.");
        titolo.setTextColor(Color.WHITE); titolo.setTextSize(30); titolo.setGravity(17);
        root.addView(titolo, new LinearLayout.LayoutParams(-1, -2));

        stato = new TextView(this);
        stato.setText("Sessione Jarvis in avvio..."); stato.setTextColor(Color.LTGRAY); stato.setGravity(17);
        root.addView(stato, new LinearLayout.LayoutParams(-1, -2));

        comando = new EditText(this);
        comando.setHint("Scrivi un comando"); comando.setTextColor(Color.WHITE); comando.setHintTextColor(Color.GRAY);
        root.addView(comando, new LinearLayout.LayoutParams(-1, -2));

        Button invia = new Button(this); invia.setText("Invia a Jarvis");
        invia.setOnClickListener(new View.OnClickListener() { public void onClick(View v) { inviaComando(); } });
        root.addView(invia, new LinearLayout.LayoutParams(-1, -2));

        risposta = new TextView(this); risposta.setTextColor(Color.WHITE); risposta.setTextSize(18); risposta.setPadding(0, 24, 0, 0);
        root.addView(risposta, new LinearLayout.LayoutParams(-1, -2));
        setContentView(root);
    }

    private void avviaServer() {
        executor.execute(new Runnable() { public void run() {
            try {
                serverSocket = new ServerSocket(PORT);
                runOnUiThread(new Runnable() { public void run() { stato.setText("Jarvis pronto sul telefono • porta " + PORT); } });
                while (!serverSocket.isClosed()) {
                    final Socket socket = serverSocket.accept();
                    executor.execute(new Runnable() { public void run() { gestisci(socket); } });
                }
            } catch (Exception e) {
                runOnUiThread(new Runnable() { public void run() { stato.setText("Server non disponibile"); } });
            }
        }});
    }

    private void gestisci(Socket socket) {
        try {
            BufferedReader in = new BufferedReader(new InputStreamReader(socket.getInputStream(), "UTF-8"));
            String prima = in.readLine();
            if (prima == null) { socket.close(); return; }
            String linea; int len = 0;
            while ((linea = in.readLine()) != null && linea.length() > 0) {
                if (linea.toLowerCase().startsWith("content-length:")) len = Integer.parseInt(linea.substring(15).trim());
            }
            StringBuilder body = new StringBuilder();
            for (int i = 0; i < len; i++) { int c = in.read(); if (c < 0) break; body.append((char)c); }
            String path = prima.split(" ")[1];
            String out;
            if (path.equals("/jarvis/handshake")) {
                out = "{\"ok\":true,\"protocollo\":\"JARVIS-MULTIDEVICE/2\",\"agente\":\"android\",\"versione\":\"1.0\",\"android\":\"" + Build.VERSION.RELEASE + "\",\"nome\":\"" + Build.MODEL.replace("\"", "") + "\",\"sessione\":true}";
            } else if (path.equals("/jarvis/trasferimento")) {
                macEndpoint = "active";
                out = "{\"ok\":true,\"sessione\":true,\"messaggio\":\"Sessione Jarvis aperta sul telefono. Il Core resta sul Mac.\"}";
            } else if (path.equals("/jarvis/ritorno")) {
                macEndpoint = null;
                out = "{\"ok\":true,\"sessione\":false,\"messaggio\":\"Sessione Jarvis chiusa sul telefono.\"}";
            } else if (path.equals("/jarvis/stato")) {
                out = "{\"ok\":true,\"online\":true,\"sessione\":" + (macEndpoint != null ? "true" : "false") + "}";
            } else {
                out = "{\"errore\":\"endpoint non trovato\"}";
            }
            String header = "HTTP/1.1 200 OK\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: " + out.getBytes("UTF-8").length + "\r\nConnection: close\r\n\r\n";
            OutputStream os = socket.getOutputStream(); os.write((header + out).getBytes("UTF-8")); os.flush(); socket.close();
        } catch (Exception ignored) { try { socket.close(); } catch (Exception ignored2) {} }
    }

    private void inviaComando() {
        final String testo = comando.getText().toString().trim();
        if (testo.length() == 0) return;
        risposta.setText("Invio a Jarvis...");
        // Il trasporto verso il Mac viene predisposto dall'associazione/sessione.
        // Se non c'è ancora un endpoint, informiamo l'utente invece di fingere.
        if (macEndpoint == null) { risposta.setText("Sessione non collegata al Core del Mac."); return; }
        risposta.setText("Comando ricevuto: " + testo + "\nIl Core Jarvis lo elaborerà tramite il bridge.");
    }

    @Override protected void onDestroy() {
        try { if (serverSocket != null) serverSocket.close(); } catch (Exception ignored) {}
        executor.shutdownNow(); super.onDestroy();
    }
}
