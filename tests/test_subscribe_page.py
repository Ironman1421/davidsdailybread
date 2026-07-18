#!/usr/bin/env python3
"""Invariant checks for the standing /subscribe.html page.

Since 2026-07-17 (per David) the email newsletter is RETIRED: this page is a
permanent "newsletter retired, take the RSS" notice. These checks enforce that
truth: no subscription form, no Buttondown reference, and the standing brand
laws (masthead art first, no em dashes, notes box, canonical metadata).
"""
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "subscribe.html"
TEXT = PAGE.read_text(encoding="utf-8")


class SubscribeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.event = 0
        self.hidden = 0
        self.masthead_at: int | None = None
        self.main_at: int | None = None
        self.forms: list[dict[str, str | None]] = []
        self.inputs: list[dict[str, str | None]] = []
        self.images: list[dict[str, str | None]] = []
        self.links: list[dict[str, str | None]] = []
        self.meta: list[dict[str, str | None]] = []
        self.visible: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.event += 1
        values = dict(attrs)
        if tag in ("head", "script", "style", "template"):
            self.hidden += 1
        if tag == "main" and self.main_at is None:
            self.main_at = self.event
        if tag == "form":
            self.forms.append(values)
        elif tag == "input":
            self.inputs.append(values)
        elif tag == "img":
            self.images.append(values)
            if (
                self.masthead_at is None
                and "masthead-art" in str(values.get("class") or "").split()
                and values.get("src") == "/header-art.png"
            ):
                self.masthead_at = self.event
        elif tag == "link":
            self.links.append(values)
        elif tag == "meta":
            self.meta.append(values)
        if not self.hidden:
            for name in ("alt", "aria-label", "title"):
                if values.get(name):
                    self.visible.append(str(values[name]))

    def handle_endtag(self, tag: str) -> None:
        if tag in ("head", "script", "style", "template") and self.hidden:
            self.hidden -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.visible.append(data)


parser = SubscribeParser()
parser.feed(TEXT)
visible_text = " ".join(" ".join(parser.visible).split())
visible_lower = visible_text.lower()

# Canonical page structure and reader-visible brand law.
assert parser.masthead_at is not None, "official header art masthead is required"
assert parser.main_at is not None, "reader content must use a main landmark"
assert parser.masthead_at < parser.main_at, "masthead must precede <main>/reader content"
assert "—" not in visible_text, "reader-visible HTML must not contain em dash characters"
assert "&mdash;" not in TEXT.lower(), "reader-visible HTML must not contain &mdash;"
assert '<html lang="en">' in TEXT
assert '<link rel="canonical" href="https://davidsdailybread.com/subscribe.html">' in TEXT
assert any(link.get("rel") == "stylesheet" and link.get("href") == "/brand.css" for link in parser.links)
for family in ("Caveat", "Newsreader", "Inter"):
    assert family in TEXT, f"missing loaded font family: {family}"

# Newsletter retired (2026-07-17, per David): no subscription mechanics anywhere.
assert parser.forms == [], "retired page must contain no forms"
assert parser.inputs == [], "retired page must contain no input fields"
assert "buttondown" not in TEXT.lower(), "no Buttondown reference may remain"
assert "retired" in visible_lower, "the page must state the newsletter is retired"

# Current operating truth: one edition each morning; no email promises.
assert "Loved by God" in TEXT
assert "each morning" in visible_lower
for forbidden_promise in ("twice daily", "twice-daily", "every morning and evening", "by email"):
    assert forbidden_promise not in visible_lower, f"current page must not promise {forbidden_promise!r}"

# Canonical art, social metadata, footer, notes, and accessible controls.
mastheads = [image for image in parser.images if image.get("src") == "/header-art.png"]
assert len(mastheads) == 1 and mastheads[0].get("alt") == "David's Daily Bread"
assert all(image.get("src") != "/og-card.png" for image in parser.images), "og-card is metadata only"
og_images = [meta.get("content") for meta in parser.meta if meta.get("property") == "og:image"]
assert og_images == ["https://davidsdailybread.com/og-card.png"]
footer = TEXT.split("<footer>", 1)[1].split("</footer>", 1)[0]
for required_link in ("/archive.html", "/feed.xml"):
    assert f'href="{required_link}"' in footer, f"missing permanent footer link: {required_link}"
assert 'data-note-key="page:subscribe"' in TEXT
assert 'aria-label="Page notes"' in TEXT and 'aria-label="Clear notes"' in TEXT
assert "localStorage" in TEXT and ">Aa</button>" in TEXT

print("PASS: subscribe.html satisfies retired-newsletter truth, structure, accessibility, brand, art, footer, notes, and no-em-dash invariants")
