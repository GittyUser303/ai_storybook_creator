"""
image_api.py
Handles image generation via Pollinations.ai (free, no API key required)
or optionally via a paid API like Stability AI.
"""

import requests
from urllib.parse import quote
from PIL import Image
from io import BytesIO
import time
import os


def generate_image_pollinations(
    prompt: str,
    width: int = 768,
    height: int = 512,
    seed: int = None,
    negative_prompt: str = "",
) -> Image.Image:
    """
    Generate image using Pollinations.ai (free, no API key needed).

    Args:
        prompt: The image generation prompt
        width: Image width
        height: Image height
        seed: Optional seed for reproducibility
        negative_prompt: Things to avoid in the image

    Returns:
        PIL Image object
    """
    encoded_prompt = quote(prompt)
    seed_param = f"&seed={seed}" if seed else ""
    negative_param = f"&negative={quote(negative_prompt)}" if negative_prompt else ""

    url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width={width}&height={height}&nologo=true{seed_param}{negative_param}"
    )

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            return img
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            raise RuntimeError(f"Image generation failed after {max_retries} attempts: {e}")


def generate_image(
    prompt: str,
    width: int = 768,
    height: int = 512,
    seed: int = None,
    negative_prompt: str = "",
) -> Image.Image:
    """
    Main image generation function. Uses Pollinations by default.
    Can be extended to use other APIs.

    Returns PIL Image.
    """
    api_provider = os.getenv("IMAGE_API_PROVIDER", "pollinations").lower()

    if api_provider == "stability":
        return _generate_stability(prompt, width, height)
    else:
        return generate_image_pollinations(prompt, width, height, seed, negative_prompt)


def _generate_stability(prompt: str, width: int = 768, height: int = 512) -> Image.Image:
    """
    Optional: Generate image using Stability AI API.
    Requires STABILITY_API_KEY environment variable.
    """
    api_key = os.getenv("STABILITY_API_KEY")
    if not api_key:
        raise ValueError("STABILITY_API_KEY not set. Using Pollinations instead.")

    url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"

    response = requests.post(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "text_prompts": [{"text": prompt, "weight": 1}],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
        },
    )

    if response.status_code != 200:
        raise ValueError(f"Stability API error: {response.text}")

    import base64

    data = response.json()
    img_data = base64.b64decode(data["artifacts"][0]["base64"])
    return Image.open(BytesIO(img_data))


def pil_to_bytes(img: Image.Image, format: str = "PNG") -> bytes:
    """Convert PIL Image to bytes for download."""
    buf = BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()
