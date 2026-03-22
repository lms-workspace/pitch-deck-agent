# Pitch Deck Generator Agent

Multi-modal AI agent that ingests mixed creative assets (PDFs, scripts, emails, images, video clips) and generates structured, narrative-driven pitch decks.

## Architecture

```
pitch-deck-agent/
├── app.py                      # Gradio frontend (entry point)
├── config.py                   # API keys, model config, constants
├── requirements.txt            # Dependencies
├── Dockerfile                  # HF Spaces deployment
├── README.md
│
├── core/
│   ├── __init__.py
│   ├── pipeline.py             # Main orchestration pipeline
│   └── models.py               # Pydantic data models (PitchDeck, Slide, NarrativeElements)
│
├── modules/
│   ├── __init__.py
│   ├── ingest.py               # Document ingestion (PDF, image, text, email, video)
│   ├── synthesize.py           # Story synthesis (Gemini/Claude) → narrative elements
│   ├── deck_builder.py         # Slide layout logic + content mapping
│   ├── google_slides.py        # Google Slides API output
│   ├── pptx_output.py          # PowerPoint output (Phase 2)
│   └── canva_output.py         # Canva output (Phase 3)
│
├── prompts/
│   ├── __init__.py
│   ├── story_synthesis.py      # Narrative extraction prompts
│   ├── slide_content.py        # Per-slide content generation prompts
│   └── refinement.py           # Polish/tone prompts
│
├── templates/
│   ├── deck_10_slide.json      # 10-slide pitch deck template
│   └── deck_6_slide.json       # 6-slide sizzle template
│
├── utils/
│   ├── __init__.py
│   ├── file_handlers.py        # File type detection, temp storage
│   ├── video_utils.py          # ffmpeg frame extraction, Whisper transcription
│   └── image_utils.py          # Image preprocessing for Gemini
│
├── tests/
│   ├── test_ingest.py
│   ├── test_synthesize.py
│   └── test_pipeline.py
│
└── assets/
    └── sample_inputs/          # Test files
```

## Phase 1 Scope
- Upload: PDF, .txt, .eml, images (.png/.jpg)
- Processing: Gemini 2.0 Flash for multi-modal parsing
- Synthesis: Extract characters, plot arc, themes, tone, setting, conflict, hook
- Output: Google Slides API (10-slide narrative deck)
- Frontend: Gradio on Hugging Face Spaces

## Phase 2 Additions
- Video clip ingestion (ffmpeg + Whisper)
- PowerPoint output (python-pptx)
- Claude API for enhanced story synthesis

## Phase 3 Additions
- Canva output
- Iterative editing via chat
- Style/brand kit integration
