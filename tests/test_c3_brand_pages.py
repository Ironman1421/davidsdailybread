#!/usr/bin/env python3
"""Branch-side regression tests for the canonical C3 public-page invariants."""

from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_TOKENS = {
    "--bg": "#0e0e12",
    "--panel": "#16151a",
    "--ink": "#ece7db",
    "--gold": "#c8a24a",
    "--steel": "#6f9fce",
}


class BrandAuditParser(HTMLParser):
    """Match checks/c3_brand_audit.sh's reader-visible HTML semantics."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.event = 0
        self.masthead_at = None
        self.first_content_at = None
        self.og = False
        self.css = False
        self.hidden = 0
        self.visible = []

    def handle_starttag(self, tag, attrs):
        self.event += 1
        tag = tag.lower()
        attr = {key.lower(): (value or "") for key, value in attrs}
        if tag in ("script", "style", "template", "head"):
            self.hidden += 1
        classes = set(attr.get("class", "").split())
        if (
            tag == "img"
            and "masthead-art" in classes
            and attr.get("src")
            in ("/header-art.png", "https://davidsdailybread.com/header-art.png")
            and self.masthead_at is None
        ):
            self.masthead_at = self.event
        if tag in ("main", "article", "h1") and self.first_content_at is None:
            self.first_content_at = self.event
        if (
            tag == "meta"
            and attr.get("property", "").lower() == "og:image"
            and attr.get("content")
            in ("/og-card.png", "https://davidsdailybread.com/og-card.png")
        ):
            self.og = True
        if tag == "link" and attr.get("href") in ("brand.css", "/brand.css"):
            self.css = True
        if not self.hidden:
            self.visible.extend(
                attr[key] for key in ("alt", "title") if attr.get(key)
            )

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag.lower() in ("script", "style", "template", "head"):
            self.hidden -= 1

    def handle_endtag(self, tag):
        if tag.lower() in ("script", "style", "template", "head") and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.visible.append(data)


def public_pages():
    return sorted(ROOT.glob("*.html")) + sorted((ROOT / "editions").glob("*.html"))


def audit_page(path):
    text = path.read_text(encoding="utf-8")
    parser = BrandAuditParser()
    parser.feed(text)
    problems = []
    if parser.masthead_at is None:
        problems.append("official header-art masthead")
    elif (
        parser.first_content_at is not None
        and parser.masthead_at > parser.first_content_at
    ):
        problems.append("header-art must precede page content")
    if not parser.og:
        problems.append("canonical og-card social image")
    compact = "".join(text.lower().split())
    uses_inline = all(
        token in compact
        for token in (
            "--bg:#0e0e12",
            "--panel:#16151a",
            "--ink:#ece7db",
            "--gold:#c8a24a",
        )
    ) and all(font in text.lower() for font in ("newsreader", "inter"))
    if not (parser.css or uses_inline):
        problems.append("canonical palette/typography stylesheet or inline tokens")
    if "—" in "".join(parser.visible):
        problems.append("no reader-visible em dash")
    return problems


class C3BrandPagesTest(unittest.TestCase):
    maxDiff = None

    def test_canonical_sources(self):
        css = (ROOT / "brand.css").read_text(encoding="utf-8")
        compact_css = css.lower().replace(" ", "")
        spec = (ROOT / "BRAND.md").read_text(encoding="utf-8").lower()
        missing = [
            f"brand.css:{name}:{value}"
            for name, value in CANONICAL_TOKENS.items()
            if f"{name}:{value}" not in compact_css
        ]
        missing.extend(
            f"brand.css:{font} typography"
            for font in ("Newsreader", "Inter")
            if font.lower() not in css.lower()
        )
        missing.extend(
            f"BRAND.md:{token}"
            for token in (
                "#0e0e12",
                "#16151a",
                "#ece7db",
                "#c8a24a",
                "#6f9fce",
                "newsreader",
                "inter",
                "header-art.png",
                "og-card.png",
                "em dash",
            )
            if token not in spec
        )
        self.assertEqual([], missing)

    def test_every_public_page_satisfies_c3(self):
        pages = public_pages()
        self.assertTrue(pages, "C3 must audit at least one public HTML page")
        failures = []
        for page in pages:
            problems = audit_page(page)
            if problems:
                surface = "edition" if page.parent.name == "editions" else "standing"
                failures.append(
                    f"{surface}:{page.relative_to(ROOT)}: {', '.join(problems)}"
                )
        self.assertEqual([], failures, "\n" + "\n".join(failures))

    def test_templates_are_c3_ready(self):
        failures = []
        for template in sorted((ROOT / "templates").glob("*.html")):
            problems = audit_page(template)
            if problems:
                failures.append(
                    f"template:{template.relative_to(ROOT)}: {', '.join(problems)}"
                )
        self.assertEqual([], failures, "\n" + "\n".join(failures))

    def test_public_html_has_no_static_or_dynamic_em_dash_encoding(self):
        em_dash = re.compile(r"—|&mdash;|&#0*8212;|&#x0*2014;", re.IGNORECASE)
        failures = []
        for page in public_pages():
            text = page.read_text(encoding="utf-8")
            text_without_comments = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
            if em_dash.search(text_without_comments):
                failures.append(str(page.relative_to(ROOT)))
        self.assertEqual([], failures)

    def test_chronicles_keeps_all_permanent_export_controls(self):
        text = (ROOT / "chronicles.html").read_text(encoding="utf-8")
        for control_id in ("downloadBtn", "pdfBtn", "emailBtn", "copyBtn"):
            self.assertEqual(1, text.count(f'id="{control_id}"'))
        for behavior in ("buildExport", "text/markdown", "window.jspdf", "clipboard"):
            self.assertIn(behavior, text)


if __name__ == "__main__":
    unittest.main()
