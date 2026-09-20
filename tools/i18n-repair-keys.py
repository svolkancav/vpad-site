# Bayat anahtarları onarır.
#
# Anahtar İngilizce metnin kendisi olduğu için, kaynak listesi düzeldiğinde
# (ya da bir İngilizce cümle değiştiğinde) çeviri dosyalarındaki eski anahtar
# artık hiçbir düğümle eşleşmez ve o satır sessizce İngilizce kalır.
#
# Bu araç YALNIZ kesin olan durumu onarır: kaynaktaki TEK BİR metnin önekini
# oluşturan eski anahtar. Eksik kuyruk sadece işaretleme ise (`</span>` gibi,
# içinde harf yok) değere de eklenir ve anahtar yeniden adlandırılır. Kuyrukta
# çevrilecek kelime varsa DOKUNULMAZ, rapor edilir — onu bir insan ya da
# çevirmen tamamlamalı.
#
# 2026-09-20: `<span lang="en">` çıkarıcısı iç içe span'ları kırpıyordu;
# "Install the ViGEmBus driver — <span class=\"good\">…" bu yüzden kapanış
# etiketsiz kaydedilmişti.
import glob
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from i18n_common import normalize  # noqa: E402  (yol yukarıda kuruluyor)

ROOT = os.path.join(HERE, "..", "docs", "i18n")
LETTER = re.compile(r"[^\W\d_]", re.UNICODE)


def load(path):
    return json.load(io.open(path, encoding="utf-8"))


def save(path, data):
    with io.open(path, "w", encoding="utf-8", newline="\r\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    source = load(os.path.join(ROOT, "_source.json"))
    src = set(source)
    total = 0

    for path in sorted(glob.glob(os.path.join(ROOT, "*.json"))):
        code = os.path.splitext(os.path.basename(path))[0]
        if code.startswith("_"):
            continue
        data = load(path)
        fixed, skipped = [], []
        for old in [k for k in data if k not in src]:
            # 1) Varlık farkı: anahtar kaynaktaki ham HTML'den üretilmişse
            #    (`&mdash;`), tarayıcı serileştirmesine çevir.
            as_dom = normalize(old)
            if as_dom in src and as_dom not in data:
                data[as_dom] = data.pop(old)
                fixed.append(as_dom)
                continue
            # 2) Kırpılmış anahtar: kaynaktaki TEK bir metnin öneki.
            matches = [s for s in source if s.startswith(old) and s != old]
            if len(matches) != 1:
                skipped.append((old, f"{len(matches)} aday"))
                continue
            new = matches[0]
            tail = new[len(old):]
            # 🪤 Harf araması ETİKETLERDEN SONRA: `</span>` içinde de harf var,
            # ham kuyruğa bakmak her işaretleme kuyruğunu "çevrilecek metin"
            # sanıyordu.
            if LETTER.search(re.sub(r"<[^>]+>", "", tail)):
                skipped.append((old, f"kuyrukta çevrilecek metin var: {tail!r}"))
                continue
            value = data.pop(old)
            data[new] = value + tail
            fixed.append(new)

        if fixed:
            # Kaynak sırasını koru — dosya okunur kalsın.
            ordered = {s: data[s] for s in source if s in data}
            ordered.update({k: v for k, v in data.items() if k not in src})
            save(path, ordered)
            total += len(fixed)
        state = f"{len(fixed)} onarıldı" if fixed else "gerek yok"
        print(f"{code}: {state}")
        for key, why in skipped:
            print(f"    ELLE BAK: {why} — {key[:80]}")

    print(f"toplam {total} anahtar onarıldı")
    return 0


if __name__ == "__main__":
    sys.exit(main())
