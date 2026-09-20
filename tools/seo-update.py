# SEO tamamlama: robots.txt, sitemap.xml, eksik Open Graph / Twitter kartı
# etiketleri ve yapısal veri (JSON-LD).
#
# Yeniden çalıştırılabilir: ürettiği her blok bir işaretle sarılı, ikinci
# çalıştırmada bloğun içi yenisiyle DEĞİŞTİRİLİR, ikinci kopya eklenmez.
#
# ⛔ Görünen metne, başlıklara ve açıklamalara DOKUNMAZ — onlar user'ın
# yazdığı metin. Bu araç yalnız makinelerin okuduğu alanları doldurur.
#
# 🪤 Satır sonları CRLF, dosyalar UTF-8 (depo kuralı).
import datetime
import html as html_module
import io
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")
SITE = "https://vpadcontroller.com"
CARD = f"{SITE}/assets/customise-banner.jpg"  # 2200x1016, tek sosyal kart
CARD_W, CARD_H = "2200", "1016"
PLAY = "https://play.google.com/store/apps/details?id=com.dfnmondo.gamepad.app"
APPSTORE = "https://apps.apple.com/us/app/v-pad-virtual-gamepad/id6796475673"

# Seçim kutusundaki diller; og:locale:alternate için.
LOCALES = {
    "en": "en_US", "tr": "tr_TR", "de": "de_DE", "es": "es_ES", "fr": "fr_FR",
    "id": "id_ID", "ja": "ja_JP", "ko": "ko_KR", "pt": "pt_BR", "ru": "ru_RU",
    "zh": "zh_CN", "ar": "ar_AR",
}

# sayfa → (canonical yol, gezinti adı, ÜST sayfa)
# İki platform sayfası `downloads`'ın ALTINDA: bağlantı gerçekten oradan
# veriliyor, dolayısıyla iz de üç basamaklı olmalı (denetim, 2026-09-20).
PAGES = {
    "index.html": ("/", None, None),
    "downloads.html": ("/downloads", "Downloads", None),
    "downloads-android.html": ("/downloads-android", "Android downloads",
                               "downloads.html"),
    "downloads-ios.html": ("/downloads-ios", "iPhone downloads",
                           "downloads.html"),
    "support.html": ("/support", "Support", None),
    "privacy.html": ("/privacy", "Privacy", None),
}

BEGIN = "<!-- SEO:BEGIN -->"
END = "<!-- SEO:END -->"
BLOCK = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.S)

# Aracın sahiplendiği etiketler: head'de zaten varsa SİLİNİR, blok içinde
# yeniden üretilir. Böylece ikinci bir og:image kalmaz.
OWNED = re.compile(
    r'[ \t]*<meta (?:property|name)="'
    r'(?:og:(?:title|description|type|image|image:alt|image:width|image:height'
    r'|site_name|locale|locale:alternate)|twitter:[a-z:]+)"[^>]*>\r?\n?'
)


def read(path):
    return io.open(path, encoding="utf-8", newline="").read()


def write(path, text):
    io.open(path, "w", encoding="utf-8", newline="").write(text)


def meta(prop, content, kind="property"):
    return f'<meta {kind}="{prop}" content="{content}">'


def head_of(html):
    return html[: html.find("</head>")]


def field(html, pattern, default=""):
    m = re.search(pattern, head_of(html), re.S)
    if not m:
        return default
    # 🪤 Ham öznitelik metni JSON-LD'ye giriyor ve `<script>` içeriği HTML
    # ayrıştırıcısından GEÇMİYOR — başlığa bir gün `&amp;` girerse yapısal
    # veriye harfi harfine öyle yazılırdı (denetim, 2026-09-20).
    return html_module.unescape(m.group(1).strip())


def jsonld(payload):
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    return '<script type="application/ld+json">\r\n' + body.replace(
        "\n", "\r\n") + "\r\n</script>"


def software_application(description):
    # ⚠️ UYDURMA YOK: puan/yorum sayısı iddia edilmiyor, fiyat gerçekten 0
    # (uygulama ücretsiz indiriliyor; kalıcı satın alma uygulama içinde).
    #
    # ⛔ BURAYA `aggregateRating` EKLEMEYİN. Google'ın Software App zengin
    # sonucu `aggregateRating` ya da `review` İSTİYOR, yani bu blok o sonucu
    # ÜRETEMEZ — bilinçli. Play'deki yıldızı buraya kopyalamak kendi kendine
    # verilmiş puan olur (Google'ın "self-serving review" ihlali). Blok,
    # zengin sonuç için değil, markanın varlık olarak tanınması için duruyor
    # (denetim, 2026-09-20).
    return {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "V-Pad: Virtual Gamepad",
        "alternateName": "V-Pad",
        "description": description,
        "applicationCategory": "UtilitiesApplication",
        "operatingSystem": "Android 12+, iOS",
        "url": f"{SITE}/",
        "image": CARD,
        "installUrl": [PLAY, APPSTORE],
        # `sameAs` kimlik sinyali: "V-Pad" aramasında mağaza sayfalarıyla aynı
        # varlık olduğumuzu söyleyen şey bu, `installUrl` değil.
        "sameAs": [PLAY, APPSTORE],
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "USD",
        },
    }


def breadcrumb(page):
    """Ana sayfadan bu sayfaya kadar gerçek iz (üst sayfa varsa araya girer)."""
    trail = []
    cursor = page
    while cursor:
        path, name, parent = PAGES[cursor]
        trail.append((name, SITE + path))
        cursor = parent
    trail.append(("Home", f"{SITE}/"))
    trail.reverse()
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": name, "item": url}
            for i, (name, url) in enumerate(trail, start=1)
        ],
    }


def build_block(page, html):
    path, crumb, _ = PAGES[page]
    url = SITE + path
    title = field(html, r"<title>(.*?)</title>")
    desc = field(html, r'name="description" content="(.*?)"')
    # 🪤 og:title DAİMA <title>'dan türetilir, kendi ürettiğimiz etiketten
    # değil: aksi halde blok kendi kopyasını okuyup sabitliyor ve birisi
    # başlığı değiştirdiğinde sosyal kart sessizce eski cümleyi taşımaya devam
    # ediyordu. og:description ise elle yazılmış olabilir (ana sayfada öyle),
    # o yüzden varsa korunur.
    og_title = title
    og_desc = field(html, r'property="og:description" content="(.*?)"', desc)

    lines = [BEGIN,
             "<!-- Makineler için: sosyal kart ve yapısal veri. Bu blok",
             "     tools/seo-update.py tarafından üretiliyor — elle düzenlemeyin,",
             "     aracı çalıştırın. -->",
             # og:title/description/type YALNIZ ana sayfada elle yazılmıştı;
             # diğer beş sayfa og:image taşıyıp BAŞLIK taşımıyordu, yani
             # Facebook/LinkedIn/Slack/WhatsApp önizlemesi başlıksız çıkıyordu
             # (denetim, 2026-09-20). Twitter og:*'a geri düştüğü için sorun
             # yalnız orada görünmüyordu.
             meta("og:title", og_title),
             meta("og:description", og_desc),
             meta("og:type", "website"),
             meta("og:site_name", "V-Pad"),
             meta("og:locale", LOCALES["en"])]
    for code, loc in LOCALES.items():
        if code != "en":
            lines.append(meta("og:locale:alternate", loc))
    lines += [
        meta("og:image", CARD),
        meta("og:image:width", CARD_W),
        meta("og:image:height", CARD_H),
        # Sayfadaki <img>'in kendi alt metniyle AYNI şeyi anlatmalı:
        # görsel oyun değil, özelleştirme sayfası (denetim, 2026-09-20).
        meta("og:image:alt",
             "A phone with the V-Pad customise sheet open, beside its layouts"),
        meta("twitter:card", "summary_large_image", kind="name"),
        meta("twitter:title", og_title, kind="name"),
        meta("twitter:description", og_desc, kind="name"),
        meta("twitter:image", CARD, kind="name"),
    ]
    if page == "index.html":
        lines.append(jsonld(software_application(desc)))
    elif crumb:
        lines.append(jsonld(breadcrumb(page)))
    lines.append(END)
    return "\r\n".join(lines)


def patch_page(page):
    path = os.path.join(ROOT, page)
    html = read(path)
    head_end = html.find("</head>")
    head, rest = html[:head_end], html[head_end:]
    # 🪤 İşaretçilerden biri kaybolursa (elle düzenleme, birleştirme çakışması)
    # `BLOCK` eşleşmez, eski JSON-LD ayakta kalır ve YENİSİ eklenir — dosyanın
    # kendi vaadi olan "ikinci kopya eklenmez" sessizce bozulurdu. Sayıları
    # tutmuyorsa hiç yazmadan bağır (denetim, 2026-09-20).
    if head.count(BEGIN) != head.count(END):
        raise SystemExit(
            f"{page}: SEO işaretçileri bozuk "
            f"({head.count(BEGIN)}× BEGIN, {head.count(END)}× END) — elle onarın"
        )
    head = BLOCK.sub("", head)
    head = OWNED.sub("", head)
    head = head.rstrip("\r\n") + "\r\n" + build_block(page, html) + "\r\n"
    write(path, head + rest)


def patch_404():
    # Hata sayfası indekslenmemeli; sitemap'te de yok.
    path = os.path.join(ROOT, "404.html")
    html = read(path)
    if 'name="robots"' in head_of(html):
        return False
    html = html.replace(
        "<title>", '<meta name="robots" content="noindex">\r\n<title>', 1)
    write(path, html)
    return True


def write_robots():
    body = "\r\n".join([
        "# vpadcontroller.com",
        "User-agent: *",
        "Allow: /",
        "",
        f"Sitemap: {SITE}/sitemap.xml",
        "",
    ])
    write(os.path.join(ROOT, "robots.txt"), body)


def last_modified(page):
    """Sayfanın son değişim tarihi (YYYY-MM-DD).

    Çalışma ağacında bekleyen değişiklik varsa BUGÜN, yoksa son commit'in
    tarihi. `<priority>` yerine bu var: Google ve Bing `priority` ile
    `changefreq`'i tamamen yok sayıyor, yeniden tarama için baktıkları tek
    alan `lastmod` (denetim, 2026-09-20).
    """
    rel = f"docs/{page}"
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    try:
        dirty = subprocess.run(["git", "status", "--porcelain", "--", rel],
                               cwd=root, capture_output=True, text=True,
                               check=True).stdout.strip()
        if dirty:
            return datetime.date.today().isoformat()
        stamp = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel],
                               cwd=root, capture_output=True, text=True,
                               check=True).stdout.strip()
        return stamp or datetime.date.today().isoformat()
    except (OSError, subprocess.CalledProcessError):
        return datetime.date.today().isoformat()


def write_sitemap():
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for page, (path, _, _) in PAGES.items():
        out += ["  <url>",
                f"    <loc>{SITE}{path}</loc>",
                f"    <lastmod>{last_modified(page)}</lastmod>",
                "  </url>"]
    out += ["</urlset>", ""]
    write(os.path.join(ROOT, "sitemap.xml"), "\r\n".join(out))


if __name__ == "__main__":
    for page in PAGES:
        patch_page(page)
        print(f"  head güncellendi: {page}")
    print("  404 noindex:", "eklendi" if patch_404() else "zaten vardı")
    write_robots()
    write_sitemap()
    print(f"  robots.txt ve sitemap.xml yazıldı ({len(PAGES)} URL)")
