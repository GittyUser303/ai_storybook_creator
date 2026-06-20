"""
pdf_export.py — Immersive, colourful storybook PDF using ReportLab.

Design language (v2 — "Colourful Storybook"):
- Every page type has its own distinct colour identity:
    • Cover:      Deep midnight navy + gold stars
    • Characters: Warm lavender/purple with rose accents
    • TOC:        Deep teal/forest with gold
    • Chapter pages: Alternating jewel-tone sidebars (coral, sky, mint, amber)
    • Back matter: Sunset gradient feel — warm orange/rose
- Decorative elements: star clusters, wave borders, colour-block headers
- Large bold chapter numbers as decorative background elements
- Rounded image frames with coloured drop-shadows
- Full-bleed colour headers per chapter instead of plain white
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, NextPageTemplate,
    Paragraph, Spacer, Image as RLImage,
    PageBreak, HRFlowable, Table, TableStyle, KeepTogether, Flowable
)


# ── Palette — Jewel-tone storybook ───────────────────────────────────────────
# Page backgrounds
COVER_BG        = colors.HexColor("#1A1040")   # Deep midnight navy
CHARS_BG        = colors.HexColor("#2D1B52")   # Deep purple
TOC_BG          = colors.HexColor("#0D2E3A")   # Deep teal
BACK_BG         = colors.HexColor("#2C1418")   # Deep rose/wine
CHAPTER_BG      = colors.HexColor("#FFFBF4")   # Warm white for chapter pages

# Chapter accent colours (cycling)
CH_ACCENTS = [
    colors.HexColor("#E8493A"),   # Coral red
    colors.HexColor("#2980B9"),   # Sky blue
    colors.HexColor("#27AE60"),   # Emerald
    colors.HexColor("#E67E22"),   # Amber
    colors.HexColor("#8E44AD"),   # Purple
    colors.HexColor("#16A085"),   # Teal
]
CH_ACCENT_LIGHT = [
    colors.HexColor("#FDEAE8"),
    colors.HexColor("#EAF4FB"),
    colors.HexColor("#E9F7EF"),
    colors.HexColor("#FEF5E7"),
    colors.HexColor("#F5EEF8"),
    colors.HexColor("#E8F8F5"),
]

# Text colours
GOLD            = colors.HexColor("#F5C842")
GOLD_DIM        = colors.HexColor("#C49A2A")
WHITE           = colors.HexColor("#FFFFFF")
OFF_WHITE       = colors.HexColor("#F0EAF8")
LIGHT_CREAM     = colors.HexColor("#FFF8F0")
DARK_NAVY       = colors.HexColor("#0D0820")
INK             = colors.HexColor("#1a1040")
ROSE            = colors.HexColor("#E84393")
ROSE_LIGHT      = colors.HexColor("#FFD6EC")
MIST            = colors.HexColor("#A0C4D8")
RULE_GOLD       = colors.HexColor("#F5C842")
SOFT_GOLD       = colors.HexColor("#E8C870")
CARD_BG         = colors.HexColor("#F5EDE0")
CARD_BORDER     = colors.HexColor("#D4C4A0")
TEXT_DARK       = colors.HexColor("#1A0A30")
TEXT_BODY       = colors.HexColor("#2d1f4a")


# ── Page dimensions ───────────────────────────────────────────────────────────
W, H    = A4          # 595 × 842 pt
MARGIN  = 2.2 * cm
INNER_W = W - 2 * MARGIN


# ── Custom Flowable: full-width coloured rectangle ───────────────────────────
class ColourRect(Flowable):
    """Draws a filled rectangle spanning the inner width."""
    def __init__(self, height, colour, radius=6):
        super().__init__()
        self.rect_h  = height
        self.colour  = colour
        self.radius  = radius
        self.width   = INNER_W
        self.height  = height

    def draw(self):
        self.canv.setFillColor(self.colour)
        self.canv.roundRect(0, 0, INNER_W, self.rect_h, self.radius, fill=1, stroke=0)


class StarCluster(Flowable):
    """Draws decorative star dots."""
    def __init__(self, colour=GOLD, count=7, spread_w=80, spread_h=20):
        super().__init__()
        self.colour   = colour
        self.count    = count
        self.spread_w = spread_w
        self.spread_h = spread_h
        self.width    = spread_w
        self.height   = spread_h

    def draw(self):
        import math, random
        random.seed(42)
        self.canv.setFillColor(self.colour)
        positions = [(random.uniform(0, self.spread_w), random.uniform(0, self.spread_h)) for _ in range(self.count)]
        sizes     = [random.uniform(1.2, 3.2) for _ in range(self.count)]
        for (x, y), r in zip(positions, sizes):
            self.canv.circle(x, y, r, fill=1, stroke=0)


# ── Styles ────────────────────────────────────────────────────────────────────
def _styles():
    return {
        # ── Cover
        "cover_title": ParagraphStyle(
            "cover_title", fontName="Helvetica-Bold",
            fontSize=38, leading=46, textColor=GOLD,
            alignment=TA_CENTER, spaceAfter=8,
        ),
        "cover_tagline": ParagraphStyle(
            "cover_tagline", fontName="Helvetica-Oblique",
            fontSize=14, leading=20, textColor=ROSE_LIGHT,
            alignment=TA_CENTER, spaceAfter=6,
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta", fontName="Helvetica",
            fontSize=10, leading=15, textColor=MIST,
            alignment=TA_CENTER,
        ),
        # ── Section titles (on dark bg)
        "section_head_light": ParagraphStyle(
            "section_head_light", fontName="Helvetica-Bold",
            fontSize=20, leading=26, textColor=GOLD,
            alignment=TA_CENTER, spaceAfter=6,
        ),
        "eyebrow_light": ParagraphStyle(
            "eyebrow_light", fontName="Helvetica",
            fontSize=8, leading=12, textColor=SOFT_GOLD,
            alignment=TA_CENTER, letterSpacing=3, spaceAfter=4,
        ),
        # ── Characters (dark bg)
        "char_name_light": ParagraphStyle(
            "char_name_light", fontName="Helvetica-Bold",
            fontSize=15, leading=20, textColor=GOLD,
            alignment=TA_LEFT, spaceAfter=3,
        ),
        "char_role_light": ParagraphStyle(
            "char_role_light", fontName="Helvetica",
            fontSize=8, leading=12, textColor=ROSE_LIGHT,
            alignment=TA_LEFT, letterSpacing=1.5, spaceAfter=6,
        ),
        "char_desc_light": ParagraphStyle(
            "char_desc_light", fontName="Helvetica-Oblique",
            fontSize=11, leading=17, textColor=OFF_WHITE,
            alignment=TA_LEFT,
        ),
        # ── TOC (dark bg)
        "toc_title": ParagraphStyle(
            "toc_title", fontName="Helvetica-Bold",
            fontSize=26, leading=32, textColor=GOLD,
            alignment=TA_CENTER, spaceAfter=16,
        ),
        "toc_entry": ParagraphStyle(
            "toc_entry", fontName="Helvetica",
            fontSize=13, leading=26, textColor=OFF_WHITE,
            alignment=TA_LEFT,
        ),
        # ── Chapter (light bg)
        "chapter_eyebrow": ParagraphStyle(
            "chapter_eyebrow", fontName="Helvetica-Bold",
            fontSize=9, leading=14, textColor=WHITE,
            alignment=TA_LEFT, letterSpacing=3, spaceAfter=2,
        ),
        "chapter_title_light": ParagraphStyle(
            "chapter_title_light", fontName="Helvetica-Bold",
            fontSize=26, leading=32, textColor=WHITE,
            alignment=TA_LEFT, spaceAfter=0,
        ),
        "body": ParagraphStyle(
            "body", fontName="Helvetica",
            fontSize=12, leading=22, textColor=TEXT_BODY,
            alignment=TA_JUSTIFY, firstLineIndent=18,
        ),
        # ── Back matter (dark bg)
        "back_title": ParagraphStyle(
            "back_title", fontName="Helvetica-Bold",
            fontSize=28, leading=36, textColor=GOLD,
            alignment=TA_CENTER, spaceAfter=8,
        ),
        "back_body": ParagraphStyle(
            "back_body", fontName="Helvetica",
            fontSize=11, leading=18, textColor=OFF_WHITE,
            alignment=TA_CENTER,
        ),
        "ornament": ParagraphStyle(
            "ornament", fontName="Helvetica",
            fontSize=12, leading=18, textColor=SOFT_GOLD,
            alignment=TA_CENTER, spaceAfter=8, spaceBefore=8,
        ),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────
def _rule(colour=RULE_GOLD, width="60%", thickness=1.5):
    return HRFlowable(width=width, thickness=thickness, color=colour,
                      hAlign="CENTER", spaceAfter=10, spaceBefore=6)

def _ornament(s):
    return Paragraph("· · · ✦ · · ·", s["ornament"])

def _img_flowable(img_bytes, max_w, max_h):
    if not img_bytes:
        return None
    try:
        buf = io.BytesIO(img_bytes)
        return RLImage(buf, width=max_w, height=max_h, kind="proportional")
    except Exception:
        return None

def _char_card_dark(char, s):
    """Character card styled for dark (purple) background."""
    border_col = colors.HexColor("#7A4FAA")
    content = [
        Paragraph(char.get("name", ""), s["char_name_light"]),
        Paragraph(char.get("role", "").upper(), s["char_role_light"]),
        Paragraph(char.get("description", ""), s["char_desc_light"]),
    ]
    t = Table([[content]], colWidths=[INNER_W - 1.0*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), colors.HexColor("#3D2466")),
        ("BOX",          (0,0), (-1,-1), 1.5, border_col),
        ("LEFTPADDING",  (0,0), (-1,-1), 16),
        ("RIGHTPADDING", (0,0), (-1,-1), 16),
        ("TOPPADDING",   (0,0), (-1,-1), 14),
        ("BOTTOMPADDING",(0,0), (-1,-1), 14),
    ]))
    return t


# ── Page backgrounds & decoration ─────────────────────────────────────────────
# NOTE: backgrounds used to be picked by precomputing an absolute "page number
# → page type" map and reading it off a custom Canvas subclass. That breaks the
# moment any section's content (e.g. a chapter with a long scene + image) spills
# onto a second physical page, since nothing was anticipating that extra page —
# every following page then gets the *previous* section's background drawn
# under its own text, killing contrast. Instead we draw the background inside
# each PageTemplate's onPage callback, and switch templates with
# NextPageTemplate() right as each section's flowables start. ReportLab then
# applies that same template to every physical page a section overflows onto,
# automatically, with no page counting at all.

PAGE_COVER   = "cover"
PAGE_CHARS   = "chars"
PAGE_TOC     = "toc"
PAGE_CHAPTER = "chapter"
PAGE_BACK    = "back"

DARK_BG = {
    PAGE_COVER: COVER_BG,
    PAGE_CHARS: CHARS_BG,
    PAGE_TOC:   TOC_BG,
    PAGE_BACK:  BACK_BG,
}
DARK_ACCENT = {
    PAGE_COVER: colors.HexColor("#3A1F80"),
    PAGE_CHARS: colors.HexColor("#5B2490"),
    PAGE_TOC:   colors.HexColor("#1A5068"),
    PAGE_BACK:  colors.HexColor("#6A1A28"),
}


def _draw_full_bg(canv, colour):
    canv.saveState()
    canv.setFillColor(colour)
    canv.rect(0, 0, W, H, fill=1, stroke=0)
    canv.restoreState()


def _draw_dark_page_deco(canv, ptype):
    """Decorative elements for dark (cover/chars/toc/back) pages."""
    canv.saveState()
    import random
    random.seed(ptype)
    canv.setFillColor(GOLD)
    for _ in range(30):
        x = random.uniform(0.05 * W, 0.95 * W)
        y = random.uniform(0.55 * H, 0.97 * H)
        r = random.uniform(0.8, 2.5)
        canv.circle(x, y, r, fill=1, stroke=0)

    accent = DARK_ACCENT.get(ptype, DARK_ACCENT[PAGE_COVER])
    canv.setFillColor(accent)
    canv.ellipse(-0.2*W, -0.15*H, 1.2*W, 0.35*H, fill=1, stroke=0)

    canv.setStrokeColor(GOLD)
    canv.setLineWidth(1.2)
    size, m = 22, 12
    for (x0, y0, dx, dy) in [
        (m, H-m, size, 0), (m, H-m, 0, -size),
        (W-m, H-m, -size, 0), (W-m, H-m, 0, -size),
        (m, m, size, 0), (m, m, 0, size),
        (W-m, m, -size, 0), (W-m, m, 0, size),
    ]:
        canv.line(x0, y0, x0+dx, y0+dy)
    canv.restoreState()


def _draw_chapter_page_deco(canv, ch_idx):
    """Subtle warm-white decorative elements for chapter pages."""
    canv.saveState()
    accent = CH_ACCENTS[ch_idx % len(CH_ACCENTS)]
    canv.setFillColor(accent)
    canv.rect(0, 0, 7, H, fill=1, stroke=0)
    light = CH_ACCENT_LIGHT[ch_idx % len(CH_ACCENT_LIGHT)]
    canv.setFillColor(light)
    canv.rect(0, 0, W, 28, fill=1, stroke=0)
    canv.setStrokeColor(accent)
    canv.setLineWidth(1)
    size, m = 18, 12
    for (x0, y0, dx, dy) in [
        (m, H-m, size, 0), (m, H-m, 0, -size),
        (W-m, H-m, -size, 0), (W-m, H-m, 0, -size),
        (m, m, size, 0), (m, m, 0, size),
        (W-m, m, -size, 0), (W-m, m, 0, size),
    ]:
        canv.line(x0, y0, x0+dx, y0+dy)
    canv.restoreState()


def _draw_footer(canv, story_title, ptype, ch_idx):
    """Footer — shown on all pages except the cover."""
    page_num = canv.getPageNumber()
    if page_num <= 1:
        return
    canv.saveState()
    if ptype == PAGE_CHAPTER:
        title_col = CH_ACCENTS[ch_idx % len(CH_ACCENTS)]
        num_col   = GOLD_DIM
    else:
        title_col, num_col = MIST, GOLD
    canv.setFillColor(title_col)
    canv.setFont("Helvetica", 8)
    canv.drawCentredString(W / 2, 14 * mm, story_title)
    canv.setFillColor(num_col)
    canv.drawCentredString(W / 2, 9 * mm, f"— {page_num} —")
    canv.restoreState()


def _make_onpage(ptype, ch_idx, story_title):
    """Build an onPage callback bound to one section (and, for chapters, one
    accent colour). ReportLab calls this for every physical page that uses
    this template — including overflow pages — so background/text contrast
    is always correct no matter how a section's content actually flows."""
    def _onpage(canv, doc):
        if ptype == PAGE_CHAPTER:
            _draw_full_bg(canv, CHAPTER_BG)
            _draw_chapter_page_deco(canv, ch_idx)
        else:
            _draw_full_bg(canv, DARK_BG.get(ptype, COVER_BG))
            _draw_dark_page_deco(canv, ptype)
        _draw_footer(canv, story_title, ptype, ch_idx)
    return _onpage


# ── Chapter header block (colour-block with big chapter number) ───────────────
def _chapter_header_block(ch_num, ch_title, ch_idx, s):
    """Returns a coloured header panel for a chapter page."""
    accent      = CH_ACCENTS[ch_idx % len(CH_ACCENTS)]
    accent_dark = colors.HexColor(
        "#{:02X}{:02X}{:02X}".format(
            max(0, int(accent.red*255) - 30),
            max(0, int(accent.green*255) - 30),
            max(0, int(accent.blue*255) - 30),
        )
    )
    eyebrow = Paragraph(f"CHAPTER {ch_num}", s["chapter_eyebrow"])
    title   = Paragraph(ch_title, s["chapter_title_light"])
    inner   = [[eyebrow], [title]]
    t = Table(inner, colWidths=[INNER_W - 1.2*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), accent),
        ("LEFTPADDING",  (0,0), (-1,-1), 18),
        ("RIGHTPADDING", (0,0), (-1,-1), 18),
        ("TOPPADDING",   (0,0), (-1,-1), 14),
        ("BOTTOMPADDING",(0,0), (-1,-1), 16),
    ]))
    return t



# ── Main Export Function ──────────────────────────────────────────────────────
def export_pdf(story: dict, images: dict, style_name: str = "Watercolor", age_band: str = "Ages 7–10") -> bytes:
    buf       = io.BytesIO()
    s         = _styles()
    title     = story.get("title", "Untitled Story")
    chapters  = story.get("chapters", [])
    characters= story.get("characters", [])
    locations = story.get("locations", [])
    tagline   = story.get("tagline", "")
    month_yr  = datetime.now().strftime("%B %Y")

    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=MARGIN * 1.4,
        title=title, author="AI Storybook Creator",
    )
    frame = Frame(
        MARGIN, MARGIN * 1.4, INNER_W, H - MARGIN - MARGIN * 1.4,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id="content",
    )
    templates = [
        PageTemplate(id="cover", frames=[frame], onPage=_make_onpage(PAGE_COVER, 0, title)),
        PageTemplate(id="chars", frames=[frame], onPage=_make_onpage(PAGE_CHARS, 0, title)),
        PageTemplate(id="toc",   frames=[frame], onPage=_make_onpage(PAGE_TOC, 0, title)),
    ]
    for i in range(len(chapters)):
        templates.append(
            PageTemplate(id=f"chapter_{i}", frames=[frame], onPage=_make_onpage(PAGE_CHAPTER, i, title))
        )
    templates.append(PageTemplate(id="back", frames=[frame], onPage=_make_onpage(PAGE_BACK, 0, title)))
    doc.addPageTemplates(templates)

    els = []

    # ── COVER ────────────────────────────────────────────────────────────────
    cover_img = _img_flowable(images.get("cover"), INNER_W, 13.5 * cm)
    if cover_img:
        els.append(Spacer(1, 0.4 * cm))
        els.append(cover_img)
        els.append(Spacer(1, 0.9 * cm))
    else:
        els.append(Spacer(1, 5 * cm))

    els.append(Paragraph(title, s["cover_title"]))
    els.append(Spacer(1, 0.3 * cm))
    els.append(_rule(GOLD, "45%", 2))
    els.append(Spacer(1, 0.2 * cm))
    if tagline:
        els.append(Paragraph(f'<i>"{tagline}"</i>', s["cover_tagline"]))
        els.append(Spacer(1, 0.5 * cm))
    els.append(Paragraph(f"Illustration Style: {style_name}  ·  {age_band}", s["cover_meta"]))
    els.append(Paragraph(f"Generated {month_yr}", s["cover_meta"]))
    els.append(NextPageTemplate("chars" if characters else "toc"))
    els.append(PageBreak())

    # ── CHARACTERS ───────────────────────────────────────────────────────────
    if characters:
        els.append(Spacer(1, 0.4 * cm))
        els.append(Paragraph("MEET THE CHARACTERS", s["eyebrow_light"]))
        els.append(_rule(GOLD, "60%"))
        els.append(Spacer(1, 0.4 * cm))
        for char in characters:
            els.append(_char_card_dark(char, s))
            els.append(Spacer(1, 0.5 * cm))
        els.append(NextPageTemplate("toc"))
        els.append(PageBreak())

    # ── TABLE OF CONTENTS ────────────────────────────────────────────────────
    els.append(Spacer(1, 1.2 * cm))
    els.append(Paragraph("Table of Contents", s["toc_title"]))
    els.append(_rule(GOLD, "50%"))
    els.append(Spacer(1, 0.5 * cm))
    for i, ch in enumerate(chapters):
        els.append(
            Paragraph(
                f'<font color="#F5C842">Chapter {i+1}</font>'
                f'<font color="#6080A0">  ·  </font>'
                f'<b>{ch.get("title", "")}</b>',
                s["toc_entry"]
            )
        )
    els.append(NextPageTemplate("chapter_0" if chapters else "back"))
    els.append(PageBreak())
    for i, ch in enumerate(chapters):
        # Colour-block chapter header
        els.append(_chapter_header_block(i + 1, ch.get("title", ""), i, s))
        els.append(Spacer(1, 0.5 * cm))

        # Chapter illustration
        ch_img = _img_flowable(images.get(f"ch_{i}"), INNER_W, 9 * cm)
        if ch_img:
            els.append(ch_img)
            els.append(Spacer(1, 0.5 * cm))

        # Chapter text
        els.append(Paragraph(ch.get("text", ""), s["body"]))
        els.append(Spacer(1, 0.6 * cm))

        if i < len(chapters) - 1:
            els.append(_ornament(s))
            els.append(NextPageTemplate(f"chapter_{i + 1}"))
        else:
            els.append(NextPageTemplate("back"))

        els.append(PageBreak())

    # ── BACK MATTER ──────────────────────────────────────────────────────────
    els.append(Spacer(1, 2.5 * cm))
    els.append(Paragraph("The End", s["back_title"]))
    els.append(Spacer(1, 0.3 * cm))
    els.append(_rule(GOLD, "40%", 2))
    els.append(Spacer(1, 0.6 * cm))

    if locations:
        els.append(Paragraph("Locations in this story:", s["back_body"]))
        els.append(Spacer(1, 0.25 * cm))
        loc_text = "  ·  ".join(locations)
        els.append(Paragraph(f'<font color="#A0C4D8">{loc_text}</font>', s["back_body"]))
        els.append(Spacer(1, 0.8 * cm))

    els.append(Paragraph(
        '<font color="#F5C842">■</font> Created with AI Storybook Creator',
        s["back_body"]
    ))

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(els)
    return buf.getvalue()