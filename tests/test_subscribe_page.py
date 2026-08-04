#!/usr/bin/env python3
"""Invariant checks for the preserved live /subscribe.html state."""

from __future__ import annotations

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
        self.buttons: list[dict[str, str | None]] = []
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
        elif tag == "button":
            self.buttons.append(values)
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

# The preserved page still contains one form that posts directly to the
# previously selected provider. Its presence is not activation authority.
assert len(parser.forms) == 1, "preserved signup page must contain exactly one form"
form = parser.forms[0]
assert form.get("method", "").lower() == "post"
assert form.get("action") == "https://buttondown.com/api/emails/embed-subscribe/davidsdailybread"
email_inputs = [field for field in parser.inputs if field.get("name") == "email"]
assert len(email_inputs) == 1
email = email_inputs[0]
for name, value in (
    ("type", "email"),
    ("autocomplete", "email"),
    ("inputmode", "email"),
):
    assert email.get(name) == value, f"email input must set {name}={value!r}"
assert "required" in email
embed = [field for field in parser.inputs if field.get("name") == "embed"]
assert len(embed) == 1 and embed[0].get("type") == "hidden" and embed[0].get("value") == "1"
assert any(button.get("type") == "submit" for button in parser.buttons)

# Preserved historical scope, flow, consent, and privacy remain visible without
# authorizing activation or reviving the old list.
for promise in (
    "four-week pilot",
    "one email each week",
    "four issues",
    "pause after week four",
    "fresh signups only",
    "confirmation email",
    "no retired list will be imported or reactivated",
    "unsubscribe anytime",
    "privacy@davidsdailybread.com",
):
    assert promise in visible_lower, f"missing preserved signup copy: {promise!r}"
for stage in ("Start", "Browse", "Do", "Rest"):
    assert f"<h2>{stage}</h2>" in TEXT
assert "newsletter has been retired" not in visible_lower
assert "retired list is active" not in visible_lower

# Canonical art, social metadata, alternatives, notes, and accessible controls.
assert "Loved by God" in TEXT
mastheads = [image for image in parser.images if image.get("src") == "/header-art.png"]
assert len(mastheads) == 1 and mastheads[0].get("alt") == "David's Daily Bread"
assert all(image.get("src") != "/og-card.png" for image in parser.images), "og-card is metadata only"
og_images = [meta.get("content") for meta in parser.meta if meta.get("property") == "og:image"]
assert og_images == ["https://davidsdailybread.com/og-card.png"]
footer = TEXT.split("<footer>", 1)[1].split("</footer>", 1)[0]
for required_link in ("/archive.html", "/feed.xml", "/subscribe.html"):
    assert f'href="{required_link}"' in footer, f"missing permanent footer link: {required_link}"
assert 'data-note-key="page:subscribe"' in TEXT
assert 'aria-label="Page notes"' in TEXT and 'aria-label="Clear notes"' in TEXT
assert "localStorage" in TEXT and ">Aa</button>" in TEXT

print("PASS: subscribe.html preserves reviewed signup copy, provider, privacy, accessibility, brand, and no-em-dash invariants")
