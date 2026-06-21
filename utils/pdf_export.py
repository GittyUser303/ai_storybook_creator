"""
pdf_export.py  —  Premium Storybook PDF
Matches the Storybook Creator UI: forest green desk + warm parchment paper pages.
Uses ReportLab canvas directly for full background-color control.
"""

import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage

# ── Palette (mirrors CSS vars) ────────────────────────────────────────────────
FOREST      = colors.HexColor("#2D4A35")
FOREST_DK   = colors.HexColor("#1E3325")
FOREST_LT   = colors.HexColor("#3D6147")
CREAM       = colors.HexColor("#FDF6E8")
PARCHMENT   = colors.HexColor("#F5E8C8")
PARCH_DK    = colors.HexColor("#E0CC9A")
INK         = colors.HexColor("#1E1A12")
INK_SOFT    = colors.HexColor("#4A4030")
AMBER       = colors.HexColor("#D4870A")
AMBER_LT    = colors.HexColor("#F0A820")
CORAL       = colors.HexColor("#C94A28")
SAGE        = colors.HexColor("#5A8A6A")
WHITE       = colors.white

W, H = A4   # 595.3 x 841.9 pt


# ── Helpers ───────────────────────────────────────────────────────────────────

def _page_bg(c, bg=FOREST):
    """Fill the whole page with a solid background."""
    c.saveState()
    c.setFillColor(bg)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.restoreState()


def _desk_grid(c):
    """Subtle grid texture on green desk pages."""
    c.saveState()
    c.setStrokeColor(colors.HexColor("#FFFFFF"))
    c.setStrokeAlpha(0.03)
    c.setLineWidth(0.5)
    step = 20
    for x in range(0, int(W) + step, step):
        c.line(x, 0, x, H)
    for y in range(0, int(H) + step, step):
        c.line(0, y, W, y)
    c.restoreState()


def _paper_card(c, x, y, w, h, radius=10, ruled=True):
    """Draw a cream paper card with optional ruled lines and left margin rule."""
    c.saveState()
    # Drop shadow
    c.setFillColor(colors.HexColor("#000000"))
    c.setFillAlpha(0.18)
    c.roundRect(x + 4, y - 4, w, h, radius, fill=1, stroke=0)
    c.setFillAlpha(1)

    # Paper fill
    c.setFillColor(CREAM)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=0)

    # Subtle parchment inner border
    c.setStrokeColor(PARCH_DK)
    c.setStrokeAlpha(0.4)
    c.setLineWidth(0.5)
    c.roundRect(x, y, w, h, radius, fill=0, stroke=1)
    c.setStrokeAlpha(1)

    if ruled:
        # Horizontal ruled lines
        c.setStrokeColor(colors.HexColor("#C8B48C"))
        c.setStrokeAlpha(0.18)
        c.setLineWidth(0.4)
        line_y = y + h - 28
        while line_y > y + 8:
            c.line(x + 4, line_y, x + w - 4, line_y)
            line_y -= 28
        c.setStrokeAlpha(1)

        # Left red margin rule
        c.setStrokeColor(CORAL)
        c.setStrokeAlpha(0.25)
        c.setLineWidth(1)
        c.line(x + 36, y + 8, x + 36, y + h - 8)
        c.setStrokeAlpha(1)

    c.restoreState()


def _draw_image_bytes(c, img_bytes, x, y, w, h, radius=6):
    """Draw PIL image bytes onto the canvas clipped to a rounded rect."""
    if not img_bytes:
        return
    c.saveState()
    # shadow
    c.setFillColor(colors.HexColor("#000000"))
    c.setFillAlpha(0.22)
    c.roundRect(x + 5, y - 5, w, h, radius, fill=1, stroke=0)
    c.setFillAlpha(1)

    # Draw image
    import io as _io
    img_io = _io.BytesIO(img_bytes)
    img = PILImage.open(img_io)
    # Convert to RGB if needed
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img_buf = _io.BytesIO()
    img.save(img_buf, format="JPEG", quality=90)
    img_buf.seek(0)
    from reportlab.lib.utils import ImageReader
    rl_img = ImageReader(img_buf)
    c.drawImage(rl_img, x, y, width=w, height=h, preserveAspectRatio=True, mask='auto')

    # Border
    c.setStrokeColor(PARCH_DK)
    c.setLineWidth(1.5)
    c.roundRect(x, y, w, h, radius, fill=0, stroke=1)
    c.restoreState()


def _text(c, txt, x, y, font="Helvetica-Bold", size=11, color=INK, align="left", max_width=None):
    """Draw a single line of text."""
    c.saveState()
    c.setFont(font, size)
    c.setFillColor(color)
    if max_width and c.stringWidth(txt, font, size) > max_width:
        while len(txt) > 3 and c.stringWidth(txt + "…", font, size) > max_width:
            txt = txt[:-1]
        txt = txt + "…"
    if align == "center":
        c.drawCentredString(x, y, txt)
    elif align == "right":
        c.drawRightString(x, y, txt)
    else:
        c.drawString(x, y, txt)
    c.restoreState()


def _wrapped_text(c, txt, x, y, w, font="Helvetica", size=11, color=INK_SOFT, leading=20):
    """Simple word-wrap text block. Returns final y position."""
    c.saveState()
    c.setFont(font, size)
    c.setFillColor(color)
    words = txt.split()
    line = ""
    cy = y
    for word in words:
        test = (line + " " + word).strip()
        if c.stringWidth(test, font, size) <= w:
            line = test
        else:
            if line:
                c.drawString(x, cy, line)
                cy -= leading
            line = word
    if line:
        c.drawString(x, cy, line)
        cy -= leading
    c.restoreState()
    return cy


def _divider(c, y, label=""):
    """Amber section divider line with optional centre label."""
    c.saveState()
    c.setStrokeColor(AMBER)
    c.setStrokeAlpha(0.35)
    c.setLineWidth(0.8)
    if label:
        lw = 80
        c.line(40, y, W / 2 - lw / 2 - 8, y)
        c.line(W / 2 + lw / 2 + 8, y, W - 40, y)
        c.setStrokeAlpha(1)
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(AMBER_LT)
        c.drawCentredString(W / 2, y - 3, label)
    else:
        c.line(40, y, W - 40, y)
    c.setStrokeAlpha(1)
    c.restoreState()


# ── Pages ─────────────────────────────────────────────────────────────────────

def _cover_page(c, story, images, style_name, age_band):
    _page_bg(c, FOREST_DK)
    _desk_grid(c)

    # Eyebrow
    _text(c, "✦  A LITTLE BOOK MACHINE  ✦", W / 2, H - 52,
          font="Helvetica-Bold", size=7.5, color=AMBER_LT, align="center")

    # Cover image — large, centred
    cover = images.get("cover")
    if cover:
        img_w, img_h = 420, 280
        img_x = (W - img_w) / 2
        img_y = H - 52 - 28 - img_h
        _draw_image_bytes(c, cover, img_x, img_y, img_w, img_h, radius=8)

    # Title block on cream card
    card_y = 80
    card_h = H - 52 - 28 - 280 - 20 - card_y
    _paper_card(c, 30, card_y, W - 60, card_h, radius=10, ruled=False)

    # Title
    title = story.get("title", "Untitled Story")
    c.saveState()
    c.setFont("Helvetica-Bold", 26 if len(title) < 32 else 20)
    c.setFillColor(INK)
    c.drawCentredString(W / 2, card_y + card_h - 44, title)
    c.restoreState()

    # Tagline
    tagline = story.get("tagline", "")
    if tagline:
        _wrapped_text(c, tagline, 70, card_y + card_h - 72, W - 140,
                      font="Helvetica-Oblique", size=11, color=INK_SOFT, leading=17)

    # Style + age badges
    badge_y = card_y + 20
    badge_txt = f"  {style_name}  ·  {age_band}  "
    bw = c.stringWidth(badge_txt, "Helvetica-Bold", 9) + 8
    bx = (W - bw) / 2
    c.setFillColor(CORAL)
    c.roundRect(bx, badge_y, bw, 16, 8, fill=1, stroke=0)
    _text(c, badge_txt, W / 2, badge_y + 4,
          font="Helvetica-Bold", size=9, color=WHITE, align="center")

    c.showPage()


def _characters_page(c, characters):
    _page_bg(c, FOREST)
    _desk_grid(c)

    _text(c, "Meet the Characters", W / 2, H - 54,
          font="Helvetica-Bold", size=22, color=CREAM, align="center")
    _divider(c, H - 70)

    cy = H - 96
    for char in characters:
        name = char.get("name", "")
        role = char.get("role", "").upper()
        desc = char.get("description", "")

        card_h = 80
        _paper_card(c, 40, cy - card_h, W - 80, card_h, radius=8, ruled=False)

        # Avatar circle
        c.setFillColor(SAGE)
        c.circle(74, cy - card_h / 2, 18, fill=1, stroke=0)
        _text(c, name[0].upper(), 74, cy - card_h / 2 - 5,
              font="Helvetica-Bold", size=13, color=CREAM, align="center")

        # Left accent bar
        c.setFillColor(SAGE)
        c.rect(40, cy - card_h, 4, card_h, fill=1, stroke=0)

        # Text
        _text(c, name, 102, cy - 22, font="Helvetica-Bold", size=13, color=INK)
        _text(c, role, 102, cy - 36, font="Helvetica-Bold", size=7.5, color=CORAL)
        _wrapped_text(c, desc, 102, cy - 52, W - 160,
                      font="Helvetica-Oblique", size=10, color=INK_SOFT, leading=16)

        cy -= card_h + 14
        if cy < 60:
            c.showPage()
            _page_bg(c, FOREST)
            _desk_grid(c)
            cy = H - 60

    c.showPage()


def _timeline_page(c, chapters, images):
    _page_bg(c, FOREST_DK)
    _desk_grid(c)

    _text(c, "Story Timeline", W / 2, H - 54,
          font="Helvetica-BoldOblique", size=20, color=CREAM, align="center")
    _divider(c, H - 70)

    n = len(chapters)
    if n == 0:
        c.showPage()
        return

    # Thumbnail strip
    thumb_w = (W - 80 - (n - 1) * 14) / n
    thumb_h = thumb_w * 0.65
    tx = 40
    ty = H - 90 - thumb_h

    for i, ch in enumerate(chapters):
        img = images.get(f"ch_{i}")
        _draw_image_bytes(c, img, tx, ty, thumb_w, thumb_h, radius=6)
        # Chapter label
        _text(c, f"CH. {i + 1}", tx + thumb_w / 2, ty - 14,
              font="Helvetica-Bold", size=8, color=AMBER_LT, align="center")
        _text(c, ch.get("title", ""), tx + thumb_w / 2, ty - 26,
              font="Helvetica-Oblique", size=8.5, color=CREAM, align="center",
              max_width=thumb_w)
        tx += thumb_w + 14

    # Chapter list on a paper card
    list_y = ty - 50
    list_h = n * 32 + 28
    _paper_card(c, 40, list_y - list_h, W - 80, list_h, radius=8, ruled=False)

    iy = list_y - 20
    for i, ch in enumerate(chapters):
        c.setFillColor(CORAL)
        c.circle(65, iy + 4, 5, fill=1, stroke=0)
        _text(c, f"Chapter {i + 1} — {ch.get('title', '')}", 78, iy,
              font="Helvetica", size=11, color=INK, max_width=W - 160)
        iy -= 32

    c.showPage()


def _chapter_page(c, chapter, idx, img_bytes):
    _page_bg(c, FOREST)
    _desk_grid(c)

    # Chapter label (right side, rotated)
    c.saveState()
    c.setFillColor(CORAL)
    c.rect(W - 28, H / 2 - 50, 20, 100, fill=1, stroke=0)
    c.rotate(90)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(WHITE)
    c.drawCentredString(H / 2, -(W - 18), f"CHAPTER {idx + 1}")
    c.restoreState()

    # Two-column layout: text left, image right
    text_x, text_w = 36, W * 0.52 - 50
    img_x, img_w   = W * 0.52, W * 0.48 - 36
    img_h          = img_w * 0.72

    # Image (top right)
    if img_bytes:
        _draw_image_bytes(c, img_bytes, img_x, H - 56 - img_h, img_w, img_h, radius=8)

    # Text paper card (left column, full height minus margins)
    card_h = H - 80
    _paper_card(c, text_x, 36, text_w, card_h, radius=10, ruled=True)

    inner_x = text_x + 46   # after margin rule
    inner_w  = text_w - 58

    # Chapter number eyebrow
    _text(c, f"CHAPTER {idx + 1}", inner_x, 36 + card_h - 28,
          font="Helvetica-Bold", size=7, color=AMBER)

    # Chapter title
    title = chapter.get("title", "")
    _text(c, title, inner_x, 36 + card_h - 50,
          font="Helvetica-Bold", size=18, color=INK, max_width=inner_w)

    # Divider
    c.setStrokeColor(SAGE)
    c.setStrokeAlpha(0.4)
    c.setLineWidth(0.8)
    c.line(inner_x, 36 + card_h - 62, inner_x + inner_w, 36 + card_h - 62)
    c.setStrokeAlpha(1)

    # Body text — word-wrap
    text = chapter.get("text", "")
    _wrapped_text(c, text, inner_x, 36 + card_h - 80, inner_w,
                  font="Helvetica", size=10.5, color=INK_SOFT, leading=20)

    c.showPage()


def _end_page(c):
    _page_bg(c, FOREST_DK)
    _desk_grid(c)

    # Centre ornament card
    cw, ch = 320, 160
    cx = (W - cw) / 2
    cy = (H - ch) / 2
    _paper_card(c, cx, cy, cw, ch, radius=12, ruled=False)

    _text(c, "✦", W / 2, cy + ch - 40,
          font="Helvetica-Bold", size=22, color=AMBER, align="center")
    _text(c, "The End", W / 2, cy + ch / 2,
          font="Helvetica-BoldOblique", size=28, color=INK, align="center")
    _text(c, "✦  A Little Book Machine  ✦", W / 2, cy + 26,
          font="Helvetica-Oblique", size=9, color=INK_SOFT, align="center")

    c.showPage()


# ── Public export function ────────────────────────────────────────────────────

def export_pdf(story, images, style_name="Watercolor", age_band="Ages 7–10"):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(story.get("title", "Storybook"))
    c.setAuthor("AI Storybook Creator")

    _cover_page(c, story, images, style_name, age_band)

    characters = story.get("characters", [])
    if characters:
        _characters_page(c, characters)

    chapters = story.get("chapters", [])
    _timeline_page(c, chapters, images)

    for i, ch in enumerate(chapters):
        _chapter_page(c, ch, i, images.get(f"ch_{i}"))

    _end_page(c)

    c.save()
    buf.seek(0)
    return buf.getvalue()
