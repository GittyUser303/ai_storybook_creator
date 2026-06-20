"""
style_prompts.py
Maps user-selected illustration styles to prompt suffix templates.
"""

STYLES = {
    "Watercolor": {
        "label": "🎨 Watercolor",
        "suffix": "watercolor illustration, soft washes of color, paper texture, gentle strokes, children's book art style, warm and dreamy",
        "negative": "photorealistic, dark, gritty, 3D render, photography",
    },
    "Anime": {
        "label": "✨ Anime",
        "suffix": "anime art style, vibrant colors, detailed linework, Studio Ghibli inspired, expressive characters, beautiful background",
        "negative": "photorealistic, western cartoon, ugly, deformed",
    },
    "Disney": {
        "label": "🏰 Disney",
        "suffix": "Disney animation style, colorful, expressive, polished, cinematic lighting, magical atmosphere, family-friendly",
        "negative": "dark, horror, photorealistic, anime",
    },
    "Comic": {
        "label": "💥 Comic",
        "suffix": "comic book illustration, bold outlines, halftone shading, dynamic composition, vibrant flat colors, graphic novel style",
        "negative": "photorealistic, painterly, blurry",
    },
    "Ghibli": {
        "label": "🌿 Ghibli-inspired",
        "suffix": "Studio Ghibli inspired art, lush detailed backgrounds, painterly, magical realism, soft lighting, whimsical atmosphere, hand-drawn feel",
        "negative": "photorealistic, 3D render, dark, scary",
    },
    "Pixar": {
        "label": "🎬 Pixar",
        "suffix": "Pixar 3D animation style, expressive characters, warm cinematic lighting, detailed environments, heartwarming, high quality render",
        "negative": "2D, flat, dark, sketch, rough",
    },
}


def build_image_prompt(
    scene_description: str,
    style_key: str,
    character_context: str = "",
) -> tuple[str, str]:
    """
    Build the final prompt and negative prompt to send to the image generation API.

    Args:
        scene_description: The scene to illustrate.
        style_key: Key from STYLES dict.
        character_context: Optional character consistency string.

    Returns:
        Tuple of (positive_prompt, negative_prompt).
    """
    style = STYLES.get(style_key, STYLES["Watercolor"])
    parts = []
    if character_context:
        parts.append(character_context)
    parts.append(scene_description)
    parts.append(style["suffix"])
    positive = ", ".join(parts)
    negative = style.get("negative", "")
    return positive, negative


def get_style_labels() -> dict:
    """Return {key: label} mapping for UI display."""
    return {k: v["label"] for k, v in STYLES.items()}