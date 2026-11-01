# Utility Hub

A lightweight, self-hosted Python website for daily SOC utilities: inspect logs/JSON, prepare LLM input, handle indicators, and support investigations.

**Status: final planning review; application implementation has not started.** Commands and capabilities below are targets until delivered.

## Scope

- **32 canonical services**, consolidated from 44 proposed cards without dropping capabilities. Related actions use explicit modes on one page.
- Searchable service cards, separate service modules, shared helpers, and one `run.py` launcher.
- Equal dark/light theme support, solid surfaces, distinct service accents, and small per-page assets.
- No database, accounts, saved investigation history, or external API requirements.
- Sanitizer fields for supplied sensitive strings; optional field/pattern masking, consistent aliases, preview, and replaced-output export.


## Documentation

| Document | Purpose |
| --- | --- |

## Planned Local Startup

Once Python 3.12+, `uv`, the manifest, and launcher exist, run from this directory:

```bash
uv sync --group dev
uv run python run.py
```

`python run.py` must also work in the activated environment. One process serves all implemented services, binding to localhost by default. Startup is not available yet.

## Sensitive Data and Processing

The catalog labels each service's processing mode. Ten tools run in-browser; Hash has explicit browser/server modes; the remaining tools use the self-hosted Python server. Browser workflows never upload inputs or silently fall back to server processing.

Keep content and mappings out of logs, URLs, persistent storage, and third-party services. Only theme preference may persist in browser storage. Offline reference files are separate read-only assets; custom corporate ranges remain operation-local.

Sanitizer replaces only configured matches. Review its output before sharing; it cannot guarantee complete anonymization.

## Next Step

Review the finalized plan and instruct us to begin implementation when ready. During development, update this README with actual setup/configuration and delivered features rather than treating planned behavior as working software.
