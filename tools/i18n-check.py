# Çeviri dosyalarını kaynağa karşı doğrular.
#
# NEDEN VAR: anahtar, İngilizce metnin kendisi. Bu HTML'i temiz tutuyor ama
# bir İngilizce cümle düzeltilince o metnin çevirisi sessizce düşer — sayfa
# bozulmaz, yalnız o satır İngilizce kalır ve kimse fark etmez. Yayından
# önce bunu çalıştırın.
#
# Kontroller:
#   1. Eksik anahtar   — kaynakta var, çeviride yok  (o satır İngilizce kalır)
#   2. Fazla anahtar   — çeviride var, kaynakta yok  (ölü satır; büyük ihtimal
#                        İngilizce metin değişmiş)
#   3. Boş çeviri
#   4. HTML iskeleti   — etiket dizisi kaynakla birebir aynı olmalı
#   5. Çevrilmemiş     — İngilizcenin aynısı (uyarı: "V-Pad" gibi doğru
#                        durumlar da var, bu yüzden hata değil)
import glob
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "i18n")
TAG = re.compile(r"<[^>]+>")


def skeleton(text):
    """Etiketlerin dizisi — çeviri metni değiştirir, iskeleti değiştiremez."""
    return [re.sub(r"\s+", " ", t) for t in TAG.findall(text)]


def main():
    source = json.load(io.open(os.path.join(ROOT, "_source.json"), encoding="utf-8"))
    src = set(source)
    failed = False

    for path in sorted(glob.glob(os.path.join(ROOT, "*.json"))):
        code = os.path.splitext(os.path.basename(path))[0]
        if code.startswith("_"):
            continue
        try:
            data = json.load(io.open(path, encoding="utf-8"))
        except ValueError as e:
            print(f"{code}: GEÇERSİZ JSON — {e}")
            failed = True
            continue

        missing = [s for s in source if s not in data]
        extra = [k for k in data if k not in src]
        empty = [k for k, v in data.items() if not str(v).strip()]
        broken = [k for k, v in data.items()
                  if k in src and skeleton(k) != skeleton(str(v))]
        same = [k for k, v in data.items() if k in src and k == str(v)]

        problems = bool(missing or extra or empty or broken)
        mark = "HATA" if problems else "tamam"
        print(f"{code}: {mark}  {len(data)}/{len(source)} anahtar"
              f"  (çevrilmemiş {len(same)})")
        for label, items in (("eksik", missing), ("fazla", extra),
                             ("boş", empty), ("HTML iskeleti bozuk", broken)):
            for item in items[:5]:
                print(f"    {label}: {item[:90]}")
            if len(items) > 5:
                print(f"    {label}: … +{len(items) - 5}")
        failed = failed or problems

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
