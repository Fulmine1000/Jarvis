import threading
import time

from voce.wake_word import WakeWordJarvis
from voce.riconoscimento import RiconoscitoreVoce


class MotoreAscolto:
    """Ascolto continuo: wake word -> comando -> risposta."""

    DUPLICATO_TIMEOUT = 1.5
    RISPOSTE_ECO = {"sono qui", "sono qui.", "sono qui!", "qui", "qui.", "qui!", "qui?"}

    def __init__(self, modulo_voce):
        self.modulo_voce = modulo_voce
        self.nome = "Motore Ascolto"
        self.attivo = False
        self.thread = None
        self.wake_word = self._crea_wake_word()
        self._ultimo_testo = None
        self._ultimo_testo_timestamp = 0.0
        self._duplicate_lock = threading.Lock()
        self._hud_listening = False

    def _crea_wake_word(self):
        """Costruisce la wake word usando la configurazione del modulo."""
        config = getattr(self.modulo_voce, "config", None)
        if config:
            try:
                voce = config.sezione("voce")
                parole = voce.get("wake_words")
                if not parole:
                    parola = voce.get("wake_word", "jarvis")
                    parole = [parola]
                timeout = voce.get("wake_timeout", 5)
                return WakeWordJarvis(parole=parole, timeout=timeout)
            except Exception:
                pass
        return WakeWordJarvis()

    def avvia(self):
        if self.attivo:
            return True
        self.attivo = True
        self._reset_duplicato()
        self._imposta_hud_ascolto(False)
        self.log("Motore ascolto Jarvis avviato.")
        self.thread = threading.Thread(target=self.ciclo, name="JarvisAudio", daemon=True)
        self.thread.start()
        return True

    @staticmethod
    def _normalizza_testo(testo):
        return " ".join(str(testo or "").lower().strip().split())

    @staticmethod
    def _normalizza_trascrizione(testo):
        """Applica una seconda normalizzazione mirata prima di cercare la wake word.

        Il riconoscitore principale normalizza già il testo, ma questo passaggio
        difensivo protegge il motore se un backend o un test restituisce la
        trascrizione grezza. Le correzioni restano quelle esplicite e conservative
        definite in RiconoscitoreVoce; non viene usato fuzzy matching generico.
        """
        grezzo = " ".join(str(testo or "").lower().strip().split())
        corretto = RiconoscitoreVoce.normalizza_comando_riconosciuto(grezzo)
        corretto = " ".join(str(corretto or "").lower().strip().split())

        # Non correggere qui "barry jiu su" quando è seguito da altre parole:
        # potrebbe essere una frase ambientale. Le frasi complete con comando
        # vengono recuperate tramite le alternative N-best di Vosk, se presenti.
        # In assenza di un'alternativa affidabile, manteniamo il testo originale.
        return corretto

    def _e_duplicato_immediato(self, testo):
        normalizzato = self._normalizza_testo(testo)
        if not normalizzato:
            return False
        adesso = time.monotonic()
        with self._duplicate_lock:
            duplicato = (
                normalizzato == self._ultimo_testo
                and adesso - self._ultimo_testo_timestamp < self.DUPLICATO_TIMEOUT
            )
            self._ultimo_testo = normalizzato
            self._ultimo_testo_timestamp = adesso
            return duplicato

    def _reset_duplicato(self):
        with self._duplicate_lock:
            self._ultimo_testo = None
            self._ultimo_testo_timestamp = 0.0

    @staticmethod
    def _e_prefisso_attivazione_incompleto(testo):
        """True quando Vosk ha riconosciuto solo 'ehi' o 'hey', non la wake word."""
        return " ".join(str(testo or "").lower().strip().split()) in {"ehi", "hey"}

    def _e_eco_jarvis(self, testo):
        """Ignora la risposta di Jarvis anche se Vosk include la wake word.

        Il microfono resta aperto mentre Jarvis parla: Vosk puo\n        trascrivere "Sono qui" come "jarvis sono qui" oppure "jarvis qui".
        Prima di confrontare la frase rimuoviamo soltanto un prefisso di
        attivazione noto, senza alterare il testo dei normali comandi.
        """
        normalizzato = self._normalizza_testo(testo)
        for prefisso in ("hey jarvis ", "ehi jarvis ", "jarvis "):
            if normalizzato.startswith(prefisso):
                normalizzato = normalizzato[len(prefisso):].strip()
                break
        return normalizzato in self.RISPOSTE_ECO

    def _imposta_hud_ascolto(self, attivo):
        """Aggiorna LISTENING solo quando cambia realmente la sessione vocale.

        Il microfono e sempre attivo per la wake word, quindi non dobbiamo
        chiamare HUD.imposta_ascolto() per ogni blocco audio. LISTENING viene
        mostrato soltanto dopo il rilevamento della wake word e resta stabile
        fino alla disattivazione/timeout.
        """
        attivo = bool(attivo)
        if attivo == self._hud_listening:
            return
        self._hud_listening = attivo
        hud = getattr(self.modulo_voce.kernel, "hud", None)
        if hud:
            try:
                hud.imposta_ascolto(attivo)
            except Exception:
                pass

    def _sincronizza_hud_wake_word(self):
        """Mantiene l'HUD sincronizzato con lo stato reale della wake word."""
        attiva = bool(self.wake_word.verifica_timeout())
        self._imposta_hud_ascolto(attiva)
        return attiva

    def _mostra_hud(self):
        """Porta l'HUD in primo piano quando viene rilevata la wake word."""
        hud = getattr(self.modulo_voce.kernel, "hud", None)
        if not hud or not getattr(hud, "finestra", None):
            return
        try:
            hud.mostra()
            hud.registra_evento("Wake word rilevata: HUD attivato")
        except Exception as errore:
            self.log(f"Impossibile mostrare HUD: {errore}")

    def ciclo(self):
        while self.attivo and getattr(self.modulo_voce, "ascolto_attivo", False):
            try:
                # Prima di leggere il prossimo blocco audio, aggiorna lo stato
                # visuale in base alla wake word, non in base al timeout del
                # singolo blocco del microfono.
                self._sincronizza_hud_wake_word()

                testo = self.modulo_voce.ascolta_comando()
                if not testo:
                    # ascolta_comando() ha già consumato un blocco audio (circa
                    # 100 ms) oppure ha atteso la coda. Dormire qui rallenta il
                    # consumer rispetto al microfono e accumula fino a 4 secondi
                    # di audio vecchio, facendo perdere la wake word.
                    ascoltatore = getattr(self.modulo_voce, "ascoltatore", None)
                    if ascoltatore is not None and not getattr(ascoltatore, "attivo", True):
                        # Evita un busy-loop solo se il listener si è fermato.
                        time.sleep(0.05)
                    continue

                normalizzato = self._normalizza_trascrizione(testo)
                testo_grezzo = self._normalizza_testo(testo)
                if normalizzato != testo_grezzo:
                    self.log(
                        "Correzione trascrizione vocale (motore): "
                        f"{testo_grezzo!r} -> {normalizzato!r}"
                    )
                self.log(f"Trascrizione riconosciuta: {normalizzato}")

                # Diagnostica utile per distinguere un errore di STT da un
                # problema del microfono/filtro. Non registra né salva audio.
                riconoscitore = getattr(self.modulo_voce, "riconoscitore", None)
                ascoltatore = getattr(self.modulo_voce, "ascoltatore", None)
                if riconoscitore is not None:
                    backend = getattr(riconoscitore, "backend_attivo", "sconosciuto")
                    confidenza = getattr(riconoscitore, "ultima_confidenza_media", None)
                    dettagli = getattr(riconoscitore, "ultime_parole_riconosciute", [])
                    grezzo = getattr(riconoscitore, "ultima_trascrizione_grezza", "")
                    normalizzata_stt = getattr(
                        riconoscitore, "ultima_trascrizione_normalizzata", ""
                    )
                    info = f"backend={backend}"
                    if grezzo and grezzo != normalizzata_stt:
                        info += (
                            f", trascrizione_grezza={grezzo!r}"
                            f", trascrizione_normalizzata={normalizzata_stt!r}"
                        )
                    if confidenza is not None:
                        info += f", confidenza_media={confidenza:.3f}"
                    if dettagli:
                        info += f", parole={dettagli}"
                    if ascoltatore is not None:
                        stato_audio = ascoltatore.stato()
                        info += (
                            f", rms_ingresso={stato_audio.get('rms_ingresso', 'n/d')}"
                            f", rms_filtrato={stato_audio.get('rms_filtrato', 'n/d')}"
                        )
                    self.log(f"Diagnostica riconoscimento: {info}")

                if self._e_eco_jarvis(normalizzato):
                    self.log(f"Eco della risposta Jarvis ignorata: {normalizzato}")
                    self._reset_duplicato()
                    continue

                if self._e_duplicato_immediato(normalizzato):
                    self.log(f"Trascrizione duplicata ignorata: {normalizzato}")
                    continue

                risultato = self.wake_word.controlla(normalizzato)
                if not risultato or not risultato.get("attivato", False):
                    # Se la wake word e scaduta, torna a STANDBY senza creare
                    # una nuova transizione ad ogni blocco audio.
                    self._sincronizza_hud_wake_word()
                    continue

                # Da questo momento la wake word e realmente attiva: l'HUD
                # entra in LISTENING e vi rimane fino al timeout o al comando.
                self._imposta_hud_ascolto(True)
                self._mostra_hud()

                # Una wake word seguita da una sola parola non affidabile
                # (es. "jarvis su") è spesso un frammento riconosciuto male.
                # Manteniamo la finestra di ascolto aperta senza eseguire nulla
                # e senza rispondere a voce, così non generiamo altra eco.
                if risultato.get("parziale", False):
                    self.log(
                        "Frammento vocale incompleto ignorato: "
                        f"{risultato.get('trascrizione', normalizzato)}"
                    )
                    continue

                comando = risultato.get("comando", "").strip()
                if not comando:
                    # Vosk può dividere "Ehi Jarvis" in due segmenti:
                    # "ehi" e poi "jarvis". Non rispondere al solo prefisso,
                    # altrimenti la sintesi parte prima che arrivi il comando
                    # e può rientrare nel microfono come eco.
                    if self._e_prefisso_attivazione_incompleto(normalizzato):
                        self.log(
                            f"Prefisso di attivazione incompleto ignorato: {normalizzato}"
                        )
                        continue
                    self.modulo_voce.rispondi("Sono qui.")
                    continue

                self.log(f"Comando ricevuto: {comando}")

                # La sessione di ascolto termina PRIMA di eseguire il comando.
                # La risposta vocale puo' richiedere tempo (in particolare XTTS)
                # e non deve lasciare l'HUD bloccato su LISTENING mentre Jarvis parla.
                self.wake_word.disattiva()
                self._reset_duplicato()
                self._imposta_hud_ascolto(False)

                self.modulo_voce.kernel.esegui_comando(comando)

            except Exception as errore:
                self.log(f"Errore motore ascolto: {errore}")
                self._imposta_hud_ascolto(False)
                time.sleep(1)
            # La coda audio regola già il ritmo del ciclo: una pausa qui
            # farebbe accumulare blocchi più velocemente di quanto vengano letti.

    def ferma(self):
        self.attivo = False
        self.wake_word.disattiva()
        self._reset_duplicato()
        self._imposta_hud_ascolto(False)
        if self.thread:
            self.thread.join(timeout=2)
            self.thread = None
        self.log("Motore ascolto fermato.")
        return True

    def riavvia(self):
        self.ferma()
        time.sleep(0.2)
        return self.avvia()

    def log(self, messaggio):
        try:
            if self.modulo_voce and self.modulo_voce.kernel and self.modulo_voce.kernel.logger:
                self.modulo_voce.kernel.logger.info(messaggio)
            else:
                print(messaggio)
        except Exception:
            print(messaggio)

    def stato(self):
        return {
            "nome": self.nome,
            "stato": "attivo" if self.attivo else "spento",
            "thread": self.thread.is_alive() if self.thread else False,
            "wake_word": self.wake_word.stato(),
        }


def main():
    """Avvio standalone: `python -m voce.motore_ascolto` mantiene Jarvis in ascolto."""
    from core.kernel import KernelJarvis

    kernel = KernelJarvis()
    try:
        if not kernel.avvia():
            return 1

        voce = kernel.modulo_voce
        if not getattr(voce, "ascolto_attivo", False):
            print("Audio non disponibile: impossibile avviare l'ascolto vocale.")
            return 1

        print("Jarvis in ascolto. Di' 'Ehi Jarvis' oppure 'Hey Jarvis'. Premi Ctrl+C per uscire.")
        while kernel.stato == "Operativo" and not kernel.arresto_richiesto:
            time.sleep(0.5)
        return 0
    except KeyboardInterrupt:
        print("\nArresto richiesto.")
        return 0
    finally:
        kernel.arresta()


if __name__ == "__main__":
    raise SystemExit(main())
