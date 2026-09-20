# Çıkarıcı ile onarıcının PAYLAŞTIĞI anahtar üretimi.
#
# Anahtar, site.js'in çalışma anında ürettiğiyle BİREBİR aynı olmak zorunda:
# orada anahtar düğümün `innerHTML`'i (boşlukları tekilleştirilmiş). Tarayıcı
# innerHTML'i serileştirirken kaynaktaki her şeyi aynen geri vermiyor —
# `&mdash;` metin düğümünde "—" karakterine çözülüyor ve geri yazılırken
# varlık olarak kodlanmıyor. Kaynaktaki ham HTML'i anahtar yapmak bu yüzden
# sessizce ıskalıyordu: sayfa bozulmuyor, yalnız o satır her dilde İngilizce
# kalıyordu (2026-09-20, çeviri turunda yakalandı).
#
# Tarayıcının kuralı: metin düğümlerinde yalnız `&`, `<`, `>` ve satır-içi
# bölünmez boşluk varlık olarak yazılır; diğer her şey çözülmüş karakterdir.
import html as html_module
import re

TAG_SPLIT = re.compile(r"(<[^>]+>)")


def serialize(fragment):
    """Kaynaktaki HTML parçasını tarayıcının innerHTML çıktısına çevirir."""
    out = []
    for part in TAG_SPLIT.split(fragment):
        if part.startswith("<"):
            out.append(part)  # etiketler olduğu gibi
            continue
        text = html_module.unescape(part)
        text = (text.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace(" ", "&nbsp;"))
        out.append(text)
    return "".join(out)


def normalize(fragment):
    """Anahtar biçimi: tarayıcı serileştirmesi + tekilleştirilmiş boşluk."""
    return re.sub(r"\s+", " ", serialize(fragment)).strip()
