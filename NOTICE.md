# Notices, Attribution & Third-Party Licenses

## What this project is
An independent, open-source "skill" that helps typeset CJK / CJK+Latin pages to a
high, classical standard, with a deterministic render → measure → explain loop.
The *method* it encodes was studied from Yoshihisa Shirai's writing on typographic
composition. This repository is an **independent interpretation**; it is **not
affiliated with, authorized by, or endorsed by** Yoshihisa Shirai or his publisher.

## What this project does NOT contain (by design)
- **No pages, scans, images, or annotation text from the original book.**
- The only thing derived from the book is **numeric measurement data**
  (e.g. gray-value evenness, ink density) in `benchmarks/`. These are factual
  measurements, not the book's expressive content. To (re)generate or extend them,
  run `scripts/derive_benchmark.py` against **your own legally obtained copy** of
  the book; that copy is never stored here.
- All sample texts in `assets/sample-texts/` are **original writing** or
  **public-domain** works (e.g. a Tang-dynasty poem). No copyrighted book text ships here.

## Third-party software bundled here
- **EB Garamond** (`assets/fonts/EBGaramond-*.ttf`) — © The EB Garamond Project Authors,
  licensed under the **SIL Open Font License 1.1**. Full text: `assets/fonts/EBGaramond-OFL-License.txt`.

## Third-party software referenced but NOT bundled
- **Noto Serif CJK / Noto Sans CJK** (= Source Han Serif/Sans) — SIL OFL 1.1.
  The skill resolves these from the host system; install them on your machine
  (Debian/Ubuntu: `fonts-noto-cjk`, `fonts-noto-cjk-extra`).

## License of this repository
- Code, scripts, reference docs, specs, schemas, and derived numeric data: **MIT** (see LICENSE).
- Bundled fonts: **SIL OFL 1.1** (as above).
