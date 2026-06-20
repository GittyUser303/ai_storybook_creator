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

load_dotenv()  # loads GEMINI_API_KEY from .env

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Storybook Creator",
    page_icon="📖",
    layout="wide",
)

# ─── Inject Custom CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* ── Fonts ── */
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lora:ital,wght@0,400;0,600;1,400&family=Nunito:wght@400;600&display=swap');

  /* ── Root palette ── */
  :root {
    --ink:        #1a1025;
    --deep-ink:   #0e0a17;
    --parchment:  #f5ede0;
    --cream:      #fdf6ec;
    --gold:       #d4a847;
    --gold-dim:   #a07830;
    --rose:       #c8648a;
    --mist:       #7b9cb8;
    --card-bg:    #1e1535;
    --card-border:#2e2050;
    --glow:       rgba(212,168,71,0.15);
  }

  /* ── Global background ── */
  .stApp {
    background: radial-gradient(ellipse at 20% 0%, #1e1040 0%, #0e0a17 55%, #12081e 100%);
    background-attachment: fixed;
  }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #150e2a 0%, #0e0a1a 100%) !important;
    border-right: 1px solid #2e2050 !important;
  }
  [data-testid="stSidebar"] .stMarkdown h1,
  [data-testid="stSidebar"] .stMarkdown h2,
  [data-testid="stSidebar"] .stMarkdown h3 {
    font-family: 'Playfair Display', serif !important;
    color: var(--gold) !important;
  }

  /* ── Main heading ── */
  .story-masthead {
    text-align: center;
    padding: 3rem 1rem 1.5rem;
    position: relative;
  }
  .story-masthead h1 {
    font-family: 'Playfair Display', serif;
    font-size: clamp(2.4rem, 5vw, 4rem);
    font-weight: 700;
    color: var(--gold);
    letter-spacing: 0.02em;
    line-height: 1.15;
    text-shadow: 0 0 40px rgba(212,168,71,0.4), 0 2px 8px rgba(0,0,0,0.8);
    margin: 0;
  }
  .story-masthead p {
    font-family: 'Lora', serif;
    font-style: italic;
    color: #b8a0cc;
    font-size: 1.05rem;
    margin-top: 0.4rem;
  }
  .masthead-rule {
    width: 120px;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
    margin: 1rem auto 0;
  }

  /* ── Prompt area ── */
  .stTextArea textarea {
    font-family: 'Lora', serif !important;
    font-size: 1rem !important;
    color: var(--parchment) !important;
    background: rgba(30,21,53,0.8) !important;
    border: 1.5px solid #3a2870 !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
  }
  .stTextArea textarea:focus {
    border-color: var(--gold-dim) !important;
    box-shadow: 0 0 0 3px var(--glow) !important;
  }
  .stTextArea textarea::placeholder {
    color: #6a5a88 !important;
    font-style: italic !important;
  }

  /* ── Primary buttons ── */
  .stButton > button[kind="primary"],
  div[data-testid="stButton"] > button {
    font-family: 'Nunito', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    border-radius: 8px !important;
    transition: all 0.25s ease !important;
  }

  /* ── Sample chip buttons ── */
  .chip-btn > button {
    background: rgba(30,21,53,0.7) !important;
    border: 1px solid #3a2870 !important;
    color: #c8b8e8 !important;
    font-family: 'Lora', serif !important;
    font-style: italic !important;
    font-size: 0.88rem !important;
    border-radius: 20px !important;
    padding: 0.3rem 0.8rem !important;
    text-align: center !important;
  }
  .chip-btn > button:hover {
    border-color: var(--gold-dim) !important;
    color: var(--gold) !important;
    background: rgba(50,35,80,0.9) !important;
  }

  /* ── Story title block ── */
  .story-title-block {
    padding: 2.5rem 2rem 1.5rem;
    text-align: left;
    border-bottom: 1px solid #2e2050;
    margin-bottom: 1rem;
  }
  .story-title-block h1 {
    font-family: 'Playfair Display', serif;
    font-size: clamp(1.8rem, 3.5vw, 3rem);
    font-weight: 700;
    color: var(--gold);
    line-height: 1.2;
    text-shadow: 0 0 30px rgba(212,168,71,0.3);
    margin: 0 0 0.4rem;
  }
  .story-title-block .tagline {
    font-family: 'Lora', serif;
    font-style: italic;
    color: #a890c4;
    font-size: 1rem;
  }
  .style-badge, .age-badge {
    display: inline-block;
    font-family: 'Nunito', sans-serif;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 0.25rem 0.7rem;
    border-radius: 20px;
    margin-top: 0.75rem;
    margin-right: 0.4rem;
  }
  .style-badge { background: rgba(212,168,71,0.15); color: var(--gold); border: 1px solid rgba(212,168,71,0.3); }
  .age-badge   { background: rgba(200,100,138,0.15); color: var(--rose); border: 1px solid rgba(200,100,138,0.3); }

  /* ── Stat cards ── */
  .stat-row { display:flex; gap:0.75rem; flex-wrap:wrap; padding: 0 1.5rem 1.5rem; }
  .stat-card {
    flex:1; min-width:90px;
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 1rem 0.75rem;
    text-align:center;
  }
  .stat-num {
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem;
    color: var(--gold);
    display:block;
    line-height:1;
  }
  .stat-label {
    font-family: 'Nunito', sans-serif;
    font-size: 0.65rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #7060a0;
    display:block;
    margin-top: 0.3rem;
  }

  /* ── Cover image ── */
  .cover-wrap {
    border-radius: 16px;
    overflow: hidden;
    border: 2px solid #2e2050;
    box-shadow: 0 8px 40px rgba(0,0,0,0.6), 0 0 0 1px rgba(212,168,71,0.1);
  }
  .cover-wrap img { width:100%; display:block; }

  /* ── Character cards ── */
  .char-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 0.75rem;
    border-left: 3px solid var(--gold-dim);
  }
  .char-name {
    font-family: 'Playfair Display', serif;
    font-size: 1.15rem;
    color: var(--gold);
    margin:0 0 0.2rem;
  }
  .char-role {
    font-family: 'Nunito', sans-serif;
    font-size: 0.7rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--rose);
    margin-bottom: 0.6rem;
    display:block;
  }
  .char-desc {
    font-family: 'Lora', serif;
    font-size: 0.92rem;
    color: #b0a0c8;
    line-height: 1.6;
  }

  /* ── Timeline strip ── */
  .timeline-section { padding: 1.5rem; }
  .timeline-section h3 {
    font-family: 'Playfair Display', serif;
    color: var(--gold);
    font-size: 1.1rem;
    margin-bottom: 1rem;
  }

  /* ── Chapter cards ── */
  .chapter-card {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 16px;
    padding: 1.75rem 2rem;
    margin-bottom: 0.5rem;
    position: relative;
  }
  .chapter-label {
    font-family: 'Nunito', sans-serif;
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--gold-dim);
    margin-bottom: 0.4rem;
    display:block;
  }
  .chapter-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.45rem;
    color: var(--parchment);
    margin: 0 0 1rem;
    line-height: 1.3;
  }
  .chapter-body {
    font-family: 'Lora', serif;
    font-size: 1.05rem;
    color: #c0b0d8;
    line-height: 1.85;
  }
  .chapter-body p { margin: 0; }
  .chapter-ornament {
    text-align: center;
    color: #3a2870;
    font-size: 1.2rem;
    margin: 1.25rem 0;
    letter-spacing: 0.4em;
  }

  /* ── Chapter image ── */
  .ch-img-wrap {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #2e2050;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    margin-bottom: 0.5rem;
  }
  .ch-img-wrap img { width:100%; display:block; }

  /* ── Locations strip ── */
  .location-pill {
    display:inline-block;
    font-family: 'Nunito', sans-serif;
    font-size: 0.82rem;
    color: #a090c4;
    background: rgba(30,21,53,0.6);
    border: 1px solid #2e2050;
    border-radius: 20px;
    padding: 0.3rem 0.85rem;
    margin: 0 0.35rem 0.35rem 0;
  }

  /* ── Branch section ── */
  .branch-header {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    color: var(--gold);
    margin: 0 0 0.25rem;
  }
  .branch-sub {
    font-family: 'Lora', serif;
    font-style: italic;
    color: #8870aa;
    font-size: 0.92rem;
    margin-bottom: 1.5rem;
  }
  .branch-card {
    background: linear-gradient(135deg, #2a1a5e 0%, #3d1f6e 100%);
    border: 1px solid #5030a0;
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    height: 100%;
    cursor: pointer;
    transition: border-color 0.2s, box-shadow 0.2s;
  }
  .branch-card:hover {
    border-color: var(--gold-dim);
    box-shadow: 0 0 20px rgba(212,168,71,0.15);
  }
  .branch-label {
    font-family: 'Nunito', sans-serif;
    font-size: 0.7rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--gold-dim);
    margin-bottom: 0.6rem;
    display:block;
  }
  .branch-text {
    font-family: 'Lora', serif;
    font-size: 0.88rem;
    color: #d0c0e8;
    line-height: 1.7;
    text-align: center;
  }

  /* ── Section divider ── */
  .ink-rule {
    display:flex; align-items:center; gap:1rem;
    margin: 2rem 0;
    color: #3a2870;
  }
  .ink-rule::before, .ink-rule::after {
    content:''; flex:1;
    height:1px;
    background: linear-gradient(90deg, transparent, #3a2870);
  }
  .ink-rule::after { background: linear-gradient(90deg, #3a2870, transparent); }

  /* ── Download buttons ── */
  .dl-btn > button {
    background: rgba(212,168,71,0.1) !important;
    border: 1px solid rgba(212,168,71,0.35) !important;
    color: var(--gold) !important;
    font-family: 'Nunito', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    letter-spacing: 0.04em !important;
    width: 100% !important;
  }
  .dl-btn > button:hover {
    background: rgba(212,168,71,0.2) !important;
  }

  /* ── Footer ── */
  .story-footer {
    text-align: center;
    padding: 2rem 1rem;
    font-family: 'Nunito', sans-serif;
    font-size: 0.8rem;
    color: #3a2870;
    letter-spacing: 0.05em;
  }

  /* ── Sidebar radio fix ── */
  [data-testid="stSidebar"] label {
    font-family: 'Lora', serif !important;
    color: #c0b0d8 !important;
  }
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stRadio label {
    color: #a890c4 !important;
  }
  [data-testid="stSidebar"] .stSelectbox > div > div {
    background: rgba(30,21,53,0.9) !important;
    border-color: #3a2870 !important;
    color: #d0c0e8 !important;
  }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: #0e0a17; }
  ::-webkit-scrollbar-thumb { background: #2e2050; border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: #4a3070; }
</style>
""", unsafe_allow_html=True)


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📖 Storybook")
    st.caption("Creator Settings")
    st.markdown("---")

    st.markdown("#### 🔑 Gemini API Key")
    # Priority: .env → st.secrets → manual input
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        try:
            api_key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            api_key = ""
    if api_key:
        genai.configure(api_key=api_key)
        st.success("✅ API key loaded from environment.")
    else:
        api_key = st.text_input("Enter your Gemini API key", type="password")
        if api_key:
            genai.configure(api_key=api_key)

    st.markdown("---")
    st.markdown("#### 🎨 Illustration Style")
    style_choice = st.radio(
        "Illustration Style",
        list(STYLES.keys()),
        format_func=lambda s: STYLES[s]["label"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("#### 🧒 Reading Age")
    age_band = st.selectbox(
        "Reading Age",
        ["Ages 4–6", "Ages 7–10", "Ages 11–13", "Young Adult (14+)"],
        index=1,
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("#### 📜 Prompt History")
    if "prompt_history" not in st.session_state:
        st.session_state.prompt_history = []
    if st.session_state.prompt_history:
        for ph in reversed(st.session_state.prompt_history[-5:]):
            st.caption(f"↩ {ph[:45]}…" if len(ph) > 45 else f"↩ {ph}")
    else:
        st.caption("*Your past prompts will appear here.*")


# ─── Session State Init ────────────────────────────────────────────────────────
for key, val in {
    "story": None,
    "images": {},
    "pdf_bytes": None,
    "branch_options": [],
    "_pending_prompt": None,
    "_auto_generate": False,
    "prompt_input": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Handle pending prompt (from chips/random/branch buttons — must happen BEFORE text_area)
if st.session_state._pending_prompt is not None:
    st.session_state.prompt_input = st.session_state._pending_prompt
    st.session_state._pending_prompt = None


# ─── Hero / Input Section ─────────────────────────────────────────────────────
st.markdown("""
<div class="story-masthead">
  <h1>✦ AI Storybook Creator</h1>
  <p>Turn a one-line idea into a fully illustrated, downloadable storybook.</p>
  <div class="masthead-rule"></div>
</div>
""", unsafe_allow_html=True)

col_input, col_random = st.columns([5, 1])
with col_input:
    prompt = st.text_area(
        "Your story idea",
        key="prompt_input",
        placeholder="An old lighthouse keeper meets a sea creature who grants one wish…",
        height=100,
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
    if st.button("🎲 Random", width="stretch"):
        st.session_state._pending_prompt = random.choice(RANDOM_PROMPTS)
        st.rerun()

# Sample prompt chips
st.markdown("**✨ Try one of these:**")
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
generate_btn = st.button("📖 Generate Storybook", type="primary", width="content")

# Auto-generate fires when a branch/continue button was clicked
_auto_gen = st.session_state.get("_auto_generate", False)
if _auto_gen:
    st.session_state._auto_generate = False

# ─── Generate ─────────────────────────────────────────────────────────────────
if (generate_btn or _auto_gen) and prompt.strip() and api_key:
    if prompt not in st.session_state.prompt_history:
        st.session_state.prompt_history.append(prompt)

    memory = st.session_state.get("world_memory", empty_memory())
    with st.spinner("✦ Weaving your story…"):
        story = generate_story(prompt, reading_age=age_band, style=style_choice, num_chapters=3, world_memory=memory)
    st.session_state.story = story
    st.session_state.images = {}
    st.session_state.pdf_bytes = None
    st.session_state.branch_options = []

    # Generate images — character context injected into every prompt for consistency
    images = {}
    char_context = build_character_context(story.get("characters", []))
    progress = st.progress(0, text="Illustrating the cover…")
    cover_pos, cover_neg = build_image_prompt(
        story.get("cover_scene", prompt), style_choice, character_context=char_context
    )
    cover_pil = generate_image(cover_pos, negative_prompt=cover_neg)
    images["cover"] = pil_to_bytes(cover_pil)
    chapters = story.get("chapters", [])
    for i, ch in enumerate(chapters):
        progress.progress((i + 1) / (len(chapters) + 1), text=f"Illustrating Chapter {i+1}…")
        pos, neg = build_image_prompt(
            ch.get("scene_prompt", ch["title"]), style_choice, character_context=char_context
        )
        pil = generate_image(pos, negative_prompt=neg)
        images[f"ch_{i}"] = pil_to_bytes(pil)
    progress.empty()
    st.session_state.images = images

    # PDF
    pdf_bytes = export_pdf(story, images, style_name=STYLES[style_choice]["label"], age_band=age_band)
    st.session_state.pdf_bytes = pdf_bytes

    st.session_state.world_memory = update_memory(
        st.session_state.get("world_memory", empty_memory()), story
    )
    st.rerun()

elif generate_btn and not api_key:
    st.warning("Please enter your Gemini API key in the sidebar.")
elif generate_btn and not prompt.strip():
    st.warning("Please write a story idea first!")


# ─── Story Display ─────────────────────────────────────────────────────────────
if st.session_state.story:
    story = st.session_state.story
    images = st.session_state.images
    chapters = story.get("chapters", [])
    characters = story.get("characters", [])
    locations = story.get("locations", [])
    word_count = sum(len(ch.get("text", "").split()) for ch in chapters)
    read_time = max(1, round(word_count / 200))

    st.markdown('<div class="ink-rule">⁕</div>', unsafe_allow_html=True)

    # ── Title block + cover
    col_text, col_cover = st.columns([3, 2])
    with col_text:
        style_label = STYLES[style_choice]["label"] if style_choice in STYLES else style_choice
        st.markdown(f"""
        <div class="story-title-block">
          <h1>{story.get("title", "Untitled")}</h1>
          <div class="tagline">{story.get("tagline", "")}</div>
          <span class="style-badge">🎨 {style_label}</span>
          <span class="age-badge">🧒 {age_band}</span>
        </div>
        """, unsafe_allow_html=True)

        # Stats
        st.markdown(f"""
        <div class="stat-row">
          <div class="stat-card"><span class="stat-num">{len(chapters)}</span><span class="stat-label">Chapters</span></div>
          <div class="stat-card"><span class="stat-num">{len(characters)}</span><span class="stat-label">Characters</span></div>
          <div class="stat-card"><span class="stat-num">{len(locations)}</span><span class="stat-label">Locations</span></div>
          <div class="stat-card"><span class="stat-num">{word_count}</span><span class="stat-label">Words</span></div>
          <div class="stat-card"><span class="stat-num">{read_time}<span style="font-size:1rem"> min</span></span><span class="stat-label">Read Time</span></div>
        </div>
        """, unsafe_allow_html=True)

        # Download
        st.markdown("##### 📥 Download")
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.markdown('<div class="dl-btn">', unsafe_allow_html=True)
            if st.session_state.pdf_bytes:
                st.download_button(
                    "📄 Download PDF Storybook",
                    data=st.session_state.pdf_bytes,
                    file_name=f"{story.get('title','storybook').replace(' ','_')}.pdf",
                    mime="application/pdf",
                    width="stretch"
                )
            st.markdown('</div>', unsafe_allow_html=True)
        with dl_col2:
            st.markdown('<div class="dl-btn">', unsafe_allow_html=True)
            if images.get("cover"):
                st.download_button(
                    "🖼 Download Cover",
                    data=images["cover"],
                    file_name="cover.png",
                    mime="image/png",
                    width="stretch"
                )
            st.markdown('</div>', unsafe_allow_html=True)

        # Characters
        if characters:
            st.markdown("##### 🎭 Characters")
            for char in characters:
                st.markdown(f"""
                <div class="char-card">
                  <div class="char-name">{char.get("name","")}</div>
                  <span class="char-role">{char.get("role","").upper()}</span>
                  <div class="char-desc">{char.get("description","")}</div>
                </div>
                """, unsafe_allow_html=True)

    with col_cover:
        if images.get("cover"):
            st.markdown('<div class="cover-wrap">', unsafe_allow_html=True)
            st.image(images["cover"], width="stretch")
            st.markdown('</div>', unsafe_allow_html=True)

    # ── Story Timeline
    if chapters:
        st.markdown('<div class="ink-rule">✦</div>', unsafe_allow_html=True)
        st.markdown('<div class="timeline-section"><h3>📚 Story Timeline</h3></div>', unsafe_allow_html=True)
        tl_cols = st.columns(len(chapters))
        for i, (col, ch) in enumerate(zip(tl_cols, chapters)):
            with col:
                if images.get(f"ch_{i}"):
                    st.image(images[f"ch_{i}"], width="stretch")
                st.markdown(f"<div style='text-align:center; font-family:Nunito,sans-serif; font-size:0.72rem; color:#a07830; letter-spacing:0.08em; text-transform:uppercase; margin-top:0.4rem;'>Ch. {i+1}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:center; font-family:Lora,serif; font-size:0.85rem; color:#c0b0d8; margin-top:0.15rem;'>{ch.get('title','')}</div>", unsafe_allow_html=True)

    # ── Read the Story
    st.markdown('<div class="ink-rule">⁕</div>', unsafe_allow_html=True)
    st.markdown("##### 📖 Read the Story")
    for i, ch in enumerate(chapters):
        ch_col, img_col = st.columns([3, 2])
        with ch_col:
            st.markdown(f"""
            <div class="chapter-card">
              <span class="chapter-label">Chapter {i+1}</span>
              <h2 class="chapter-title">{ch.get("title","")}</h2>
              <div class="chapter-body"><p>{ch.get("text","")}</p></div>
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
                    f"⬇ Ch.{i+1} image",
                    data=images[f"ch_{i}"],
                    file_name=f"chapter_{i+1}.png",
                    mime="image/png",
                    width="stretch",
                    key=f"dl_img_{i}"
                )
                st.markdown('</div>', unsafe_allow_html=True)
        if i < len(chapters) - 1:
            st.markdown('<div class="chapter-ornament">· · · ✦ · · ·</div>', unsafe_allow_html=True)

    # ── Locations
    if locations:
        st.markdown('<div class="ink-rule">⁕</div>', unsafe_allow_html=True)
        st.markdown("##### 📍 Locations in this story")
        loc_html = "".join(f'<span class="location-pill">📍 {loc}</span>' for loc in locations)
        st.markdown(f'<div style="padding:0.5rem 0;">{loc_html}</div>', unsafe_allow_html=True)

    # ── Branch / What Happens Next
    st.markdown('<div class="ink-rule">✦</div>', unsafe_allow_html=True)

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
        with st.spinner("Imagining what comes next…"):
            st.session_state.branch_options = generate_branch_options(story)

    branches = st.session_state.branch_options

    st.markdown("""
    <div class="branch-header">✦ What happens next?</div>
    <div class="branch-sub">Continue this story — pick a direction or write your own:</div>
    """, unsafe_allow_html=True)

    if branches and any(branches):
        b_cols = st.columns(3)
        labels = ["Option A", "Option B", "Option C"]
        for i, (col, label, branch_text) in enumerate(zip(b_cols, labels, branches)):
            with col:
                st.markdown(f"""
                <div class="branch-card" style="min-height:180px">
                  <span class="branch-label">{label}</span>
                  <div class="branch-text">{branch_text}</div>
                </div>
                """, unsafe_allow_html=True)
                # Button is a native Streamlit widget — always renders directly
                # below the card regardless of card height, no alignment issues
                if st.button(f"➜ Choose {label[-1]}", key=f"branch_{i}", width="stretch"):
                    continuation = f"{story.get('title','')} continues: {branch_text}"
                    st.session_state._pending_prompt = continuation
                    st.session_state._auto_generate = True
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    custom_cont = st.text_input(
        "Or write your own continuation…",
        placeholder="The dragon suddenly spoke for the first time…",
        label_visibility="visible"
    )
    if st.button("➜ Continue with this", width="content"):
        if custom_cont.strip():
            st.session_state._pending_prompt = f"{story.get('title','')} continues: {custom_cont}"
            st.session_state._auto_generate = True
            st.rerun()

    # Footer
    st.markdown('<div class="ink-rule">⁕</div>', unsafe_allow_html=True)
    st.markdown('<div class="story-footer">Built with ✦ Streamlit + Gemini + Pollinations.ai</div>', unsafe_allow_html=True)