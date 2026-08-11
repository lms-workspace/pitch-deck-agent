---
type: quickstart
title: Pitch Deck Agent code map
description: A derived, source-grounded navigation guide to Pitch Deck Agent implementation, boundaries, flows, integrations, and known limitations.
tags: [quickstart, pitch-deck-agent, code-map]
authority: derived-noncanonical
canonical: false
xtrace_ingest: deny
generated_by: openwiki@0.3.1
source_commit: d3425ef2e5aa00f56c0872ee913567d856569618
---

# Pitch Deck Agent code map

This wiki is **derived and replaceable**, based on tracked source inspected for this run. It is not canonical project authority, requirements, handoff, task state, or runtime verification. The LMS-Vault owner `projects/pitch-deck-agent` remains canonical authority. No tracked test suite/configuration was found, so source-present application behavior is **runtime unverified**.

## Repository map

Pitch Deck Agent is a single Python/Gradio process. Its UI accepts creative-file uploads, invokes a four-stage pipeline (ingest → synthesize → build deck → export), and renders a status, narrative text, PPTX path, or Google Slides link. Its primary sources are `app.py`, `core/pipeline.py`, `core/models.py`, and modules under `modules/`. There are no tracked application HTTP routes, command-line subcommands, scheduled jobs, event consumers, database models, migrations, queues, or caches.

Start with [architecture](architecture/overview.md) for composition and provider boundaries. Follow [pipeline runtime](runtime/pipeline.md) for event ordering and failures. The source-vs-intent distinctions and defects are consolidated in [implementation status](status/implementation-status.md).

## Task routing

| Engineering intent | Wiki page | Primary source symbols | Focused validation evidence |
|---|---|---|---|
| Change UI controls, accepted UI files, or rendered results | [Pipeline runtime](runtime/pipeline.md) | `app.py:create_app`, `generate_deck` | No tracked focused test; add/execute a handler/UI test. |
| Change pipeline stage selection, status, or export branch | [Pipeline runtime](runtime/pipeline.md) | `core.pipeline:run_pipeline`, `PipelineResult` | No tracked pipeline test. |
| Add/fix file parsing or input validation | [Asset ingestion](ingestion/ingestion.md) | `detect_file_type`, `validate_file`, `ingest_file`, parsers | No tracked ingestion test; prioritize valid/invalid extension bytes. |
| Change LLM provider, schema mapping, prompt, inference handling, or retries | [Narrative synthesis](synthesis/narrative-synthesis.md) | `synthesize_narrative`, provider helpers, `_extract_json` | No tracked provider-mocked test. |
| Change slide content, templates, PPTX, Slides, notes, or sharing | [Deck construction and exports](deck/deck-and-exports.md) | `build_deck`, `_build_slide`, `export_to_pptx`, `export_to_google_slides` | No tracked exporter test. |
| Change keys, limits, Docker, scopes, or generated-map CI | [Configuration and automation](operations/config-and-automation.md) | `config.py`, `Dockerfile`, workflow/package script | Container/workflow presence is runtime unverified. |
| Assess a stub, mismatch, unconsumed asset, absent README path, or test gap | [Implementation status](status/implementation-status.md) | cross-boundary ownership table | Source inspection only. |

## Key concepts

- **In-memory models:** `IngestedDocument → IngestResult → NarrativeElements → PitchDeck → Slide`; no persistence layer is declared. [Architecture](architecture/overview.md) and [deck exports](deck/deck-and-exports.md) explain the contract.
- **External boundaries:** uploaded content may be sent to Gemini or Claude, and service-account credentials can create/optionally share Google Slides. [Ingestion](ingestion/ingestion.md) and [synthesis](synthesis/narrative-synthesis.md) identify the exact call sites and trust limitations.
- **Output selection:** Google Slides requires exact normalized selection plus nonempty `GOOGLE_CREDENTIALS_JSON`; otherwise the pipeline writes a PPTX under `tmp`. [Pipeline runtime](runtime/pipeline.md) describes the condition.
- **Scaffolding and limits:** video is explicitly stubbed; the JSON deck template and two prompt constants are unconsumed; document-type dispatch has a source defect; README phase/path claims do not prove implementation. [Implementation status](status/implementation-status.md) is the canonical wiki location for these distinctions.

## Validation and backlog

There is no committed test harness, and this wiki must not imply that source presence equals successful execution. The highest-risk source-grounded repairs are: document-type dispatch in `modules/ingest.py`, consistent UI/config/parser file contracts, missing enforcement for `MAX_UPLOAD_FILES`, explicit slide-count policy, and Google exporter notes/partial-failure semantics. These are documented change surfaces—not new requirements—in [implementation status](status/implementation-status.md).

No valid source-blocked coverage deferrals remain: all substantive tracked application and automation components have a dedicated page or are grouped in their owning subsystem page.
