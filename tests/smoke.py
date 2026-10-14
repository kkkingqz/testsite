#!/usr/bin/env python3
"""Dependency-free static-site smoke tests: python3 tests/smoke.py"""
from html.parser import HTMLParser
from html import unescape
import csv
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1] / "public"


class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.duplicate_ids = set()
        self.urls = []
        self.alt_errors = 0

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        identifier = attrs.get("id")
        if identifier:
            if identifier in self.ids:
                self.duplicate_ids.add(identifier)
            self.ids.add(identifier)
        if tag in {"a", "link", "script", "img"}:
            url = attrs.get("href") or attrs.get("src")
            if url:
                self.urls.append(url)
        if tag == "img" and "alt" not in attrs:
            self.alt_errors += 1


def test_page(page):
    parser = SiteParser()
    parser.feed(page.read_text(encoding="utf-8"))
    assert not parser.duplicate_ids, f"Duplicate ids: {parser.duplicate_ids}"
    assert not parser.alt_errors, f"Images missing alt: {parser.alt_errors}"
    for url in parser.urls:
        if url.startswith("/"):
            target = ROOT / url.lstrip("/").split("#")[0]
            if target.is_dir() or not target.name:
                target = target / "index.html"
            assert target.exists(), f"{page.name}: missing asset or page {url}"
        elif url.startswith("#"):
            assert url[1:] in parser.ids, f"{page.name}: dead anchor {url}"
    print(f"PASS {page.relative_to(ROOT)}")


if __name__ == "__main__":
    for html in sorted(ROOT.glob("*.html")):
        test_page(html)
    for expected in ["#about", "#gallery", "#booking", "#contacts"]:
        assert f'id="{expected[1:]}"' in (ROOT / "index.html").read_text(), expected
    # Asset slots must remain stable: replace file bytes, not HTML references.
    image_dir = ROOT / "assets/images"
    expected_webp = {"hero-art.webp", "gallery-01.webp", "gallery-02.webp", "gallery-03.webp"}
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    for name in expected_webp:
        image = image_dir / name
        assert image.is_file(), f"Missing replaceable photo: {image}"
        raw = image.read_bytes()
        assert raw[:4] == b"RIFF" and raw[8:12] == b"WEBP", f"Invalid WebP: {image}"
        assert f'/assets/images/{name}' in index, f"Image not used: {name}"
    for name in ("logo.svg", "og-image.jpg"):
        image = image_dir / name
        assert image.exists() and image.stat().st_size > 200, f"Missing image: {name}"
        assert f'/assets/images/{name}' in index, f"Image not referenced: {name}"
    ET.parse(image_dir / "logo.svg")
    ET.parse(ROOT / "favicon.svg")
    jpg = (image_dir / "og-image.jpg").read_bytes()
    assert jpg[:2] == b"\xff\xd8" and jpg[-2:] == b"\xff\xd9", "Invalid OG JPEG"
    assert 'property="og:image"' in index, "Missing Open Graph preview"
    for page in ("index.html", "privacy.html", "404.html"):
        assert "/assets/images/logo.svg" in (ROOT / page).read_text(encoding="utf-8"), f"Logo missing on {page}"
    print("All static-site and graphic asset checks passed")
    # KTAWF test copy should be present and old Forma copy removed.
    assert '<html lang="uk">' in index
    assert 'KTAWF Global Security' in index
    assert 'Професійний тактичний захист' in index
    assert 'id="cal-inline"' in index
    assert 'id="booking-open-link"' in index
    assert 'booking-placeholder' not in index
    assert '/assets/js/booking-config.js' in index
    assert '/assets/js/booking.js' in index
    assert 'eventUrl: "https://cal.com/bogdan-n-usjpw6/consultation"' in (ROOT / 'assets/js/booking-config.js').read_text()
    assert 'https://app.cal.com' in (ROOT / 'assets/js/booking.js').read_text()
    assert 'Forma' not in index
    print('KTAWF Ukrainian demo content checks passed')

    # Verify every CSV text field is embedded in the published HTML / metadata.
    with (ROOT.parent / 'docs/content-source.csv').open(encoding='utf-8-sig', newline='') as source:
        items = {int(row[0]): row[2].strip() for row in csv.reader(source, delimiter=';')}
    assert len(items) == 40 and set(items) == set(range(1, 41))
    decoded = unescape(index)
    for number, text in items.items():
        # Multiple advantages and operating hours are rendered as separate blocks.
        parts = [piece.strip() for piece in text.split(' | ')] if number in (8, 28) else [text]
        for part in parts:
            assert part in decoded, f'Missing content source block {number}: {part[:60]}'
    print('All 40 source-copy items included')
