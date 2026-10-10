"""Cybersecurity difensiva, locale e con limiti espliciti per Jarvis.

Il modulo non esegue exploit, brute force, spoofing, deauth o scansioni di
intere reti. I controlli attivi sono limitati a un singolo IP privato,
richiedono conferma esplicita e provano solo una lista ridotta di porte TCP.
Le funzioni radio/NFC/IR richiedono hardware esterno: il Mac non le emula da
solo.
"""
from __future__ import annotations

import ipaddress
import platform
import socket
from typing import Optional


class CybersecurityJarvis:
    """Strumenti di inventario e verifica difensiva per dispositivi autorizzati."""

    PORTE_CONSENTITE = (22, 53, 80, 443, 445, 548, 631, 8000, 8080, 8443)
    MASSIMO_TIMEOUT = 0.35

    def __init__(self, logger=None):
        self.logger = logger
        self._host_in_attesa: Optional[str] = None
        self._ultimo_risultato = None

    def stato(self):
        """Restituisce capacità e limiti effettivi dell'host corrente."""
        return {
            "modulo": "Cybersecurity Jarvis",
            "stato": "pronto",
            "sistema": platform.system(),
            "modalita": ["inventario passivo", "controllo TCP su singolo host privato con conferma"],
            "porte_consentite": list(self.PORTE_CONSENTITE),
            "host_in_attesa_di_conferma": self._host_in_attesa,
            "hardware_radio_nfc_ir": "non disponibile senza accessorio esterno compatibile",
            "limiti": ["nessuna scansione di subnet", "nessun exploit o brute force", "solo sistemi autorizzati"],
        }

    def analizza_rete_locale(self):
        """Mostra informazioni locali senza scansire altri dispositivi."""
        nome = socket.gethostname()
        indirizzi = set()
        try:
            for risultato in socket.getaddrinfo(nome, None, type=socket.SOCK_STREAM):
                indirizzo = risultato[4][0].split("%", 1)[0]
                try:
                    ip = ipaddress.ip_address(indirizzo)
                    if not ip.is_unspecified and not ip.is_multicast:
                        indirizzi.add(str(ip))
                except ValueError:
                    continue
        except OSError:
            pass
        try:
            import psutil  # opzionale, già usato da altri componenti Jarvis
            interfacce = sorted(psutil.net_if_addrs().keys())
        except Exception:
            interfacce = []
        risultato = {
            "host": nome,
            "indirizzi_locali": sorted(indirizzi),
            "interfacce": interfacce,
            "tipo_controllo": "sola lettura; nessun pacchetto inviato ad altri host",
        }
        self._ultimo_risultato = risultato
        self._log("Inventario rete locale completato (sola lettura).")
        return risultato

    @staticmethod
    def _valida_host_privato(host):
        try:
            ip = ipaddress.ip_address(str(host).strip())
        except ValueError:
            return None, "Indirizzo non valido: inserisca un IP numerico, non un nome host."
        if not (ip.is_private or ip.is_loopback or ip.is_link_local):
            return None, "Per sicurezza sono ammessi solo IP privati, loopback o link-local."
        if ip.version != 4:
            return None, "Per ora il controllo è limitato a un singolo indirizzo IPv4."
        return str(ip), None

    def richiedi_scansione_host(self, host):
        """Prepara una verifica limitata; non effettua connessioni prima della conferma."""
        ip, errore = self._valida_host_privato(host)
        if errore:
            return errore
        self._host_in_attesa = ip
        porte = ", ".join(str(p) for p in self.PORTE_CONSENTITE)
        return (f"Pronto a verificare il solo host {ip}, esclusivamente sulle porte TCP {porte}. "
                f"La verifica invia tentativi di connessione e richiede autorizzazione. "
                f"Per procedere dica: confermo scansione {ip}. Per annullare dica annulla scansione.")

    def annulla_scansione(self):
        self._host_in_attesa = None
        return "Verifica cybersecurity annullata."

    def conferma_scansione_host(self, host):
        """Esegue solo la scansione già richiesta e confermata dello stesso IP."""
        ip, errore = self._valida_host_privato(host)
        if errore:
            return errore
        if not self._host_in_attesa or ip != self._host_in_attesa:
            return "Nessuna verifica corrispondente in attesa. Prima chieda 'scansiona host IP' e poi confermi lo stesso IP."
        self._host_in_attesa = None
        aperte = []
        for porta in self.PORTE_CONSENTITE:
            try:
                with socket.create_connection((ip, porta), timeout=self.MASSIMO_TIMEOUT):
                    aperte.append(porta)
            except (OSError, TimeoutError):
                continue
        risultato = {"host": ip, "porte_tcp_raggiungibili": aperte, "porte_verificate": list(self.PORTE_CONSENTITE)}
        self._ultimo_risultato = risultato
        self._log(f"Verifica TCP limitata eseguita su host autorizzato indicato dall'utente: {ip}.")
        if aperte:
            elenco = ", ".join(str(p) for p in aperte)
            return f"Verifica completata su {ip}. Porte TCP raggiungibili tra quelle controllate: {elenco}. Questo risultato non prova da solo una vulnerabilità."
        return f"Verifica completata su {ip}: nessuna delle porte TCP consentite ha accettato una connessione. Firewall e timeout possono influenzare il risultato."

    def capacita_hardware(self):
        """Descrive ciò che il solo Mac può fare senza fingere radio dedicate."""
        return {
            "usb_seriale": "possibile con adattatore e driver compatibili; non viene aperto automaticamente",
            "nfc": "nessun lettore NFC generico integrato da assumere presente",
            "sub_ghz": "richiede radio esterna compatibile; nessuna trasmissione attiva implementata",
            "infrarossi": "richiede emettitore/ricevitore IR esterno compatibile",
            "prossimo_passaggio": "collegare un accessorio specifico e aggiungere un driver dedicato con test",
        }

    def _log(self, messaggio):
        if not self.logger:
            return
        try:
            self.logger.info(messaggio)
        except Exception:
            pass
