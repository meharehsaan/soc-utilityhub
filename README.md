# SOC UtilityHub

Utility tools for SOC analysts, created by **Ehsaan Mehar**. A lightweight, self-hosted Python workbench for everyday SOC tasks. **32 dedicated services** share a searchable card homepage, dark/light console themes, and one launcher. No database, accounts, saved investigation history, telemetry, or external service dependencies.

## Run Locally

Use Python 3.12+ in an isolated environment. In this workspace, the provided environment is /home/ubuntu/pyenv:

    cd /home/ubuntu/codex-projects/utility-hub
    /home/ubuntu/pyenv/bin/python -m pip install -r requirements.txt
    /home/ubuntu/pyenv/bin/python run.py

Open **http://127.0.0.1:8000**. In another activated environment, use Python to install requirements.txt and run [run.py](run.py). There is no frontend build step.

Optional launcher arguments: --port 8080, --host 127.0.0.1, --reload for development. No environment variables or credentials are required. The application has no authentication; bind it to networks you control.

## Use the Workbench

Search or filter cards, open a service, paste content or select a file, choose explicit options, then Run. Results offer Copy/Download; Reset clears operation state. Ctrl/Cmd+Enter runs a tool. The theme button switches modes; theme preference alone is stored. Desktop navigation collapses to an icon rail, and mobile navigation opens as a keyboard-accessible drawer.


**Processing:** Encoder, Regex, Signature, User-Agent, Cron, CIDR, MAC, SID, HTTP Status, and Entropy stay in the browser. Hash explicitly selects browser/server processing. Other services submit only to this Python instance. Browser tools never silently switch engines.

**Limits:** generally 5 MiB / one million characters for text, 50 MiB server hash files, 5 MiB browser files, 20,000 spelling characters, and 10 MiB API results. Tools impose smaller record/depth/time budgets where needed. Uploads are request-scoped; names never become filesystem paths.

Review sanitized output before sharing. Hash guesses, entropy, vendor/ASN context, JWT claims, and certificate metadata are observations rather than trust verdicts. Offline lookup snapshots are dated and intentionally partial.

## Validation and Delivery Status


This workspace blocks network socket binding and lacks Chromium, so live-server/browser/theme interaction QA remains pending. All runtime packages are now installed and unit/API checks include spelling and safe XML. Dependency locking remains pending because package-index metadata is unavailable.

Advanced logfmt/CEF/LEEF/native Zeek adapters, fuzzy/PE hashes, EVTX, and Sigma backend conversion remain explicitly deferred. Existing Zeek/Suricata network summaries accept their JSON field mappings.

## Visual Design

The supplied UI_STYLE_GUIDE.md is adapted using existing Jinja/CSS/JavaScript: graphite and slate themes, gold interactions, blue actions, restrained gradients, and 32 distinct service colors/SVG icons. Cards add a small desktop hover tilt, stronger service-colored edges, and large decorative SVG watermarks. Touch/reduced-motion users retain color feedback without tilt. Ubuntu Sans Regular is preferred for UI text; the logo uses a distinct serif wordmark. The 16.3 KiB regular WOFF2 font is bundled locally with its license; [font provenance](app/static/fonts/README.md) records its version and checksums. No React/Tailwind runtime, icon package, chart library, or remote font request was added.

## Project Documentation

- [Reference data](app/static/data/README.md) and [fonts](app/static/fonts/README.md): provenance and redistribution notices.

[GitHub — Ehsaan Mehar](https://github.com/meharehsaan)
