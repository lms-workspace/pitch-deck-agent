"""
Data models for the Pitch Deck Agent pipeline.

These models define the contract between every module:
  IngestedDocument → NarrativeElements → PitchDeck → Slide
"""
from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ── File Ingestion Models ─────────────────────────────────────────────

class FileType(str, Enum):
    PDF = "pdf"
    IMAGE = "image"
    TEXT = "text"
    EMAIL = "email"
    VIDEO = "video"
    UNKNOWN = "unknown"


class IngestedDocument(BaseModel):
    """Result of parsing a single uploaded file."""
    filename: str
    file_type: FileType
    extracted_text: str = ""
    page_count: int = 0
    image_descriptions: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    raw_content_preview: str = Field(
        default="",
        description="First 500 chars for quick inspection"
    )

    @property
    def has_content(self) -> bool:
        return bool(self.extracted_text.strip() or self.image_descriptions)


class IngestResult(BaseModel):
    """Aggregated result from all uploaded files."""
    documents: list[IngestedDocument] = Field(default_factory=list)
    total_files: int = 0
    total_text_chars: int = 0
    errors: list[str] = Field(default_factory=list)

    @property
    def combined_text(self) -> str:
        """Merge all extracted text with source attribution."""
        sections = []
        for doc in self.documents:
            if doc.has_content:
                sections.append(
                    f"--- SOURCE: {doc.filename} ({doc.file_type.value}) ---\n"
                    f"{doc.extracted_text}\n"
                )
                if doc.image_descriptions:
                    sections.append(
                        "IMAGE DESCRIPTIONS:\n" +
                        "\n".join(f"  - {d}" for d in doc.image_descriptions) +
                        "\n"
                    )
        return "\n".join(sections)


# ── Narrative / Story Synthesis Models ────────────────────────────────

class Character(BaseModel):
    name: str
    role: str = ""
    description: str = ""
    arc: str = ""


class NarrativeElements(BaseModel):
    """Core story elements extracted by the synthesis step."""
    title: str = "Untitled Project"
    logline: str = ""
    genre: str = ""
    tone: str = ""
    themes: list[str] = Field(default_factory=list)
    setting: str = ""
    time_period: str = ""
    characters: list[Character] = Field(default_factory=list)
    protagonist: str = ""
    antagonist: str = ""
    conflict: str = ""
    plot_summary: str = ""
    plot_arc: str = Field(
        default="",
        description="Setup → Confrontation → Resolution breakdown"
    )
    hook: str = Field(
        default="",
        description="Opening hook / elevator pitch"
    )
    target_audience: str = ""
    comparable_titles: list[str] = Field(
        default_factory=list,
        description="Comp titles (e.g., 'Stranger Things meets The OA')"
    )
    visual_style: str = ""
    key_scenes: list[str] = Field(default_factory=list)
    raw_synthesis: str = Field(
        default="",
        description="Full synthesis text for debugging"
    )


# ── Pitch Deck Models ────────────────────────────────────────────────

class SlideType(str, Enum):
    TITLE = "title"
    LOGLINE = "logline"
    GENRE_TONE = "genre_tone"
    CHARACTERS = "characters"
    SETTING = "setting"
    PLOT = "plot"
    CONFLICT = "conflict"
    KEY_SCENES = "key_scenes"
    AUDIENCE_COMPS = "audience_comps"
    CLOSING = "closing"


class Slide(BaseModel):
    """Single slide in the pitch deck."""
    slide_number: int
    slide_type: SlideType
    title: str
    subtitle: str = ""
    body: str = ""
    bullets: list[str] = Field(default_factory=list)
    speaker_notes: str = ""
    image_prompt: str = Field(
        default="",
        description="AI image generation prompt for visual slides"
    )


class PitchDeck(BaseModel):
    """Complete pitch deck output."""
    title: str
    slides: list[Slide] = Field(default_factory=list)
    narrative: Optional[NarrativeElements] = None
    source_file_count: int = 0
    generation_model: str = ""

    @property
    def slide_count(self) -> int:
        return len(self.slides)
