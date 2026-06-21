# 📖 AI Storybook Creator

Turn a one-line idea into a fully illustrated, downloadable storybook — powered by Google Gemini and Pollinations.ai.

## What It Does

You type a story prompt (e.g. *"A girl discovers a tiny dragon living in her schoolbag"*), choose an illustration style and reading age, and the app:

1. Uses **Gemini LLM** to write a structured multi-chapter story with characters, scene descriptions, and locations
2. Generates **AI illustrations** for the cover and every chapter via Pollinations.ai (free, no API key required), using a shared seed and scene-aware character descriptions to keep characters looking as consistent as possible across chapters
3. Compiles everything into a **downloadable PDF storybook** with a cover page, character cards, table of contents, and chapter illustrations

---

## How to Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/your-username/ai-storybook-creator.git
cd ai-storybook-creator
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add your API key (see section below)

### 4. Run the app

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## How to Add Your API Key

This app uses the **Google Gemini API** for story generation. Image generation uses Pollinations.ai, which is completely free and requires no key.

### Option A — `.env` file (local development)

Create a file named `.env` in the project root:

```
GEMINI_API_KEY=your_key_here
```

Get a free Gemini API key at: https://aistudio.google.com/app/apikey

### Option B — Enter in the app

If no key is found in the environment, the sidebar will show a password input where you can paste your key at runtime.

### Option C — Streamlit Secrets (deployed apps)

Add to your Streamlit Cloud secrets:

```toml
GEMINI_API_KEY = "your_key_here"
```

> ⚠️ Never commit your `.env` file to version control. It is already listed in `.gitignore`.

---

## File Structure

```
ai-storybook-creator/
├── app.py                  # Main Streamlit app (UI + generation flow)
├── utils/
│   ├── __init__.py
│   ├── story_engine.py     # Gemini story generation logic
│   ├── image_api.py        # Image generation via Pollinations.ai
│   ├── style_prompts.py    # Style definitions and prompt builder
│   ├── pdf_export.py       # PDF storybook compiler (ReportLab)
│   └── world_memory.py     # Story world state and analytics
├── requirements.txt
├── .env                    # Local secrets (do not commit)
└── README.md
```

---
## Deployed on Streamlit Cloud (recommended, free)
https://aistorybookcreator-bxakwbznp82undcekup5ua.streamlit.app/

---

## Known Limitations

**Image reliability.** Image generation relies on **Pollinations.ai**, a free public API with no rate-limit guarantees. During high traffic periods, individual image requests may time out or return errors. The app handles this gracefully (failed images are skipped rather than crashing), but a story with 5 chapters may occasionally generate with 1–2 missing illustrations. Using the **Small** image size option in the sidebar reduces timeout likelihood significantly.

**Character consistency.** Every image is generated independently from a text prompt — Pollinations is a pure text-to-image API with no reference-image conditioning in this app. To keep characters as visually consistent as possible across the cover and every chapter, the app reuses one random seed for the whole story (so palette, lighting, and rendering style stay aligned) and only includes the description of characters actually present in each scene, rather than listing every character on every page. This noticeably improves consistency but can't guarantee an identical face in every illustration — true character locking would require an image-reference/img2img pipeline, which is a possible future upgrade.
