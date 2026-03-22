"""
Main Pipeline Orchestrator

Connects all modules: Ingest → Synthesize → Build Deck → Export

This is the single entry point that Gradio (or any frontend) calls.
"""
from __future__ import annotations

from pathlib import Path

from loguru import logger

from core.models import IngestResult, NarrativeElements, PitchDeck
from modules.ingest import ingest_from_gradio, ingest_files
from modules.synthesize import synthesize_narrative
from modules.deck_builder import build_deck
from modules.google_slides import export_to_google_slides, export_to_pptx
from config import GOOGLE_CREDENTIALS_JSON, SYNTHESIS_PROVIDER


class PipelineResult:
    """Container for pipeline output."""

    def __init__(self):
        self.ingest_result: IngestResult | None = None
        self.narrative: NarrativeElements | None = None
        self.deck: PitchDeck | None = None
        self.output_url: str = ""
        self.output_file: str = ""
        self.errors: list[str] = []
        self.status: str = "pending"

    @property
    def summary(self) -> str:
        """Human-readable summary of the pipeline run."""
        lines = [f"Status: {self.status}"]

        if self.ingest_result:
            lines.append(
                f"Ingested: {len(self.ingest_result.documents)}/{self.ingest_result.total_files} files "
                f"({self.ingest_result.total_text_chars:,} chars)"
            )

        if self.narrative:
            lines.append(f"Title: {self.narrative.title}")
            lines.append(f"Genre: {self.narrative.genre}")
            lines.append(f"Logline: {self.narrative.logline}")
            lines.append(f"Characters: {len(self.narrative.characters)}")

        if self.deck:
            lines.append(f"Slides: {self.deck.slide_count}")

        if self.output_url:
            lines.append(f"Google Slides: {self.output_url}")
        if self.output_file:
            lines.append(f"PowerPoint: {self.output_file}")

        if self.errors:
            lines.append(f"Errors: {'; '.join(self.errors)}")

        return "\n".join(lines)


def run_pipeline(
    uploaded_files,
    output_format: str = "pptx",
    slide_count: int = 10,
    synthesis_provider: str | None = None,
    share_email: str = "",
) -> PipelineResult:
    """
    Run the full pitch deck generation pipeline.

    Args:
        uploaded_files: List of Gradio file objects or (filename, bytes) tuples.
        output_format: "google_slides" or "pptx".
        slide_count: Number of slides (default 10).
        synthesis_provider: "gemini" or "claude" (defaults to config).
        share_email: Email to share Google Slides with.

    Returns:
        PipelineResult with all intermediate and final outputs.
    """
    result = PipelineResult()
    provider = synthesis_provider or SYNTHESIS_PROVIDER

    try:
        # ── Step 1: Ingest ────────────────────────────────────────
        logger.info("Step 1: Ingesting files...")
        result.status = "ingesting"

        if uploaded_files and hasattr(uploaded_files[0], "name"):
            result.ingest_result = ingest_from_gradio(uploaded_files)
        elif uploaded_files and isinstance(uploaded_files[0], tuple):
            result.ingest_result = ingest_files(uploaded_files)
        else:
            result.errors.append("No valid files provided")
            result.status = "failed"
            return result

        if not result.ingest_result.documents:
            result.errors.append("No content could be extracted from uploaded files")
            result.status = "failed"
            return result

        result.errors.extend(result.ingest_result.errors)

        # ── Step 2: Synthesize ────────────────────────────────────
        logger.info("Step 2: Synthesizing narrative...")
        result.status = "synthesizing"

        result.narrative = synthesize_narrative(
            result.ingest_result, provider=provider
        )

        if not result.narrative.logline:
            logger.warning("Synthesis produced empty logline — narrative may be thin")

        # ── Step 3: Build Deck ────────────────────────────────────
        logger.info("Step 3: Building deck structure...")
        result.status = "building"

        result.deck = build_deck(result.narrative, slide_count=slide_count)
        result.deck.source_file_count = result.ingest_result.total_files
        result.deck.generation_model = provider

        # ── Step 4: Export ────────────────────────────────────────
        logger.info(f"Step 4: Exporting to {output_format}...")
        result.status = "exporting"

        if output_format == "google_slides" and GOOGLE_CREDENTIALS_JSON:
            export_result = export_to_google_slides(
                result.deck, share_with_email=share_email or None
            )
            result.output_url = export_result["url"]
        else:
            # Default to PowerPoint (works without any API keys)
            output_path = str(Path("tmp") / f"{result.deck.title.replace(' ', '_')}_pitch.pptx")
            Path("tmp").mkdir(exist_ok=True)
            result.output_file = export_to_pptx(result.deck, output_path)

        result.status = "complete"
        logger.info(f"Pipeline complete: {result.deck.slide_count} slides generated")

    except Exception as e:
        logger.exception("Pipeline failed")
        result.errors.append(str(e))
        result.status = "failed"

    return result
