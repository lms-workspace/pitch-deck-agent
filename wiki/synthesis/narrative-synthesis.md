---
type: subsystem map
title: Narrative synthesis
description: Provider selection, prompt assembly, retries, JSON extraction, and NarrativeElements construction for the synthesis stage.
tags: [synthesis, llm, external-integrations]
authority: derived-noncanonical
canonical: false
xtrace_ingest: deny
generated_by: openwiki@0.3.1
source_commit: d3425ef2e5aa00f56c0872ee913567d856569618
---

# Narrative synthesis

`modules.synthesize:synthesize_narrative` consumes `IngestResult.combined_text` and returns `NarrativeElements`. It is called by `run_pipeline` after at least one ingested document exists. The module supports two source-visible provider integrations: Gemini via `google.generativeai` and Claude via `anthropic`. Calls are present in tracked source; no committed test demonstrates them running.

## Input and model contract

`IngestResult.combined_text` concatenates usable documents with filename and `FileType` attribution plus optional image descriptions. `synthesize_narrative` returns a default empty `NarrativeElements` without provider calls when that string is blank. Otherwise it truncates content to 100,000 characters, preserving the prefix only, then formats `STORY_SYNTHESIS_PROMPT` with the result.

`_parse_narrative` maps a JSON dictionary into the Pydantic model in `core.models`: title, logline, genre/tone, setting/time, `Character` records, conflict/plot/hook, audience/comparables, visual style, and scenes. Absent scalar fields get model defaults; only dictionary-valued character entries are included. The original provider response is retained in `raw_synthesis`.

## Provider selection and calls

| Condition | Call | Configuration | Retry behavior |
|---|---|---|---|
| `provider == "claude"` and `CLAUDE_API_KEY` is nonempty | `_synthesize_with_claude` | `CLAUDE_MODEL`, system text and user prompt supplied to `client.messages.create`. | At most 3 attempts with exponential waits from 2 seconds up to 30. |
| Every other case with nonempty `GEMINI_API_KEY` | `_synthesize_with_gemini` | `GEMINI_MODEL`, system instruction, temperature 0.7, max 4096 tokens, JSON MIME type. | Same retry decorator. |
| Neither applicable key exists | No provider call | Raises `ValueError`. | Pipeline catches it and marks the run failed. |

The provider parameter is not validated against an allowlist. In particular, a value other than `claude` selects Gemini when a Gemini key exists. The UI checks selected key presence before it invokes the pipeline, but callers of `run_pipeline` may bypass that UI check.

## Structured-output tolerance

`_extract_json` first attempts `json.loads` on the complete response. If that fails, it tries a fenced `json` block, any fenced block, then a greedy brace regex. Failure raises `ValueError` including only the response prefix. This is resilience code rather than schema enforcement: Pydantic field defaults and `data.get` coerce only the explicitly mapped values; no validation proves the provider followed the requested semantic constraints.

The system and task prompts live in `prompts/story_synthesis.py`. The active task explicitly tells the model to fill unclear/missing information and label it `[INFERRED]`. The code does not detect, require, remove, or separately expose those markers, so generated deck content can combine source-derived and model-inferred claims. Treat the prompt instruction as behavior of the request, not assurance that every output is marked.

## Trust and data boundaries

This is the point where aggregated uploaded text—including extracted email headers/body and image descriptions—leaves the application for Gemini or Claude. The source provides API key injection through `config.py`; it does not implement consent, per-user provider authorization, prompt-injection defenses, output moderation, data residency controls, or a retention policy. Provider exceptions retry at the SDK-call level, then bubble to `run_pipeline` after exhaustion.

`SLIDE_CONTENT_PROMPT` and `REFINEMENT_PROMPT` are defined beside the active story prompt but are not imported by other application modules. They do not create a per-slide generation or refinement stage in current tracked source; see [deck and exports](../deck/deck-and-exports.md).
