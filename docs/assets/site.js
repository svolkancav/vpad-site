// Language switch. The page renders correctly with JS disabled — both
// languages are in the DOM and CSS hides one based on <html data-lang>.
// This only flips that attribute, remembers the choice, and keeps the URL
// shareable via ?lang=.
(function () {
  var KEY = "vpad-lang";
  var root = document.documentElement;

  function apply(lang) {
    lang = lang === "tr" ? "tr" : "en";
    root.setAttribute("data-lang", lang);
    root.setAttribute("lang", lang);
    var buttons = document.querySelectorAll(".langs button");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].setAttribute(
        "aria-pressed", buttons[i].dataset.lang === lang ? "true" : "false");
    }
    try { localStorage.setItem(KEY, lang); } catch (e) { /* private mode */ }
  }

  // Precedence: explicit ?lang= → previous choice → browser language.
  var url = new URLSearchParams(location.search).get("lang");
  var saved = null;
  try { saved = localStorage.getItem(KEY); } catch (e) { /* private mode */ }
  var guess = (navigator.language || "").toLowerCase().indexOf("tr") === 0
    ? "tr" : "en";
  apply(url || saved || guess);

  document.addEventListener("click", function (event) {
    var button = event.target.closest(".langs button");
    if (button) apply(button.dataset.lang);
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
