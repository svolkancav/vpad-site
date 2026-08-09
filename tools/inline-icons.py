#!/usr/bin/env python3
"""Inline src/icons.svg into every page between its ICONS markers.

Why a script instead of just pasting the sprite four times: an icon sprite
has to be in the document for <use href="#id"> to resolve, external sprite
files are still unreliable across browsers, and our privacy policy promises
no third-party requests — so no CDN either. That leaves duplication, and
duplication wants one source of truth.

Run after editing src/icons.svg:  python3 tools/inline-icons.py
Idempotent, and it reports whether anything actually changed.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPRITE = ROOT / "src" / "icons.svg"
BEGIN, END = "<!-- ICONS:BEGIN -->", "<!-- ICONS:END -->"


def main() -> int:
    sprite = SPRITE.read_text(encoding="utf-8").strip()
    pages = sorted((ROOT / "docs").glob("*.html"))
    if not pages:
        print("no pages found", file=sys.stderr)
        return 1

    block = f"{BEGIN}\n{sprite}\n{END}"
    pattern = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.S)
    changed, skipped = [], []

    for page in pages:
        text = page.read_text(encoding="utf-8")
        if BEGIN not in text:
            skipped.append(page.name)          # a page that wants no icons
            continue
        if END not in text:
            print(f"{page.name}: {BEGIN} without {END}", file=sys.stderr)
            return 1
        new = pattern.sub(lambda _: block, text, count=1)
        if new != text:
            page.write_text(new, encoding="utf-8")
            changed.append(page.name)

    print("updated:", ", ".join(changed) if changed else "nothing (already current)")
    if skipped:
        print("no markers:", ", ".join(skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
