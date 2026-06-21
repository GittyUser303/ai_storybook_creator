import os
import streamlit as st
import random
from dotenv import load_dotenv
from utils.story_engine import generate_story, GEMINI_MODEL, build_character_context
from utils.image_api import generate_image, pil_to_bytes
from utils.style_prompts import build_image_prompt, STYLES
from utils.pdf_export import export_pdf
from utils.world_memory import empty_memory, update_memory
import google.generativeai as genai

load_dotenv()

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Storybook Creator",
    page_icon="📖",
    layout="wide",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,ital,wght@9..144,0,400;9..144,0,600;9..144,0,700;9..144,1,400&family=Nunito:wght@400;600;700;800&family=Lora:ital,wght@0,400;1,400&display=swap');

  :root {
    --forest:     #2d4a35;
    --forest-dk:  #1e3325;
    --forest-lt:  #3d6147;
    --cream:      #fdf6e8;
    --parchment:  #f5e8c8;
    --parch-dk:   #e0cc9a;
    --ink:        #1e1a12;
    --ink-soft:   #4a4030;
    --amber:      #d4870a;
    --amber-lt:   #f0a820;
    --coral:      #c94a28;
    --sage:       #5a8a6a;
    --gold-line:  #c8a040;
  }

  * { box-sizing: border-box; }

  /* ── Background: warm forest green desk ── */
  .stApp {
    background: var(--forest) !important;
    background-image:
      radial-gradient(circle at 15% 85%, rgba(212,135,10,0.08) 0%, transparent 50%),
      radial-gradient(circle at 85% 10%, rgba(90,138,106,0.12) 0%, transparent 50%),
      linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px) !important;
    background-size: auto, auto, 24px 24px, 24px 24px !important;
    background-attachment: fixed !important;
  }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: var(--forest-dk) !important;
    border-right: 2px solid #162a1d !important;
  }
  [data-testid="stSidebar"] .stMarkdown h1,
  [data-testid="stSidebar"] .stMarkdown h2,
  [data-testid="stSidebar"] .stMarkdown h3,
  [data-testid="stSidebar"] .stMarkdown h4 {
    font-family: 'Fraunces', serif !important;
    color: var(--amber-lt) !important;
    font-weight: 600 !important;
  }
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] .stMarkdown p,
  [data-testid="stSidebar"] .stMarkdown li,
  [data-testid="stSidebar"] .stCaption {
    font-family: 'Nunito', sans-serif !important;
    color: #a8c4b0 !important;
  }
  [data-testid="stSidebar"] .stRadio label {
    color: #c0d8c8 !important;
    font-family: 'Nunito', sans-serif !important;
    font-size: 0.92rem !important;
  }
  [data-testid="stSidebar"] .stSelectbox > div > div {
    background: #162a1d !important;
    border-color: #3a5a42 !important;
    color: var(--cream) !important;
    font-family: 'Nunito', sans-serif !important;
  }
  [data-testid="stSidebar"] .stSuccess > div {
    background: rgba(90,138,106,0.2) !important;
    border: 1px solid var(--sage) !important;
    color: #a8d8b8 !important;
    font-family: 'Nunito', sans-serif !important;
    font-size: 0.82rem !important;
    border-radius: 8px !important;
  }

  /* ── ALL buttons base reset ── */
  div[data-testid="stButton"] > button {
    font-family: 'Nunito', sans-serif !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    transition: all 0.2s !important;
    border: 2px solid transparent !important;
  }

  /* Primary — generate */
  .stButton > button[kind="primary"] {
    background: var(--coral) !important;
    border: 2px solid #8a2e14 !important;
    color: #fff5ee !important;
    font-size: 1rem !important;
    padding: 0.6rem 1.8rem !important;
    letter-spacing: 0.02em !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 0 #8a2e14 !important;
  }
  .stButton > button[kind="primary"]:hover {
    background: #b03e20 !important;
    transform: translateY(2px) !important;
    box-shadow: 0 2px 0 #8a2e14 !important;
  }
  .stButton > button[kind="primary"]:active {
    transform: translateY(4px) !important;
    box-shadow: none !important;
  }

  /* Chip / sample buttons */
  .chip-btn > button {
    background: var(--parchment) !important;
    border: 2px solid var(--parch-dk) !important;
    color: var(--ink) !important;
    font-family: 'Lora', serif !important;
    font-style: italic !important;
    font-size: 0.88rem !important;
    font-weight: 400 !important;
    border-radius: 30px !important;
    padding: 0.4rem 1rem !important;
    text-align: center !important;
  }
  .chip-btn > button:hover {
    background: var(--amber-lt) !important;
    border-color: var(--amber) !important;
    color: var(--ink) !important;
    transform: translateY(-1px) !important;
  }

  /* Random button */
  .random-btn > button {
    background: var(--amber) !important;
    border: 2px solid #8a5500 !important;
    color: var(--ink) !important;
    border-radius: 10px !important;
    font-size: 0.9rem !important;
    box-shadow: 0 3px 0 #8a5500 !important;
  }
  .random-btn > button:hover {
    background: var(--amber-lt) !important;
    transform: translateY(1px) !important;
    box-shadow: 0 2px 0 #8a5500 !important;
  }

  /* Branch choose buttons */
  .branch-btn > button {
    background: var(--forest) !important;
    border: 2px solid var(--sage) !important;
    color: #c0e0c8 !important;
    border-radius: 10px !important;
    font-size: 0.86rem !important;
    width: 100% !important;
    margin-top: 8px !important;
  }
  .branch-btn > button:hover {
    background: var(--forest-lt) !important;
    border-color: var(--amber-lt) !important;
    color: var(--amber-lt) !important;
  }

  /* Download buttons */
  .dl-btn > button {
    background: rgba(253,246,232,0.12) !important;
    border: 1.5px solid rgba(253,246,232,0.3) !important;
    color: var(--cream) !important;
    border-radius: 8px !important;
    font-size: 0.84rem !important;
    font-family: 'Nunito', sans-serif !important;
    width: 100% !important;
  }
  .dl-btn > button:hover {
    background: rgba(253,246,232,0.2) !important;
    border-color: var(--amber-lt) !important;
    color: var(--amber-lt) !important;
  }

  /* Continue button */
  .continue-btn > button {
    background: var(--forest-lt) !important;
    border: 2px solid var(--sage) !important;
    color: var(--cream) !important;
    border-radius: 10px !important;
  }
  .continue-btn > button:hover {
    background: var(--sage) !important;
    border-color: var(--amber) !important;
    color: var(--amber-lt) !important;
  }

  /* ── Textarea ── */
  .stTextArea textarea {
    font-family: 'Lora', serif !important;
    font-size: 1rem !important;
    color: var(--ink) !important;
    background: var(--cream) !important;
    border: 2px solid var(--parch-dk) !important;
    border-radius: 12px !important;
    padding: 1rem 1.1rem !important;
    line-height: 1.65 !important;
  }
  .stTextArea textarea:focus {
    border-color: var(--sage) !important;
    box-shadow: 0 0 0 3px rgba(90,138,106,0.2) !important;
  }
  .stTextArea textarea::placeholder {
    color: #a89870 !important;
    font-style: italic !important;
  }

  /* Text input (continuation) */
  .stTextInput input {
    font-family: 'Lora', serif !important;
    font-style: italic !important;
    color: var(--ink) !important;
    background: var(--cream) !important;
    border: 2px solid var(--parch-dk) !important;
    border-radius: 10px !important;
    padding: 0.6rem 1rem !important;
  }
  .stTextInput input:focus {
    border-color: var(--sage) !important;
    box-shadow: 0 0 0 2px rgba(90,138,106,0.2) !important;
  }

  /* ── MASTHEAD ── */
  .masthead {
    text-align: center;
    padding: 2.2rem 1rem 1.6rem;
  }
  .masthead-eyebrow {
    font-family: 'Nunito', sans-serif;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--amber-lt);
    display: block;
    margin-bottom: 10px;
  }
  .masthead-title {
    font-family: 'Fraunces', serif;
    font-size: clamp(2.4rem, 5vw, 3.8rem);
    font-weight: 700;
    color: var(--cream);
    letter-spacing: -0.02em;
    line-height: 1.1;
    margin: 0;
    text-shadow: 0 2px 12px rgba(0,0,0,0.3);
  }
  .masthead-title em {
    font-style: italic;
    font-weight: 400;
    color: var(--amber-lt);
  }
  .masthead-sub {
    font-family: 'Lora', serif;
    font-style: italic;
    color: #a8c4a8;
    font-size: 1.05rem;
    margin: 0.5rem 0 0;
    display: block;
  }
  .masthead-stars {
    font-size: 1.2rem;
    letter-spacing: 0.5em;
    margin: 0.8rem 0 0;
    display: block;
    color: var(--amber);
    opacity: 0.7;
  }

  /* ── Input section label ── */
  .input-label {
    font-family: 'Fraunces', serif;
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--cream);
    display: block;
    margin-bottom: 8px;
  }
  .chips-label {
    font-family: 'Nunito', sans-serif;
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--amber);
    display: block;
    margin: 1rem 0 8px;
  }

  /* ── Paper pages (story output) ── */
  .paper-page {
    background: var(--cream);
    border-radius: 14px;
    padding: 2rem 2.25rem;
    margin-bottom: 4px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 8px 24px rgba(0,0,0,0.25), inset 0 0 0 1px rgba(200,160,64,0.15);
  }
  /* Ruled lines effect */
  .paper-page::after {
    content: '';
    position: absolute;
    left: 0; right: 0; top: 0; bottom: 0;
    background: repeating-linear-gradient(
      180deg,
      transparent 0px,
      transparent 27px,
      rgba(200,180,140,0.18) 27px,
      rgba(200,180,140,0.18) 28px
    );
    pointer-events: none;
    border-radius: 14px;
  }
  .paper-page-inner { position: relative; z-index: 1; }

  /* Left margin on paper */
  .paper-margin {
    display: flex;
    gap: 0;
  }
  .paper-margin-line {
    width: 2px;
    background: rgba(201,74,40,0.3);
    border-radius: 2px;
    flex-shrink: 0;
    margin-right: 20px;
    margin-top: 4px;
  }

  /* ── Book title inside paper ── */
  .book-badge {
    font-family: 'Nunito', sans-serif;
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--coral);
    border: 2px solid var(--coral);
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    margin-bottom: 12px;
  }
  .book-title {
    font-family: 'Fraunces', serif;
    font-size: clamp(1.6rem, 3vw, 2.4rem);
    font-weight: 700;
    color: var(--ink);
    line-height: 1.15;
    letter-spacing: -0.02em;
    margin: 0 0 10px;
  }
  .book-tagline {
    font-family: 'Lora', serif;
    font-style: italic;
    font-size: 1rem;
    color: var(--ink-soft);
    line-height: 1.65;
    margin: 0 0 22px;
    border-left: 3px solid var(--sage);
    padding-left: 12px;
    max-width: 46ch;
  }

  /* ── Stats ── */
  .stat-row {
    display: flex;
    border-top: 1px solid var(--parch-dk);
    padding-top: 14px;
    gap: 0;
    margin-top: 4px;
  }
  .stat-item {
    flex: 1;
    text-align: center;
    border-right: 1px solid var(--parch-dk);
    padding: 4px 0;
  }
  .stat-item:last-child { border-right: none; }
  .stat-n {
    font-family: 'Fraunces', serif;
    font-size: 1.7rem;
    font-weight: 700;
    color: var(--coral);
    display: block;
    line-height: 1;
  }
  .stat-l {
    font-family: 'Nunito', sans-serif;
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--ink-soft);
    display: block;
    margin-top: 3px;
  }

  /* ── Cover image ── */
  .cover-wrap {
    border-radius: 12px;
    overflow: hidden;
    border: 3px solid var(--parch-dk);
    box-shadow: 6px 6px 0 rgba(0,0,0,0.35);
  }
  .cover-wrap img { width: 100%; display: block; }

  /* ── Character cards ── */
  .char-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 14px;
    padding-bottom: 14px;
    border-bottom: 1px dashed var(--parch-dk);
  }
  .char-item:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
  .char-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: var(--sage);
    border: 2px solid var(--parch-dk);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-family: 'Fraunces', serif;
    font-size: 1rem;
    font-weight: 700;
    color: var(--cream);
  }
  .char-name {
    font-family: 'Fraunces', serif;
    font-size: 1rem;
    font-weight: 600;
    color: var(--ink);
    margin: 0 0 2px;
  }
  .char-role {
    font-family: 'Nunito', sans-serif;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--coral);
    display: block;
    margin-bottom: 4px;
  }
  .char-desc {
    font-family: 'Lora', serif;
    font-size: 0.88rem;
    color: var(--ink-soft);
    line-height: 1.55;
    margin: 0;
  }

  /* ── Section divider ── */
  .section-div {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 2rem 0 1.5rem;
    color: var(--amber);
  }
  .section-div::before, .section-div::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(212,135,10,0.35);
  }
  .section-div-text {
    font-family: 'Fraunces', serif;
    font-size: 1rem;
    font-style: italic;
    font-weight: 400;
    color: var(--amber-lt);
    white-space: nowrap;
  }

  /* ── Timeline ── */
  .tl-label {
    font-family: 'Fraunces', serif;
    font-size: 1.15rem;
    font-style: italic;
    color: var(--cream);
    display: block;
    margin-bottom: 14px;
  }
  .tl-img-wrap {
    border-radius: 10px;
    overflow: hidden;
    border: 2px solid rgba(253,246,232,0.15);
    box-shadow: 4px 4px 0 rgba(0,0,0,0.3);
  }
  .tl-ch-num {
    font-family: 'Fraunces', serif;
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--amber-lt);
    text-align: center;
    display: block;
    margin-top: 8px;
  }
  .tl-ch-title {
    font-family: 'Lora', serif;
    font-style: italic;
    font-size: 0.8rem;
    color: #a0b8a0;
    text-align: center;
    display: block;
    margin-top: 2px;
  }

  /* ── Chapter cards ── */
  .chapter-card {
    background: var(--cream);
    border-radius: 14px;
    padding: 1.75rem 2rem 1.75rem;
    margin-bottom: 4px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 6px 20px rgba(0,0,0,0.22), inset 0 0 0 1px rgba(200,160,64,0.12);
  }
  .chapter-card::after {
    content: '';
    position: absolute;
    left: 0; right: 0; top: 0; bottom: 0;
    background: repeating-linear-gradient(
      180deg, transparent 0px, transparent 27px,
      rgba(200,180,140,0.15) 27px, rgba(200,180,140,0.15) 28px
    );
    pointer-events: none;
    border-radius: 14px;
  }
  .chapter-card-inner { position: relative; z-index: 1; }
  .chapter-num {
    font-family: 'Nunito', sans-serif;
    font-size: 0.65rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--amber);
    display: block;
    margin-bottom: 4px;
  }
  .chapter-title {
    font-family: 'Fraunces', serif;
    font-size: 1.4rem;
    font-weight: 600;
    color: var(--ink);
    margin: 0 0 14px;
    line-height: 1.2;
    letter-spacing: -0.01em;
  }
  .chapter-text {
    font-family: 'Lora', serif;
    font-size: 1rem;
    color: var(--ink-soft);
    line-height: 1.85;
    margin: 0;
  }

  /* ── Chapter image ── */
  .ch-img-wrap {
    border-radius: 10px;
    overflow: hidden;
    border: 2px solid rgba(253,246,232,0.15);
    box-shadow: 4px 4px 0 rgba(0,0,0,0.3);
    margin-bottom: 8px;
  }
  .ch-img-wrap img { width: 100%; display: block; }

  /* ── Locations ── */
  .loc-pill {
    display: inline-block;
    font-family: 'Nunito', sans-serif;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--cream);
    background: rgba(90,138,106,0.25);
    border: 1.5px solid rgba(90,138,106,0.5);
    border-radius: 20px;
    padding: 4px 12px;
    margin: 0 6px 6px 0;
  }

  /* ── Branch cards ── */
  .branch-card {
    background: var(--parchment);
    border-radius: 12px;
    padding: 1.1rem 1.25rem 1rem;
    border-left: 4px solid var(--sage);
    box-shadow: 0 4px 12px rgba(0,0,0,0.18);
    min-height: 160px;
  }
  .branch-label {
    font-family: 'Nunito', sans-serif;
    font-size: 0.65rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--coral);
    display: block;
    margin-bottom: 8px;
  }
  .branch-text {
    font-family: 'Lora', serif;
    font-size: 0.9rem;
    color: var(--ink-soft);
    line-height: 1.7;
    margin: 0;
  }

  /* ── Footer ── */
  .story-footer {
    text-align: center;
    padding: 2rem 1rem;
    font-family: 'Nunito', sans-serif;
    font-size: 0.75rem;
    letter-spacing: 0.06em;
    color: rgba(168,196,168,0.5);
  }

  /* ── Warnings ── */
  .stWarning > div {
    font-family: 'Nunito', sans-serif !important;
    border-radius: 10px !important;
    font-size: 0.9rem !important;
  }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: var(--forest-dk); }
  ::-webkit-scrollbar-thumb { background: var(--forest-lt); border-radius: 4px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--sage); }

  /* ── CRITICAL: force dark ink inside paper surfaces ──
     Streamlit sets a global light/white text color that leaks into
     custom HTML. These rules lock every element inside paper cards
     to the correct dark palette values. ── */
  .paper-page, .paper-page * { color: var(--ink) !important; }
  .paper-page .book-tagline { color: var(--ink-soft) !important; }
  .paper-page .stat-l       { color: var(--ink-soft) !important; }
  .paper-page .stat-n       { color: var(--coral) !important; }
  .paper-page .book-badge   { color: var(--coral) !important; }
  .paper-page .char-role    { color: var(--coral) !important; }
  .paper-page .char-desc    { color: var(--ink-soft) !important; }
  .paper-page .char-avatar  { color: var(--cream) !important; }

  .chapter-card, .chapter-card * { color: var(--ink) !important; }
  .chapter-card .chapter-num     { color: var(--amber) !important; }
  .chapter-card .chapter-text    { color: var(--ink-soft) !important; }

  .branch-card, .branch-card *   { color: var(--ink) !important; }
  .branch-card .branch-label     { color: var(--coral) !important; }
  .branch-card .branch-text      { color: var(--ink-soft) !important; }
</style>
""", unsafe_allow_html=True)


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Storybook Creator")
    st.caption("Settings & Controls")
    st.markdown("---")

    st.markdown("#### API Key")
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        try:
            api_key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            api_key = ""
    if api_key:
        genai.configure(api_key=api_key)
        st.success("Key loaded from environment.")
    else:
        api_key = st.text_input("Gemini API key", type="password")
        if api_key:
            genai.configure(api_key=api_key)

    st.markdown("---")
    st.markdown("#### Illustration style")
    style_choice = st.radio(
        "Illustration Style",
        list(STYLES.keys()),
        format_func=lambda s: STYLES[s]["label"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("#### Reading age")
    age_band = st.selectbox(
        "Reading Age",
        ["Ages 4–6", "Ages 7–10", "Ages 11–13", "Young Adult (14+)"],
        index=1,
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("#### Past prompts")
    if "prompt_history" not in st.session_state:
        st.session_state.prompt_history = []
    if st.session_state.prompt_history:
        for ph in reversed(st.session_state.prompt_history[-5:]):
            st.caption(f"↩ {ph[:45]}…" if len(ph) > 45 else f"↩ {ph}")
    else:
        st.caption("*Your past prompts will appear here.*")


# ─── Session State ────────────────────────────────────────────────────────────
for key, val in {
    "story": None, "images": {}, "pdf_bytes": None,
    "branch_options": [], "_pending_prompt": None,
    "_auto_generate": False, "prompt_input": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

if st.session_state._pending_prompt is not None:
    st.session_state.prompt_input = st.session_state._pending_prompt
    st.session_state._pending_prompt = None


# ─── Masthead ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="masthead">
  <span class="masthead-eyebrow">✦ &nbsp; a little book machine &nbsp; ✦</span>
  <h1 class="masthead-title">Storybook <em>Creator</em></h1>
  <span class="masthead-sub">Turn one idea into a fully illustrated storybook</span>
  <span class="masthead-stars">★ &nbsp; ★ &nbsp; ★</span>
</div>
""", unsafe_allow_html=True)


# ─── Input ────────────────────────────────────────────────────────────────────
st.markdown('<span class="input-label">What\'s your story idea?</span>', unsafe_allow_html=True)

col_input, col_random = st.columns([5, 1])
with col_input:
    prompt = st.text_area(
        "Your story idea",
        key="prompt_input",
        placeholder="An old lighthouse keeper meets a sea creature who grants one wish…",
        height=96,
        label_visibility="collapsed"
    )
with col_random:
    st.markdown("<br>", unsafe_allow_html=True)
    RANDOM_PROMPTS = [
        "A clockmaker discovers her clocks predict the future",
        "A boy finds a door in the library that opens to different eras",
        "Two rival bakers discover they share a magical recipe book",
        "A lighthouse keeper meets a sea creature who grants one wish",
        "A girl discovers a tiny dragon living in her grandmother's attic",
        "A young chef enters a competition where the ingredients are enchanted",
        "A cartographer maps a city that only exists at night",
    ]
    st.markdown('<div class="random-btn">', unsafe_allow_html=True)
    if st.button("Random", width="stretch"):
        st.session_state._pending_prompt = random.choice(RANDOM_PROMPTS)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<span class="chips-label">or try one of these</span>', unsafe_allow_html=True)
SAMPLES = [
    "A girl discovers a tiny dragon living in her attic",
    "A boy finds a map that leads to a living city",
    "An old lighthouse keeper meets a sea creature",
    "Two rival chefs compete in a magical kitchen",
]
chip_cols = st.columns(len(SAMPLES))
for i, (col, sample) in enumerate(zip(chip_cols, SAMPLES)):
    with col:
        st.markdown('<div class="chip-btn">', unsafe_allow_html=True)
        if st.button(sample[:35] + "…" if len(sample) > 35 else sample, key=f"chip_{i}", width="stretch"):
            st.session_state._pending_prompt = sample
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
generate_btn = st.button("Generate my storybook", type="primary", width="content")

_auto_gen = st.session_state.get("_auto_generate", False)
if _auto_gen:
    st.session_state._auto_generate = False


# ─── Generate ─────────────────────────────────────────────────────────────────
if (generate_btn or _auto_gen) and prompt.strip() and api_key:
    if prompt not in st.session_state.prompt_history:
        st.session_state.prompt_history.append(prompt)

    memory = st.session_state.get("world_memory", empty_memory())
    with st.spinner("Writing your story…"):
        story = generate_story(prompt, reading_age=age_band, style=style_choice, num_chapters=3, world_memory=memory)
    st.session_state.story = story
    st.session_state.images = {}
    st.session_state.pdf_bytes = None
    st.session_state.branch_options = []

    images = {}
    char_context = build_character_context(story.get("characters", []))
    progress = st.progress(0, text="Painting the cover…")
    cover_pos, cover_neg = build_image_prompt(
        story.get("cover_scene", prompt), style_choice, character_context=char_context
    )
    cover_pil = generate_image(cover_pos, negative_prompt=cover_neg)
    images["cover"] = pil_to_bytes(cover_pil)
    chapters = story.get("chapters", [])
    for i, ch in enumerate(chapters):
        progress.progress((i + 1) / (len(chapters) + 1), text=f"Painting chapter {i+1}…")
        pos, neg = build_image_prompt(
            ch.get("scene_prompt", ch["title"]), style_choice, character_context=char_context
        )
        pil = generate_image(pos, negative_prompt=neg)
        images[f"ch_{i}"] = pil_to_bytes(pil)
    progress.empty()
    st.session_state.images = images

    pdf_bytes = export_pdf(story, images, style_name=STYLES[style_choice]["label"], age_band=age_band)
    st.session_state.pdf_bytes = pdf_bytes
    st.session_state.world_memory = update_memory(
        st.session_state.get("world_memory", empty_memory()), story
    )
    st.rerun()

elif generate_btn and not api_key:
    st.warning("Add your Gemini API key in the sidebar first.")
elif generate_btn and not prompt.strip():
    st.warning("Write a story idea above to get started.")


# ─── Story Display ─────────────────────────────────────────────────────────────
if st.session_state.story:
    story = st.session_state.story
    images = st.session_state.images
    chapters = story.get("chapters", [])
    characters = story.get("characters", [])
    locations = story.get("locations", [])
    word_count = sum(len(ch.get("text", "").split()) for ch in chapters)
    read_time = max(1, round(word_count / 200))
    style_label = STYLES[style_choice]["label"] if style_choice in STYLES else style_choice

    st.markdown('<div class="section-div"><span class="section-div-text">your story is ready</span></div>', unsafe_allow_html=True)

    # ── Title block + cover ───────────────────────────────────────────────────
    col_text, col_cover = st.columns([3, 2])

    with col_text:
        st.markdown(f"""
        <div class="paper-page">
          <div class="paper-page-inner">
            <div class="paper-margin">
              <div class="paper-margin-line"></div>
              <div style="flex:1;">
                <span class="book-badge">{style_label} &nbsp;·&nbsp; {age_band}</span>
                <h2 class="book-title">{story.get("title", "Untitled")}</h2>
                <p class="book-tagline">{story.get("tagline", "")}</p>
                <div class="stat-row">
                  <div class="stat-item"><span class="stat-n">{len(chapters)}</span><span class="stat-l">Chapters</span></div>
                  <div class="stat-item"><span class="stat-n">{len(characters)}</span><span class="stat-l">Characters</span></div>
                  <div class="stat-item"><span class="stat-n">{len(locations)}</span><span class="stat-l">Locations</span></div>
                  <div class="stat-item"><span class="stat-n">{word_count}</span><span class="stat-l">Words</span></div>
                  <div class="stat-item"><span class="stat-n">{read_time}<span style="font-size:0.9rem">m</span></span><span class="stat-l">Read time</span></div>
                </div>
              </div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.markdown('<div class="dl-btn">', unsafe_allow_html=True)
            if st.session_state.pdf_bytes:
                st.download_button(
                    "Download PDF storybook",
                    data=st.session_state.pdf_bytes,
                    file_name=f"{story.get('title','storybook').replace(' ','_')}.pdf",
                    mime="application/pdf", width="stretch"
                )
            st.markdown('</div>', unsafe_allow_html=True)
        with dl_col2:
            st.markdown('<div class="dl-btn">', unsafe_allow_html=True)
            if images.get("cover"):
                st.download_button(
                    "Download cover image",
                    data=images["cover"],
                    file_name="cover.png", mime="image/png", width="stretch"
                )
            st.markdown('</div>', unsafe_allow_html=True)

        if characters:
            st.markdown('<div class="section-div" style="margin:1.2rem 0 1rem;"><span class="section-div-text">characters</span></div>', unsafe_allow_html=True)
            chars_html = ""
            for char in characters:
                initials = "".join(w[0].upper() for w in char.get("name","?").split()[:2])
                chars_html += f"""
                <div class="char-item">
                  <div class="char-avatar">{initials}</div>
                  <div>
                    <div class="char-name">{char.get("name","")}</div>
                    <span class="char-role">{char.get("role","")}</span>
                    <p class="char-desc">{char.get("description","")}</p>
                  </div>
                </div>"""
            st.markdown(f'<div class="paper-page"><div class="paper-page-inner">{chars_html}</div></div>', unsafe_allow_html=True)

    with col_cover:
        if images.get("cover"):
            st.markdown('<div class="cover-wrap">', unsafe_allow_html=True)
            st.image(images["cover"], width="stretch")
            st.markdown('</div>', unsafe_allow_html=True)

    # ── Timeline ──────────────────────────────────────────────────────────────
    if chapters:
        st.markdown('<div class="section-div"><span class="section-div-text">story timeline</span></div>', unsafe_allow_html=True)
        tl_cols = st.columns(len(chapters))
        for i, (col, ch) in enumerate(zip(tl_cols, chapters)):
            with col:
                if images.get(f"ch_{i}"):
                    st.markdown('<div class="tl-img-wrap">', unsafe_allow_html=True)
                    st.image(images[f"ch_{i}"], width="stretch")
                    st.markdown('</div>', unsafe_allow_html=True)
                st.markdown(f'<span class="tl-ch-num">Chapter {i+1}</span>', unsafe_allow_html=True)
                st.markdown(f'<span class="tl-ch-title">{ch.get("title","")}</span>', unsafe_allow_html=True)

    # ── Chapters ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-div"><span class="section-div-text">read the story</span></div>', unsafe_allow_html=True)

    for i, ch in enumerate(chapters):
        ch_col, img_col = st.columns([3, 2])
        with ch_col:
            st.markdown(f"""
            <div class="chapter-card">
              <div class="chapter-card-inner">
                <span class="chapter-num">Chapter {i+1}</span>
                <h3 class="chapter-title">{ch.get("title","")}</h3>
                <p class="chapter-text">{ch.get("text","")}</p>
              </div>
            </div>
            """, unsafe_allow_html=True)
        with img_col:
            if images.get(f"ch_{i}"):
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<div class="ch-img-wrap">', unsafe_allow_html=True)
                st.image(images[f"ch_{i}"], width="stretch")
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('<div class="dl-btn">', unsafe_allow_html=True)
                st.download_button(
                    f"Download ch. {i+1} illustration",
                    data=images[f"ch_{i}"],
                    file_name=f"chapter_{i+1}.png",
                    mime="image/png", width="stretch",
                    key=f"dl_img_{i}"
                )
                st.markdown('</div>', unsafe_allow_html=True)

        if i < len(chapters) - 1:
            st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

    # ── Locations ─────────────────────────────────────────────────────────────
    if locations:
        st.markdown('<div class="section-div"><span class="section-div-text">places in this story</span></div>', unsafe_allow_html=True)
        loc_html = "".join(f'<span class="loc-pill">&#x25B8; {loc}</span>' for loc in locations)
        st.markdown(f'<div style="padding:0.25rem 0 0.5rem;">{loc_html}</div>', unsafe_allow_html=True)

    # ── Branch ────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-div"><span class="section-div-text">what happens next?</span></div>', unsafe_allow_html=True)

    def generate_branch_options(story_data):
        last_ch = story_data.get("chapters", [])[-1] if story_data.get("chapters") else {}
        prompt_text = f"""
Based on this children's story ending:
Title: {story_data.get('title','')}
Last chapter: "{last_ch.get('text','')}"

Write exactly 3 short continuation options (2-3 sentences each).
Label them A, B, and C.
Make each feel meaningfully different in tone and direction.
Return ONLY the 3 options, no preamble.
Format:
A: [text]
B: [text]
C: [text]
"""
        model = genai.GenerativeModel(GEMINI_MODEL)
        resp = model.generate_content(prompt_text)
        text = resp.text.strip()
        opts = {}
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("A:"):
                opts["A"] = line[2:].strip()
            elif line.startswith("B:"):
                opts["B"] = line[2:].strip()
            elif line.startswith("C:"):
                opts["C"] = line[2:].strip()
        return [opts.get("A",""), opts.get("B",""), opts.get("C","")]

    if not st.session_state.branch_options and api_key:
        with st.spinner("Dreaming up what comes next…"):
            st.session_state.branch_options = generate_branch_options(story)

    branches = st.session_state.branch_options

    st.markdown("""
    <p style="font-family:'Lora',serif; font-style:italic; color:#a8c4a8; font-size:0.95rem; margin-bottom:1rem;">
    Continue the adventure — pick a direction or write your own:
    </p>""", unsafe_allow_html=True)

    if branches and any(branches):
        b_cols = st.columns(3)
        labels = ["Option A", "Option B", "Option C"]
        for i, (col, label, branch_text) in enumerate(zip(b_cols, labels, branches)):
            with col:
                st.markdown(f"""
                <div class="branch-card">
                  <span class="branch-label">{label}</span>
                  <p class="branch-text">{branch_text}</p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown('<div class="branch-btn">', unsafe_allow_html=True)
                if st.button(f"Choose {label[-1]}", key=f"branch_{i}", width="stretch"):
                    continuation = f"{story.get('title','')} continues: {branch_text}"
                    st.session_state._pending_prompt = continuation
                    st.session_state._auto_generate = True
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    custom_cont = st.text_input(
        "Or write your own continuation…",
        placeholder="The dragon suddenly spoke for the first time…",
        label_visibility="visible"
    )
    st.markdown('<div class="continue-btn">', unsafe_allow_html=True)
    if st.button("Continue with this", width="content"):
        if custom_cont.strip():
            st.session_state._pending_prompt = f"{story.get('title','')} continues: {custom_cont}"
            st.session_state._auto_generate = True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-div"></div>', unsafe_allow_html=True)
    st.markdown('<div class="story-footer">Storybook Creator &nbsp;·&nbsp; Streamlit + Gemini + Pollinations.ai</div>', unsafe_allow_html=True)
