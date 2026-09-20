# Sitedeki çevrilecek metinleri tek bir kaynak listesine çıkarır.
#
# Neden metnin KENDİSİ anahtar: sayfalar elle düzenleniyor ve iki indirme
# sayfasının "birebir aynı metin" kuralı var. 203 span'a `data-i18n="..."`
# eklemek o dosyaları okunmaz hale getirir ve her yeni cümlede anahtar
# uydurmayı zorunlu kılardı. İngilizce metni anahtar yapmak HTML'i hiç
# kirletmiyor; bedeli, İngilizce bir cümle değişince çevirinin sessizce
# düşmesi — `i18n-check.py` tam olarak onu yakalıyor.
#
# privacy.html KAPSAM DIŞI (user kararı, 2026-09-20): hukuki metin yalnız
# EN + TR kalıyor.
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")
SKIP = {"privacy.html"}
PAGES = [
    "index.html",
    "downloads.html",
    "downloads-android.html",
    "downloads-ios.html",
    "support.html",
    "404.html",
]

# <span lang="en"> … </span>
#
# 🪤 Burada bir zamanlar `(.*?)</span>` vardı ve İÇ İÇE span'ı kırpıyordu
# (`…<span class="good">download, install and forget` — kapanış etiketi
# düşüyordu). Sonucu sessizdi ve sinsiydi: çalışma anında anahtar düğümün
# GERÇEK innerHTML'i olduğu için kırpık anahtar hiçbir zaman eşleşmez, o
# satır her dilde İngilizce kalırdı. Bu yüzden artık açılış/kapanış
# sayılarak dengeli eşleşme yapılıyor.
OPEN = re.compile(r'<span lang="en"[^>]*>')
STEP = re.compile(r"<span\b|</span>")


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from i18n_common import normalize  # noqa: E402  (yol yukarıda kuruluyor)


def en_spans(html):
    """Her <span lang="en"> düğümünün iç HTML'i, iç içe span'lar dahil."""
    out = []
    for opening in OPEN.finditer(html):
        start = opening.end()
        depth, at = 1, start
        while depth:
            step = STEP.search(html, at)
            if not step:  # bozuk HTML: sessizce atla, üretime sızmasın
                break
            if step.group(0) == "</span>":
                depth -= 1
                at = step.end()
            else:
                depth += 1
                at = step.end()
        else:
            out.append(html[start : at - len("</span>")])
    return out


def extract():
    strings = []
    seen = set()
    per_page = {}
    for page in PAGES:
        path = os.path.join(ROOT, page)
        if not os.path.exists(path) or page in SKIP:
            continue
        html = io.open(path, encoding="utf-8").read()
        found = [normalize(m) for m in en_spans(html)]
        per_page[page] = len(found)
        for s in found:
            if s and s not in seen:
                seen.add(s)
                strings.append(s)
    return strings, per_page


if __name__ == "__main__":
    strings, per_page = extract()
    out = os.path.join(ROOT, "i18n", "_source.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with io.open(out, "w", encoding="utf-8", newline="\r\n") as f:
        json.dump(strings, f, ensure_ascii=False, indent=2)
        f.write("\n")
    for page, n in per_page.items():
        print(f"{page:26s} {n:3d}")
    print(f"benzersiz: {len(strings)}  →  {out}")
