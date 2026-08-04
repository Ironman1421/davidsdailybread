#!/usr/bin/env python3
"""Executable contracts for the local-only installable web app package."""

from __future__ import annotations

import json
from pathlib import Path
import struct
import unittest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
CONTRACT = json.loads(
    (ROOT / "operations" / "pwa.contract.json").read_text(encoding="utf-8")
)


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise AssertionError(f"not a PNG with an IHDR header: {path}")
    return struct.unpack(">II", data[16:24])


class PwaContractTest(unittest.TestCase):
    def test_manifest_uses_the_canonical_site_and_approved_brand(self):
        self.assertEqual("/", MANIFEST["id"])
        self.assertEqual("/", MANIFEST["start_url"])
        self.assertEqual("/", MANIFEST["scope"])
        self.assertEqual("standalone", MANIFEST["display"])
        self.assertEqual("#0e0e12", MANIFEST["background_color"])
        self.assertEqual("#0e0e12", MANIFEST["theme_color"])
        self.assertIn("News and Scripture each morning", MANIFEST["description"])
        self.assertIn(
            "An evening Field Guide with useful tools and workflows",
            MANIFEST["description"],
        )
        self.assertIn("Loved by God", MANIFEST["description"])

        expected_icons = {
            "/icons/icon-192.png": (192, 192),
            "/icons/icon-512.png": (512, 512),
        }
        self.assertEqual(expected_icons, {
            icon["src"]: tuple(map(int, icon["sizes"].split("x")))
            for icon in MANIFEST["icons"]
        })
        for source, dimensions in expected_icons.items():
            self.assertEqual(dimensions, png_dimensions(ROOT / source.removeprefix("/")))

    def test_templates_and_standing_pages_register_one_shared_app(self):
        surfaces = [
            ROOT / "templates" / name
            for name in ("home.html", "evening.html", "category.html")
        ] + [
            ROOT / name
            for name in (
                "archive.html",
                "chronicles.html",
                "subscribe.html",
                "tools.html",
                "workflows.html",
                "404.html",
                "secret-menu.html",
                "offline.html",
            )
        ]
        for path in surfaces:
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8")
                self.assertIn('rel="manifest" href="/manifest.webmanifest"', text)
                self.assertIn('name="theme-color" content="#0e0e12"', text)
                self.assertIn('href="/pwa.css"', text)
                self.assertIn('src="/pwa.js"', text)

    def test_service_worker_is_same_origin_bounded_and_correction_safe(self):
        worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
        install_block = worker.split(
            'self.addEventListener("install"', 1
        )[1].split('self.addEventListener("activate"', 1)[0]

        self.assertIn("url.origin !== self.location.origin", worker)
        self.assertIn('request.mode === "navigate"', worker)
        self.assertIn("networkFirst(event, PAGE_CACHE", worker)
        self.assertIn("networkFirst(event, DATA_CACHE", worker)
        self.assertIn('fetch(request, { cache: "no-store" })', worker)
        for canonical_data in ("/archive.json", "/feed.xml", "/evening-catalog.json"):
            self.assertIn(canonical_data, worker)
        self.assertIn("MAX_PAGE_ENTRIES = 80", worker)
        self.assertIn("MAX_DATA_ENTRIES = 8", worker)
        self.assertIn("if (url.search || !canCache(response)) return", worker)
        self.assertIn('new Request(path, { cache: "reload" })', worker)
        self.assertIn('name.startsWith("ddb-pwa-")', worker)
        self.assertNotIn("skipWaiting", install_block)
        self.assertNotIn('addEventListener("push"', worker)
        self.assertNotIn("showNotification", worker)
        self.assertNotIn("PushManager", worker)

    def test_install_layer_does_not_touch_notes_or_activate_notifications(self):
        script = (ROOT / "pwa.js").read_text(encoding="utf-8")
        for forbidden in (
            "localStorage",
            "indexedDB",
            "Notification",
            "PushManager",
            "pushManager",
        ):
            self.assertNotIn(forbidden, script)
        self.assertIn("beforeinstallprompt", script)
        self.assertIn('aria-live', script)
        self.assertIn("Add to Home Screen", script)
        self.assertIn("ACTIVATE_UPDATE", script)

    def test_machine_contract_fails_closed(self):
        self.assertEqual(1, CONTRACT["version"])
        self.assertEqual("phase-1-local-ready-not-published", CONTRACT["status"])
        self.assertTrue(CONTRACT["canonical"]["websiteRemainsCanonical"])
        self.assertFalse(CONTRACT["canonical"]["separateEditorialProductCreated"])
        self.assertTrue(CONTRACT["cachePolicy"]["correctionsCheckedOnEveryOnlineNavigation"])
        self.assertEqual(
            "no-store", CONTRACT["cachePolicy"]["canonicalNetworkFetchCacheMode"]
        )
        self.assertFalse(CONTRACT["personalData"]["notesReadByPwaLayer"])
        self.assertFalse(CONTRACT["personalData"]["notesDeletedByPwaLayer"])
        self.assertFalse(CONTRACT["personalData"]["savedItemSchemaAdded"])
        self.assertTrue(CONTRACT["install"]["readerInitiated"])
        self.assertEqual("v2", CONTRACT["updates"]["cacheGeneration"])
        self.assertEqual(
            "reload", CONTRACT["updates"]["staticAssetInstallFetchCacheMode"]
        )
        self.assertFalse(CONTRACT["updates"]["skipWaitingDuringInstall"])
        for field, value in CONTRACT["activation"].items():
            with self.subTest(field=field):
                if field == "spendAuthorizedUsd":
                    self.assertEqual(0, value)
                else:
                    self.assertFalse(value)

    def test_offline_page_obeys_reader_visible_brand_law(self):
        page = (ROOT / "offline.html").read_text(encoding="utf-8")
        self.assertIn('<img class="masthead-art" src="/header-art.png"', page)
        self.assertIn(
            '<meta property="og:image" content="https://davidsdailybread.com/og-card.png">',
            page,
        )
        self.assertIn('data-note-key="page:offline"', page)
        self.assertIn("ddb-note:page:offline", page)
        self.assertNotIn("—", page)
        self.assertNotIn("&mdash;", page.lower())


if __name__ == "__main__":
    unittest.main()
