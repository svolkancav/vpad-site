// Language switch, twelve languages — the same list the app ships.
//
// English and Turkish live in the DOM as <span lang="en"> / <span lang="tr">
// pairs, so those two are correct before any script runs and both are visible
// to crawlers. The other ten are fetched from i18n/<code>.json and written
// into the English slot; if the fetch fails or a string is missing, that slot
// simply keeps its English, which is why nothing here has an error path that
// leaves the page blank.
//
// The key of a translation IS its English text (whitespace-collapsed). That
// keeps the pages free of data-i18n attributes — they are edited by hand, and
// two of them must stay word-for-word identical — at the price of a copy edit
// silently dropping a translation. tools/i18n-check.py exists to catch that.
(function () {
  var KEY = "vpad-lang";
  // Order matters only for the picker; it matches the app's language list.
  var SUPPORTED = ["en", "tr", "de", "es", "fr", "id", "ja", "ko", "pt", "ru",
                   "zh", "ar"];
  var IN_DOM = { en: 1, tr: 1 };
  var root = document.documentElement;
  var slots = null;
  var cache = {};
  var inflight = {};
  // Bu sayfanın metni çevrilmiyor mu (gizlilik metni bilerek yalnız EN + TR).
  var textFixed = document.documentElement.getAttribute("data-i18n") === "off";

  // `?lang=TR`, `?lang=pt-BR`, `?lang=zh-Hant` de kabul edilir — tarayıcı
  // tespitiyle aynı hoşgörü.
  function supported(code) {
    if (!code) return null;
    var tag = String(code).toLowerCase();
    if (SUPPORTED.indexOf(tag) !== -1) return tag;
    var base = tag.split("-")[0];
    return SUPPORTED.indexOf(base) === -1 ? null : base;
  }

  // The English slots and their original markup, captured before anything is
  // overwritten so switching back is exact.
  function snapshot() {
    if (slots) return slots;
    slots = [];
    // 🚨 `document.querySelectorAll` DEĞİL: her sayfa `<html lang="en">` ile
    // başlıyor, yani kök düğüm de eşleşiyordu ve ilk yuva BELGENİN TAMAMI
    // oluyordu. Sonraki her boyamada o yuvanın anahtarı sözlükte
    // bulunamayınca `documentElement.innerHTML` baştan yazılıyor, belge
    // yeniden ayrıştırılıyor, script'ler bir daha çalışmıyor ve önbelleğe
    // alınmış bütün yuvalar belgeden KOPUYORDU — on dil sessizce ölüyor,
    // EN/TR salt CSS olduğu için çalışıyormuş gibi görünüyordu
    // (denetim, 2026-09-20).
    var nodes = document.body.querySelectorAll('[lang="en"]');
    for (var i = 0; i < nodes.length; i++) {
      slots.push({ el: nodes[i], en: nodes[i].innerHTML });
    }
    return slots;
  }

  function keyOf(html) { return html.replace(/\s+/g, " ").trim(); }

  function paint(lang, dict) {
    var list = snapshot();
    for (var i = 0; i < list.length; i++) {
      var slot = list[i];
      var text = dict ? dict[keyOf(slot.en)] : null;
      var next = text || slot.en;
      if (slot.el.innerHTML !== next) slot.el.innerHTML = next;
      // An untranslated slot stays English and says so, so a screen reader
      // does not read English with a German voice.
      slot.el.setAttribute("lang", text ? lang : "en");
    }
  }

  function load(lang) {
    // Başarısızlık da önbelleğe girer (`in` ile sorulduğu için `null` da
    // sayılır): çevrimdışı bir ziyaretçi her dil değişiminde aynı isteği
    // yeniden yapmasın.
    if (lang in cache) return Promise.resolve(cache[lang]);
    if (inflight[lang]) return inflight[lang];
    if (!window.fetch) return Promise.resolve(null);
    // Yol KÖKTEN: `404.html` Cloudflare tarafından herhangi bir adreste
    // sunuluyor (`not_found_handling`), belgeye göreli bir yol orada
    // `/foo/i18n/de.json` olur ve sessizce İngilizce kalırdı.
    inflight[lang] = fetch("/i18n/" + lang + ".json", { credentials: "omit" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .catch(function () { return null; })
      .then(function (d) {
        cache[lang] = d;
        delete inflight[lang];
        return d;
      });
    return inflight[lang];
  }

  function apply(lang) {
    lang = supported(lang) || "en";
    // Gizlilik metni yalnız EN + TR. Orada başka bir dil seçilirse sayfa
    // İNGİLİZCE kalır — yarısı çevrilmiş bir hukuk metninden iyidir — ve
    // Arapça'da da SAĞDAN SOLA ÇEVRİLMEZ: İngilizce bir metni ters yöne
    // akıtmak onu okunmaz yapardı (denetim, 2026-09-20). Seçim yine de
    // hatırlanır, diğer sayfalar o dilde açılır.
    var textLang = (textFixed && !IN_DOM[lang]) ? "en" : lang;
    root.setAttribute("data-lang", lang);
    root.setAttribute("lang", textLang);
    // Arabic is the only right-to-left language in the list.
    if (textLang === "ar") root.setAttribute("dir", "rtl");
    else root.removeAttribute("dir");

    var select = document.querySelector(".langs select");
    if (select && select.value !== lang) select.value = lang;
    try { localStorage.setItem(KEY, lang); } catch (e) { /* private mode */ }

    if (IN_DOM[textLang]) { paint(textLang, null); return; }
    load(lang).then(function (dict) {
      // A slower answer for a language the visitor has already switched away
      // from must not repaint the page.
      if (root.getAttribute("data-lang") === lang) paint(lang, dict);
    });
  }

  // Closest supported language for this visitor, e.g. pt-BR → pt, zh-Hant → zh.
  function fromBrowser() {
    var list = navigator.languages || [navigator.language || ""];
    for (var i = 0; i < list.length; i++) {
      var hit = supported(list[i]);
      if (hit) return hit;
    }
    return null;
  }

  // Precedence: explicit ?lang= → previous choice → browser language.
  var url = new URLSearchParams(location.search).get("lang");
  var saved = null;
  try { saved = localStorage.getItem(KEY); } catch (e) { /* private mode */ }
  apply(supported(url) || supported(saved) || fromBrowser() || "en");

  document.addEventListener("change", function (event) {
    var select = event.target.closest && event.target.closest(".langs select");
    if (select) apply(select.value);
  });
})();

// Tap a screenshot to see it full size, the way a store listing does.
//
// Built on <dialog>: the backdrop, Esc-to-close, focus trapping and the top
// layer all come for free, so there is no z-index fight and no library. The
// page is unaffected if this never runs — the images are already on it, at a
// readable size; this is only an enlargement.
(function () {
  var groups = document.querySelectorAll('.reel, .shots');
  if (!groups.length || !window.HTMLDialogElement) return;

  var dialog = document.createElement('dialog');
  dialog.className = 'lightbox';
  dialog.innerHTML =
    '<button class="lb-close" aria-label="Close">✕</button>' +
    '<button class="lb-nav lb-prev" aria-label="Previous">‹</button>' +
    '<img alt="">' +
    '<button class="lb-nav lb-next" aria-label="Next">›</button>' +
    '<p class="lb-count" aria-live="polite"></p>';
  document.body.appendChild(dialog);

  var img = dialog.querySelector('img');
  var count = dialog.querySelector('.lb-count');
  var shots = [];
  var index = 0;

  function show(i) {
    index = (i + shots.length) % shots.length;   // wrap, so the ends are not dead
    var source = shots[index];
    img.src = source.currentSrc || source.src;
    img.alt = source.alt || '';
    count.textContent = (index + 1) + ' / ' + shots.length;
    // One image means the arrows are noise.
    dialog.classList.toggle('lb-single', shots.length < 2);
  }

  groups.forEach(function (group) {
    group.addEventListener('click', function (event) {
      var hit = event.target.closest('img');
      if (!hit) return;
      shots = Array.prototype.slice.call(group.querySelectorAll('img'));
      show(shots.indexOf(hit));
      dialog.showModal();
    });
  });

  dialog.querySelector('.lb-next').addEventListener('click', function () { show(index + 1); });
  dialog.querySelector('.lb-prev').addEventListener('click', function () { show(index - 1); });
  dialog.querySelector('.lb-close').addEventListener('click', function () { dialog.close(); });

  // Clicking the empty space around the picture closes it, which is what the
  // gesture means. Clicks on the image or a button must not.
  dialog.addEventListener('click', function (event) {
    if (event.target === dialog) dialog.close();
  });

  dialog.addEventListener('keydown', function (event) {
    if (event.key === 'ArrowRight') { event.preventDefault(); show(index + 1); }
    if (event.key === 'ArrowLeft') { event.preventDefault(); show(index - 1); }
  });

  // Swipe, for the phone this site is mostly read on.
  var startX = null;
  dialog.addEventListener('touchstart', function (e) {
    startX = e.changedTouches[0].clientX;
  }, { passive: true });
  dialog.addEventListener('touchend', function (e) {
    if (startX === null) return;
    var dx = e.changedTouches[0].clientX - startX;
    startX = null;
    if (Math.abs(dx) > 45) show(index + (dx < 0 ? 1 : -1));
  }, { passive: true });

  // Free the decoded image when closed; a 900px JPEG held open costs nothing
  // much, but there is no reason to keep it.
  dialog.addEventListener('close', function () { img.removeAttribute('src'); });
})();
