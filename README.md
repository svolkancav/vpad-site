# V-Pad — website

Static site for **V-Pad: Virtual Gamepad**: what it is, the download for the
free desktop helper, setup instructions, privacy policy and support.

No build step, no dependencies, no external requests (no CDN, no web fonts,
no analytics) — three HTML files, one stylesheet, one small script.

```
index.html     landing page: how it works, setup, screenshots, downloads
support.html   troubleshooting + contact  → the App Store "Support URL"
privacy.html   privacy policy             → the store "Privacy Policy URL"
assets/        stylesheet, language switch, icon, screenshots
```

**Languages.** English and Turkish both live in the DOM; CSS hides one based
on `<html data-lang>`. The page therefore renders correctly with JavaScript
disabled, and `assets/site.js` only flips the attribute (honouring `?lang=tr`,
then a stored choice, then the browser language).

**Deployment.** <https://vpadcontroller.com> is served by **Cloudflare Workers**
(static assets — no Worker script, the files are uploaded to the edge).
`.github/workflows/deploy.yml` publishes on every push to `main` and needs two
repository secrets: `CLOUDFLARE_API_TOKEN` (Workers Scripts: Edit) and
`CLOUDFLARE_ACCOUNT_ID`.

GitHub Pages stays enabled as a fallback/staging URL
(<https://svolkancav.github.io/vpad-site/>). There is deliberately **no**
`CNAME` file: adding one would make Pages claim the domain too and fight
Cloudflare for it.
