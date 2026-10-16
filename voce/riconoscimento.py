from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from typing import Any


class RiconoscitoreVoce:
    """Riconoscimento vocale Vosk con caricamento nativo ritardato e sicuro."""

    def __init__(self, config=None):
        self.nome = "Riconoscitore Vocale"
        self.config = config
        self.attivo = False
        self.modello = None
        self.riconoscitore = None
        self.lingua = "it"
        self.disponibile = self._vosk_disponibile()
        self.ultimo_errore = None
        # Conserva la coppia grezzo/corretto per diagnosticare le trascrizioni
        # vocali senza registrare o salvare l'audio.
        self.ultima_trascrizione_grezza = ""
        self.ultima_trascrizione_normalizzata = ""
        # Confidenza Vosk solo diagnostica: non viene usata per scartare comandi.
        self.ultima_confidenza_media = None
        self.ultime_parole_riconosciute = []
        self._Model = None
        self._KaldiRecognizer = None
        self.multilingue = None
        self.backend_attivo = "vosk"
        self.usa_multilingue = False

        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Se è presente il modello italiano completo, preferiscilo: nei benchmark
        # ufficiali ha un tasso di errore sensibilmente inferiore al modello small.
        # Non scarichiamo modelli grandi automaticamente e manteniamo il fallback.
        self._modello_auto = True
        self.percorso_modello = self._modello_italiano_predefinito(base)
        self.sample_rate = 16000

        if self.config:
            voce = self.config.sezione("voce")
            modello = voce.get("modello_riconoscimento", None)
            if modello:
                self._modello_auto = False
                self.percorso_modello = (
                    modello if os.path.isabs(modello) else os.path.join(base, modello)
                )
            self.sample_rate = int(voce.get("sample_rate", 16000))
            self.usa_multilingue = bool(voce.get("riconoscimento_multilingue", False))
            if self.usa_multilingue:
                try:
                    from voce.whisper_multilingue import WhisperMultilingue
                    modello_multi = voce.get("modello_multilingue", "motore_ia/whisper.cpp/models/ggml-base.bin")
                    eseguibile_multi = voce.get("eseguibile_multilingue", "")
                    self.multilingue = WhisperMultilingue(
                        modello=os.path.join(base, modello_multi) if not os.path.isabs(modello_multi) else modello_multi,
                        eseguibile=eseguibile_multi,
                        sample_rate=self.sample_rate,
                        timeout=voce.get("timeout_multilingue", 90),
                        soglia_rms=voce.get("soglia_rms_whisper", 100),
                        lingua=voce.get("lingua", "it-IT"),
                    )
                except (ImportError, OSError, ValueError, TypeError) as errore:
                    self.ultimo_errore = str(errore)

    @staticmethod
    def _modello_italiano_predefinito(base):
        """Seleziona il modello italiano migliore già installato, senza download impliciti."""
        completo = os.path.join(base, "vosk-model-it-0.22")
        leggero = os.path.join(base, "vosk-model-small-it-0.22")
        if os.path.isdir(completo):
            return completo
        return leggero

    @staticmethod
    def _vosk_disponibile():
        """Verifica Vosk rispettando anche i test che bloccano il modulo."""
        if "vosk" in sys.modules and sys.modules["vosk"] is None:
            return False
        try:
            return importlib.util.find_spec("vosk") is not None
        except (ImportError, ModuleNotFoundError, OSError, ValueError):
            return False

    @staticmethod
    def normalizza_comando_riconosciuto(testo):
        """Normalizza errori fonetici frequenti senza riscrivere frasi arbitrarie.

        Le correzioni si applicano a frasi complete e non usano fuzzy matching
        sui comandi operativi. I testi non riconosciuti restano invariati.
        """
        originale = str(testo or "").strip()
        confronto = re.sub(r"\s+", " ", originale.lower()).strip()
        confronto = re.sub(r"[.,!?;:]+$", "", confronto).strip()
        confronto = confronto.replace("’", "'")

        # Variante osservata nei log del Mac: Vosk può trascrivere
        # la wake word isolata come "barry jiu su". Correggiamo SOLO la
        # frase esatta: estendere l'alias a qualunque frase successiva può
        # trasformare conversazioni ambientali in comandi involontari.
        alias_wake = "barry jiu su"
        if confronto == alias_wake:
            return "jarvis"

        # Correggi anche la sola frase completa osservata nei log quando
        # Vosk unisce wake word e richiesta dell'ora. La correzione è
        # intenzionalmente esatta: non correggere prefissi ambigui o frasi
        # con punteggiatura interna, che potrebbero essere conversazioni.
        alias_frasi_complete = {
            "barry jiu su che ore sono": "jarvis che ore sono",
            "barry jiu su che harrison": "jarvis che ore sono",
        }
        if confronto in alias_frasi_complete:
            return alias_frasi_complete[confronto]

        prefisso = ""
        wake_errata = False
        resto_originale = ""
        for wake in ("hey jarvis ", "ehi jarvis ", "jarvis ", "jervis ", "gervis "):
            if confronto.startswith(wake):
                prefisso = "jarvis " if wake in ("jervis ", "gervis ") else wake
                wake_errata = wake in ("jervis ", "gervis ")
                resto_originale = originale[len(wake):].strip()
                confronto = confronto[len(wake):].strip()
                break

        alias = (
            (r"^(?:stato\s+)?sei\s+bersi\s+giur(?:\s+it)?$", "stato cybersecurity"),
            (r"^stato\s+sai\s+per\s+giur(?:\s+it)?$", "stato cybersecurity"),
            (r"^stato\s+sarebb(?:e|ero)\s+(?:security|servizi|service|giur(?:\s+it)?)$", "stato cybersecurity"),
            (r"^stato\s+sarebbe\s+security$", "stato cybersecurity"),
            (r"^(?:controlla|controllare|controllo)\s+(?:la\s+)?sicurezza$", "stato cybersecurity"),
            (r"^(?:stato\s+)?(?:sai\s+per\s+security|cyber\s*security|cybersecurity)$", "stato cybersecurity"),
            (r"^stato\s+sai\s+bersi\s+uniti$", "stato cybersecurity"),
            (r"^sai\s+bersi\s+uniti$", "cybersecurity"),
            (r"^analizzano\s+(?:il|la)\s+mia\s+rete$", "analizza la mia rete"),
            (r"^analizza\s+il\s+mia\s+rete$", "analizza la mia rete"),
            (r"^(?:che\s+)?ore\s+(?:sono|e|adesso|ora)(?:\s+(?:adesso|ora))?$", "che ore sono"),
            # Errore fonetico osservato nei log: "che harrison" per "che ore sono".
            (r"^che\s+harrison$", "che ore sono"),
            # Altre trascrizioni fonetiche osservate per la richiesta dell’ora.
            (r"^(?:georges|george)\s+harrison$", "che ore sono"),
            (r"^(?:che\s+)?ora\s+e$", "che ore sono"),
            (r"^(?:che\s+)?giorno\s+(?:e|è)(?:\s+oggi)?$", "che giorno è"),
            (r"^(?:che\s+)?giorno\s+oggi$", "che giorno è"),
            (r"^(?:che\s+)?data\s+(?:e|è)(?:\s+oggi)?$", "che data è"),
            (r"^(?:che\s+)?data\s+oggi$", "che data è"),
            (r"^ricerca\s+(?:web|online)\s+(.+)$", r"cerca sul web \1"),
            (r"^cerca\s+(?:sul\s+uep|sul\s+webb)\s+(.+)$", r"cerca sul web \1"),
            (r"^cerca\s+su\s+internet\s+(.+)$", r"cerca sul web \1"),
            (r"^cerca\s+online\s+(.+)$", r"cerca sul web \1"),
        )
        modificato = False
        for pattern, canonico in alias:
            nuovo = re.sub(pattern, canonico, confronto, count=1)
            if nuovo != confronto:
                confronto = nuovo.strip()
                modificato = True
                break

        if prefisso and modificato:
            return (prefisso + confronto).strip() if confronto else prefisso.strip()
        if prefisso and wake_errata:
            return (prefisso + resto_originale).strip() if resto_originale else prefisso.strip()
        if modificato:
            return confronto
        return originale

    def _carica_vosk(self):
        """Carica Vosk solo quando serve realmente il riconoscimento."""
        if self._Model is not None and self._KaldiRecognizer is not None:
            return True
        if not self._vosk_disponibile():
            self.disponibile = False
            self.ultimo_errore = "Vosk non disponibile"
            return False
        try:
            from vosk import KaldiRecognizer, Model
        except (ImportError, ModuleNotFoundError, OSError, RuntimeError) as errore:
            self.disponibile = False
            self.ultimo_errore = str(errore)
            return False
        self._Model = Model
        self._KaldiRecognizer = KaldiRecognizer
        self.disponibile = True
        return True

    def avvia(self):
        if self.attivo:
            return True

        # Se Whisper è stato selezionato esplicitamente in configurazione,
        # non passare silenziosamente a Vosk: sarebbe impossibile capire quale
        # motore sta riconoscendo la voce e il problema originale resterebbe.
        if self.usa_multilingue:
            if self.multilingue is None:
                self.attivo = False
                self.ultimo_errore = (
                    self.ultimo_errore
                    or "Whisper è selezionato ma non è stato inizializzato."
                )
                return False

            if self.multilingue.avvia():
                self.backend_attivo = "whisper"
                self.lingua = "auto"
                self.attivo = True
                self.ultimo_errore = None
                return True

            self.attivo = False
            self.backend_attivo = "whisper"
            self.ultimo_errore = (
                self.multilingue.ultimo_errore
                or "Whisper è selezionato ma non è riuscito ad avviarsi."
            )
            return False

        if not self.disponibile or not self._vosk_disponibile():
            self.disponibile = False
            self.attivo = False
            if not self.ultimo_errore:
                self.ultimo_errore = "Vosk non disponibile"
            return False

        if not os.path.isdir(self.percorso_modello):
            self.attivo = False
            self.ultimo_errore = f"Modello Vosk non trovato: {self.percorso_modello}"
            return False

        try:
            if not self._carica_vosk():
                return False

            try:
                self.modello = self._Model(self.percorso_modello)
            except (OSError, RuntimeError, ValueError) as errore_modello:
                # Il modello completo può richiedere troppa memoria su hardware
                # datato. Se la selezione era automatica, ripiega sul modello small.
                base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                leggero = os.path.join(base, "vosk-model-small-it-0.22")
                if not (
                    self._modello_auto
                    and os.path.basename(self.percorso_modello) == "vosk-model-it-0.22"
                    and os.path.isdir(leggero)
                ):
                    raise
                self.percorso_modello = leggero
                self.modello = self._Model(self.percorso_modello)
                self.ultimo_errore = (
                    "Modello Vosk completo non caricabile; uso il modello small. "
                    f"Dettaglio: {errore_modello}"
                )
            self.riconoscitore = self._KaldiRecognizer(self.modello, self.sample_rate)
            self._abilita_dettaglio_parole()
            self.backend_attivo = "vosk"
            self.lingua = "it"
            self.attivo = True
            self.ultimo_errore = None
            return True
        except (OSError, RuntimeError, ValueError) as errore:
            self.modello = None
            self.riconoscitore = None
            self.attivo = False
            self.ultimo_errore = str(errore)
            return False

    def _abilita_dettaglio_parole(self):
        """Abilita le confidenze senza attivare il formato N-best di Vosk.

        Su alcune build/versioni di Vosk, SetMaxAlternatives insieme a
        SetWords può produrre risultati non validi o incompatibili. Per
        mantenere stabile il riconoscimento live usiamo il risultato standard
        e conserviamo soltanto i dettagli delle parole quando supportati.
        La wake word viene gestita dalla normalizzazione conservativa.
        """
        metodo = getattr(self.riconoscitore, "SetWords", None)
        if callable(metodo):
            try:
                metodo(True)
            except (OSError, RuntimeError, TypeError, ValueError):
                pass

    @classmethod
    def _scegli_alternativa_vosk(cls, risultato):
        """Preferisce una variante vicina alla migliore solo se contiene la wake word."""
        alternative = risultato.get("alternatives")
        if not isinstance(alternative, list) or not alternative:
            return risultato
        valide = [
            item for item in alternative
            if isinstance(item, dict) and str(item.get("text", "")).strip()
        ]
        if not valide:
            return risultato

        def confidenza(item):
            try:
                return float(item.get("confidence", -1.0))
            except (TypeError, ValueError):
                return -1.0

        migliore = max(valide, key=confidenza)
        confidenza_migliore = confidenza(migliore)
        if confidenza_migliore < 0:
            return migliore

        for candidata in valide:
            testo = str(candidata.get("text", "")).strip()
            normalizzato = cls.normalizza_comando_riconosciuto(testo).lower()
            wake_rilevata = (
                normalizzato == "jarvis"
                or normalizzato.startswith("jarvis ")
                or normalizzato.startswith("hey jarvis ")
                or normalizzato.startswith("ehi jarvis ")
            )
            if wake_rilevata and confidenza(candidata) >= confidenza_migliore - 0.20:
                # Restituisci anche il testo normalizzato: prima la funzione
                # sceglieva l'alternativa corretta per la wake word, ma
                # lasciava "barry jiu su..." nel campo text, vanificando
                # la scelta quando il chiamante leggeva il risultato.
                scelta = dict(candidata)
                scelta["text"] = normalizzato
                return scelta
        return migliore

    def _registra_dettaglio_vosk(self, risultato):
        """Memorizza confidenza media e parole per diagnosi, senza filtrare comandi."""
        parole = risultato.get("result", [])
        confidenze = []
        dettagli = []
        if isinstance(parole, list):
            for parola in parole:
                if not isinstance(parola, dict):
                    continue
                testo = str(parola.get("word", "")).strip()
                if testo:
                    dettagli.append(testo)
                try:
                    confidenza = float(parola.get("conf", -1))
                except (TypeError, ValueError):
                    continue
                if 0.0 <= confidenza <= 1.0:
                    confidenze.append(confidenza)
        self.ultime_parole_riconosciute = dettagli
        self.ultima_confidenza_media = (
            round(sum(confidenze) / len(confidenze), 3) if confidenze else None
        )

    def riconosci(self, audio):
        if not self.attivo or not audio:
            return None
        if self.backend_attivo == "whisper" and self.multilingue is not None:
            testo = self.multilingue.riconosci(audio)
            if testo:
                grezzo = str(testo).strip()
                normalizzato = self.normalizza_comando_riconosciuto(grezzo)
                self.ultima_trascrizione_grezza = grezzo
                self.ultima_trascrizione_normalizzata = normalizzato
                self.ultimo_errore = None
                return normalizzato or None
            return None
        if self.riconoscitore is None:
            return None
        try:
            if not self.riconoscitore.AcceptWaveform(audio):
                return None

            risposta = self.riconoscitore.Result()
            try:
                risultato = json.loads(risposta)
            except json.JSONDecodeError as errore_json:
                # Non propagare una risposta malformata al motore di ascolto.
                # Non registriamo il testo grezzo: potrebbe contenere parole private.
                lunghezza = (
                    len(risposta)
                    if isinstance(risposta, (str, bytes, bytearray))
                    else "n/d"
                )
                self.ultimo_errore = (
                    "Risultato JSON Vosk non valido "
                    f"(riga={errore_json.lineno}, colonna={errore_json.colno}, "
                    f"lunghezza={lunghezza}); riconoscitore reimpostato"
                )
                self.reset()
                return None

            if not isinstance(risultato, dict):
                self.ultimo_errore = (
                    "Risultato Vosk inatteso: era atteso un oggetto JSON; "
                    "riconoscitore reimpostato"
                )
                self.reset()
                return None

            risultato = self._scegli_alternativa_vosk(risultato)
            self._registra_dettaglio_vosk(risultato)
            testo = str(risultato.get("text", "")).strip()
            # Conserva i dettagli appena estratti da Result(): azzerarli qui
            # cancellava la diagnostica prima che il modulo voce potesse leggerli.
            normalizzato = self.normalizza_comando_riconosciuto(testo)
            self.ultima_trascrizione_grezza = testo
            self.ultima_trascrizione_normalizzata = normalizzato
            self.ultimo_errore = None
            return normalizzato or None
        except (OSError, RuntimeError, ValueError, TypeError, json.JSONDecodeError) as errore:
            self.ultimo_errore = str(errore)
        return None

    def reset(self):
        if self.modello is not None and self._KaldiRecognizer is not None:
            try:
                self.riconoscitore = self._KaldiRecognizer(self.modello, self.sample_rate)
                self._abilita_dettaglio_parole()
            except (OSError, RuntimeError, ValueError) as errore:
                self.ultimo_errore = str(errore)
                self.riconoscitore = None
                self.attivo = False

    def ferma(self):
        self.attivo = False
        self.modello = None
        self.riconoscitore = None
        if self.multilingue is not None:
            self.multilingue.ferma()
        self.backend_attivo = "vosk"
        return True

    def stato(self):
        return {
            "nome": self.nome,
            "stato": "attivo" if self.attivo else "spento",
            "lingua": self.lingua,
            "backend": self.backend_attivo,
            "multilingue_configurato": self.usa_multilingue,
            "stato_multilingue": self.multilingue.stato() if self.multilingue else None,
            "modello": (
                self.multilingue.stato().get("modello", self.percorso_modello)
                if self.backend_attivo == "whisper" and self.multilingue
                else self.percorso_modello
            ),
            "sample_rate": self.sample_rate,
            "disponibile": self.disponibile,
            "ultimo_errore": self.ultimo_errore,
            "ultima_trascrizione_grezza": self.ultima_trascrizione_grezza,
            "ultima_trascrizione_normalizzata": self.ultima_trascrizione_normalizzata,
            "ultima_confidenza_media": self.ultima_confidenza_media,
            "ultime_parole_riconosciute": list(self.ultime_parole_riconosciute),
        }
