"""
Deck Builder Module

Takes NarrativeElements and maps them to a structured 10-slide pitch deck.
Each slide type has a specific purpose in the pitch flow.
"""
from __future__ import annotations

from core.models import NarrativeElements, PitchDeck, Slide, SlideType


# ── 10-Slide Pitch Deck Template ──────────────────────────────────────

SLIDE_FLOW_10 = [
    SlideType.TITLE,
    SlideType.LOGLINE,
    SlideType.GENRE_TONE,
    SlideType.CHARACTERS,
    SlideType.SETTING,
    SlideType.PLOT,
    SlideType.CONFLICT,
    SlideType.KEY_SCENES,
    SlideType.AUDIENCE_COMPS,
    SlideType.CLOSING,
]


def build_deck(narrative: NarrativeElements, slide_count: int = 10) -> PitchDeck:
    """
    Build a complete PitchDeck from NarrativeElements.

    Maps each narrative field to the appropriate slide with
    title, body, bullets, and speaker notes.
    """
    slides = []
    flow = SLIDE_FLOW_10[:slide_count]

    for i, slide_type in enumerate(flow, 1):
        slide = _build_slide(i, slide_type, narrative)
        slides.append(slide)

    return PitchDeck(
        title=narrative.title,
        slides=slides,
        narrative=narrative,
        source_file_count=0,  # Set by pipeline
    )


def _build_slide(num: int, stype: SlideType, n: NarrativeElements) -> Slide:
    """Build a single slide from narrative elements."""

    builders = {
        SlideType.TITLE: lambda: Slide(
            slide_number=num,
            slide_type=stype,
            title=n.title,
            subtitle=n.logline,
            body=f"{n.genre} • {n.tone}",
            speaker_notes=f"Open with the hook: {n.hook}",
        ),
        SlideType.LOGLINE: lambda: Slide(
            slide_number=num,
            slide_type=stype,
            title="The Story",
            subtitle=n.logline,
            body=n.hook,
            speaker_notes=(
                f"This is your elevator pitch moment. Lead with: '{n.hook}' "
                f"Then deliver the logline. Pause. Let it land."
            ),
        ),
        SlideType.GENRE_TONE: lambda: Slide(
            slide_number=num,
            slide_type=stype,
            title="Genre & Tone",
            subtitle=n.genre,
            body=f"Tone: {n.tone}",
            bullets=n.themes[:4],
            speaker_notes=(
                f"Position this as: '{n.genre}' with a tone that's '{n.tone}'. "
                f"The themes we're exploring are {', '.join(n.themes[:3])}. "
                f"Visual style: {n.visual_style}"
            ),
        ),
        SlideType.CHARACTERS: lambda: Slide(
            slide_number=num,
            slide_type=stype,
            title="Characters",
            subtitle=n.protagonist,
            body=n.antagonist,
            bullets=[
                f"{c.name} — {c.description}" for c in n.characters[:5]
            ],
            speaker_notes=(
                f"Lead with the protagonist: {n.protagonist}. "
                f"The antagonist/opposing force: {n.antagonist}. "
                + " ".join(f"{c.name}'s arc: {c.arc}." for c in n.characters[:3])
            ),
        ),
        SlideType.SETTING: lambda: Slide(
            slide_number=num,
            slide_type=stype,
            title="World & Setting",
            subtitle=n.setting,
            body=f"Time period: {n.time_period}" if n.time_period else "",
            speaker_notes=(
                f"Paint the world: {n.setting}. "
                f"Visual style: {n.visual_style}. "
                f"This world should feel lived-in and specific."
            ),
            image_prompt=f"Cinematic establishing shot of {n.setting}, {n.visual_style} style, {n.tone} mood",
        ),
        SlideType.PLOT: lambda: Slide(
            slide_number=num,
            slide_type=stype,
            title="Story Arc",
            body=n.plot_summary,
            bullets=_split_arc(n.plot_arc),
            speaker_notes=(
                f"Walk them through the arc: {n.plot_arc}"
            ),
        ),
        SlideType.CONFLICT: lambda: Slide(
            slide_number=num,
            slide_type=stype,
            title="Central Conflict",
            subtitle=n.conflict,
            speaker_notes=(
                f"This is the engine of the show: {n.conflict}. "
                f"Every episode/chapter returns to this question."
            ),
        ),
        SlideType.KEY_SCENES: lambda: Slide(
            slide_number=num,
            slide_type=stype,
            title="Signature Moments",
            bullets=n.key_scenes[:4],
            speaker_notes=(
                "These are the moments that sell the show. "
                "Describe each one cinematically — what does the audience SEE?"
            ),
        ),
        SlideType.AUDIENCE_COMPS: lambda: Slide(
            slide_number=num,
            slide_type=stype,
            title="Audience & Comparables",
            subtitle=n.target_audience,
            bullets=n.comparable_titles[:4],
            speaker_notes=(
                f"Target audience: {n.target_audience}. "
                f"Position as: {' / '.join(n.comparable_titles[:2])}. "
                f"This fills a gap in the current market because..."
            ),
        ),
        SlideType.CLOSING: lambda: Slide(
            slide_number=num,
            slide_type=stype,
            title=n.title,
            subtitle="Let's make this.",
            body=n.logline,
            speaker_notes=(
                f"Close by restating the logline: '{n.logline}'. "
                f"End with: 'This is {n.title}. Let's make this.'"
            ),
        ),
    }

    builder = builders.get(stype)
    if builder:
        return builder()

    return Slide(slide_number=num, slide_type=stype, title=f"Slide {num}")


def _split_arc(arc_text: str) -> list[str]:
    """Split plot arc text into Setup/Confrontation/Resolution bullets."""
    if not arc_text:
        return []

    # Try to split on common delimiters
    for sep in ["→", "->", "—", " - ", "\n"]:
        if sep in arc_text:
            parts = [p.strip() for p in arc_text.split(sep) if p.strip()]
            labels = ["SETUP:", "CONFRONTATION:", "RESOLUTION:"]
            result = []
            for i, part in enumerate(parts[:3]):
                label = labels[i] if i < len(labels) else ""
                result.append(f"{label} {part}")
            return result

    return [arc_text]
