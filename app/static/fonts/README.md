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

Ubuntu Sans is preferred in CSS but is **not bundled yet**: no local copy exists, and agent-shell downloads fail DNS. Until the files below are available, browsers use the documented local fallback stack. No font-CDN request is made at runtime.

From an enabled terminal inside foo:

    cd /home/ubuntu/codex-projects/utility-hub
    curl -fL 'https://cdn.jsdelivr.net/fontsource/fonts/ubuntu-sans@latest/latin-400-normal.woff2' -o app/static/fonts/UbuntuSans-Regular.woff2
    curl -fL 'https://raw.githubusercontent.com/canonical/Ubuntu-Sans-fonts/main/LICENCE.txt' -o app/static/fonts/Ubuntu-FONT-LICENCE.txt

The [Fontsource regular Latin file](https://fontsource.org/fonts/ubuntu-sans) derives from [Canonical Ubuntu Sans](https://github.com/canonical/Ubuntu-Sans-fonts). Retain the full Ubuntu Font Licence. Before committing, verify the font family/weight, WOFF2 header, size, and checksum; record its resolved version and provenance here.

The shared template includes ui-font.css only when both local font and license files exist at startup. Restart the server after installing them. The stylesheet uses font-display: swap and weight 400. Existing signature assets stay separate.

Local fallback stacks:

- Interface/headings: Ubuntu Sans, Ubuntu, system-ui, Segoe UI, Arial, sans-serif.
- Data: IBM Plex Mono, SFMono-Regular, Consolas, Liberation Mono, monospace.
- Logo: Georgia, Palatino Linotype, Book Antiqua, serif.

Keep the combined UI font payload below 200 KiB. Do not create a placeholder font or add a missing-file request to the rendered page.
