#!/usr/bin/env python3
"""
OPSINTEL Executive Presentation Generator
==========================================
Generates a polished 15-slide executive PowerPoint using python-pptx.
Design: Dark navy/charcoal enterprise technology aesthetic with electric blue/cyan accents.
"""

import os
import sys
from datetime import datetime

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

# ──────────────────────────────────────────
# DESIGN SYSTEM — Color Palette
# ──────────────────────────────────────────
NAVY_DARK   = RGBColor(0x0B, 0x0F, 0x1A)   # Background primary
NAVY_MED    = RGBColor(0x10, 0x17, 0x2A)   # Background secondary
CHARCOAL    = RGBColor(0x1A, 0x20, 0x35)   # Card background
SLATE       = RGBColor(0x2A, 0x30, 0x50)   # Divider/accent bg

ELECTRIC_BLUE = RGBColor(0x00, 0x9E, 0xFF) # Primary accent
CYAN         = RGBColor(0x00, 0xE5, 0xD0)  # Secondary accent
VIOLET       = RGBColor(0x8B, 0x5C, 0xF6)  # Tertiary accent
GREEN_HEALTH = RGBColor(0x10, 0xB9, 0x81)  # Healthy state
AMBER_WARN   = RGBColor(0xF5, 0x9E, 0x0B)  # Warning
RED_CRITICAL = RGBColor(0xEF, 0x44, 0x44)  # Critical

WHITE        = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY   = RGBColor(0xB0, 0xBC, 0xD0)
MED_GRAY     = RGBColor(0x70, 0x7E, 0x96)
DIM_GRAY     = RGBColor(0x48, 0x52, 0x6A)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# ──────────────────────────────────────────
# HELPER FUNCTIONS
# ──────────────────────────────────────────

def set_slide_bg(slide, color=NAVY_DARK):
    """Set solid background color for a slide."""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_shape(slide, left, top, width, height, fill_color=None, border_color=None, border_width=Pt(0)):
    """Add a rectangle shape."""
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.line.fill.background()
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = border_width
    else:
        shape.line.fill.background()
    return shape

def add_rounded_rect(slide, left, top, width, height, fill_color=None, border_color=None):
    """Add a rounded rectangle."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    return shape

def add_text_box(slide, left, top, width, height, text, font_size=14, color=WHITE,
                  bold=False, alignment=PP_ALIGN.LEFT, font_name="Calibri"):
    """Add a text box with a single run of text."""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = alignment
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.name = font_name
    return txBox

def add_multiline_textbox(slide, left, top, width, height, lines, default_size=14,
                            default_color=WHITE, default_bold=False, alignment=PP_ALIGN.LEFT,
                            font_name="Calibri", line_spacing=1.2):
    """
    lines: list of dicts: { 'text': str, 'size': int, 'color': RGBColor, 'bold': bool, 'spacing_before': Pt, 'spacing_after': Pt }
    """
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True

    for i, line in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.alignment = alignment
        run = p.add_run()
        run.text = line.get('text', '')
        run.font.size = Pt(line.get('size', default_size))
        run.font.color.rgb = line.get('color', default_color)
        run.font.bold = line.get('bold', default_bold)
        run.font.name = font_name
        if 'spacing_before' in line:
            p.space_before = line['spacing_before']
        if 'spacing_after' in line:
            p.space_after = line['spacing_after']
        p.line_spacing = Pt(line.get('line_spacing', int(line.get('size', default_size) * line_spacing)))
    return txBox

def add_accent_line(slide, left, top, width, color=ELECTRIC_BLUE, height=Pt(3)):
    """Add a thin horizontal accent line."""
    shape = add_shape(slide, left, top, width, height, fill_color=color)
    return shape

def add_pill_box(slide, left, top, width, height, text, fill_color, text_color=WHITE, font_size=10):
    """Add a rounded pill-shaped label."""
    shape = add_rounded_rect(slide, left, top, width, height, fill_color=fill_color)
    tf = shape.text_frame
    tf.word_wrap = True
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    run = tf.paragraphs[0].add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.color.rgb = text_color
    run.font.bold = True
    run.font.name = "Calibri"
    tf.paragraphs[0].space_before = Pt(0)
    tf.paragraphs[0].space_after = Pt(0)
    return shape

def set_speaker_notes(slide, notes_text):
    """Set speaker notes for a slide."""
    notes_slide = slide.notes_slide
    notes_slide.notes_text_frame.text = notes_text

def add_flow_arrow(slide, left, top, size=Inches(0.25), color=ELECTRIC_BLUE):
    """Add a downward arrow indicator."""
    shape = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, left, top, size, size)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape

def add_right_arrow(slide, left, top, width=Inches(0.4), height=Inches(0.2), color=ELECTRIC_BLUE):
    """Add a right arrow."""
    shape = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


# ──────────────────────────────────────────
# SLIDE BUILDERS
# ──────────────────────────────────────────

def build_slide_01_title(prs):
    """SLIDE 1 — Title Slide"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank
    set_slide_bg(slide, NAVY_DARK)

    # Top accent bar
    add_shape(slide, Inches(0), Inches(0), SLIDE_W, Pt(4), fill_color=ELECTRIC_BLUE)

    # Vertical accent line left
    add_shape(slide, Inches(1.0), Inches(1.5), Pt(4), Inches(3.5), fill_color=ELECTRIC_BLUE)

    # Main title
    add_text_box(slide, Inches(1.5), Inches(1.8), Inches(10), Inches(1.2),
                 "OPSINTEL", font_size=60, color=WHITE, bold=True, font_name="Calibri Light")

    # Subtitle
    add_text_box(slide, Inches(1.5), Inches(3.0), Inches(10), Inches(0.6),
                 "AI-Powered Automated IT Operations Reporting", font_size=24, color=ELECTRIC_BLUE,
                 bold=False, font_name="Calibri")

    # Supporting line
    add_text_box(slide, Inches(1.5), Inches(3.8), Inches(9), Inches(0.8),
                 "Turning fragmented ITSM operational data into timely, consistent,\nexecutive-ready intelligence.",
                 font_size=14, color=LIGHT_GRAY, bold=False, font_name="Calibri")

    # Bottom info bar
    add_shape(slide, Inches(0), Inches(6.7), SLIDE_W, Inches(0.8), fill_color=NAVY_MED)
    add_text_box(slide, Inches(1.5), Inches(6.85), Inches(5), Inches(0.4),
                 "Proof of Concept  •  Executive Presentation", font_size=11, color=DIM_GRAY)
    add_text_box(slide, Inches(8), Inches(6.85), Inches(4), Inches(0.4),
                 datetime.now().strftime("%B %Y"), font_size=11, color=DIM_GRAY,
                 alignment=PP_ALIGN.RIGHT)

    # POC badge
    add_pill_box(slide, Inches(1.5), Inches(4.8), Inches(1.4), Inches(0.35),
                 "POC", fill_color=VIOLET, font_size=10)

    set_speaker_notes(slide, """Welcome everyone. This is OPSINTEL — our AI-Powered Automated IT Operations Reporting platform.

What you'll see today is a Proof of Concept that demonstrates how we can transform the way we produce and consume operational intelligence.

The core idea: take all of our fragmented ITSM data — incidents, problems, changes, SLAs — and automatically turn it into consistent, executive-ready reporting with AI-powered analysis.

After this presentation, I'll show you the live system in action.""")


def build_slide_02_problem(prs):
    """SLIDE 2 — The Business Problem"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, NAVY_DARK)
    add_shape(slide, Inches(0), Inches(0), SLIDE_W, Pt(4), fill_color=ELECTRIC_BLUE)

    # Headline
    add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7),
                 "Operational Reporting Is Still Too Manual", font_size=32, color=WHITE, bold=True)
    add_accent_line(slide, Inches(0.8), Inches(1.2), Inches(3.0))

    # Current workflow — vertical flow boxes
    flow_steps = [
        ("Incidents  •  Problems  •  Changes  •  SLAs", MED_GRAY),
        ("Manual Data Collection", AMBER_WARN),
        ("Spreadsheet Consolidation", AMBER_WARN),
        ("Manual KPI Calculation", AMBER_WARN),
        ("Manual Analysis & Report Writing", AMBER_WARN),
        ("Manual Distribution", AMBER_WARN),
    ]

    box_w = Inches(3.2)
    box_h = Inches(0.45)
    start_x = Inches(1.2)
    start_y = Inches(1.7)
    gap = Inches(0.65)

    for i, (text, accent) in enumerate(flow_steps):
        y = start_y + i * gap
        bg = CHARCOAL if i == 0 else SLATE
        shape = add_rounded_rect(slide, start_x, y, box_w, box_h, fill_color=bg, border_color=accent)
        tf = shape.text_frame
        tf.word_wrap = True
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER
        run = tf.paragraphs[0].add_run()
        run.text = text
        run.font.size = Pt(11)
        run.font.color.rgb = WHITE if i > 0 else LIGHT_GRAY
        run.font.bold = i > 0
        run.font.name = "Calibri"

        # Down arrow between boxes
        if i < len(flow_steps) - 1:
            arrow_x = start_x + box_w / 2 - Inches(0.12)
            arrow_y = y + box_h + Pt(2)
            add_flow_arrow(slide, arrow_x, arrow_y, Inches(0.24), AMBER_WARN)

    # Right side — Resulting Problems
    right_x = Inches(6.5)
    add_text_box(slide, right_x, Inches(1.7), Inches(5.5), Inches(0.5),
                 "The Result", font_size=18, color=AMBER_WARN, bold=True)

    problems = [
        ("⏱  Hours of manual effort", "per reporting cycle"),
        ("⚠  Inconsistent calculations", "across teams & periods"),
        ("📅  Delayed reporting", "days or weeks behind operations"),
        ("🔀  Fragmented operational view", "no single source of truth"),
        ("🔄  Repetitive work", "same process, every cycle"),
    ]

    for i, (title, subtitle) in enumerate(problems):
        y = Inches(2.4) + i * Inches(0.85)
        add_rounded_rect(slide, right_x, y, Inches(5.5), Inches(0.7), fill_color=CHARCOAL, border_color=DIM_GRAY)
        add_text_box(slide, right_x + Inches(0.2), y + Inches(0.05), Inches(5), Inches(0.35),
                     title, font_size=13, color=WHITE, bold=True)
        add_text_box(slide, right_x + Inches(0.2), y + Inches(0.35), Inches(5), Inches(0.3),
                     subtitle, font_size=10, color=MED_GRAY)

    set_speaker_notes(slide, """The key point here is that our problem isn't a lack of data. The problem is the manual work required to turn that data into consistent management information.

Today, producing an operational report means: someone collects data from incident queues, problem backlog, change records, and SLA trackers. They consolidate it in spreadsheets. They calculate KPIs manually. They write analysis. They format a report. They distribute it.

This takes hours. It's inconsistent between teams and time periods. And by the time leadership sees it, the data is already stale.

Let me show you why this matters beyond just reporting effort.""")


def build_slide_03_why_matters(prs):
    """SLIDE 3 — Why This Matters"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, NAVY_DARK)
    add_shape(slide, Inches(0), Inches(0), SLIDE_W, Pt(4), fill_color=ELECTRIC_BLUE)

    add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7),
                 "The Cost Isn't Just Reporting Effort", font_size=32, color=WHITE, bold=True)
    add_accent_line(slide, Inches(0.8), Inches(1.2), Inches(3.0))

    # Four consequence boxes across top
    consequences = [
        ("Manual\nEffort", "⏱", AMBER_WARN),
        ("Inconsistent\nData", "⚠", RED_CRITICAL),
        ("Delayed\nVisibility", "📅", AMBER_WARN),
        ("Limited\nContext", "🔀", VIOLET),
    ]

    for i, (label, icon, accent) in enumerate(consequences):
        x = Inches(0.8) + i * Inches(3.0)
        shape = add_rounded_rect(slide, x, Inches(1.7), Inches(2.6), Inches(1.2),
                                 fill_color=CHARCOAL, border_color=accent)
        add_text_box(slide, x + Inches(0.3), Inches(1.8), Inches(2.0), Inches(0.4),
                     icon, font_size=28, color=accent, alignment=PP_ALIGN.CENTER)
        add_text_box(slide, x + Inches(0.3), Inches(2.2), Inches(2.0), Inches(0.6),
                     label, font_size=14, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)

    # Impact statement
    add_rounded_rect(slide, Inches(1.5), Inches(3.3), Inches(10), Inches(0.7),
                     fill_color=SLATE, border_color=RED_CRITICAL)
    add_text_box(slide, Inches(1.8), Inches(3.4), Inches(9.5), Inches(0.5),
                 "Leadership receives information later than the operation generates it.",
                 font_size=16, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)

    # Before vs After contrast
    # BEFORE
    add_text_box(slide, Inches(1.5), Inches(4.4), Inches(4.5), Inches(0.4),
                 "TODAY", font_size=14, color=AMBER_WARN, bold=True, alignment=PP_ALIGN.CENTER)
    before_steps = ["Operational Event", "???", "Manual Reporting", "Leadership Sees It"]
    for i, step in enumerate(before_steps):
        y = Inches(4.9) + i * Inches(0.5)
        c = RED_CRITICAL if step == "???" else LIGHT_GRAY
        add_text_box(slide, Inches(2.0), y, Inches(3.5), Inches(0.35),
                     ("↓  " if i > 0 else "   ") + step, font_size=12, color=c, alignment=PP_ALIGN.CENTER)

    # AFTER
    add_text_box(slide, Inches(7.3), Inches(4.4), Inches(4.5), Inches(0.4),
                 "WITH OPSINTEL", font_size=14, color=GREEN_HEALTH, bold=True, alignment=PP_ALIGN.CENTER)
    after_steps = ["Operational Event", "Automated Intelligence", "Leadership Sees It"]
    for i, step in enumerate(after_steps):
        y = Inches(4.9) + i * Inches(0.6)
        c = GREEN_HEALTH if "Automated" in step else LIGHT_GRAY
        add_text_box(slide, Inches(7.8), y, Inches(3.5), Inches(0.35),
                     ("↓  " if i > 0 else "   ") + step, font_size=12, color=c, alignment=PP_ALIGN.CENTER)

    set_speaker_notes(slide, """The cost of manual reporting goes beyond just person-hours.

When reporting is manual, it's inconsistent — different people calculate metrics differently. It's delayed — by the time the report reaches leadership, the operational picture has already changed. And it lacks context — without cross-domain analysis, you see numbers but not the story behind them.

The fundamental problem: leadership receives information later than the operation generates it.

What we want is simple: when an operational event happens, leadership should see it through automated intelligence — not through a manual reporting chain.

That's what OPSINTEL delivers. Let me show you the solution.""")


def build_slide_04_solution(prs):
    """SLIDE 4 — The OPSINTEL Solution"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, NAVY_DARK)
    add_shape(slide, Inches(0), Inches(0), SLIDE_W, Pt(4), fill_color=ELECTRIC_BLUE)

    add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7),
                 "OPSINTEL Automates the Reporting Lifecycle", font_size=32, color=WHITE, bold=True)
    add_accent_line(slide, Inches(0.8), Inches(1.2), Inches(3.0))

    # Core pipeline — horizontal flow
    pipeline_steps = [
        ("ITSM\nDATA", ELECTRIC_BLUE),
        ("INGEST", CYAN),
        ("NORMALIZE", CYAN),
        ("ANALYZE", VIOLET),
        ("AI\nINSIGHT", VIOLET),
        ("EXECUTIVE\nREPORT", GREEN_HEALTH),
        ("SCHEDULE", GREEN_HEALTH),
        ("DELIVER", GREEN_HEALTH),
    ]

    total_w = Inches(11.5)
    box_w = Inches(1.25)
    box_h = Inches(1.0)
    start_x = Inches(0.9)
    start_y = Inches(2.0)
    spacing = (total_w - box_w) / (len(pipeline_steps) - 1)

    for i, (label, accent) in enumerate(pipeline_steps):
        x = start_x + i * spacing
        shape = add_rounded_rect(slide, x, start_y, box_w, box_h,
                                 fill_color=CHARCOAL, border_color=accent)
        tf = shape.text_frame
        tf.word_wrap = True
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER
        run = tf.paragraphs[0].add_run()
        run.text = label
        run.font.size = Pt(11)
        run.font.color.rgb = accent
        run.font.bold = True
        run.font.name = "Calibri"

        # Arrow between steps
        if i < len(pipeline_steps) - 1:
            arrow_x = x + box_w + Pt(4)
            arrow_y = start_y + box_h / 2 - Inches(0.1)
            add_right_arrow(slide, arrow_x, arrow_y, spacing - box_w - Pt(8), Inches(0.2), accent)

    # Tagline box
    add_rounded_rect(slide, Inches(1.5), Inches(3.6), Inches(10), Inches(0.8),
                     fill_color=SLATE, border_color=ELECTRIC_BLUE)
    add_text_box(slide, Inches(1.8), Inches(3.7), Inches(9.5), Inches(0.6),
                 "OPSINTEL transforms operational data into automated,\nevidence-backed management intelligence.",
                 font_size=16, color=WHITE, bold=False, alignment=PP_ALIGN.CENTER)

    # Three value pillars
    pillars = [
        ("Deterministic KPIs", "Consistent, repeatable\ncalculations every time", ELECTRIC_BLUE),
        ("AI Interpretation", "Gemini explains what the\nnumbers actually mean", VIOLET),
        ("Automated Delivery", "Scheduled reports delivered\nto Slack, Teams, PDF", GREEN_HEALTH),
    ]

    for i, (title, desc, accent) in enumerate(pillars):
        x = Inches(1.0) + i * Inches(4.0)
        y = Inches(5.0)
        add_rounded_rect(slide, x, y, Inches(3.6), Inches(1.6), fill_color=CHARCOAL, border_color=accent)
        add_text_box(slide, x + Inches(0.2), y + Inches(0.15), Inches(3.2), Inches(0.4),
                     title, font_size=15, color=accent, bold=True, alignment=PP_ALIGN.CENTER)
        add_accent_line(slide, x + Inches(0.5), y + Inches(0.55), Inches(2.6), accent, Pt(2))
        add_text_box(slide, x + Inches(0.2), y + Inches(0.7), Inches(3.2), Inches(0.7),
                     desc, font_size=11, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

    set_speaker_notes(slide, """This is the core of OPSINTEL. Instead of a manual process, we've automated the entire reporting lifecycle.

ITSM data — incidents, problems, changes, SLAs — is ingested, normalized into a canonical data model, analyzed through a deterministic KPI engine, enriched with AI-powered interpretation, formatted into executive reports, and delivered on schedule.

Three key design principles:
1. Deterministic KPIs — the same calculation, every time, no human variance.
2. AI Interpretation — Google Gemini doesn't replace the metrics, it explains them in executive-ready language.
3. Automated Delivery — reports generate and deliver themselves to Slack, Teams, or PDF.

This is the strongest slide in terms of our value proposition. Let me walk you through what the system actually consolidates.""")


def build_slide_05_consolidation(prs):
    """SLIDE 5 — What OPSINTEL Consolidates"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, NAVY_DARK)
    add_shape(slide, Inches(0), Inches(0), SLIDE_W, Pt(4), fill_color=ELECTRIC_BLUE)

    add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7),
                 "One Operational View Across ITSM Domains", font_size=32, color=WHITE, bold=True)
    add_accent_line(slide, Inches(0.8), Inches(1.2), Inches(3.0))

    # Center hub
    center_x = Inches(5.4)
    center_y = Inches(3.2)
    hub_w = Inches(2.5)
    hub_h = Inches(1.0)
    add_rounded_rect(slide, center_x, center_y, hub_w, hub_h,
                     fill_color=ELECTRIC_BLUE, border_color=WHITE)
    add_text_box(slide, center_x, center_y + Inches(0.1), hub_w, Inches(0.8),
                 "OPSINTEL", font_size=22, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)

    # Input domains — arranged around the hub
    domains = [
        ("INCIDENTS", Inches(1.0), Inches(1.6), RED_CRITICAL),
        ("PROBLEMS", Inches(4.2), Inches(1.6), AMBER_WARN),
        ("CHANGES", Inches(7.8), Inches(1.6), VIOLET),
        ("SERVICES", Inches(10.5), Inches(1.6), CYAN),
        ("SLA", Inches(1.0), Inches(5.0), GREEN_HEALTH),
        ("TRENDS", Inches(4.2), Inches(5.0), ELECTRIC_BLUE),
    ]

    for label, x, y, accent in domains:
        add_rounded_rect(slide, x, y, Inches(2.0), Inches(0.7),
                         fill_color=CHARCOAL, border_color=accent)
        add_text_box(slide, x, y + Inches(0.1), Inches(2.0), Inches(0.5),
                     label, font_size=13, color=accent, bold=True, alignment=PP_ALIGN.CENTER)

    # Output targets — bottom right
    outputs = [
        ("Dashboard", Inches(7.8), Inches(5.0), ELECTRIC_BLUE),
        ("AI Insights", Inches(9.0), Inches(5.0), VIOLET),
        ("Reports", Inches(10.2), Inches(5.0), GREEN_HEALTH),
        ("Automation", Inches(11.4), Inches(5.0), CYAN),
    ]

    for label, x, y, accent in outputs:
        add_rounded_rect(slide, x, y, Inches(1.2), Inches(0.7),
                         fill_color=CHARCOAL, border_color=accent)
        add_text_box(slide, x, y + Inches(0.1), Inches(1.2), Inches(0.5),
                     label, font_size=10, color=accent, bold=True, alignment=PP_ALIGN.CENTER)

    # Flow label
    add_text_box(slide, Inches(7.8), Inches(4.5), Inches(4.5), Inches(0.35),
                 "→  Operational Intelligence  →", font_size=12, color=ELECTRIC_BLUE,
                 bold=True, alignment=PP_ALIGN.CENTER)

    # POC dataset stats
    add_rounded_rect(slide, Inches(1.0), Inches(6.3), Inches(11.3), Inches(0.7),
                     fill_color=SLATE, border_color=DIM_GRAY)
    add_text_box(slide, Inches(1.3), Inches(6.4), Inches(10.5), Inches(0.5),
                 "POC Dataset:  30,000+ Incidents  •  2,900+ Problems  •  7,000+ Changes  •  12,500+ SLA Records  •  20 Services",
                 font_size=12, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

    set_speaker_notes(slide, """OPSINTEL consolidates six operational domains into a single intelligence platform.

Incidents, problems, changes, services, SLAs, and operational trends all flow into the same canonical data model. From there, the system produces four outputs: an interactive dashboard, AI-powered insights, automated executive reports, and scheduled automation.

For this POC, we've loaded a substantial synthetic dataset — over 30,000 incidents, 2,900 problems, 7,000 changes, and 12,500 SLA records across 20 enterprise services. This gives the system realistic data density to demonstrate real analytical value.

Now let me explain how the system actually processes this data end-to-end.""")


def build_slide_06_how_it_works(prs):
    """SLIDE 6 — How the System Works"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, NAVY_DARK)
    add_shape(slide, Inches(0), Inches(0), SLIDE_W, Pt(4), fill_color=ELECTRIC_BLUE)

    add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7),
                 "From Raw ITSM Data to Executive Intelligence", font_size=32, color=WHITE, bold=True)
    add_accent_line(slide, Inches(0.8), Inches(1.2), Inches(3.0))

    # Layered architecture — vertical stack
    layers = [
        ("DATA SOURCES", "CSV Upload  •  Synthetic Datasets  •  ServiceNow (Future)", ELECTRIC_BLUE),
        ("INGESTION & VALIDATION", "Auto-detect entity type  •  Schema normalization  •  Data quality checks", CYAN),
        ("CANONICAL DATA MODEL", "Incidents  •  Problems  •  Changes  •  SLAs  •  Services  (SQLAlchemy ORM)", CYAN),
        ("DETERMINISTIC KPI ENGINE", "Health Score  •  MTTR  •  SLA Compliance %  •  Change Success Rate  •  Problem Backlog", VIOLET),
        ("CORRELATION & INSIGHT", "Change-Incident correlation  •  Service health scoring  •  Trend analysis", VIOLET),
        ("AI INTERPRETATION", "Google Gemini  •  Executive summaries  •  Interactive Q&A  •  RCA  •  Risk forecast", VIOLET),
        ("REPORTING & DASHBOARD", "React Dashboard  •  PDF Reports  •  Markdown  •  10-section executive format", GREEN_HEALTH),
        ("SCHEDULER & NOTIFICATIONS", "Automated daily/weekly/monthly  •  Slack Block Kit  •  Teams Adaptive Cards", GREEN_HEALTH),
    ]

    start_y = Inches(1.5)
    box_h = Inches(0.58)
    gap = Inches(0.08)

    for i, (title, desc, accent) in enumerate(layers):
        y = start_y + i * (box_h + gap)

        # Background bar
        add_rounded_rect(slide, Inches(0.8), y, Inches(11.7), box_h,
                         fill_color=CHARCOAL, border_color=accent)

        # Title
        add_text_box(slide, Inches(1.0), y + Inches(0.02), Inches(3.5), Inches(0.3),
                     title, font_size=12, color=accent, bold=True)

        # Description
        add_text_box(slide, Inches(4.5), y + Inches(0.05), Inches(7.8), Inches(0.45),
                     desc, font_size=10, color=LIGHT_GRAY)

        # Down arrow
        if i < len(layers) - 1:
            add_flow_arrow(slide, Inches(6.3), y + box_h, Inches(0.2), accent)

    set_speaker_notes(slide, """This slide shows the end-to-end data flow at a conceptual level.

Starting from the top: data enters through CSV upload — in production, this would connect to ServiceNow or other ITSM tools. The ingestion layer auto-detects what kind of data it is — incidents, problems, changes, or SLAs — and normalizes it into our canonical data model.

From there, the deterministic KPI engine computes consistent metrics: a composite health score, MTTR, SLA compliance rates, change success rates, and problem backlog age. These are facts — the same calculation every time.

The correlation engine then looks for patterns, like incidents that occurred shortly after a change on the same service. 

AI interpretation — using Google Gemini — then explains what these facts mean in executive-ready language. 

Finally, the reporting layer formats everything into dashboard views and PDF reports, and the scheduler automates delivery on daily, weekly, and monthly cycles.

Now let me focus specifically on where AI adds value — this is a critical distinction.""")


def build_slide_07_ai_value(prs):
    """SLIDE 7 — AI Value"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, NAVY_DARK)
    add_shape(slide, Inches(0), Inches(0), SLIDE_W, Pt(4), fill_color=VIOLET)

    add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7),
                 "AI Doesn't Replace the Metrics — It Explains Them", font_size=30, color=WHITE, bold=True)
    add_accent_line(slide, Inches(0.8), Inches(1.2), Inches(3.0), VIOLET)

    # Left — The pipeline
    pipe_steps = [
        ("RAW DATA", LIGHT_GRAY),
        ("DETERMINISTIC ANALYTICS", CYAN),
        ("FACTS", ELECTRIC_BLUE),
        ("AI (GEMINI)", VIOLET),
        ("INSIGHT", GREEN_HEALTH),
        ("RECOMMENDATION", GREEN_HEALTH),
    ]

    for i, (label, color) in enumerate(pipe_steps):
        y = Inches(1.7) + i * Inches(0.8)
        add_rounded_rect(slide, Inches(0.8), y, Inches(2.8), Inches(0.5),
                         fill_color=CHARCOAL, border_color=color)
        add_text_box(slide, Inches(0.8), y + Inches(0.05), Inches(2.8), Inches(0.4),
                     label, font_size=12, color=color, bold=True, alignment=PP_ALIGN.CENTER)
        if i < len(pipe_steps) - 1:
            add_flow_arrow(slide, Inches(2.0), y + Inches(0.52), Inches(0.2), color)

    # Right — Example
    # FACT box
    add_text_box(slide, Inches(4.5), Inches(1.7), Inches(3.0), Inches(0.35),
                 "FACT", font_size=14, color=ELECTRIC_BLUE, bold=True)
    add_rounded_rect(slide, Inches(4.5), Inches(2.1), Inches(7.8), Inches(0.8),
                     fill_color=CHARCOAL, border_color=ELECTRIC_BLUE)
    add_text_box(slide, Inches(4.8), Inches(2.15), Inches(7.2), Inches(0.7),
                 "SLA compliance dropped to 91.07%.  MTTR increased to 9.63 hours.\n464 active P1 incidents across 20 services.",
                 font_size=12, color=LIGHT_GRAY)

    # AI INTERPRETATION box
    add_text_box(slide, Inches(4.5), Inches(3.2), Inches(3.0), Inches(0.35),
                 "AI INTERPRETATION", font_size=14, color=VIOLET, bold=True)
    add_rounded_rect(slide, Inches(4.5), Inches(3.6), Inches(7.8), Inches(1.3),
                     fill_color=CHARCOAL, border_color=VIOLET)
    add_text_box(slide, Inches(4.8), Inches(3.65), Inches(7.2), Inches(1.2),
                 "\"The SLA breach concentration maps primarily to Payment Gateway and\nCore Database Cluster, both of which experienced elevated emergency\nchange volumes in the preceding 48 hours. Cross-correlation analysis\nindicates a 32% probability of continued degradation during upcoming\nmaintenance windows unless change governance is tightened.\"",
                 font_size=11, color=LIGHT_GRAY)

    # MANAGEMENT VALUE box
    add_text_box(slide, Inches(4.5), Inches(5.2), Inches(3.0), Inches(0.35),
                 "MANAGEMENT VALUE", font_size=14, color=GREEN_HEALTH, bold=True)
    add_rounded_rect(slide, Inches(4.5), Inches(5.6), Inches(7.8), Inches(0.8),
                     fill_color=CHARCOAL, border_color=GREEN_HEALTH)
    add_text_box(slide, Inches(4.8), Inches(5.65), Inches(7.2), Inches(0.7),
                 "Prioritize Payment Gateway and Database Cluster investigation.\nFreeze non-essential changes during maintenance windows.\nDeploy dedicated incident swarming teams for active P1 resolution.",
                 font_size=12, color=GREEN_HEALTH)

    # Distinction label
    add_rounded_rect(slide, Inches(4.5), Inches(6.7), Inches(7.8), Inches(0.4),
                     fill_color=SLATE, border_color=VIOLET)
    add_text_box(slide, Inches(4.8), Inches(6.72), Inches(7.2), Inches(0.35),
                 "Facts are deterministic  →  AI adds context, correlation, and actionable language",
                 font_size=11, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

    set_speaker_notes(slide, """This is arguably the most important slide in the presentation.

We need to be very clear about what AI does and doesn't do in OPSINTEL.

The facts — SLA compliance at 91%, MTTR at 9.63 hours, 464 active P1 incidents — these are computed deterministically. Same data, same calculation, same result every time. There's no AI involved in producing these numbers.

What AI does is interpret those facts in executive-ready language. It identifies that the SLA breaches are concentrated in Payment Gateway and Database services. It correlates this with the volume of emergency changes. It forecasts risk.

The management value is clear: instead of a table of numbers, leadership gets actionable recommendations — prioritize these services, freeze changes here, deploy swarming teams there.

This is the critical design principle: facts are deterministic, AI adds context.

Let me now show you the interactive AI assistant.""")


def build_slide_08_ai_assistant(prs):
    """SLIDE 8 — AI Assistant"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, NAVY_DARK)
    add_shape(slide, Inches(0), Inches(0), SLIDE_W, Pt(4), fill_color=VIOLET)

    add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7),
                 "Ask Operations Questions in Natural Language", font_size=32, color=WHITE, bold=True)
    add_accent_line(slide, Inches(0.8), Inches(1.2), Inches(3.0), VIOLET)

    # Chat interface mockup
    chat_bg_x = Inches(0.8)
    chat_bg_y = Inches(1.6)
    add_rounded_rect(slide, chat_bg_x, chat_bg_y, Inches(7.0), Inches(5.2),
                     fill_color=CHARCOAL, border_color=VIOLET)

    # Chat header
    add_rounded_rect(slide, chat_bg_x, chat_bg_y, Inches(7.0), Inches(0.5),
                     fill_color=SLATE, border_color=VIOLET)
    add_text_box(slide, chat_bg_x + Inches(0.2), chat_bg_y + Inches(0.05), Inches(5.0), Inches(0.4),
                 "🤖  OPSINTEL AI Operational Analyst", font_size=12, color=VIOLET, bold=True)

    # User question bubble
    q_y = chat_bg_y + Inches(0.8)
    add_rounded_rect(slide, Inches(3.0), q_y, Inches(4.5), Inches(0.5),
                     fill_color=ELECTRIC_BLUE, border_color=None)
    add_text_box(slide, Inches(3.2), q_y + Inches(0.05), Inches(4.2), Inches(0.4),
                 "Why did incidents increase this week?", font_size=12, color=WHITE, bold=False)

    # AI answer bubble
    a_y = q_y + Inches(0.7)
    add_rounded_rect(slide, Inches(1.0), a_y, Inches(6.5), Inches(2.0),
                     fill_color=NAVY_MED, border_color=VIOLET)
    add_text_box(slide, Inches(1.2), a_y + Inches(0.1), Inches(6.1), Inches(1.8),
                 "Based on current metrics, we have 32,403 total incidents\nwith 5,085 currently open. The increase is concentrated in\nPayment Gateway and Authentication Service, coinciding\nwith 1,125 emergency changes executed this period.\n\nMTTR stands at 9.63 hours against a 4.0-hour target.\nSLA compliance has dropped to 91.07%.\n\n📊 Sources: Incidents DB, SLA Engine, Problem Backlog",
                 font_size=10, color=LIGHT_GRAY)

    # Evidence tag
    add_pill_box(slide, Inches(1.0), a_y + Inches(2.1), Inches(2.0), Inches(0.28),
                 "Evidence-Grounded", fill_color=VIOLET, font_size=9)

    # Right side — example questions
    add_text_box(slide, Inches(8.5), Inches(1.6), Inches(4.0), Inches(0.4),
                 "Example Questions", font_size=16, color=VIOLET, bold=True)

    questions = [
        "Why did incidents increase this week?",
        "Which service is most at risk?",
        "What changed compared with last week?",
        "What are the top operational concerns?",
        "Summarize this month's operational health.",
        "What is our current SLA breach rate?",
        "Generate an RCA for the Payment Gateway.",
    ]

    for i, q in enumerate(questions):
        y = Inches(2.2) + i * Inches(0.65)
        add_rounded_rect(slide, Inches(8.5), y, Inches(4.2), Inches(0.5),
                         fill_color=CHARCOAL, border_color=DIM_GRAY)
        add_text_box(slide, Inches(8.7), y + Inches(0.05), Inches(3.8), Inches(0.4),
                     f"💬  {q}", font_size=10, color=LIGHT_GRAY)

    # Key capability label
    add_rounded_rect(slide, Inches(8.5), Inches(6.3), Inches(4.2), Inches(0.5),
                     fill_color=SLATE, border_color=VIOLET)
    add_text_box(slide, Inches(8.7), Inches(6.35), Inches(3.8), Inches(0.4),
                 "All answers grounded in actual KPI data\nRole-aware: Admin vs Viewer access",
                 font_size=10, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

    set_speaker_notes(slide, """The AI assistant allows anyone to ask operational questions in plain English.

Instead of digging through dashboards or asking someone to pull data, you can simply ask: 'Why did incidents increase this week?' — and the AI responds with evidence-grounded answers based on the actual current operational metrics.

Key design decisions:
- Every answer is grounded in the same canonical KPI data. The AI cannot invent numbers — it only references what's in the database.
- The assistant is role-aware: admins can discuss system configuration, viewers get read-only insights.
- It can generate RCA reports for specific incidents, correlating them with recent changes.

I'll demonstrate this live in the demo. For now, let me show you the executive dashboard.""")


def build_slide_09_dashboard(prs):
    """SLIDE 9 — Executive Dashboard"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, NAVY_DARK)
    add_shape(slide, Inches(0), Inches(0), SLIDE_W, Pt(4), fill_color=ELECTRIC_BLUE)

    add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7),
                 "One Screen for Operational Health", font_size=32, color=WHITE, bold=True)
    add_accent_line(slide, Inches(0.8), Inches(1.2), Inches(3.0))

    # Dashboard wireframe representation
    # Health Score Gauge
    add_rounded_rect(slide, Inches(0.8), Inches(1.6), Inches(3.5), Inches(2.2),
                     fill_color=CHARCOAL, border_color=ELECTRIC_BLUE)
    add_text_box(slide, Inches(0.8), Inches(1.7), Inches(3.5), Inches(0.3),
                 "OPERATIONAL HEALTH", font_size=10, color=MED_GRAY, alignment=PP_ALIGN.CENTER)
    add_text_box(slide, Inches(0.8), Inches(2.1), Inches(3.5), Inches(0.8),
                 "41.3", font_size=48, color=RED_CRITICAL, bold=True, alignment=PP_ALIGN.CENTER)
    add_text_box(slide, Inches(0.8), Inches(2.9), Inches(3.5), Inches(0.3),
                 "CRITICAL", font_size=14, color=RED_CRITICAL, bold=True, alignment=PP_ALIGN.CENTER)
    add_text_box(slide, Inches(0.8), Inches(3.3), Inches(3.5), Inches(0.3),
                 "/ 100", font_size=12, color=MED_GRAY, alignment=PP_ALIGN.CENTER)

    # KPI Cards Row
    kpis = [
        ("Total Incidents", "32,403", RED_CRITICAL),
        ("Open Backlog", "5,085", AMBER_WARN),
        ("MTTR", "9.63 hrs", AMBER_WARN),
        ("SLA Compliance", "91.07%", RED_CRITICAL),
        ("Change Success", "91.86%", AMBER_WARN),
    ]

    for i, (label, value, accent) in enumerate(kpis):
        x = Inches(4.8) + i * Inches(1.7)
        y = Inches(1.6)
        add_rounded_rect(slide, x, y, Inches(1.55), Inches(1.0),
                         fill_color=CHARCOAL, border_color=accent)
        add_text_box(slide, x + Inches(0.05), y + Inches(0.05), Inches(1.45), Inches(0.25),
                     label, font_size=8, color=MED_GRAY, alignment=PP_ALIGN.CENTER)
        add_text_box(slide, x + Inches(0.05), y + Inches(0.35), Inches(1.45), Inches(0.5),
                     value, font_size=18, color=accent, bold=True, alignment=PP_ALIGN.CENTER)

    # Trend Chart Area
    add_rounded_rect(slide, Inches(4.8), Inches(2.8), Inches(8.0), Inches(1.0),
                     fill_color=CHARCOAL, border_color=DIM_GRAY)
    add_text_box(slide, Inches(5.0), Inches(2.85), Inches(3.0), Inches(0.25),
                 "📈  INCIDENT & CHANGE TRENDS", font_size=9, color=MED_GRAY)
    # Simulated chart bars
    bar_data = [0.6, 0.7, 0.5, 0.8, 0.9, 0.65, 0.75, 0.85, 0.7, 0.6, 0.5, 0.7, 0.8, 0.9]
    for j, h in enumerate(bar_data):
        bar_x = Inches(5.0) + j * Inches(0.5)
        bar_h = Inches(h * 0.5)
        bar_y = Inches(3.65) - bar_h
        add_shape(slide, bar_x, bar_y, Inches(0.35), bar_h,
                  fill_color=ELECTRIC_BLUE if h < 0.8 else AMBER_WARN)

    # Service Health Grid
    add_rounded_rect(slide, Inches(0.8), Inches(4.1), Inches(6.0), Inches(2.5),
                     fill_color=CHARCOAL, border_color=DIM_GRAY)
    add_text_box(slide, Inches(1.0), Inches(4.15), Inches(4.0), Inches(0.3),
                 "🛡  SERVICE HEALTH GRID", font_size=10, color=MED_GRAY)

    services_display = [
        ("Payment Gateway", "CRITICAL", RED_CRITICAL),
        ("Auth Service", "WARNING", AMBER_WARN),
        ("Core Database", "CRITICAL", RED_CRITICAL),
        ("E-Commerce", "WARNING", AMBER_WARN),
        ("Order Mgmt", "HEALTHY", GREEN_HEALTH),
        ("API Gateway", "CRITICAL", RED_CRITICAL),
        ("Network Switch", "WARNING", AMBER_WARN),
        ("Inventory", "HEALTHY", GREEN_HEALTH),
    ]

    for i, (svc, status, accent) in enumerate(services_display):
        col = i % 2
        row = i // 2
        sx = Inches(1.0) + col * Inches(3.0)
        sy = Inches(4.5) + row * Inches(0.5)
        add_text_box(slide, sx, sy, Inches(1.8), Inches(0.3),
                     svc, font_size=9, color=LIGHT_GRAY)
        add_pill_box(slide, sx + Inches(2.0), sy, Inches(0.8), Inches(0.25),
                     status, fill_color=accent, font_size=7)

    # AI Insights Panel
    add_rounded_rect(slide, Inches(7.2), Inches(4.1), Inches(5.5), Inches(2.5),
                     fill_color=CHARCOAL, border_color=VIOLET)
    add_text_box(slide, Inches(7.4), Inches(4.15), Inches(4.0), Inches(0.3),
                 "🤖  AI INSIGHTS & RISK FORECAST", font_size=10, color=VIOLET)
    add_text_box(slide, Inches(7.4), Inches(4.5), Inches(5.0), Inches(1.8),
                 "⚡ High Risk: Payment Gateway predicted\n   32% SLA breach probability this week\n\n⚠ Medium Risk: Auth Service memory\n   growth pattern after deployments\n\n✅ Improving: Change success rate up\n   3.2% over last 14 days",
                 font_size=9, color=LIGHT_GRAY)

    # Live feed badge
    add_pill_box(slide, Inches(0.8), Inches(6.8), Inches(1.6), Inches(0.3),
                 "● LIVE FEED", fill_color=RED_CRITICAL, font_size=9)
    add_text_box(slide, Inches(2.6), Inches(6.82), Inches(6.0), Inches(0.3),
                 "Real-time WebSocket incident feed  •  Auto-refreshing KPIs  •  Live NOC ticker",
                 font_size=10, color=DIM_GRAY)

    set_speaker_notes(slide, """This is a representation of the OPSINTEL dashboard. You'll see the actual live dashboard in the demo.

Key sections:
- Top left: Operational Health Score — a composite gauge from 0 to 100 based on SLA compliance, active P1s, problem backlog, and change success rate.
- Top center: KPI cards showing total incidents, open backlog, MTTR, SLA compliance, and change success rate.
- Middle: Trend charts showing incident and change volumes over the past 14 days.
- Bottom left: Service Health Grid — every monitored service with its current status.
- Bottom right: AI Insights panel — predictive risk forecasting and pattern detection.

The dashboard is live. WebSocket connections push new incident events to the UI in real-time. You'll see this in action during the demo.

Don't study every number here — you'll see the real dashboard momentarily. Let me now show the automated reporting capabilities.""")


def build_slide_10_reporting(prs):
    """SLIDE 10 — Automated Reporting"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, NAVY_DARK)
    add_shape(slide, Inches(0), Inches(0), SLIDE_W, Pt(4), fill_color=GREEN_HEALTH)

    add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7),
                 "Daily. Weekly. Monthly. Automatically.", font_size=32, color=WHITE, bold=True)
    add_accent_line(slide, Inches(0.8), Inches(1.2), Inches(3.0), GREEN_HEALTH)

    # Report cadences
    cadences = [
        ("DAILY", "Operational pulse check\nIncident volumes, active P1s, MTTR", ELECTRIC_BLUE),
        ("WEEKLY", "Performance review\nTrend analysis, SLA compliance, change audit", CYAN),
        ("MONTHLY", "Executive governance digest\nStrategic insights, capacity planning, risk forecast", VIOLET),
    ]

    for i, (period, desc, accent) in enumerate(cadences):
        x = Inches(0.8) + i * Inches(4.2)
        add_rounded_rect(slide, x, Inches(1.7), Inches(3.8), Inches(1.4),
                         fill_color=CHARCOAL, border_color=accent)
        add_text_box(slide, x + Inches(0.2), Inches(1.8), Inches(3.4), Inches(0.4),
                     period, font_size=22, color=accent, bold=True, alignment=PP_ALIGN.CENTER)
        add_accent_line(slide, x + Inches(0.5), Inches(2.3), Inches(2.8), accent, Pt(2))
        add_text_box(slide, x + Inches(0.2), Inches(2.4), Inches(3.4), Inches(0.6),
                     desc, font_size=10, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

    # Automated pipeline
    add_text_box(slide, Inches(0.8), Inches(3.4), Inches(5), Inches(0.4),
                 "AUTOMATED PIPELINE", font_size=14, color=GREEN_HEALTH, bold=True)

    pipe = [
        ("Schedule\nTrigger", GREEN_HEALTH),
        ("Analytics\nEngine", ELECTRIC_BLUE),
        ("AI\nSynthesis", VIOLET),
        ("Report\nGeneration", CYAN),
        ("PDF\nCreation", CYAN),
        ("Notification\nDelivery", GREEN_HEALTH),
    ]

    for i, (label, accent) in enumerate(pipe):
        x = Inches(0.8) + i * Inches(2.05)
        add_rounded_rect(slide, x, Inches(3.9), Inches(1.8), Inches(0.8),
                         fill_color=CHARCOAL, border_color=accent)
        add_text_box(slide, x, Inches(3.95), Inches(1.8), Inches(0.7),
                     label, font_size=10, color=accent, bold=True, alignment=PP_ALIGN.CENTER)
        if i < len(pipe) - 1:
            add_right_arrow(slide, x + Inches(1.82), Inches(4.2), Inches(0.2), Inches(0.15), accent)

    # Scheduler capabilities
    add_rounded_rect(slide, Inches(0.8), Inches(5.1), Inches(11.7), Inches(1.8),
                     fill_color=CHARCOAL, border_color=DIM_GRAY)
    add_text_box(slide, Inches(1.0), Inches(5.2), Inches(5.0), Inches(0.3),
                 "SCHEDULER CAPABILITIES  (Implemented)", font_size=12, color=GREEN_HEALTH, bold=True)

    capabilities = [
        ("⏰  Automated Scheduling", "Hourly background scheduler with configurable intervals"),
        ("▶  Run Now", "Manual trigger for any report period via API or UI"),
        ("📜  Execution History", "Full audit trail of every scheduled and manual run"),
        ("📊  Report Archive", "All generated reports stored as Markdown + PDF"),
        ("🔔  Notification Dispatch", "Automatic dispatch to Slack / Teams after generation"),
        ("🔄  Live Feed", "Real-time incident injection via WebSocket for demo"),
    ]

    for i, (title, desc) in enumerate(capabilities):
        col = i % 2
        row = i // 2
        x = Inches(1.0) + col * Inches(5.8)
        y = Inches(5.55) + row * Inches(0.4)
        add_text_box(slide, x, y, Inches(2.5), Inches(0.3),
                     title, font_size=10, color=WHITE, bold=True)
        add_text_box(slide, x + Inches(2.6), y, Inches(3.0), Inches(0.3),
                     desc, font_size=9, color=MED_GRAY)

    set_speaker_notes(slide, """Reporting in OPSINTEL runs at three cadences: daily, weekly, and monthly. Each produces a 10-section executive report.

The automated pipeline is simple: a schedule trigger fires, the analytics engine computes fresh KPIs, AI synthesizes the executive narrative, the report is generated in both Markdown and PDF formats, and notifications are dispatched to Slack and Teams.

The same pipeline can be triggered manually — via the dashboard or the API — or it runs automatically on schedule.

The scheduler maintains a complete execution history, so you can audit exactly when each report was generated and what was dispatched.

The key message: the same reporting pipeline works whether you trigger it manually or let it run automatically. Consistency is guaranteed.

Let me show you what an actual generated report looks like.""")


def build_slide_11_report_output(prs):
    """SLIDE 11 — Executive Report"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, NAVY_DARK)
    add_shape(slide, Inches(0), Inches(0), SLIDE_W, Pt(4), fill_color=GREEN_HEALTH)

    add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7),
                 "From Operational Metrics to Executive-Ready Reporting", font_size=30, color=WHITE, bold=True)
    add_accent_line(slide, Inches(0.8), Inches(1.2), Inches(3.0), GREEN_HEALTH)

    # Report structure — left side
    add_text_box(slide, Inches(0.8), Inches(1.5), Inches(4.0), Inches(0.4),
                 "10-SECTION REPORT STRUCTURE", font_size=13, color=GREEN_HEALTH, bold=True)

    sections = [
        ("1.", "AI Executive Summary", "AI-synthesized governance scorecard"),
        ("2.", "KPI Matrix", "Health, incidents, SLA, problems, changes"),
        ("3.", "Incident Deep Dive", "Priority analysis & root drivers"),
        ("4.", "SLA Compliance Audit", "Service-level breach analysis"),
        ("5.", "Problem Backlog", "Aging investigation & chronic issues"),
        ("6.", "Change Governance", "Risk analytics & rollback audit"),
        ("7.", "Service Scorecards", "Per-service health breakdown"),
        ("8.", "SLA Trend Charts", "Visual 7-day compliance trends"),
        ("9.", "AI Predictive Signals", "Anomaly detection & risk correlation"),
        ("10.", "Remediation Roadmap", "Actionable engineering mandates"),
    ]

    for i, (num, title, desc) in enumerate(sections):
        y = Inches(2.0) + i * Inches(0.47)
        add_text_box(slide, Inches(0.8), y, Inches(0.4), Inches(0.3),
                     num, font_size=10, color=ELECTRIC_BLUE, bold=True)
        add_text_box(slide, Inches(1.2), y, Inches(2.3), Inches(0.3),
                     title, font_size=11, color=WHITE, bold=True)
        add_text_box(slide, Inches(3.5), y, Inches(2.8), Inches(0.3),
                     desc, font_size=9, color=MED_GRAY)

    # Right side — report preview mockup
    add_rounded_rect(slide, Inches(6.8), Inches(1.5), Inches(5.7), Inches(5.3),
                     fill_color=RGBColor(0xF8, 0xFA, 0xFC), border_color=DIM_GRAY)

    # Report header
    add_text_box(slide, Inches(7.0), Inches(1.7), Inches(5.3), Inches(0.4),
                 "OPSINTEL Daily Executive Report", font_size=14,
                 color=RGBColor(0x1E, 0x1B, 0x4B), bold=True)
    add_shape(slide, Inches(7.0), Inches(2.1), Inches(5.3), Pt(2),
              fill_color=RGBColor(0x4F, 0x46, 0xE5))

    # Report content preview
    report_lines = [
        ("Document Scope: Daily Governance Digest", 8, RGBColor(0x64, 0x74, 0x8B)),
        ("Classification: Executive Leadership Restricted", 8, RGBColor(0x64, 0x74, 0x8B)),
        ("", 6, RGBColor(0x64, 0x74, 0x8B)),
        ("1. AI Executive Summary", 11, RGBColor(0x31, 0x2E, 0x81)),
        ("Overall Health Index: 41.3/100 (CRITICAL)", 9, RGBColor(0x1E, 0x29, 0x3B)),
        ("SLA compliance sits at 91.07% against target...", 9, RGBColor(0x47, 0x55, 0x69)),
        ("", 6, RGBColor(0x64, 0x74, 0x8B)),
        ("2. Executive KPI Matrix", 11, RGBColor(0x31, 0x2E, 0x81)),
        ("┌──────────┬────────┬────────┐", 7, RGBColor(0x94, 0xA3, 0xB8)),
        ("│ Metric   │ Value  │ Status │", 7, RGBColor(0x94, 0xA3, 0xB8)),
        ("├──────────┼────────┼────────┤", 7, RGBColor(0x94, 0xA3, 0xB8)),
        ("│ Health   │ 41.3   │ CRIT   │", 7, RGBColor(0x94, 0xA3, 0xB8)),
        ("│ MTTR     │ 9.63h  │ EVAL   │", 7, RGBColor(0x94, 0xA3, 0xB8)),
        ("└──────────┴────────┴────────┘", 7, RGBColor(0x94, 0xA3, 0xB8)),
    ]

    for i, (text, size, color) in enumerate(report_lines):
        add_text_box(slide, Inches(7.0), Inches(2.2) + i * Inches(0.25), Inches(5.3), Inches(0.25),
                     text, font_size=size, color=color, font_name="Consolas" if "│" in text or "┌" in text else "Calibri")

    # Format badges
    add_pill_box(slide, Inches(7.0), Inches(6.0), Inches(1.0), Inches(0.25), "PDF", fill_color=RED_CRITICAL, font_size=8)
    add_pill_box(slide, Inches(8.2), Inches(6.0), Inches(1.2), Inches(0.25), "MARKDOWN", fill_color=ELECTRIC_BLUE, font_size=8)
    add_pill_box(slide, Inches(9.6), Inches(6.0), Inches(1.5), Inches(0.25), "AI + DETERMINISTIC", fill_color=VIOLET, font_size=8)

    # Consistency note
    add_rounded_rect(slide, Inches(0.8), Inches(6.8), Inches(11.7), Inches(0.4),
                     fill_color=SLATE, border_color=GREEN_HEALTH)
    add_text_box(slide, Inches(1.0), Inches(6.82), Inches(11.3), Inches(0.35),
                 "Dashboard and reports use the same underlying analytics engine — ensuring consistency across all outputs",
                 font_size=11, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

    set_speaker_notes(slide, """Every generated report follows a 10-section structure — from AI Executive Summary through to a remediation roadmap with linked Obsidian runbooks.

The report is generated in both Markdown and PDF formats. The AI writes the executive summary dynamically based on the current operational metrics, while the KPI tables, trend charts, and service scorecards are deterministically generated from the same analytics engine that powers the dashboard.

This is important: the dashboard and the reports share the same calculation engine. If you see a number on the dashboard, it matches the report. Consistency is guaranteed by design, not by manual cross-checking.

During the demo, I'll generate a report live and open the PDF.

Now let me show the notification and integration layer.""")


def build_slide_12_integration(prs):
    """SLIDE 12 — Automation & Integration"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, NAVY_DARK)
    add_shape(slide, Inches(0), Inches(0), SLIDE_W, Pt(4), fill_color=CYAN)

    add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7),
                 "Designed for Automation and Extensibility", font_size=32, color=WHITE, bold=True)
    add_accent_line(slide, Inches(0.8), Inches(1.2), Inches(3.0), CYAN)

    # Current data input
    add_text_box(slide, Inches(0.8), Inches(1.7), Inches(3.0), Inches(0.4),
                 "DATA INPUT", font_size=14, color=ELECTRIC_BLUE, bold=True)

    inputs = [
        ("CSV Upload", "IMPLEMENTED", GREEN_HEALTH),
        ("ServiceNow API", "FUTURE — INTEGRATION READY", AMBER_WARN),
        ("Jira / ITSM", "FUTURE", DIM_GRAY),
        ("Observability Tools", "FUTURE", DIM_GRAY),
    ]

    for i, (label, status, accent) in enumerate(inputs):
        y = Inches(2.2) + i * Inches(0.7)
        add_rounded_rect(slide, Inches(0.8), y, Inches(3.5), Inches(0.55),
                         fill_color=CHARCOAL, border_color=accent)
        add_text_box(slide, Inches(1.0), y + Inches(0.03), Inches(2.0), Inches(0.25),
                     label, font_size=12, color=WHITE, bold=True)
        add_text_box(slide, Inches(1.0), y + Inches(0.27), Inches(2.8), Inches(0.22),
                     status, font_size=8, color=accent, bold=True)

    # Processing Core — center
    add_text_box(slide, Inches(5.0), Inches(1.7), Inches(3.5), Inches(0.4),
                 "PROCESSING", font_size=14, color=VIOLET, bold=True, alignment=PP_ALIGN.CENTER)

    add_rounded_rect(slide, Inches(5.0), Inches(2.2), Inches(3.5), Inches(3.0),
                     fill_color=CHARCOAL, border_color=VIOLET)

    core_items = ["Ingestion & Validation", "Canonical Data Model", "KPI Engine", "AI Synthesis (Gemini)",
                  "Correlation Analysis", "Report Generation"]
    for i, item in enumerate(core_items):
        add_text_box(slide, Inches(5.2), Inches(2.4) + i * Inches(0.42), Inches(3.0), Inches(0.3),
                     f"▸  {item}", font_size=10, color=LIGHT_GRAY)

    # Arrow from input to core
    add_right_arrow(slide, Inches(4.4), Inches(3.5), Inches(0.5), Inches(0.2), ELECTRIC_BLUE)

    # Output & Delivery — right
    add_text_box(slide, Inches(9.3), Inches(1.7), Inches(3.5), Inches(0.4),
                 "DELIVERY", font_size=14, color=GREEN_HEALTH, bold=True)

    outputs = [
        ("Interactive Dashboard", "IMPLEMENTED", GREEN_HEALTH),
        ("PDF Reports", "IMPLEMENTED", GREEN_HEALTH),
        ("Slack (Block Kit)", "CONFIGURED", CYAN),
        ("Teams (Adaptive Cards)", "CONFIGURED", CYAN),
        ("Email Notifications", "LOGGED — SMTP FUTURE", AMBER_WARN),
    ]

    for i, (label, status, accent) in enumerate(outputs):
        y = Inches(2.2) + i * Inches(0.7)
        add_rounded_rect(slide, Inches(9.3), y, Inches(3.5), Inches(0.55),
                         fill_color=CHARCOAL, border_color=accent)
        add_text_box(slide, Inches(9.5), y + Inches(0.03), Inches(2.0), Inches(0.25),
                     label, font_size=12, color=WHITE, bold=True)
        add_text_box(slide, Inches(9.5), y + Inches(0.27), Inches(2.8), Inches(0.22),
                     status, font_size=8, color=accent, bold=True)

    # Arrow from core to output
    add_right_arrow(slide, Inches(8.6), Inches(3.5), Inches(0.5), Inches(0.2), GREEN_HEALTH)

    # Legend
    add_rounded_rect(slide, Inches(0.8), Inches(5.8), Inches(11.7), Inches(1.1),
                     fill_color=SLATE, border_color=DIM_GRAY)
    add_text_box(slide, Inches(1.0), Inches(5.9), Inches(3.0), Inches(0.25),
                 "INTEGRATION STATUS LEGEND", font_size=10, color=WHITE, bold=True)

    legend_items = [
        ("●  IMPLEMENTED", "Fully functional in the POC", GREEN_HEALTH),
        ("●  CONFIGURED", "Webhook code built; requires active webhook URL", CYAN),
        ("●  FUTURE", "Architecture supports it; not built yet", AMBER_WARN),
    ]
    for i, (label, desc, color) in enumerate(legend_items):
        add_text_box(slide, Inches(1.0) + i * Inches(4.0), Inches(6.25), Inches(1.8), Inches(0.25),
                     label, font_size=9, color=color, bold=True)
        add_text_box(slide, Inches(1.0) + i * Inches(4.0), Inches(6.5), Inches(3.5), Inches(0.25),
                     desc, font_size=8, color=MED_GRAY)

    set_speaker_notes(slide, """This slide shows what's actually connected and what's architected for the future. Transparency is important.

Data Input: Currently, data enters through CSV upload. The architecture supports ServiceNow API integration — the code structure is ready for it, but it's not connected in this POC. Future sources like Jira and observability tools can be added.

Processing: The core pipeline — ingestion, validation, KPI engine, AI synthesis, correlation analysis, and report generation — is fully implemented and functional.

Delivery: The dashboard and PDF reports are fully working. Slack and Teams integration code is written using Block Kit and Adaptive Cards respectively, and webhook URLs are configurable from the UI. Email is logged but doesn't send via SMTP yet.

The key message: the architecture is extensible. Adding a new data source or delivery channel doesn't require rebuilding the system.

Now let's talk about the business value this delivers.""")


def build_slide_13_business_value(prs):
    """SLIDE 13 — Business Value"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, NAVY_DARK)
    add_shape(slide, Inches(0), Inches(0), SLIDE_W, Pt(4), fill_color=GREEN_HEALTH)

    add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7),
                 "What Changes With OPSINTEL?", font_size=32, color=WHITE, bold=True)
    add_accent_line(slide, Inches(0.8), Inches(1.2), Inches(3.0), GREEN_HEALTH)

    # BEFORE column
    add_text_box(slide, Inches(0.8), Inches(1.6), Inches(5.5), Inches(0.4),
                 "BEFORE", font_size=20, color=RED_CRITICAL, bold=True, alignment=PP_ALIGN.CENTER)

    before_items = [
        "Manual Data Collection",
        "Manual KPI Calculations",
        "Manual Trend Analysis",
        "Manual Report Writing",
        "Manual Distribution",
        "Inconsistent Across Teams",
    ]

    for i, item in enumerate(before_items):
        y = Inches(2.2) + i * Inches(0.65)
        add_rounded_rect(slide, Inches(0.8), y, Inches(5.5), Inches(0.5),
                         fill_color=CHARCOAL, border_color=RED_CRITICAL)
        add_text_box(slide, Inches(1.2), y + Inches(0.05), Inches(4.8), Inches(0.4),
                     f"✗  {item}", font_size=13, color=RED_CRITICAL)

    # AFTER column
    add_text_box(slide, Inches(7.0), Inches(1.6), Inches(5.5), Inches(0.4),
                 "AFTER", font_size=20, color=GREEN_HEALTH, bold=True, alignment=PP_ALIGN.CENTER)

    after_items = [
        "Automated Ingestion",
        "Deterministic KPI Engine",
        "Automated Trend Analysis",
        "AI-Assisted Report Generation",
        "Scheduled Delivery",
        "Single Source of Truth",
    ]

    for i, item in enumerate(after_items):
        y = Inches(2.2) + i * Inches(0.65)
        add_rounded_rect(slide, Inches(7.0), y, Inches(5.5), Inches(0.5),
                         fill_color=CHARCOAL, border_color=GREEN_HEALTH)
        add_text_box(slide, Inches(7.4), y + Inches(0.05), Inches(4.8), Inches(0.4),
                     f"✓  {item}", font_size=13, color=GREEN_HEALTH)

    # Business Outcomes
    add_rounded_rect(slide, Inches(0.8), Inches(6.3), Inches(11.7), Inches(0.8),
                     fill_color=SLATE, border_color=GREEN_HEALTH)

    outcomes = [
        ("Less Manual\nEffort", ELECTRIC_BLUE),
        ("More Consistent\nReporting", CYAN),
        ("Faster Executive\nVisibility", VIOLET),
        ("Better Operational\nContext", GREEN_HEALTH),
    ]

    for i, (text, accent) in enumerate(outcomes):
        x = Inches(1.2) + i * Inches(2.9)
        add_text_box(slide, x, Inches(6.38), Inches(2.5), Inches(0.65),
                     text, font_size=13, color=accent, bold=True, alignment=PP_ALIGN.CENTER)

    set_speaker_notes(slide, """The business value is straightforward.

Before OPSINTEL: every aspect of operational reporting was manual. Collection, calculation, analysis, writing, distribution — all done by people, resulting in inconsistency across teams and time periods.

After OPSINTEL: each of those manual steps is automated. Ingestion is automated. KPIs are calculated deterministically. Trend analysis runs continuously. Reports are AI-assisted. Delivery is scheduled. And everything uses a single source of truth.

The outcomes:
- Less manual effort — what used to take hours now runs automatically.
- More consistent reporting — the same calculation every time.
- Faster executive visibility — reports generate within seconds, not days.
- Better operational context — AI connects the dots across domains.

Now let me briefly touch on governance and trust, which matters for leadership adoption.""")


def build_slide_14_governance(prs):
    """SLIDE 14 — Architecture & Governance"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, NAVY_DARK)
    add_shape(slide, Inches(0), Inches(0), SLIDE_W, Pt(4), fill_color=ELECTRIC_BLUE)

    add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7),
                 "Built for Trust, Not Just Automation", font_size=32, color=WHITE, bold=True)
    add_accent_line(slide, Inches(0.8), Inches(1.2), Inches(3.0))

    # Trust pipeline
    trust_steps = [
        ("Data Quality", "CSV validation, schema normalization,\nauto-entity detection", ELECTRIC_BLUE),
        ("Deterministic KPIs", "Same data → same result,\nevery time, no human variance", CYAN),
        ("Evidence Grounding", "AI answers reference actual metrics,\nnot hallucinated data", VIOLET),
        ("AI Interpretation", "Gemini adds context and language,\nnot invented facts", VIOLET),
        ("Audit Trail", "Execution history, report archive,\nscheduler run records", GREEN_HEALTH),
        ("Secure Access", "JWT authentication, RBAC,\nadmin vs viewer roles", GREEN_HEALTH),
    ]

    for i, (title, desc, accent) in enumerate(trust_steps):
        col = i % 2
        row = i // 2
        x = Inches(0.8) + col * Inches(6.2)
        y = Inches(1.6) + row * Inches(1.5)

        add_rounded_rect(slide, x, y, Inches(5.8), Inches(1.2),
                         fill_color=CHARCOAL, border_color=accent)

        # Number circle
        add_pill_box(slide, x + Inches(0.15), y + Inches(0.15), Inches(0.4), Inches(0.35),
                     str(i + 1), fill_color=accent, font_size=14)

        add_text_box(slide, x + Inches(0.7), y + Inches(0.1), Inches(4.8), Inches(0.35),
                     title, font_size=14, color=accent, bold=True)
        add_text_box(slide, x + Inches(0.7), y + Inches(0.5), Inches(4.8), Inches(0.6),
                     desc, font_size=10, color=LIGHT_GRAY)

    # Technology stack
    add_rounded_rect(slide, Inches(0.8), Inches(6.2), Inches(11.7), Inches(0.8),
                     fill_color=SLATE, border_color=DIM_GRAY)
    add_text_box(slide, Inches(1.0), Inches(6.25), Inches(3.0), Inches(0.25),
                 "TECHNOLOGY STACK", font_size=10, color=WHITE, bold=True)
    add_text_box(slide, Inches(1.0), Inches(6.5), Inches(11.0), Inches(0.4),
                 "Backend: FastAPI + SQLAlchemy + SQLite  •  Frontend: React + Vite + TypeScript + TailwindCSS  •  AI: Google Gemini  •  Real-time: WebSocket",
                 font_size=9, color=MED_GRAY)

    set_speaker_notes(slide, """Automation without trust doesn't get adopted. OPSINTEL is designed with six trust principles.

1. Data Quality — every CSV upload is validated, schema is normalized, entity types are auto-detected. Bad data doesn't silently corrupt metrics.

2. Deterministic KPIs — the health score, MTTR, SLA compliance, and change success rate are calculated the same way every time. No human variance.

3. Evidence Grounding — when the AI assistant answers a question, it references actual metrics from the database. It can't invent numbers.

4. AI Interpretation — Gemini adds executive-ready language and context, but the underlying facts are always deterministic.

5. Audit Trail — every scheduled run, every generated report, every manual trigger is logged with timestamps and delivery status.

6. Secure Access — JWT-based authentication with role-based access control. Admins can trigger reports and manage data. Viewers get read-only dashboard access.

This isn't a technical security slide — it's a trust slide. Leadership can rely on the numbers because the system is designed for consistency and transparency.

Now, let me set up the transition to the live demo.""")


def build_slide_15_demo_future(prs):
    """SLIDE 15 — Demo + Future"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, NAVY_DARK)
    add_shape(slide, Inches(0), Inches(0), SLIDE_W, Pt(4), fill_color=ELECTRIC_BLUE)

    add_text_box(slide, Inches(0.8), Inches(0.5), Inches(11), Inches(0.7),
                 "From POC to Automated Operations Intelligence", font_size=30, color=WHITE, bold=True)
    add_accent_line(slide, Inches(0.8), Inches(1.2), Inches(3.0))

    # Left — LIVE DEMO
    add_text_box(slide, Inches(0.8), Inches(1.6), Inches(5.5), Inches(0.4),
                 "▶  LIVE DEMO", font_size=18, color=GREEN_HEALTH, bold=True)

    demo_steps = [
        "Open Dashboard & Review Health Score",
        "Upload ITSM Dataset (CSV)",
        "Watch Dashboard Update in Real-Time",
        "Explore Incident / Problem / Change / SLA Metrics",
        "Ask AI: \"Why did incidents increase?\"",
        "View Evidence-Backed AI Response",
        "Generate Weekly Executive Report",
        "Open Generated PDF Report",
        "Review Scheduler & Execution History",
        "Show Notification Configuration",
    ]

    for i, step in enumerate(demo_steps):
        y = Inches(2.1) + i * Inches(0.48)
        add_rounded_rect(slide, Inches(0.8), y, Inches(5.5), Inches(0.38),
                         fill_color=CHARCOAL, border_color=GREEN_HEALTH if i < 6 else CYAN)
        add_text_box(slide, Inches(1.0), y + Inches(0.02), Inches(0.4), Inches(0.3),
                     f"{i+1}.", font_size=10, color=GREEN_HEALTH, bold=True)
        add_text_box(slide, Inches(1.4), y + Inches(0.02), Inches(4.6), Inches(0.3),
                     step, font_size=10, color=LIGHT_GRAY)

    # Right — FUTURE ROADMAP
    add_text_box(slide, Inches(7.0), Inches(1.6), Inches(5.5), Inches(0.4),
                 "→  FUTURE ROADMAP", font_size=18, color=VIOLET, bold=True)

    future_items = [
        ("ServiceNow Live Integration", "Direct API connection to production ITSM"),
        ("Additional ITSM Sources", "Jira, PagerDuty, Datadog, Splunk"),
        ("Predictive Intelligence", "ML-based incident volume forecasting"),
        ("Advanced AI Agents", "Autonomous operational recommendations"),
        ("Enterprise Scale", "Multi-tenant, PostgreSQL, cloud deployment"),
        ("Executive Mobile View", "Leadership access on mobile devices"),
    ]

    for i, (title, desc) in enumerate(future_items):
        y = Inches(2.1) + i * Inches(0.75)
        add_rounded_rect(slide, Inches(7.0), y, Inches(5.5), Inches(0.6),
                         fill_color=CHARCOAL, border_color=VIOLET)
        add_text_box(slide, Inches(7.2), y + Inches(0.03), Inches(5.0), Inches(0.3),
                     title, font_size=12, color=VIOLET, bold=True)
        add_text_box(slide, Inches(7.2), y + Inches(0.3), Inches(5.0), Inches(0.25),
                     desc, font_size=9, color=MED_GRAY)

    # Labels
    add_pill_box(slide, Inches(0.8), Inches(7.0), Inches(2.0), Inches(0.28),
                 "CURRENT POC", fill_color=GREEN_HEALTH, font_size=9)
    add_pill_box(slide, Inches(7.0), Inches(7.0), Inches(2.0), Inches(0.28),
                 "FUTURE ROADMAP", fill_color=VIOLET, font_size=9)

    # Transition statement
    add_text_box(slide, Inches(3.5), Inches(7.0), Inches(6.0), Inches(0.3),
                 "Rather than showing you another diagram, let me show you the system working.",
                 font_size=11, color=MED_GRAY, alignment=PP_ALIGN.CENTER)

    set_speaker_notes(slide, """This is our transition slide to the live demo.

On the left: the demo flow I'll walk you through momentarily. We'll open the dashboard, upload data, watch it update in real-time, explore metrics across all ITSM domains, interact with the AI assistant, generate a report, review the scheduler, and show notification configuration.

On the right: where OPSINTEL can go from here. The architecture already supports extending data sources beyond CSV — ServiceNow API integration, additional ITSM platforms, observability tools. Future capabilities include predictive intelligence using ML models, advanced AI agents, enterprise-scale deployment, and mobile leadership views.

The distinction is clear: the left side is what we've built. The right side is where it can go.

Rather than showing you another architecture diagram, let me show you the system actually working.

[TRANSITION TO LIVE DEMO]""")


def build_slide_16_closing(prs):
    """SLIDE 16 — Closing Vision (Optional)"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide, NAVY_DARK)
    add_shape(slide, Inches(0), Inches(0), SLIDE_W, Pt(4), fill_color=ELECTRIC_BLUE)

    # Vertical accent
    add_shape(slide, Inches(1.0), Inches(2.0), Pt(4), Inches(3.0), fill_color=ELECTRIC_BLUE)

    # Vision statement
    add_text_box(slide, Inches(1.5), Inches(2.0), Inches(10), Inches(1.0),
                 "The Vision", font_size=36, color=WHITE, bold=True)

    add_text_box(slide, Inches(1.5), Inches(3.0), Inches(10), Inches(1.0),
                 "From reporting what happened\nto understanding what matters next.",
                 font_size=24, color=ELECTRIC_BLUE, bold=False, font_name="Calibri Light")

    # Pipeline
    vision_flow = [
        ("DATA", LIGHT_GRAY),
        ("INTELLIGENCE", ELECTRIC_BLUE),
        ("DECISION", VIOLET),
        ("ACTION", GREEN_HEALTH),
    ]

    for i, (label, accent) in enumerate(vision_flow):
        x = Inches(1.5) + i * Inches(2.8)
        y = Inches(4.8)
        add_rounded_rect(slide, x, y, Inches(2.2), Inches(0.7),
                         fill_color=CHARCOAL, border_color=accent)
        add_text_box(slide, x, y + Inches(0.1), Inches(2.2), Inches(0.5),
                     label, font_size=16, color=accent, bold=True, alignment=PP_ALIGN.CENTER)
        if i < len(vision_flow) - 1:
            add_right_arrow(slide, x + Inches(2.25), y + Inches(0.25), Inches(0.4), Inches(0.2), accent)

    # Bottom
    add_text_box(slide, Inches(1.5), Inches(5.8), Inches(10), Inches(0.5),
                 "OPSINTEL  •  AI-Powered Automated IT Operations Reporting",
                 font_size=12, color=DIM_GRAY, alignment=PP_ALIGN.CENTER)

    set_speaker_notes(slide, """The vision is simple.

Today, operational reporting tells leadership what happened — after the fact, through manual effort.

OPSINTEL moves us from reporting what happened to understanding what matters next.

Data becomes intelligence. Intelligence informs decisions. Decisions drive action.

Thank you. Let's move to the live demonstration.""")


# ──────────────────────────────────────────
# MAIN — Build Presentation
# ──────────────────────────────────────────

def main():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    print("Building OPSINTEL Executive Presentation...")

    build_slide_01_title(prs)
    print("  [OK] Slide 1: Title")

    build_slide_02_problem(prs)
    print("  [OK] Slide 2: Business Problem")

    build_slide_03_why_matters(prs)
    print("  [OK] Slide 3: Why This Matters")

    build_slide_04_solution(prs)
    print("  [OK] Slide 4: The Solution")

    build_slide_05_consolidation(prs)
    print("  [OK] Slide 5: What OPSINTEL Consolidates")

    build_slide_06_how_it_works(prs)
    print("  [OK] Slide 6: How It Works")

    build_slide_07_ai_value(prs)
    print("  [OK] Slide 7: AI Value")

    build_slide_08_ai_assistant(prs)
    print("  [OK] Slide 8: AI Assistant")

    build_slide_09_dashboard(prs)
    print("  [OK] Slide 9: Dashboard")

    build_slide_10_reporting(prs)
    print("  [OK] Slide 10: Automated Reporting")

    build_slide_11_report_output(prs)
    print("  [OK] Slide 11: Executive Report")

    build_slide_12_integration(prs)
    print("  [OK] Slide 12: Automation & Integration")

    build_slide_13_business_value(prs)
    print("  [OK] Slide 13: Business Value")

    build_slide_14_governance(prs)
    print("  [OK] Slide 14: Architecture & Governance")

    build_slide_15_demo_future(prs)
    print("  [OK] Slide 15: Demo + Future")

    build_slide_16_closing(prs)
    print("  [OK] Slide 16: Closing Vision")

    # Save
    output_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(output_dir, ".."))
    output_path = os.path.join(project_root, "OPSINTEL_Executive_Presentation.pptx")
    prs.save(output_path)
    print(f"\n[DONE] Presentation saved: {output_path}")
    print(f"   Slides: {len(prs.slides)}")
    return output_path


if __name__ == "__main__":
    main()
