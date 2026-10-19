from __future__ import annotations

import threading
import time

from voce.ascoltatore import AscoltatoreVoce
from voce.riconoscimento import RiconoscitoreVoce
from voce.sintesi import SintesiVocale
from voce.assistente_voce import AssistenteVoce
from voce.motore_ascolto import MotoreAscolto


class ModuloVoce:
    """Gestisce sintesi, microfono e riconoscimento senza bloccare Jarvis in modalita testo."""

    def __init__(self, kernel):
        self.kernel = kernel
        self.nome = "Voce"
        self.attivo = False
        self.ascolto_attivo = False
        self.sintesi_attiva = False
        self.config = kernel.config if kernel else None
        self.riconoscitore = RiconoscitoreVoce(self.config)
        voce_config = self.config.sezione("voce") if self.config else {}
        filtro_attivo = voce_config.get("filtro_rumore", True)
        livello_filtro = voce_config.get("livello_filtro_rumore", 2)
        self.ascoltatore = AscoltatoreVoce(
            frequenza=self.riconoscitore.sample_rate,
            filtro_rumore=filtro_attivo,
            livello_filtro=livello_filtro,
            soglia_rms_minima=voce_config.get("soglia_rms_minima", 12),
        )
        self.sintesi = SintesiVocale(self.config)
        self.voce_jarvis = self.sintesi
        self.assistente = AssistenteVoce(self.kernel)
        self.motore = MotoreAscolto(self)
        self._speech_lock = threading.RLock()
        self.ultimo_errore_ascolto = None
        self._ultima_diagnostica_microfono = 0.0
        self._ultimo_errore_whisper_loggato = None

    def avvia(self):
        if self.attivo:
            return True

        try:
            self.sintesi_attiva = bool(self.sintesi.avvia())
            if self.kernel and self.kernel.logger:
                stato_sintesi = self.sintesi.stato()
                motore = stato_sintesi.get("motore", "sconosciuto")
                voce_sistema = stato_sintesi.get("voce_sistema")
                if self.sintesi_attiva:
                    self.kernel.logger.info(
                        "Sintesi vocale inizializzata: "
                        f"motore={motore}, voce_sistema={voce_sistema or 'predefinita'}, "
                        f"piper_disponibile={stato_sintesi.get('piper_disponibile', False)}, "
                        f"campione_locale={stato_sintesi.get('campione_voce_locale', False)}"
                    )
                else:
                    self.kernel.logger.warning(
                        "Sintesi vocale non disponibile: Jarvis non potrà rispondere a voce."
                    )

            # Prima verifica il microfono. Se non e disponibile non carichiamo
            # Vosk: in questo modo l'avvio solo-testo non tocca librerie native.
            microfono = self.ascoltatore.avvia()
            if not microfono:
                self.riconoscitore.ferma()
                self.ascoltatore.ferma()
                self.ascolto_attivo = False
                self.attivo = True
                if self.kernel and self.kernel.logger:
                    dettaglio = self.ascoltatore.ultimo_errore or "errore non specificato"
                    self.kernel.logger.warning(
                        f"Microfono non disponibile ({dettaglio}): modalita solo-testo attiva."
                    )
                return True

            modello = self.riconoscitore.avvia()
            if not modello:
                self.ascoltatore.ferma()
                self.riconoscitore.ferma()
                self.ascolto_attivo = False
                self.attivo = True
                if self.kernel and self.kernel.logger:
                    dettaglio = self.riconoscitore.ultimo_errore or "modello o backend non disponibile"
                    self.kernel.logger.warning(
                        f"Riconoscimento vocale non disponibile ({dettaglio}): modalita solo-testo attiva."
                    )
                return True

            self.ascolto_attivo = True
            if self.kernel and self.kernel.logger:
                stato = self.riconoscitore.stato()
                stato_filtro = self.ascoltatore.stato().get("filtro_rumore", {})
                self.kernel.logger.info(
                    f"Riconoscimento vocale attivo: backend={stato.get('backend')}, "
                    f"sample_rate={stato.get('sample_rate')}, modello={stato.get('modello')}"
                )
                self.kernel.logger.info(
                    "Filtro antirumore: "
                    f"{stato_filtro.get('modalita', 'sconosciuta')} "
                    f"(attivo={stato_filtro.get('attivo', False)}, "
                    f"livello={stato_filtro.get('livello', 'n/d')})"
                )
                dettaglio_filtro = stato_filtro.get("ultimo_errore")
                if dettaglio_filtro:
                    self.kernel.logger.info(f"Filtro antirumore: {dettaglio_filtro}")
            self.assistente.avvia()
            self.motore.avvia()
            self.attivo = True
            return True

        except Exception as errore:
            try:
                self.motore.ferma()
                self.assistente.ferma()
                self.ascoltatore.ferma()
                self.riconoscitore.ferma()
            except Exception:
                pass
            self.attivo = True
            self.ascolto_attivo = False
            if self.kernel and self.kernel.logger:
                self.kernel.logger.warning(f"Voce non disponibile: modalita solo-testo attiva ({errore})")
            return True

    def _diagnostica_microfono_senza_trascrizione(self, motivo):
        """Registra ogni 5 s i livelli audio quando Vosk non produce testo.

        Serve a distinguere un microfono silenzioso/non autorizzato da un
        problema di riconoscimento. Non registra né salva l'audio.
        """
        adesso = time.monotonic()
        if adesso - self._ultima_diagnostica_microfono < 5.0:
            return
        self._ultima_diagnostica_microfono = adesso

        try:
            stato_audio = self.ascoltatore.stato()
        except Exception as errore:
            stato_audio = {}
            dettaglio_audio = f"impossibile leggere stato microfono: {errore}"
        else:
            dettaglio_audio = (
                f"microfono={stato_audio.get('stato', 'n/d')}, "
                f"stream={stato_audio.get('stream', 'n/d')}, "
                f"rms_ingresso={stato_audio.get('rms_ingresso', 'n/d')}, "
                f"rms_filtrato={stato_audio.get('rms_filtrato', 'n/d')}, "
                f"buffer={stato_audio.get('buffer', 'n/d')}/"
                f"{stato_audio.get('buffer_massimo', 'n/d')}, "
                f"blocchi_scartati={stato_audio.get('blocchi_audio_scartati', 'n/d')}, "
                f"errore_microfono={stato_audio.get('ultimo_errore') or 'nessuno'}"
            )

        errore_riconoscimento = getattr(self.riconoscitore, "ultimo_errore", None)
        messaggio = (
            f"Diagnostica audio senza trascrizione: motivo={motivo}; "
            f"backend={getattr(self.riconoscitore, 'backend_attivo', 'n/d')}; "
            f"{dettaglio_audio}; "
            f"errore_riconoscimento={errore_riconoscimento or 'nessuno'}"
        )
        if self.kernel and self.kernel.logger:
            self.kernel.logger.info(messaggio)
        else:
            print(messaggio)

    def ascolta_comando(self):
        """Acquisisce audio senza modificare lo stato LISTENING dell'HUD.

        Il microfono resta aperto continuamente per poter rilevare la wake word.
        Per questo motivo ogni blocco audio NON deve essere rappresentato come
        un nuovo ingresso/uscita dalla modalita LISTENING: lo stato visuale
        viene gestito dal MotoreAscolto in base alla wake word.
        """
        if not self.ascolto_attivo:
            return None
        try:
            audio = self.ascoltatore.ascolta()
            if not audio:
                self._diagnostica_microfono_senza_trascrizione("nessun blocco audio ricevuto")
                return None
            testo = self.riconoscitore.riconosci(audio)
            if not testo:
                self._diagnostica_microfono_senza_trascrizione("Vosk non ha ancora completato una trascrizione")
            if testo:
                self.ultimo_errore_ascolto = None
                grezzo = getattr(self.riconoscitore, "ultima_trascrizione_grezza", "")
                normalizzato = getattr(
                    self.riconoscitore, "ultima_trascrizione_normalizzata", ""
                )
                if grezzo and normalizzato and grezzo != normalizzato:
                    if self.kernel and self.kernel.logger:
                        self.kernel.logger.info(
                            "Correzione trascrizione vocale: "
                            f"{grezzo!r} -> {normalizzato!r}"
                        )

                # Diagnostica leggera: non salva né registra audio, mostra solo
                # il testo già riconosciuto e i dettagli forniti da Vosk.
                if (
                    self.riconoscitore.backend_attivo == "vosk"
                    and grezzo
                    and self.kernel
                    and self.kernel.logger
                ):
                    confidenza = self.riconoscitore.ultima_confidenza_media
                    parole = self.riconoscitore.ultime_parole_riconosciute
                    confidenza_testo = (
                        f"{confidenza:.3f}" if confidenza is not None else "non disponibile"
                    )
                    self.kernel.logger.info(
                        "Diagnostica Vosk: "
                        f"confidenza_media={confidenza_testo}; "
                        f"parole={parole if parole else 'non disponibili'}"
                    )
            if testo:
                self._ultimo_errore_whisper_loggato = None
            elif self.riconoscitore.backend_attivo == "whisper":
                # Whisper non trascrive finché non rileva voce e una pausa.
                # Rendiamo visibili errori e livelli microfono senza riempire il log.
                multilingue = self.riconoscitore.multilingue
                errore_whisper = getattr(multilingue, "ultimo_errore", None)
                if errore_whisper and errore_whisper != self._ultimo_errore_whisper_loggato:
                    self._ultimo_errore_whisper_loggato = errore_whisper
                    if self.kernel and self.kernel.logger:
                        self.kernel.logger.warning(f"Errore riconoscimento Whisper: {errore_whisper}")
                adesso = time.monotonic()
                if adesso - self._ultima_diagnostica_microfono >= 5.0:
                    self._ultima_diagnostica_microfono = adesso
                    microfono = self.ascoltatore.stato()
                    stato_whisper = multilingue.stato() if multilingue else {}
                    if self.kernel and self.kernel.logger:
                        self.kernel.logger.info(
                            "Diagnostica microfono/Whisper: "
                            f"rms_ingresso={microfono.get('rms_ingresso', 0)}, "
                            f"rms_filtrato={microfono.get('rms_filtrato', 0)}, "
                            f"soglia_voce={stato_whisper.get('soglia_rms', 'n/d')}, "
                            f"segmento={stato_whisper.get('segmento', 'n/d')}, "
                            f"lingua={stato_whisper.get('lingua_riconoscimento', 'n/d')}"
                        )
            return testo
        except Exception as errore:
            messaggio = f"{type(errore).__name__}: {errore}"
            if messaggio != self.ultimo_errore_ascolto:
                self.ultimo_errore_ascolto = messaggio
                if self.kernel and self.kernel.logger:
                    self.kernel.logger.warning(
                        f"Errore durante l'ascolto/riconoscimento: {messaggio}"
                    )
                else:
                    print(f"Errore durante l'ascolto/riconoscimento: {messaggio}")
            return None

    def elabora_voce(self, testo):
        return self.assistente.elabora(testo)

    def rispondi(self, testo):
        if not self.sintesi_attiva or not testo:
            return False
        hud = getattr(self.kernel, "hud", None)
        with self._speech_lock:
            if hud:
                hud.imposta_parlato(True)
            try:
                riuscita = bool(self.sintesi.parla(testo))
                if not riuscita and self.kernel and self.kernel.logger:
                    stato = self.sintesi.stato()
                    self.kernel.logger.warning(
                        "Sintesi vocale fallita: nessun audio riprodotto "
                        f"(motore={stato.get('motore')}, voce_sistema={stato.get('voce_sistema')})."
                    )
                return riuscita
            finally:
                if hud:
                    hud.imposta_parlato(False)

    def ferma(self):
        try:
            self.motore.ferma()
            self.assistente.ferma()
            self.ascoltatore.ferma()
            self.riconoscitore.ferma()
            self.sintesi.ferma()
        except Exception as errore:
            if self.kernel and self.kernel.logger:
                self.kernel.logger.warning(f"Errore arresto modulo voce: {errore}")
        self.attivo = False
        self.ascolto_attivo = False
        self.sintesi_attiva = False
        return True

    def stato(self):
        return {
            "nome": self.nome,
            "stato": "attivo" if self.attivo else "spento",
            "ascolto": "attivo" if self.ascolto_attivo else "spento",
            "microfono": self.ascoltatore.stato(),
            "sintesi": self.sintesi.stato(),
            "riconoscimento": self.riconoscitore.stato(),
            "assistente": self.assistente.stato(),
            "motore_ascolto": self.motore.stato(),
            "ultimo_errore_ascolto": self.ultimo_errore_ascolto,
        }
