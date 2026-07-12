#!/usr/bin/env python3
"""Invariant checks for the first-party DDB subscribe page."""
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "subscribe.html"
TEXT = PAGE.read_text(encoding="utf-8")
ENDPOINT = "https://buttondown.com/api/emails/embed-subscribe/davidsdailybread"


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
        self.anchors: list[dict[str, str | None]] = []
        self.labels: list[dict[str, str | None]] = []
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
        elif tag == "a":
            self.anchors.append(values)
        elif tag == "label":
            self.labels.append(values)
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

# Exact real Buttondown form schema.
assert len(parser.forms) == 1, "subscribe page must contain exactly one form"
form = parser.forms[0]
assert str(form.get("method") or "").lower() == "post"
assert form.get("action") == ENDPOINT
email_fields = [field for field in parser.inputs if field.get("name") == "email"]
assert len(email_fields) == 1, "form must contain one name=email field"
email = email_fields[0]
assert email.get("type") == "email"
assert "required" in email
assert email.get("id") and any(label.get("for") == email.get("id") for label in parser.labels)
tag_fields = [field for field in parser.inputs if field.get("name") == "tag"]
assert len(tag_fields) == 3, "form must contain exactly three name=tag controls"
assert {field.get("value") for field in tag_fields} == {"morning", "evening", "both"}
assert all(field.get("type") == "radio" for field in tag_fields)
assert all(field.get("id") for field in tag_fields)
assert all(any(label.get("for") == field.get("id") for label in parser.labels) for field in tag_fields)
assert "<fieldset" in TEXT and "<legend" in TEXT, "tag choices need an accessible group name"

# Current operating truth: one production morning edition; evening is not promised yet.
assert "Loved by God" in TEXT
assert "one edition each morning" in visible_lower
assert "evening" in visible_lower and "testing" in visible_lower
assert "future" in visible_lower and "preference" in visible_lower
for forbidden_promise in ("twice daily", "twice-daily", "every morning and evening"):
    assert forbidden_promise not in TEXT.lower(), f"current page must not promise {forbidden_promise!r}"

# Canonical art, social metadata, footer, notes, and accessible controls.
mastheads = [image for image in parser.images if image.get("src") == "/header-art.png"]
assert len(mastheads) == 1 and mastheads[0].get("alt") == "David's Daily Bread"
assert all(image.get("src") != "/og-card.png" for image in parser.images), "og-card is metadata only"
og_images = [meta.get("content") for meta in parser.meta if meta.get("property") == "og:image"]
assert og_images == ["https://davidsdailybread.com/og-card.png"]
footer = TEXT.split("<footer>", 1)[1].split("</footer>", 1)[0]
for required_link in ("/archive.html", "/feed.xml", "/subscribe.html"):
    assert f'href="{required_link}"' in footer, f"missing permanent footer link: {required_link}"
assert 'class="sub-cta"' in TEXT and 'class="sub-btn"' in TEXT
assert 'data-note-key="page:subscribe"' in TEXT
assert 'aria-label="Page notes"' in TEXT and 'aria-label="Clear notes"' in TEXT
assert "localStorage" in TEXT and ">Aa</button>" in TEXT

print("PASS: subscribe.html satisfies structure, exact schema, cadence truth, accessibility, brand, art, footer, notes, and no-em-dash invariants")
