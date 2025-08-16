from __future__ import annotations

from html.parser import HTMLParser
from typing import Dict, Optional


class _TitleTextParser(HTMLParser):
    """Very lightweight HTML parser to extract title and visible text.

    Avoids heavy dependencies. Not perfect, but adequate for minimal parsing
    and unit tests without external libraries.
    """

    def __init__(self):
        super().__init__()
        self._in_title = False
        self.title: Optional[str] = None
        self.text_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            # keep the first non-empty title
            if (data := data.strip()):
                self.title = self.title or data
        else:
            d = data.strip()
            if d:
                self.text_parts.append(d)

    def result(self) -> Dict[str, Optional[str]]:
        text = " ".join(self.text_parts).strip() or None
        return {"title": self.title, "text": text}


def parse_article_basic(html: str) -> Dict[str, Optional[str]]:
    parser = _TitleTextParser()
    parser.feed(html)
    return parser.result()


def parse_article(html: str) -> Dict[str, Optional[str]]:
    """Try to parse article content.

    If BeautifulSoup and readability-lxml are available, prefer them; otherwise
    fallback to the basic parser.
    """
    try:
        from readability import Document  # type: ignore
        from bs4 import BeautifulSoup  # type: ignore
        doc = Document(html)
        cleaned = doc.summary()
        soup = BeautifulSoup(cleaned, "lxml") if BeautifulSoup else None
        title = doc.short_title() or (soup.title.get_text(strip=True) if soup and soup.title else None)
        text = soup.get_text(" ", strip=True) if soup else None
        return {"title": title, "text": text}
    except Exception:
        return parse_article_basic(html)
