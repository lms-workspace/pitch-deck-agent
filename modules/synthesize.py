"""
Story Synthesis Module

Takes ingested document content and runs it through an LLM to extract
structured narrative elements (characters, plot, themes, etc.).

Supports both Gemini 2.0 Flash and Claude as synthesis backends.
"""
from __future__ import annotations

import json
import re

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from core.models import Character, IngestResult, NarrativeElements
from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    CLAUDE_API_KEY,
    CLAUDE_MODEL,
    SYNTHESIS_PROVIDER,
)
from prompts.story_synthesis import STORY_SYNTHESIS_SYSTEM, STORY_SYNTHESIS_PROMPT


# ── JSON Extraction Helper ────────────────────────────────────────────

def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown fences and extras."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences
    patterns = [
        r"```json\s*(.*?)\s*```",
        r"```\s*(.*?)\s*```",
        r"\{.*\}",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                candidate = match.group(1) if match.lastindex else match.group(0)
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Could not extract valid JSON from response:\n{text[:500]}...")


def _parse_narrative(data: dict, raw_text: str = "") -> NarrativeElements:
    """Convert raw JSON dict to NarrativeElements model."""
    characters = []
    for char_data in data.get("characters", []):
        if isinstance(char_data, dict):
            characters.append(Character(
                name=char_data.get("name", "Unknown"),
                role=char_data.get("role", ""),
                description=char_data.get("description", ""),
                arc=char_data.get("arc", ""),
            ))

    return NarrativeElements(
        title=data.get("title", "Untitled Project"),
        logline=data.get("logline", ""),
        genre=data.get("genre", ""),
        tone=data.get("tone", ""),
        themes=data.get("themes", []),
        setting=data.get("setting", ""),
        time_period=data.get("time_period", ""),
        characters=characters,
        protagonist=data.get("protagonist", ""),
        antagonist=data.get("antagonist", ""),
        conflict=data.get("conflict", ""),
        plot_summary=data.get("plot_summary", ""),
        plot_arc=data.get("plot_arc", ""),
        hook=data.get("hook", ""),
        target_audience=data.get("target_audience", ""),
        comparable_titles=data.get("comparable_titles", []),
        visual_style=data.get("visual_style", ""),
        key_scenes=data.get("key_scenes", []),
        raw_synthesis=raw_text,
    )


# ── Gemini Synthesis ──────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def _synthesize_with_gemini(combined_text: str) -> NarrativeElements:
    """Run story synthesis through Gemini 2.0 Flash."""
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        GEMINI_MODEL,
        system_instruction=STORY_SYNTHESIS_SYSTEM,
    )

    prompt = STORY_SYNTHESIS_PROMPT.format(combined_text=combined_text)

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.7,
            max_output_tokens=4096,
            response_mime_type="application/json",
        ),
    )

    raw_text = response.text
    logger.debug(f"Gemini synthesis response length: {len(raw_text)} chars")

    data = _extract_json(raw_text)
    return _parse_narrative(data, raw_text)


# ── Claude Synthesis ──────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
def _synthesize_with_claude(combined_text: str) -> NarrativeElements:
    """Run story synthesis through Claude."""
    import anthropic

    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    prompt = STORY_SYNTHESIS_PROMPT.format(combined_text=combined_text)

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=STORY_SYNTHESIS_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text
    logger.debug(f"Claude synthesis response length: {len(raw_text)} chars")

    data = _extract_json(raw_text)
    return _parse_narrative(data, raw_text)


# ── Main Entry Point ──────────────────────────────────────────────────

def synthesize_narrative(ingest_result: IngestResult, provider: str | None = None) -> NarrativeElements:
    """
    Extract narrative elements from ingested documents.

    Args:
        ingest_result: Output from the ingestion module.
        provider: "gemini" or "claude". Defaults to config.SYNTHESIS_PROVIDER.

    Returns:
        NarrativeElements with all story structure extracted.
    """
    provider = provider or SYNTHESIS_PROVIDER
    combined_text = ingest_result.combined_text

    if not combined_text.strip():
        logger.warning("No content to synthesize — returning empty narrative")
        return NarrativeElements()

    # Truncate if needed (Gemini context is 1M tokens, but be reasonable)
    max_chars = 100_000
    if len(combined_text) > max_chars:
        logger.warning(f"Truncating combined text from {len(combined_text)} to {max_chars} chars")
        combined_text = combined_text[:max_chars]

    logger.info(f"Running story synthesis with {provider} ({len(combined_text)} chars input)")

    if provider == "claude" and CLAUDE_API_KEY:
        return _synthesize_with_claude(combined_text)
    elif GEMINI_API_KEY:
        return _synthesize_with_gemini(combined_text)
    else:
        raise ValueError(
            "No API key configured. Set GEMINI_API_KEY or CLAUDE_API_KEY environment variable."
        )
