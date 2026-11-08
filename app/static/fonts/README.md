# Local Signature Font

- File: `DejaVuSerif.ttf`, unchanged DejaVu Serif regular from `fonts-dejavu-core` 2.37-8build1.
- Source file: `/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf`.
- Upstream: https://dejavu-fonts.github.io/
- Retrieved locally: 2026-11-11.
- Size: 380,660 bytes; SHA-256: `a52c2a69dfc93d0b511b98c1019a57eb3d6a62d328bdf1387f00851b02e3a315`.
- License: [DejaVu/Bitstream Vera notice](DejaVu-LICENSE.txt), including copyright/trademark and redistribution conditions. The font is copied unchanged; packaging GPL text is not the font license.

This is a regular serif face, not a handwriting font. Load it only on the signature page. A browser may synthesize italic styling, but do not label it as a separate bundled italic or cursive font. The asset supports typed-name rendering without an external font service; drawn signatures remain freehand canvas input.

Suggested CSS family name: `Utility Signature Serif`, sourced from `/static/fonts/DejaVuSerif.ttf` with `format("truetype")`, regular weight/style, and `font-display: swap`. The application owns the CSS declaration.

## Console UI Typography

The console style guide specifies IBM Plex Sans for interface text, IBM Plex Mono for data, and Syne for display headings. These three families are **not bundled**: no authentic local copies were available and the download source could not be resolved in this environment.

Use system fallbacks without making external font requests:

- Interface: `"IBM Plex Sans", "Segoe UI", Arial, sans-serif`.
- Data: `"IBM Plex Mono", "SFMono-Regular", Consolas, "Liberation Mono", monospace`.
- Display: `Syne, "Arial Black", "Segoe UI", sans-serif`.

Do not declare font-face URLs or preload files that do not exist. When licensed local WOFF2 assets become available, prefer Latin subsets or variable files with only required weights, retain their upstream license notices and checksums, and keep the combined UI font payload below 200 KiB. The existing DejaVu signature asset remains separate and loads only on the signature page.
