# Local Signature Font

- File: `DejaVuSerif.ttf`, unchanged DejaVu Serif regular from `fonts-dejavu-core` 2.37-8build1.
- Source file: `/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf`.
- Upstream: https://dejavu-fonts.github.io/
- Retrieved locally: 2026-11-11.
- Size: 380,660 bytes; SHA-256: `a52c2a69dfc93d0b511b98c1019a57eb3d6a62d328bdf1387f00851b02e3a315`.
- License: [DejaVu/Bitstream Vera notice](DejaVu-LICENSE.txt), including copyright/trademark and redistribution conditions. The font is copied unchanged; packaging GPL text is not the font license.

This is a regular serif face, not a handwriting font. Load it only on the signature page. A browser may synthesize italic styling, but do not label it as a separate bundled italic or cursive font. The asset supports typed-name rendering without an external font service; drawn signatures remain freehand canvas input.

Suggested CSS family name: `Utility Signature Serif`, sourced from `/static/fonts/DejaVuSerif.ttf` with `format("truetype")`, regular weight/style, and `font-display: swap`. The application owns the CSS declaration.

## SOC UtilityHub Typography

The latest UI direction uses **Ubuntu Sans Regular (400)** for interface text and headings. The logo uses a distinct italic serif stack (Georgia / Palatino / system serif), with no additional font payload. Data retains a monospace stack.

Ubuntu Sans Regular is bundled locally. No font-CDN request is made at runtime.

- File: [UbuntuSans-Regular.woff2](UbuntuSans-Regular.woff2), regular 400, Latin subset, unchanged from the user-downloaded Fontsource asset.
- Family/PostScript name: Ubuntu Sans / UbuntuSans-Regular; embedded font version 1.006 (Fontconfig value 65929).
- Source: https://cdn.jsdelivr.net/fontsource/fonts/ubuntu-sans@latest/latin-400-normal.woff2 ; upstream [Canonical Ubuntu Sans](https://github.com/canonical/Ubuntu-Sans-fonts).
- Size: 16,692 bytes; SHA-256: 048644555a97c54450f7cb7a9e1c6728a20e447f8895d6c66ee9bbdbd92db8be.
- License: full [Ubuntu Font Licence 1.0](Ubuntu-FONT-LICENCE.txt), downloaded unchanged from https://raw.githubusercontent.com/canonical/Ubuntu-Sans-fonts/main/LICENCE.txt .
- License size: 4,673 bytes; SHA-256: 2f0015108d68627bd788d313f529c21ff4da2c2c42a5e1f3883acc83480f9002.
- Verified with Fontconfig metadata, WOFF2 signature/header length, and in-process HTTP delivery matching the local bytes. The CDN URL used a latest alias; the checked-in file, embedded version, and checksum identify the exact delivered asset.

For deliberate future updates, retain the full license, verify the new family/weight/version and file size, update checksums, and review the font before committing. Do not refresh it automatically.

The shared template includes ui-font.css only when both local font and license files exist at startup. Restart the server after installing them. The stylesheet uses font-display: swap and weight 400. Existing signature assets stay separate.

Local fallback stacks:

- Interface/headings: Ubuntu Sans, Ubuntu, system-ui, Segoe UI, Arial, sans-serif.
- Data: IBM Plex Mono, SFMono-Regular, Consolas, Liberation Mono, monospace.
- Logo: Georgia, Palatino Linotype, Book Antiqua, serif.

Keep the combined UI font payload below 200 KiB. Do not create a placeholder font or add a missing-file request to the rendered page.
