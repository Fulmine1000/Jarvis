"""Caricamento sicuro di mesh 3D per la modalità olografica di Jarvis.

Supporta Wavefront OBJ e STL ASCII. Non esegue il contenuto del file e non
richiede librerie grafiche aggiuntive: restituisce vertici e spigoli normalizzati
che il renderer Qt Quick può disegnare. I file binari STL sono riconosciuti e
rifiutati esplicitamente finché non è disponibile un parser binario dedicato.
"""
from __future__ import annotations

import math
import os


ESTENSIONI_SUPPORTATE = (".obj", ".stl")
MAX_VERTICI = 20000
MAX_SPIGOLI = 40000
MAX_BYTES = 16 * 1024 * 1024


class ErroreModello3D(ValueError):
    """File 3D non leggibile o non supportato."""


def carica_modello(percorso):
    """Carica una mesh OBJ o STL ASCII e restituisce geometria normalizzata."""
    if not percorso:
        raise ErroreModello3D("Nessun file selezionato.")
    percorso = os.path.abspath(os.path.expanduser(str(percorso).strip().strip('"').strip("'")))
    if not os.path.isfile(percorso):
        raise ErroreModello3D("Il file selezionato non esiste.")
    estensione = os.path.splitext(percorso)[1].lower()
    if estensione not in ESTENSIONI_SUPPORTATE:
        raise ErroreModello3D("Formato non supportato. Selezionare un file .obj o .stl ASCII.")
    try:
        dimensione = os.path.getsize(percorso)
        if dimensione <= 0 or dimensione > MAX_BYTES:
            raise ErroreModello3D("Il file è vuoto o supera il limite di 16 MB.")
        with open(percorso, "r", encoding="utf-8-sig", errors="strict") as sorgente:
            righe = sorgente.readlines()
    except UnicodeDecodeError:
        raise ErroreModello3D("Il file non è testo UTF-8: gli STL binari non sono ancora supportati.")
    except OSError as errore:
        raise ErroreModello3D("Impossibile leggere il file: " + str(errore))

    if estensione == ".obj":
        vertici, facce = _leggi_obj(righe)
    else:
        vertici, facce = _leggi_stl_ascii(righe)
    return _normalizza(percorso, vertici, facce)


def _leggi_obj(righe):
    vertici = []
    facce = []
    for numero, riga in enumerate(righe, 1):
        parti = riga.strip().split()
        if not parti or parti[0].startswith("#"):
            continue
        if parti[0] == "v":
            if len(parti) < 4:
                raise ErroreModello3D("Vertice OBJ non valido alla riga %d." % numero)
            try:
                punto = tuple(float(x) for x in parti[1:4])
            except ValueError:
                raise ErroreModello3D("Coordinate OBJ non valide alla riga %d." % numero)
            if not all(math.isfinite(x) for x in punto):
                raise ErroreModello3D("Coordinate non finite alla riga %d." % numero)
            vertici.append(punto)
            if len(vertici) > MAX_VERTICI:
                raise ErroreModello3D("Il modello supera il limite di vertici.")
        elif parti[0] == "f":
            if len(parti) < 4:
                continue
            faccia = []
            for riferimento in parti[1:]:
                try:
                    indice = int(riferimento.split("/")[0])
                except (ValueError, IndexError):
                    raise ErroreModello3D("Faccia OBJ non valida alla riga %d." % numero)
                indice = indice - 1 if indice > 0 else len(vertici) + indice
                if indice < 0 or indice >= len(vertici):
                    raise ErroreModello3D("Indice OBJ fuori intervallo alla riga %d." % numero)
                faccia.append(indice)
            facce.append(faccia)
    return vertici, facce


def _leggi_stl_ascii(righe):
    vertici = []
    facce = []
    triangolo = []
    for numero, riga in enumerate(righe, 1):
        parti = riga.strip().split()
        if len(parti) >= 4 and parti[0].lower() == "vertex":
            try:
                punto = tuple(float(x) for x in parti[1:4])
            except ValueError:
                raise ErroreModello3D("Vertice STL non valido alla riga %d." % numero)
            if not all(math.isfinite(x) for x in punto):
                raise ErroreModello3D("Coordinate STL non finite alla riga %d." % numero)
            vertici.append(punto)
            triangolo.append(len(vertici) - 1)
            if len(vertici) > MAX_VERTICI:
                raise ErroreModello3D("Il modello supera il limite di vertici.")
            if len(triangolo) == 3:
                facce.append(triangolo)
                triangolo = []
    if triangolo or not facce:
        raise ErroreModello3D("STL ASCII non valido o privo di triangoli.")
    return vertici, facce


def _normalizza(percorso, vertici, facce):
    if not vertici or not facce:
        raise ErroreModello3D("Il file non contiene una mesh 3D valida.")
    minimo = [min(p[i] for p in vertici) for i in range(3)]
    massimo = [max(p[i] for p in vertici) for i in range(3)]
    centro = [(minimo[i] + massimo[i]) / 2.0 for i in range(3)]
    scala = max(massimo[i] - minimo[i] for i in range(3))
    if not math.isfinite(scala) or scala <= 0:
        raise ErroreModello3D("Il modello ha dimensioni nulle o non valide.")
    punti = [tuple((p[i] - centro[i]) * 2.0 / scala for i in range(3)) for p in vertici]
    spigoli = set()
    for faccia in facce:
        if len(faccia) < 3:
            continue
        for i, indice in enumerate(faccia):
            altro = faccia[(i + 1) % len(faccia)]
            if indice != altro:
                spigoli.add((min(indice, altro), max(indice, altro)))
                if len(spigoli) > MAX_SPIGOLI:
                    raise ErroreModello3D("Il modello supera il limite di spigoli.")
    if not spigoli:
        raise ErroreModello3D("Non sono stati trovati spigoli da visualizzare.")
    return {
        "nome": os.path.basename(percorso),
        "percorso": percorso,
        "vertici": punti,
        "spigoli": [list(x) for x in sorted(spigoli)],
        "numero_vertici": len(punti),
        "numero_spigoli": len(spigoli),
        "formato": os.path.splitext(percorso)[1][1:].upper(),
    }


__all__ = ["carica_modello", "ErroreModello3D", "ESTENSIONI_SUPPORTATE"]
