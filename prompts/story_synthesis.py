"""
Story Synthesis Prompts

These prompts drive the core intelligence of the agent — extracting
narrative structure from raw ingested content and turning it into
structured elements that map directly to pitch deck slides.
"""

STORY_SYNTHESIS_SYSTEM = """You are an elite creative development executive at a major entertainment studio. 
You specialize in analyzing raw creative materials — scripts, treatments, notes, emails, 
concept art descriptions — and distilling them into clear, compelling narrative structures.

You think like a showrunner who needs to pitch this project to a network president in 10 minutes.
You identify what makes a story unique, who the audience is, and why it matters NOW."""


STORY_SYNTHESIS_PROMPT = """Analyze the following creative materials and extract a complete narrative structure.
These materials come from multiple sources (scripts, PDFs, emails, notes, images) related to a single project.

## SOURCE MATERIALS
{combined_text}

## YOUR TASK
Extract the following narrative elements. Be specific and vivid — this will power a pitch deck.
If information is unclear or missing, make your best creative inference based on available context
and mark it as [INFERRED].

Respond in EXACTLY this JSON format (no markdown code fences, just raw JSON):

{{
    "title": "Project title (use the most prominent title from materials, or create one)",
    "logline": "One sentence that captures the entire story. Format: [Character] must [goal] before [stakes]. Think TV Guide listing meets movie poster tagline.",
    "genre": "Primary genre + subgenre (e.g., 'Sci-fi thriller', 'Dark comedy drama')",
    "tone": "2-3 words describing the feeling (e.g., 'Tense, atmospheric, darkly funny')",
    "themes": ["Theme 1", "Theme 2", "Theme 3"],
    "setting": "Where and what world this takes place in — be vivid",
    "time_period": "When this takes place",
    "characters": [
        {{
            "name": "Character name",
            "role": "protagonist/antagonist/supporting",
            "description": "Who they are in 1-2 sentences",
            "arc": "How they change over the story"
        }}
    ],
    "protagonist": "Name and one-line description",
    "antagonist": "Name/force and one-line description",
    "conflict": "The central dramatic question or conflict driving the story",
    "plot_summary": "3-5 sentence summary of the full story",
    "plot_arc": "Break the story into: SETUP (world + characters introduced) → CONFRONTATION (escalating conflict) → RESOLUTION (climax + aftermath). 2-3 sentences each.",
    "hook": "The 'why now' — what makes this story urgent, timely, or irresistible. This is your opening line in the pitch meeting.",
    "target_audience": "Who watches/reads this and why",
    "comparable_titles": ["Comp 1 meets Comp 2", "Similar to X"],
    "visual_style": "What this looks/feels like visually (cinematography, art direction, color palette)",
    "key_scenes": ["Scene 1 description", "Scene 2 description", "Scene 3 description"]
}}

IMPORTANT:
- Every field must have a value — even if you have to infer
- The logline must be ONE sentence, punchy and specific
- Comparable titles should be real, well-known properties
- Key scenes should be the most visually/emotionally compelling moments
- Write as if you're pitching to Netflix, HBO, or A24
"""


SLIDE_CONTENT_PROMPT = """You are writing pitch deck slide content for a {genre} project called "{title}".
The tone is {tone}. The target audience is {target_audience}.

Write the content for a {slide_type} slide with these guidelines:
- Title: Short, punchy (3-6 words max)
- Subtitle: One compelling sentence
- Body: 2-4 sentences of supporting detail
- Speaker notes: What the presenter should SAY (conversational, persuasive)

Slide context:
{slide_context}

Respond in JSON:
{{
    "title": "...",
    "subtitle": "...",
    "body": "...",
    "bullets": ["point 1", "point 2", "point 3"],
    "speaker_notes": "..."
}}"""


REFINEMENT_PROMPT = """Review and polish this pitch deck content for a studio presentation.
Ensure:
1. Consistent tone throughout
2. No redundancy between slides
3. Building energy/momentum from slide 1 → 10
4. The hook hits in the first 30 seconds
5. The closing slide leaves them wanting more

Current deck:
{deck_json}

Return the refined deck in the same JSON format with improvements applied."""
