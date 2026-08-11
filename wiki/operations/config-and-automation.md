---
type: operations map
title: Configuration, container, and code-map automation
description: Environment-backed application settings, Docker execution boundary, and separate derived documentation workflow behavior.
tags: [configuration, operations, automation]
authority: derived-noncanonical
canonical: false
xtrace_ingest: deny
generated_by: openwiki@0.3.1
source_commit: d3425ef2e5aa00f56c0872ee913567d856569618
---

# Configuration, container, and code-map automation

## Application configuration

`config.py` reads named environment values without embedding their values: `GEMINI_API_KEY`, `CLAUDE_API_KEY`, and `GOOGLE_CREDENTIALS_JSON`. It also supplies model IDs, default synthesis provider, size/page limits, extension lists, deck defaults, and the Google OAuth scopes. `TEMP_DIR` is calculated under `BASE_DIR` and created during config import.

| Configuration | Consumed by | Source-visible effect |
|---|---|---|
| `GEMINI_API_KEY` / `GEMINI_MODEL` | UI key check, ingestion vision helper, Gemini synthesis | Enables selected vision fallbacks and Gemini calls. |
| `CLAUDE_API_KEY` / `CLAUDE_MODEL` | UI key check, Claude synthesis | Enables Claude branch only when provider equals `claude`. |
| `GOOGLE_CREDENTIALS_JSON` | Pipeline branch selection, Google service construction | Enables the Google export branch and supplies service-account JSON when nonempty. |
| `SYNTHESIS_PROVIDER` | Pipeline/synthesis default | Used when caller does not supply provider. |
| upload/page limits and extensions | Ingestion | Extension/size validation and PDF page cap; file-count setting is not enforced. |
| Slides/Drive scopes | Google service account | Requests presentation and `drive.file` access. |

The code also falls back to `GOOGLE_APPLICATION_CREDENTIALS` or `credentials.json` inside the Google exporter when JSON is absent, although pipeline normally chooses PPTX when the JSON config is empty. Do not document credential values. No secrets are stored in this derived wiki.

## Container boundary

`Dockerfile` uses `python:3.11-slim`, installs `libmagic1`, installs `requirements.txt`, copies the repository, creates `/app/tmp`, exposes 7860, and executes `python app.py`. Requirements declare Gradio, Pydantic, Gemini/Anthropic SDKs, PyMuPDF/Pillow, Google client/auth packages, `python-pptx`, Loguru, Tenacity, dotenv, and `python-magic`. Commented Whisper/ffmpeg dependencies are not installed. Docker presence is source evidence only; no image build/run test is tracked.

## Derived code-map workflow—not application deployment

`.github/workflows/code-map.yml` defines a GitHub Actions workflow that uses OpenWiki to generate documentation. It is separate from the Pitch Deck application and should never be interpreted as an app build, integration test, or deployment validation.

- **Trigger asymmetry:** pushes to `main` respond to listed source/config/workflow paths; pull requests respond only to `.openwikiignore`, instructions, and workflow/package-script paths, not ordinary application source changes.
- **Credential boundary:** it explicitly checks only a GitHub-provided `GEMINI_API_KEY` for the documentation provider. That is separate from runtime application provider configuration.
- **Concurrency and permissions:** it has ref-scoped `code-map` concurrency with cancellation in progress and `contents: write` permission.
- **Publication:** it uploads a 14-day review artifact; on non-PR `main` runs, it creates an orphan commit and force-pushes a `code-map` branch.
- **Tool pin:** it installs `openwiki@0.3.1` and invokes its code-init command with a configured Gemini model ID.

The packaging script `.github/scripts/package-code-map.py` rejects selected filenames/automation directories and secret-like patterns, copies generated markdown, stamps it as `derived-noncanonical`, repairs/validates internal links, produces a manifest/provenance JSON, and writes a branch README. Those checks constrain generated documentation only. They do not run `app.py`, invoke the pitch pipeline, verify external provider credentials, or prove output correctness.

## Change and validation routing

- Change a provider/model/limit/scope: update `config.py` and its direct consumer; review UI and pipeline behavior too.
- Change startup/container packages: update `Dockerfile` and `requirements.txt`; video support additionally needs actual implementation rather than uncommenting intent.
- Change documentation automation: update both the workflow and package script; assess its trigger/publishing consequences separately from application behavior.
- Input and policy gaps are catalogued in [implementation status](../status/implementation-status.md); runtime selection is in [pipeline runtime](../runtime/pipeline.md).

No committed test command exists. A narrow validation strategy must be introduced with tests for the specific changed component; generated-map packaging success is not a substitute.
