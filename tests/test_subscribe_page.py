#!/usr/bin/env python3
"""Invariant checks for the first-party DDB subscribe page."""
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "subscribe.html"
TEXT = PAGE.read_text(encoding="utf-8")


class SubscribeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.forms: list[dict[str, str | None]] = []
        self.inputs: list[dict[str, str | None]] = []
        self.images: list[dict[str, str | None]] = []
        self.links: list[str] = []
        self.meta: list[dict[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "form":
            self.forms.append(values)
        elif tag == "input":
            self.inputs.append(values)
        elif tag == "img":
            self.images.append(values)
        elif tag == "a" and values.get("href"):
            self.links.append(str(values["href"]))
        elif tag == "meta":
            self.meta.append(values)


parser = SubscribeParser()
parser.feed(TEXT)

assert "—" not in TEXT, "reader-visible HTML must not contain em dash characters"
assert "&mdash;" not in TEXT.lower(), "reader-visible HTML must not contain &mdash;"
assert len(parser.forms) == 1, "subscribe page must contain exactly one form"
form = parser.forms[0]
assert str(form.get("method") or "").lower() == "post"
assert form.get("action") == "https://buttondown.com/api/emails/embed-subscribe/davidsdailybread"
email_fields = [field for field in parser.inputs if field.get("name") == "email"]
assert len(email_fields) == 1, "form must contain one name=email field"
email = email_fields[0]
assert email.get("type") == "email"
assert "required" in email
assert any(image.get("src") == "/header-art.png" for image in parser.images)
assert all(image.get("src") != "/og-card.png" for image in parser.images), "og-card is metadata only"
og_images = [meta.get("content") for meta in parser.meta if meta.get("property") == "og:image"]
assert og_images == ["https://davidsdailybread.com/og-card.png"]
footer = TEXT.split("<footer>", 1)[1].split("</footer>", 1)[0]
for required_link in ("/archive.html", "/feed.xml", "/subscribe.html"):
    assert f'href="{required_link}"' in footer, f"missing permanent footer link: {required_link}"
assert '<link rel="stylesheet" href="/brand.css">' in TEXT
for family in ("Caveat", "Newsreader", "Inter"):
    assert family in TEXT, f"missing loaded font family: {family}"
assert "morning" in TEXT.lower() and "evening" in TEXT.lower()
assert 'class="sub-cta"' in TEXT and 'class="sub-btn"' in TEXT
assert 'data-note-key="page:subscribe"' in TEXT
assert "localStorage" in TEXT and '>Aa</button>' in TEXT

print("PASS: subscribe.html satisfies endpoint, accessibility, brand, art, cadence, footer, notes, and no-em-dash invariants")
