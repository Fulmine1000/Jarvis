"""Test per le correzioni mirate delle trascrizioni Vosk osservate in Jarvis."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voce.riconoscimento import RiconoscitoreVoce


class TestSelezioneModelloVosk(unittest.TestCase):
    def test_preferisce_modello_completo_se_installato_fuori_da_mac_intel(self):
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as base:
            os.mkdir(os.path.join(base, "vosk-model-small-it-0.22"))
            os.mkdir(os.path.join(base, "vosk-model-it-0.22"))
            with patch("voce.riconoscimento.sys.platform", "linux"), patch(
                "voce.riconoscimento.platform.machine", return_value="x86_64"
            ):
                self.assertEqual(
                    RiconoscitoreVoce._modello_italiano_predefinito(base),
                    os.path.join(base, "vosk-model-it-0.22"),
                )

    def test_preferisce_modello_small_su_mac_intel_anche_se_completo_installato(self):
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as base:
            os.mkdir(os.path.join(base, "vosk-model-small-it-0.22"))
            os.mkdir(os.path.join(base, "vosk-model-it-0.22"))
            with patch("voce.riconoscimento.sys.platform", "darwin"), patch(
                "voce.riconoscimento.platform.machine", return_value="x86_64"
            ):
                self.assertEqual(
                    RiconoscitoreVoce._modello_italiano_predefinito(base),
                    os.path.join(base, "vosk-model-small-it-0.22"),
                )

    def test_usa_modello_small_se_completo_non_installato(self):
        with tempfile.TemporaryDirectory() as base:
            os.mkdir(os.path.join(base, "vosk-model-small-it-0.22"))
            self.assertEqual(
                RiconoscitoreVoce._modello_italiano_predefinito(base),
                os.path.join(base, "vosk-model-small-it-0.22"),
            )

    def test_fornisce_percorso_small_se_non_ce_nessun_modello(self):
        with tempfile.TemporaryDirectory() as base:
            self.assertEqual(
                RiconoscitoreVoce._modello_italiano_predefinito(base),
                os.path.join(base, "vosk-model-small-it-0.22"),
            )


class TestDettaglioVosk(unittest.TestCase):
    def test_calcola_confidenza_media_solo_per_diagnostica(self):
        riconoscitore = RiconoscitoreVoce()
        riconoscitore._registra_dettaglio_vosk({
            "text": "jarvis ciao",
            "result": [
                {"word": "jarvis", "conf": 0.8},
                {"word": "ciao", "conf": 0.6},
                {"word": "rumore", "conf": -1},
            ],
        })
        self.assertEqual(riconoscitore.ultima_confidenza_media, 0.7)
        self.assertEqual(riconoscitore.ultime_parole_riconosciute, ["jarvis", "ciao", "rumore"])

    def test_dettaglio_vosk_mancante_non_blocca(self):
        riconoscitore = RiconoscitoreVoce()
        riconoscitore._registra_dettaglio_vosk({"text": "jarvis"})
        self.assertIsNone(riconoscitore.ultima_confidenza_media)
        self.assertEqual(riconoscitore.ultime_parole_riconosciute, [])


class TestAlternativeVosk(unittest.TestCase):
    def test_abilita_alternative_nbest_solo_fuori_da_macos(self):
        from unittest.mock import patch

        class RiconoscitoreFinto:
            def __init__(self):
                self.words_calls = []
                self.alternative_count = None

            def SetWords(self, valore):
                self.words_calls.append(valore)

            def SetMaxAlternatives(self, numero):
                self.alternative_count = numero

        riconoscitore = RiconoscitoreVoce()
        riconoscitore.riconoscitore = RiconoscitoreFinto()

        # Sul Mac disabilitiamo N-best perché i log live hanno mostrato
        # ripetuti JSON Vosk malformati. Su Linux/Windows resta disponibile.
        with patch("voce.riconoscimento.sys.platform", "darwin"):
            riconoscitore._abilita_dettaglio_parole()
        self.assertEqual(riconoscitore.riconoscitore.words_calls, [])
        self.assertIsNone(riconoscitore.riconoscitore.alternative_count)

        with patch("voce.riconoscimento.sys.platform", "linux"):
            riconoscitore._abilita_dettaglio_parole()
        self.assertEqual(riconoscitore.riconoscitore.alternative_count, 5)

    def test_compatibile_se_vosk_non_supporta_metodi_opzionali(self):
        class RiconoscitoreFinto:
            pass

        riconoscitore = RiconoscitoreVoce()
        riconoscitore.riconoscitore = RiconoscitoreFinto()
        self.assertTrue(riconoscitore._abilita_dettaglio_parole())

    def test_preferisce_wake_word_se_alternativa_e_vicina(self):
        risultato = {
            "alternatives": [
                {"text": "vari giù", "confidence": 0.81},
                {"text": "barry jiu su", "confidence": 0.76},
                {"text": "rumore", "confidence": 0.30},
            ]
        }
        scelta = RiconoscitoreVoce._scegli_alternativa_vosk(risultato)
        self.assertEqual(scelta["text"], "jarvis")

    def test_recupera_comando_se_alternativa_contiene_wake_word(self):
        risultato = {
            "alternatives": [
                {"text": "barry jiu su che ore sono", "confidence": 0.90},
                {"text": "jarvis che ore sono", "confidence": 0.82},
                {"text": "che ore sono", "confidence": 0.55},
            ]
        }
        scelta = RiconoscitoreVoce._scegli_alternativa_vosk(risultato)
        self.assertEqual(scelta["text"], "jarvis che ore sono")

    def test_non_preferisce_wake_word_con_confidenza_troppo_bassa(self):
        risultato = {
            "alternatives": [
                {"text": "apri safari", "confidence": 0.91},
                {"text": "jarvis", "confidence": 0.40},
            ]
        }
        scelta = RiconoscitoreVoce._scegli_alternativa_vosk(risultato)
        self.assertEqual(scelta["text"], "apri safari")

    def test_risultato_vosk_standard_senza_alternative_invariato(self):
        risultato = {"text": "jarvis che ore sono", "result": []}
        self.assertIs(
            RiconoscitoreVoce._scegli_alternativa_vosk(risultato), risultato
        )

class TestNormalizzazioneVocale(unittest.TestCase):
    def test_riconosci_registra_trascrizione_grezza_e_correzione(self):
        class RiconoscitoreFinto:
            def AcceptWaveform(self, audio):
                return True

            def Result(self):
                return (
                    '{"text": "barry jiu su che ore sono", '
                    '"result": ['
                    '{"word": "barry", "conf": 0.8}, '
                    '{"word": "jiu", "conf": 0.6}, '
                    '{"word": "su", "conf": 0.7}, '
                    '{"word": "che", "conf": 0.9}, '
                    '{"word": "ore", "conf": 0.9}, '
                    '{"word": "sono", "conf": 0.9}'
                    ']}'
                )

        riconoscitore = RiconoscitoreVoce()
        riconoscitore.attivo = True
        riconoscitore.backend_attivo = "vosk"
        riconoscitore.riconoscitore = RiconoscitoreFinto()

        comando = riconoscitore.riconosci(b"\\x00\\x00")

        self.assertEqual(comando, "jarvis che ore sono")
        self.assertEqual(
            riconoscitore.ultima_trascrizione_grezza,
            "barry jiu su che ore sono",
        )
        self.assertEqual(
            riconoscitore.ultima_trascrizione_normalizzata,
            "jarvis che ore sono",
        )
        self.assertEqual(riconoscitore.ultima_confidenza_media, 0.8)
        self.assertEqual(
            riconoscitore.ultime_parole_riconosciute,
            ["barry", "jiu", "su", "che", "ore", "sono"],
        )

    def test_stato_cybersecurity_trascritto_male(self):
        casi = (
            "stato sai per security",
            "stato sarebbe security",
            "stato sarebbero security",
            "stato sarebbero servizi",
            "stato sarebbero giur it",
            "controlla la sicurezza",
            "controllare la sicurezza",
            "controllo sicurezza",
            "stato sai per giur it",
            "stato sei bersi giur it",
            "sei bersi giur it",
            "stato sai bersi uniti",
            "sai per security",
            "cybersecurity",
            "cyber security",
        )
        for testo in casi:
            with self.subTest(testo=testo):
                self.assertEqual(
                    RiconoscitoreVoce.normalizza_comando_riconosciuto(testo),
                    "stato cybersecurity",
                )

    def test_wake_word_errata_e_comandi_quotidiani(self):
        casi = {
            "giardino controllo la sicurezza": "giardino controllo la sicurezza",
            "jervis che ore sono": "jarvis che ore sono",
            "gervis che giorno oggi": "jarvis che giorno è",
            "che ore e": "che ore sono",
            "che data oggi": "che data è",
            "ricerca web ultime novità sull'intelligenza artificiale":
                "cerca sul web ultime novità sull'intelligenza artificiale",
            "cerca sul webb ultime novità": "cerca sul web ultime novità",
            "hey jarvis che ore e": "hey jarvis che ore sono",
            "barry jiu su": "jarvis",
            "Barry Jiu Su,": "jarvis",
            "barry giu su": "jarvis",
            "barry giù su": "jarvis",
            "barri jiu su": "jarvis",
            "vari giu su": "jarvis",
            "vari giù su": "jarvis",
            "barry jiu su che ore sono": "jarvis che ore sono",
            "barry giu su che ore sono": "jarvis che ore sono",
            "barri jiu su che ore sono": "jarvis che ore sono",
            "vari giu su che ore sono": "jarvis che ore sono",
            "jarvis che risuona": "jarvis che ore sono",
            "jervis che risuona": "jarvis che ore sono",
            "gervis che risuona": "jarvis che ore sono",
            "barry jiu su, che ore sono": "jarvis che ore sono",
            "Barry Jiu Su, che ore sono?": "jarvis che ore sono",
            "barry jiu su; che ore e": "jarvis che ore sono",
            "barry jiu su, george harrison": "jarvis che ore sono",
            # Non correggere testo libero dopo una wake word ambigua.
            "barry jiu su, vicino alla porta": "barry jiu su, vicino alla porta",
        }
        for testo, atteso in casi.items():
            with self.subTest(testo=testo):
                self.assertEqual(
                    RiconoscitoreVoce.normalizza_comando_riconosciuto(testo),
                    atteso,
                )

    def test_frase_non_correlata_conserva_maiuscole(self):
        testo = "Jarvis leggi file /Users/Simone/Documenti/Prova.txt"
        self.assertEqual(
            RiconoscitoreVoce.normalizza_comando_riconosciuto(testo),
            testo,
        )

    def test_stato_cybersecurity_con_wake_word(self):
        casi = (
            "jarvis stato sai per security",
            "jarvis stato sarebbero security",
            "jarvis controllare la sicurezza",
            "ehi jarvis stato sai per security",
            "hey jarvis stato sai per security",
        )
        atteso = (
            "jarvis stato cybersecurity",
            "jarvis stato cybersecurity",
            "jarvis stato cybersecurity",
            "ehi jarvis stato cybersecurity",
            "hey jarvis stato cybersecurity",
        )
        for testo, canonico in zip(casi, atteso):
            with self.subTest(testo=testo):
                self.assertEqual(
                    RiconoscitoreVoce.normalizza_comando_riconosciuto(testo),
                    canonico,
                )

    def test_cybersecurity_trascritto_foneticamente(self):
        self.assertEqual(
            RiconoscitoreVoce.normalizza_comando_riconosciuto("sai bersi uniti"),
            "cybersecurity",
        )

    def test_comando_rete_trascritto_male(self):
        casi = (
            "analizzano il mia rete",
            "analizzano la mia rete",
            "analizza il mia rete",
        )
        for testo in casi:
            with self.subTest(testo=testo):
                self.assertEqual(
                    RiconoscitoreVoce.normalizza_comando_riconosciuto(testo),
                    "analizza la mia rete",
                )

    def test_comando_rete_con_wake_word(self):
        self.assertEqual(
            RiconoscitoreVoce.normalizza_comando_riconosciuto(
                "jarvis analizzano il mia rete"
            ),
            "jarvis analizza la mia rete",
        )

    def test_punteggiatura_finale_non_impedisce_correzione(self):
        self.assertEqual(
            RiconoscitoreVoce.normalizza_comando_riconosciuto("stato sai per security."),
            "stato cybersecurity",
        )

    def test_frasi_non_correlate_restano_invariate(self):
        for testo in ("che ore sono", "che risuona", "apri Safari", "ricorda colore è blu"):
            with self.subTest(testo=testo):
                self.assertEqual(
                    RiconoscitoreVoce.normalizza_comando_riconosciuto(testo),
                    testo,
                )


if __name__ == "__main__":
    unittest.main()
