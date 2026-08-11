---
type: subsystem map
title: Asset ingestion and validation
description: File intake, validation, parser dispatch, normalization, and external vision fallbacks in the tracked ingestion module.
tags: [ingestion, validation, security]
authority: derived-noncanonical
canonical: false
xtrace_ingest: deny
generated_by: openwiki@0.3.1
source_commit: d3425ef2e5aa00f56c0872ee913567d856569618
---

# Asset ingestion and validation

`modules/ingest.py` turns uploaded byte content into `IngestedDocument` objects and aggregates them as `IngestResult`. `core.pipeline.run_pipeline` invokes it before LLM synthesis. The interface accepts `(filename, bytes)` pairs; `ingest_from_gradio` converts Gradio-like objects by reading `Path(f.name).read_bytes()`. This makes upload paths and their content a trust boundary within the application process.

## Contract and dispatch

| Symbol | Responsibility | Output / failure handling |
|---|---|---|
| `validate_file` | Checks filename extension against config and enforces `MAX_FILE_SIZE_MB` (50). | Returns an error string or `None`. |
| `detect_file_type` | Attempts to map extension to `FileType`. | Has a source defect for configured document types; see below. |
| `ingest_file` | Detects, validates, gets parser from `PARSER_MAP`, catches parser exceptions. | Returns an `IngestedDocument`; failures live in `metadata["error"]`. |
| `ingest_files` | Iterates pairs, excludes documents with `metadata.error` from `documents`, and aggregates error strings/text length. | `IngestResult`. |
| `IngestResult.combined_text` | Emits source-attributed text and image descriptions for usable documents. | Input to synthesis. |

`SUPPORTED_EXTENSIONS` in `config.py` lists document (`.pdf`, `.txt`, `.md`, `.rtf`), email (`.eml`, `.msg`), image (`.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`), and video extensions. The displayed Gradio file filter is not the same set. Current mismatches and their owner locations are listed in [implementation status](../status/implementation-status.md).

## Parser behavior

| File type | Function | Implemented behavior | External boundary |
|---|---|---|---|
| PDF | `parse_pdf` | Uses PyMuPDF to extract up to `MAX_PDF_PAGES` (100) text pages and tags page headings. Under 200 extracted characters, it tries a Gemini fallback if a key is set. | Fallback rasterizes at most ten pages and submits PNG bytes to Gemini. |
| Image | `parse_image` | Optionally requests a Gemini description; independently tries Pillow metadata (`size`, `format`, `mode`). | The image bytes are base64 encoded for Gemini when configured. |
| Text | `parse_text` | Decodes UTF-8, UTF-16, Latin-1, or CP1252, then uses replacement UTF-8. `.rtf` is only decoded as text; no RTF structure parser is present. | No network call. |
| Email | `parse_email` | Uses Python email parsing, adds selected headers and plain text body; uses stripped HTML only if no plain text was collected. | Attachment names/count are recorded; attachment bytes are not recursively ingested. |
| Video | `parse_video` | Returns an `IngestedDocument` that states transcription is pending and marks metadata `not_implemented`. | No ffmpeg/Whisper call exists. |

## Implemented constraints and limits

The validation function only checks extension and byte size. It does not inspect MIME bytes despite imports that might suggest otherwise, does not enforce `MAX_UPLOAD_FILES`, and does not scan content. `ingest_files` processes sequentially. PDF fallback is conditional on a configured Gemini key and catches its own exception, preserving the native extraction result where available; image Gemini failure similarly degrades to an empty description/metadata attempt.

The `raw_content_preview` field stores the first 500 characters of extracted content and `combined_text` carries both text and image descriptions. Consequently, potentially sensitive uploaded material can cross into the synthesis prompt and optional Gemini vision requests. The inspected source contains no user identity checks, tenant policy, redaction, retention policy, or deletion/temporary-file cleanup protocol.

## Critical tracked-source defect

`detect_file_type` loops through `SUPPORTED_EXTENSIONS` and immediately returns `FileType(ftype.rstrip("s"))` on a match. For `ftype == "documents"`, this asks the enum to construct `FileType("document")`, but enum values are `pdf`, `image`, `text`, `email`, `video`, and `unknown`. The later `ext_map` that correctly distinguishes PDF/text is therefore unreachable for recognized document extensions. `ingest_file` calls detection outside its parser `try`, so this exception propagates to the outer pipeline handler and causes a failed run. This is source analysis, not execution evidence.

## Safe change surface

To add a real file type, update `SUPPORTED_EXTENSIONS`, make `detect_file_type` return a valid enum, register parser in `PARSER_MAP`, ensure `validate_file` permits it, align the UI filter/help, and add focused tests for valid and invalid bytes. For email attachments or video, there is no current extension seam beyond replacing the named/stub behavior. Review [configuration](../operations/config-and-automation.md) for the nominal limits and [pipeline runtime](../runtime/pipeline.md) for error propagation.
