# Tek seferlik: iki düğmelik EN/TR anahtarını 12 dillik seçim kutusuyla
# değiştirir. Satır sonları (CRLF) ve UTF-8 korunur.
import glob
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")

LANGS = [
    ("en", "English"),
    ("tr", "Türkçe"),
    ("de", "Deutsch"),
    ("es", "Español"),
    ("fr", "Français"),
    ("id", "Bahasa Indonesia"),
    ("ja", "日本語"),
    ("ko", "한국어"),
    ("pt", "Português"),
    ("ru", "Русский"),
    ("zh", "中文"),
    ("ar", "العربية"),
]

OLD = re.compile(
    r'<div class="langs">\s*'
    r'<button data-lang="en"[^>]*>EN</button>\s*'
    r'<button data-lang="tr"[^>]*>TR</button>\s*'
    r"</div>",
    re.S,
)


def block(indent):
    pad = " " * indent
    out = [f'{pad}<div class="langs">']
    out.append(f'{pad}  <select aria-label="Language">')
    for code, name in LANGS:
        out.append(f'{pad}    <option value="{code}">{name}</option>')
    out.append(f"{pad}  </select>")
    out.append(f"{pad}</div>")
    return "\r\n".join(out)


changed = 0
for path in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
    raw = io.open(path, encoding="utf-8", newline="").read()
    m = OLD.search(raw)
    if not m:
        print(f"  atlandı (eşleşme yok): {os.path.basename(path)}")
        continue
    line_start = raw.rfind("\n", 0, m.start()) + 1
    indent = len(raw[line_start : m.start()])
    new = raw[: m.start()] + block(indent).lstrip() + raw[m.end() :]
    io.open(path, "w", encoding="utf-8", newline="").write(new)
    changed += 1
    print(f"  değişti: {os.path.basename(path)}")

print(f"{changed} sayfa")
