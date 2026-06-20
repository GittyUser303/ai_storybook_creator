"""
story_engine.py
Handles story generation via Gemini LLM.
"""

import json
import google.generativeai as genai
from typing import Optional

# ── Single source of truth for the Gemini model name ────────────────────────
# Update ONLY this constant when Google retires a model — every caller in
# the project (story generation, branch generation in app.py) imports it
# from here instead of hardcoding the string separately.
#
# Verified against this project's API key on 2026-06-20 via test_models.py.
# gemini-2.5-flash is confirmed available; stable and well-documented as of
# this date. Google's deprecation cadence has been fast recently (2.0 Flash
# retired June 1 2026), so if generation starts failing with a 404 again,
# rerun test_models.py and update this one line.
GEMINI_MODEL = "gemini-2.5-flash"


def configure_gemini(api_key: str):
    genai.configure(api_key=api_key)


def generate_story(
    prompt: str,
    reading_age: str,
    style: str,
    num_chapters: int,
    world_memory: dict,
    model_name: str = GEMINI_MODEL,
) -> dict:
    """
    Generate a structured story from a user prompt.

    Returns a dict:
    {
        "title": str,
        "tagline": str,
        "characters": [{"name": str, "description": str, "role": str}],
        "chapters": [{"title": str, "text": str, "scene_prompt": str}],
        "locations": [str],
        "world_notes": str
    }
    """
    age_instruction = {
        "Ages 4–6": "Use very simple words, short sentences (max 3 per paragraph). Sentences should feel like read-aloud picture books.",
        "Ages 7–10": "Use clear, engaging language. Sentences can be a bit longer. Use vivid descriptive words kids will enjoy.",
        "Ages 11–14": "Write with richer vocabulary and more complex plot beats. Slightly longer chapters are fine.",
        "Teen": "Write with nuanced language, deeper emotions, and more sophisticated narrative beats.",
    }.get(reading_age, "Use clear, engaging language suitable for children.")

    # Include world memory context if continuing a story
    memory_context = ""
    if world_memory.get("characters") or world_memory.get("events"):
        chars = world_memory.get("characters", [])
        events = world_memory.get("events", [])
        char_str = "; ".join([f"{c['name']} ({c['description']})" for c in chars]) if chars else "none"
        event_str = "; ".join(events[-3:]) if events else "none"
        memory_context = f"\n\nWORLD MEMORY (maintain continuity):\nCharacters: {char_str}\nRecent events: {event_str}"

    system_prompt = f"""You are a master children's storyteller and illustrator's writer.
{age_instruction}
Generate a complete illustrated storybook from the user's prompt.
Maintain character consistency — every chapter should reference the same character descriptions.
{memory_context}

RESPOND ONLY IN VALID JSON. No markdown, no preamble, no explanation.
Schema:
{{
  "title": "string",
  "tagline": "string (movie-poster style, 1 sentence)",
  "characters": [
    {{"name": "string", "description": "string (physical appearance, 1 sentence)", "role": "string"}}
  ],
  "chapters": [
    {{
      "title": "string",
      "text": "string (the story chapter, 2–4 paragraphs)",
      "scene_prompt": "string (vivid image generation prompt for this scene, 1–2 sentences, third person, describe what to illustrate)"
    }}
  ],
  "locations": ["string"],
  "world_notes": "string (1 sentence summary of key world facts)"
}}

Generate exactly {num_chapters} chapters.
Make scene_prompts highly visual and specific — they will be sent to an image generator."""

    model = genai.GenerativeModel(model_name)
    response = model.generate_content(
        [{"role": "user", "parts": [f"{system_prompt}\n\nUser prompt: {prompt}"]}]
    )

    raw = response.text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    story_data = json.loads(raw)
    return story_data


def build_character_context(characters: list) -> str:
    """Build a character consistency string for image prompts."""
    if not characters:
        return ""
    descriptions = [f"{c['name']}: {c['description']}" for c in characters[:3]]
    return "featuring " + "; ".join(descriptions)