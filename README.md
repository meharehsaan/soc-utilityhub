# SOC UtilityHub

Utility tools for SOC analysts, created by **[Ehsaan Mehar](https://github.com/meharehsaan)**. A lightweight, self-hosted Python workbench for everyday SOC tasks. **32 dedicated services** share a searchable card homepage, dark/light console themes, and one launcher. No database, accounts, saved investigation history, telemetry, or external service dependencies.

## Run Locally

Use Python 3.12+ and run these commands from the repository root:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    python run.py

Open **http://127.0.0.1:8000**. An existing activated Python environment also works. There is no frontend build or database setup.

Launcher options: --port 8080, --host 127.0.0.1, and --reload for development. No environment variables or credentials are required.

For a Multipass VM such as foo, run the server inside the VM with:

    python run.py --host 0.0.0.0 --port 8000

On the host, use the VM's IPv4 from multipass info foo and open http://VM_IP:8000. The application has no authentication; use networks you control. Some browser capabilities, including native SHA hashing and clipboard access, require HTTPS or a browser-trusted localhost origin.

## Repository Layout

- app/: per-service Python modules, templates, local JavaScript/CSS, fonts, and offline reference data.
- tests/: synthetic unit/API/browser checks and fixtures.
- run.py: single launcher for every service.
- pyproject.toml, requirements.txt: project metadata and runtime dependencies.
- requirements.txt: runtime dependencies plus development and testing tools.

Virtual environments, caches, test reports, local configuration, and working data are excluded through .gitignore. Publish only this project's repository to [soc-utilityhub](https://github.com/meharehsaan/soc-utilityhub), rather than its parent workspace. Licensed assets and their notices are required parts of the application.

## Use the Workbench

Search or filter cards, open a service, paste content or select a file, choose explicit options, then Run. Results offer Copy/Download; Reset clears operation state. Ctrl/Cmd+Enter runs a tool. The theme button switches modes; theme preference alone is stored. Desktop navigation collapses to an icon rail, and mobile navigation opens as a keyboard-accessible drawer.

Highlights include exact-string sanitization, line/word/grapheme sorting and deduplication, lossless JSON with collapsible trees and field pins, log tables/network summaries, multi-hash calculation, layered decoding, IOC handling, timelines, process trees, certificate/email inspection, and local utilities. The homepage lists all 32 services. Related actions are modes within one service.

**Processing:** Encoder, Regex, Signature, User-Agent, Cron, CIDR, MAC, SID, HTTP Status, and Entropy stay in the browser. Hash explicitly selects browser/server processing. Other services submit only to this Python instance. Browser tools never silently switch engines.

**Limits:** generally 5 MiB / one million characters for text, 50 MiB server hash files, 5 MiB browser files, 20,000 spelling characters, and 10 MiB API results. Tools impose smaller record/depth/time budgets where needed. Uploads are request-scoped; names never become filesystem paths.

Review sanitized output before sharing. Hash guesses, entropy, vendor/ASN context, JWT claims, and certificate metadata are observations rather than trust verdicts. Offline lookup snapshots are dated and intentionally partial.

## Validation and Delivery Status

All 32 pages/controllers are implemented. The last complete checks passed 111 Python tests with 168 subtests and 51 Node engine tests, together with Ruff and dependency consistency checks.

This workspace blocks network socket binding and lacks Chromium, so live-server/browser/theme interaction QA remains pending. All runtime packages are now installed and unit/API checks include spelling and safe XML. Dependency locking remains pending because package-index metadata is unavailable.

Advanced logfmt/CEF/LEEF/native Zeek adapters, fuzzy/PE hashes, EVTX, and Sigma backend conversion remain explicitly deferred. Existing Zeek/Suricata network summaries accept their JSON field mappings.

## Visual Design

The interface uses Jinja/CSS/JavaScript: graphite and slate themes, gold interactions, blue actions, restrained gradients, and 32 distinct service colors/SVG icons. Cards add a small desktop hover tilt, stronger service-colored edges, and large decorative SVG watermarks. Touch/reduced-motion users retain color feedback without tilt. Ubuntu Sans Regular is preferred for UI text; the logo uses a distinct serif wordmark. The 16.3 KiB regular WOFF2 font is bundled locally with its license; [font provenance](app/static/fonts/README.md) records its version and checksums. No React/Tailwind runtime, icon package, chart library, or remote font request was added.

## Development and Checks

From an activated Python 3.12+ environment:

    python -m pip install -r requirements.txt
    python -m ruff check app run.py tests
    python -m ruff format --check app run.py tests
    python -m pytest tests/unit tests/integration -q
    node --experimental-default-type=module tests/browser/engines.test.mjs
    node --experimental-default-type=module tests/browser/utilities.test.mjs

Node checks require Node 22+ and no npm installation. Runtime dependencies in requirements.txt mirror project.dependencies in pyproject.toml; requirements.txt mirrors its dev group and includes the runtime file. Keep both formats synchronized when changing packages. A uv.lock still needs resolution and review with package-index access; requirements files currently declare compatible ranges rather than a fully pinned environment.

For browser workflows, run the server in another terminal, then:

    python -m playwright install chromium
    python -m pytest tests/browser/test_workflows.py --base-url http://127.0.0.1:8000

Keep services in separate Python/template/JavaScript modules, with small shared helpers. Use typed Python, four-space indentation, two-space JavaScript indentation, and one short purpose comment above each function. Test bounded input handling, malformed data, browser/server isolation, and both themes with synthetic data. Review diffs and use clear 4–5 word commit subjects.

Reference sources, coverage, checksums, and third-party notices remain beside [reference data](app/static/data/README.md), [fonts](app/static/fonts/README.md), and [vendor code](app/static/vendor/README.md).

## License and Author

Original project code is licensed under the [MIT License](LICENSE), copyright © 2026 [Ehsaan Mehar](https://github.com/meharehsaan). Bundled fonts, MD5 implementation, and reference assets retain the licenses/notices stored beside them.
