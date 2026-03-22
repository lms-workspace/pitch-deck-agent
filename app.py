"""
Pitch Deck Generator — Gradio Frontend

Upload creative assets → get a structured pitch deck.
Deployable on Hugging Face Spaces.
"""
import gradio as gr
from pathlib import Path

from core.pipeline import run_pipeline
from config import GEMINI_API_KEY, CLAUDE_API_KEY, GOOGLE_CREDENTIALS_JSON


# ── Pipeline Wrapper for Gradio ───────────────────────────────────────

def generate_deck(
    files,
    output_format: str,
    slide_count: int,
    synthesis_provider: str,
    share_email: str,
    progress=gr.Progress(),
):
    """Main Gradio handler — runs the full pipeline."""
    if not files:
        return (
            "❌ No files uploaded. Please upload at least one file.",
            None,
            "",
        )

    # Validate API keys
    if synthesis_provider == "gemini" and not GEMINI_API_KEY:
        return "❌ GEMINI_API_KEY not set. Add it in HF Space secrets.", None, ""
    if synthesis_provider == "claude" and not CLAUDE_API_KEY:
        return "❌ CLAUDE_API_KEY not set. Add it in HF Space secrets.", None, ""

    progress(0.1, desc="Ingesting files...")
    result = run_pipeline(
        uploaded_files=files,
        output_format=output_format.lower().replace(" ", "_"),
        slide_count=int(slide_count),
        synthesis_provider=synthesis_provider.lower(),
        share_email=share_email.strip(),
    )

    # Build status output
    status = result.summary

    # Narrative details
    narrative_md = ""
    if result.narrative:
        n = result.narrative
        narrative_md = f"""## {n.title}

**Logline:** {n.logline}

**Genre:** {n.genre} | **Tone:** {n.tone}

**Themes:** {', '.join(n.themes)}

**Setting:** {n.setting}

**Protagonist:** {n.protagonist}
**Antagonist:** {n.antagonist}

**Conflict:** {n.conflict}

**Plot Arc:**
{n.plot_arc}

**Hook:** {n.hook}

**Target Audience:** {n.target_audience}

**Comparable Titles:** {', '.join(n.comparable_titles)}

**Visual Style:** {n.visual_style}

### Characters
"""
        for c in n.characters:
            narrative_md += f"- **{c.name}** ({c.role}): {c.description}\n"

        narrative_md += "\n### Key Scenes\n"
        for i, scene in enumerate(n.key_scenes, 1):
            narrative_md += f"{i}. {scene}\n"

    # File output
    output_file = result.output_file if result.output_file else None

    # URL output
    url_display = ""
    if result.output_url:
        url_display = f"🔗 [Open in Google Slides]({result.output_url})"

    return status, output_file, narrative_md, url_display


# ── Gradio UI ─────────────────────────────────────────────────────────

def create_app():
    with gr.Blocks(
        title="Pitch Deck Generator",
        theme=gr.themes.Base(
            primary_hue="blue",
            neutral_hue="slate",
            font=["Inter", "system-ui", "sans-serif"],
        ),
        css="""
        .main-header { text-align: center; margin-bottom: 1rem; }
        .status-box { font-family: monospace; font-size: 0.85rem; }
        """,
    ) as app:

        gr.Markdown(
            """
            # 🎬 Pitch Deck Generator
            Upload your creative materials — scripts, PDFs, emails, images, notes — and get a
            structured pitch deck with narrative analysis, character breakdowns, and story arc.

            **Supported files:** PDF, TXT, MD, EML, PNG, JPG, WEBP
            """,
            elem_classes="main-header",
        )

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📁 Upload Files")
                file_upload = gr.File(
                    label="Drop your creative assets here",
                    file_count="multiple",
                    file_types=[
                        ".pdf", ".txt", ".md", ".rtf",
                        ".eml", ".msg",
                        ".png", ".jpg", ".jpeg", ".webp",
                    ],
                )

                gr.Markdown("### ⚙️ Settings")
                output_format = gr.Radio(
                    choices=["PPTX", "Google Slides"],
                    value="PPTX",
                    label="Output Format",
                )
                slide_count = gr.Slider(
                    minimum=6, maximum=15, value=10, step=1,
                    label="Number of Slides",
                )
                synthesis_provider = gr.Radio(
                    choices=["Gemini", "Claude"],
                    value="Gemini",
                    label="AI Model for Synthesis",
                )
                share_email = gr.Textbox(
                    label="Share with email (Google Slides only)",
                    placeholder="name@studio.com",
                )

                generate_btn = gr.Button(
                    "🚀 Generate Pitch Deck",
                    variant="primary",
                    size="lg",
                )

            with gr.Column(scale=2):
                gr.Markdown("### 📊 Results")

                status_output = gr.Textbox(
                    label="Pipeline Status",
                    lines=8,
                    interactive=False,
                    elem_classes="status-box",
                )

                slides_url = gr.Markdown(label="Google Slides Link")

                file_output = gr.File(
                    label="Download PowerPoint",
                    interactive=False,
                )

                with gr.Accordion("📖 Narrative Analysis", open=False):
                    narrative_output = gr.Markdown()

        # Wire up
        generate_btn.click(
            fn=generate_deck,
            inputs=[file_upload, output_format, slide_count, synthesis_provider, share_email],
            outputs=[status_output, file_output, narrative_output, slides_url],
        )

        gr.Markdown(
            """
            ---
            **How it works:** Files are parsed → AI extracts narrative elements
            (characters, plot, themes, tone) → structured into a professional pitch deck.

            Built with Gemini 2.0 Flash, Claude, and Gradio.
            """
        )

    return app


# ── Entry Point ───────────────────────────────────────────────────────

if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )
