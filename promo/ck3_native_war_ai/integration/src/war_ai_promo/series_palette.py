"""The brown-and-gold packaging established by Episodes 0 and 1.

These colors apply to authored packaging, never to original game pixels.
"""

BG = "#211813"
PANEL = "#35291F"
INK = "#F0E5CF"
MUTED = "#BBA98D"
GOLD = "#CBA56A"
RED = "#CA7962"
BLUE = "#9AAEAB"  # A muted faction accent; not a background or panel fill.
GREEN = "#ABB582"
PAPER = "#D9C39B"
PAPER_INK = "#3E2C20"
FAINT_RULE = "#61503C"
HIGHLIGHT = "#453724"


def ass_color(color: str) -> str:
    """Convert an RGB palette entry to an opaque ASS BGR color."""
    return "&H00" + color[5:7] + color[3:5] + color[1:3]
