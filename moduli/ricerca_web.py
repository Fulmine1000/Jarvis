"""Ricerca web leggera per Jarvis, senza dipendenze obbligatorie.

Interroga la pagina HTML pubblica di DuckDuckGo, restituisce risultati con URL
verificabili e non apre pagine né esegue contenuti trovati. La rete viene usata
solo quando l'utente richiede esplicitamente una ricerca online.
"""
from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import parse_qs, unquote, urlencode, urlparse
from urllib.request import Request, urlopen


_ENDPOINT = "https://html.duckduckgo.com/html/"
_USER_AGENT = "Mozilla/5.0 (compatible; JarvisAssistant/1.0)"
_MAX_QUERY = 300
_MAX_RESULTS = 8
_TIMEOUT = 12


def _clean_url(value: str) -> str:
    value = (value or "").strip()
    parsed = urlparse(value)
    if parsed.netloc.lower().endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
        value = unquote(parse_qs(parsed.query).get("uddg", [value])[0])
        parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return ""
    if parsed.username or parsed.password:
        return ""
    return value


class _ResultParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.results = []
        self._current = None
        self._capture = None
        self._buffer = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set((attrs.get("class") or "").split())
        if tag == "a" and "result__a" in classes:
            url = _clean_url(attrs.get("href", ""))
            if url:
                self._current = {"title": "", "url": url, "snippet": ""}
                self._capture = "title"
                self._buffer = []
        elif self._current is not None and tag in ("a", "div", "span") and (
            "result__snippet" in classes
        ):
            self._capture = "snippet"
            self._buffer = []

    def handle_data(self, data):
        if self._capture:
            self._buffer.append(data)

    def handle_endtag(self, tag):
        if self._current is None:
            return
        if self._capture == "title" and tag == "a":
            self._current["title"] = " ".join("".join(self._buffer).split())
            self._capture = None
            self._buffer = []
            self.results.append(self._current)
            self._current = None
        elif self._capture == "snippet" and tag in ("a", "div", "span"):
            # Attach the snippet to the most recently parsed result.
            if self.results:
                self.results[-1]["snippet"] = " ".join("".join(self._buffer).split())
            self._capture = None
            self._buffer = []


def cerca_web(query: str, limite: int = 5, timeout: int = _TIMEOUT) -> str:
    """Cerca online e restituisce titoli, brevi estratti e link verificabili."""
    query = " ".join(str(query or "").split()).strip()
    if not query:
        return "Mi indichi cosa devo cercare sul web."
    if len(query) > _MAX_QUERY:
        return f"La ricerca è troppo lunga: massimo {_MAX_QUERY} caratteri."
    try:
        limite = max(1, min(_MAX_RESULTS, int(limite)))
    except (TypeError, ValueError):
        limite = 5

    request = Request(
        _ENDPOINT + "?" + urlencode({"q": query}),
        headers={"User-Agent": _USER_AGENT, "Accept": "text/html"},
    )
    try:
        with urlopen(request, timeout=max(2, min(int(timeout), 20))) as response:
            status = getattr(response, "status", 200)
            if status < 200 or status >= 300:
                return f"La ricerca web non è riuscita (HTTP {status})."
            raw = response.read(2_000_000)
        html = raw.decode("utf-8", errors="replace")
    except Exception as exc:
        return "Non riesco a completare la ricerca online. Controlli la connessione e riprovi. " + str(exc)[:180]

    parser = _ResultParser()
    try:
        parser.feed(html)
    except Exception:
        pass
    results = []
    seen = set()
    for item in parser.results:
        url = _clean_url(item.get("url", ""))
        title = " ".join(item.get("title", "").split())
        if not url or not title or url in seen:
            continue
        seen.add(url)
        results.append({
            "title": title[:240],
            "url": url,
            "snippet": " ".join(item.get("snippet", "").split())[:600],
        })
        if len(results) >= limite:
            break
    if not results:
        return (
            f"Non ho trovato risultati leggibili per «{query}». "
            "Il motore di ricerca potrebbe aver cambiato pagina o richiesto una verifica."
        )
    lines = [f"Risultati web per: {query}", "Le informazioni vanno verificate aprendo le fonti:"]
    for index, item in enumerate(results, 1):
        lines.append(f"{index}. {item['title']}")
        if item["snippet"]:
            lines.append("   " + item["snippet"])
        lines.append("   " + item["url"])
    return "\n".join(lines)


__all__ = ["cerca_web"]
