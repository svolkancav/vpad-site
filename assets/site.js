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
