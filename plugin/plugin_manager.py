import importlib
import os


class PluginManager:
    """Caricamento e ciclo di vita dei plugin Jarvis."""

    def __init__(self, kernel=None, cartella="plugin"):
        self.kernel = kernel
        self.cartella = cartella
        self.plugin = {}
        self.errori = {}

    def registra(self, nome, plugin):
        if not nome or plugin is None:
            return False
        self.plugin[str(nome)] = plugin
        return True

    def carica_plugin(self):
        os.makedirs(self.cartella, exist_ok=True)
        self.errori.clear()
        caricati = 0
        for file in sorted(os.listdir(self.cartella)):
            if not file.endswith(".py") or file.startswith("_"):
                continue
            nome = file[:-3]
            if nome in {"plugin_manager", "plugin_base"}:
                continue
            try:
                modulo = importlib.import_module(f"plugin.{nome}")
                creatore = getattr(modulo, "crea_plugin", None)
                if not callable(creatore):
                    continue
                plugin = creatore(self.kernel)
                if self.registra(nome, plugin):
                    caricati += 1
            except Exception as errore:
                self.errori[nome] = str(errore)
        return caricati

    def avvia_tutti(self):
        avviati = 0
        for nome, plugin in self.plugin.items():
            try:
                risultato = plugin.avvia() if hasattr(plugin, "avvia") else True
                plugin.attivo = bool(risultato) if risultato is not None else True
                if plugin.attivo:
                    avviati += 1
            except Exception as errore:
                self.errori[nome] = str(errore)
        return avviati

    def ferma_tutti(self):
        fermati = 0
        for nome, plugin in self.plugin.items():
            try:
                if hasattr(plugin, "ferma"):
                    plugin.ferma()
                plugin.attivo = False
                fermati += 1
            except Exception as errore:
                self.errori[nome] = str(errore)
        return fermati

    def stato(self):
        risultato = {}
        for nome, plugin in self.plugin.items():
            try:
                risultato[nome] = plugin.stato() if hasattr(plugin, "stato") else {"attivo": bool(getattr(plugin, "attivo", False))}
            except Exception as errore:
                risultato[nome] = {"stato": "errore", "errore": str(errore)}
        return risultato

    def elenco(self):
        return sorted(self.plugin.keys())

    def numero(self):
        return len(self.plugin)

    def stato_completo(self):
        return {
            "caricati": self.numero(),
            "plugin": self.elenco(),
            "errori": dict(self.errori),
        }
