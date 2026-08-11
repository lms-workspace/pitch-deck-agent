---
type: implementation status
title: Implementation status and known limits
description: Evidence-backed gaps, stubs, contract mismatches, and unverified behavior in tracked Pitch Deck Agent source.
tags: [status, limitations, scaffolding]
authority: derived-noncanonical
canonical: false
xtrace_ingest: deny
generated_by: openwiki@0.3.1
source_commit: d3425ef2e5aa00f56c0872ee913567d856569618
---

# Implementation status and known limits

This page separates source-present behavior from README/product intent. All items below are based on inspected tracked source and are **runtime unverified**: no tracked `tests/` directory, test-named source file, or test configuration was found. The README lists test paths, but a README is not execution evidence.

## Cross-boundary contract issues

| Status | Evidence-backed condition | Impact | Owning change surface |
|---|---|---|---|
| Defect | `detect_file_type` constructs invalid `FileType("document")` for every extension categorized as `documents`, before the intended map executes. | PDF/text/Markdown/RTF detected via configured document category can fail before parser dispatch. | `modules/ingest.py:detect_file_type`; see [ingestion](../ingestion/ingestion.md). |
| Mismatch | UI accepts `.rtf` and `.msg` without mentioning them in its supported-files copy; config permits GIF/video but UI filter does not. | UI, help text, and config do not describe one consistent input contract. | `app.py:create_app`, `config.SUPPORTED_EXTENSIONS`. |
| Incomplete compatibility | `.msg` is routed to `parse_email`, which uses RFC `email.message_from_bytes` intended for `.eml`-style content. | No dedicated Outlook MSG parser is present. | `modules/ingest.py:parse_email`. |
| Deliberate non-recursion | Email parser records attachment names/count only. | Attachments do not enter the parser/synthesis chain. | `modules/ingest.py:parse_email`. |
| Stub | `parse_video` returns text declaring transcription pending and `status: not_implemented`. | No video frames, ffmpeg, or Whisper processing occurs. | `modules/ingest.py:parse_video`. |
| Unenforced config | `MAX_UPLOAD_FILES = 10` exists but no inspected code checks it. | File-count limit is not enforced by the pipeline. | `config.py`, `modules/ingest.py`. |
| Mismatch | UI allows 6–15 slides; builder slices a fixed 10-entry flow. | Requests above 10 silently yield 10 slides. | `app.py:create_app`, `modules/deck_builder.py:build_deck`. |
| Export divergence | PPTX writes notes; Google Slides helper exists but is never invoked. | Speaker notes are output only in PPTX branch. | `modules/google_slides.py`; see [deck and exports](../deck/deck-and-exports.md). |
| Partial remote result | Google presentation is created before batch update; sharing errors are only logged. | A failed export can leave a presentation; returned URL does not prove sharing succeeded. | `modules/google_slides.py:export_to_google_slides`. |

## Source versus README matrix

| Claim/material | Tracked-source conclusion |
|---|---|
| README `tests/test_ingest.py`, `test_synthesize.py`, `test_pipeline.py` | No `tests/` directory was found. There is no committed behavior test evidence for parser, provider, pipeline, or export contracts. |
| README `modules/pptx_output.py` | Not present. PPTX writer is implemented in `modules/google_slides.py:export_to_pptx`. |
| README `modules/canva_output.py`, `prompts/slide_content.py`, `prompts/refinement.py`, `utils/file_handlers.py`, `utils/video_utils.py`, `utils/image_utils.py`, six-slide template, assets/sample inputs | Not present in inspected source. Do not treat phase descriptions or listed paths as implemented. |
| `templates/deck_10_slide.json` | Present, but no application code imports it; the Python `SLIDE_FLOW_10` controls actual builder order. |
| `SLIDE_CONTENT_PROMPT`, `REFINEMENT_PROMPT` in `prompts/story_synthesis.py` | Present constants but not imported outside that file; no refinement or per-slide LLM stage runs. |

## Present components, still unverified

Gradio UI composition, input parsing functions, Gemini/Claude SDK integration calls, Pydantic in-memory models, deterministic slide mapping, local PPTX writing, Google API request creation, Docker command, and GitHub code-map workflow all exist in tracked source. Their presence does not demonstrate that credentials, external APIs, package versions, filesystem paths, generated files, or deployment environment work together. In particular, the documentation workflow is not an application test; see [configuration and automation](../operations/config-and-automation.md).

## Recommended repair sequence

1. Repair `detect_file_type` and add focused byte-level tests for each configured extension and validation failure.
2. Decide/implement one coherent file-type contract across config, UI filter/help, and parsers; explicitly handle `.msg`, attachments, and video rather than relying on labels.
3. Make slide count policy explicit in builder/pipeline and test boundary values.
4. Decide whether Google speaker notes, cleanup on failed batch updates, and sharing failure reporting are required; implement/test accordingly.
5. Add isolated provider mocks and exporter fixtures only after defining expected contracts; current source contains no test harness.

These are change-routing observations, not project requirements or canonical task decisions.
