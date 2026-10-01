"""Draws the illustrative sample artwork as SVG. Output is rasterised with QuickLook."""
import math, random, sys
from pathlib import Path

NAVY, BLUE, MID, SKY, PALE = "#123a7d", "#0f4fa8", "#3b74c4", "#7fa8de", "#c9dcf5"
out = Path(sys.argv[1])

def leaf(x, y, angle, length, width, fill="none", stroke=BLUE, sw=5, vein=True, opacity=1):
    d = "M0,0 C%.1f,%.1f %.1f,%.1f %.1f,0 C%.1f,%.1f %.1f,%.1f 0,0 Z" % (length*.3, -width, length*.72, -width*.9, length, length*.72, width*.9, length*.3, width)
    v = '<path d="M0,0 L%.1f,0" fill="none" stroke="%s" stroke-width="%.1f" stroke-linecap="round"/>' % (length*.82, stroke, sw*.7) if vein else ""
    return '<g transform="translate(%.1f %.1f) rotate(%.1f)" opacity="%.2f"><path d="%s" fill="%s" stroke="%s" stroke-width="%.1f" stroke-linejoin="round"/>%s</g>' % (x, y, angle, opacity, d, fill, stroke if sw else "none", sw, v)

def sprig(x, y, height, pairs=5, lean=0, stroke=BLUE, sw=5, fill="none", scale=1.0):
    """A stem growing upward from (x, y) with paired leaves that shrink toward the tip."""
    parts = []
    tip_x = x + lean
    parts.append('<path d="M%.1f,%.1f Q%.1f,%.1f %.1f,%.1f" fill="none" stroke="%s" stroke-width="%.1f" stroke-linecap="round"/>' % (x, y, x - lean*.4, y - height*.5, tip_x, y - height, stroke, sw))
    for i in range(pairs):
        t = 0.22 + 0.7 * i / max(1, pairs - 1)
        # point on the quadratic stem
        px = (1-t)**2*x + 2*(1-t)*t*(x - lean*.4) + t*t*tip_x
        py = (1-t)**2*y + 2*(1-t)*t*(y - height*.5) + t*t*(y - height)
        size = height * (0.30 - 0.17 * i / max(1, pairs - 1)) * scale
        for side in (-1, 1):
            parts.append(leaf(px, py, -90 + side * (52 - 6*i), size, size*.30, fill, stroke, sw))
    parts.append(leaf(tip_x, y - height, -90 + lean*.05, height*.13*scale, height*.04*scale, fill, stroke, sw))
    return "".join(parts)

def page(body, defs=""):
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 1200" width="1200" height="1200"><defs>%s</defs><rect width="1200" height="1200" fill="#ffffff"/>%s</svg>' % (defs, body)

# v2 - oversized wrap lettering
v2 = page(
    '<g transform="translate(600 0) scale(.60 1) translate(-600 0)">'
    '<text x="600" y="835" font-family="\'Bodoni 72\', Didot, Georgia, serif" font-weight="700" font-size="660" text-anchor="middle" letter-spacing="-8" fill="%s">ALEX</text></g>'
    % BLUE + '<g>%s</g>' % sprig(528, 820, 430, pairs=6, lean=6, stroke="#ffffff", sw=0, fill="#ffffff")
    + '<g>%s</g>' % sprig(528, 820, 430, pairs=6, lean=6, stroke=BLUE, sw=5))

# v3 - watercolour wreath
random.seed(11)
ring = []
for i in range(34):
    a = i / 34 * 360 + random.uniform(-4, 4)
    r = 330 + random.uniform(-14, 14)
    x, y = 600 + r * math.cos(math.radians(a)), 585 + r * math.sin(math.radians(a))
    ring.append(leaf(x, y, a + 90 + random.choice((-38, 38)) + random.uniform(-10, 10), random.uniform(95, 150), random.uniform(24, 36),
                     fill=random.choice((NAVY, BLUE, MID, SKY, SKY, PALE)), stroke="none", sw=0, vein=False, opacity=random.uniform(.55, .85)))
berries = "".join('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" opacity=".7"/>' % (600 + 330*math.cos(math.radians(a)), 585 + 330*math.sin(math.radians(a)), random.uniform(9, 15), random.choice((MID, SKY)))
                  for a in (18, 77, 141, 203, 262, 318))
v3 = page('<g filter="url(#wash)">%s%s</g>'
          '<text x="600" y="640" font-family="Didot, \'Bodoni 72\', Georgia, serif" font-size="178" text-anchor="middle" letter-spacing="26" fill="%s">ALEX</text>'
          '<path d="M455,690 H745" stroke="%s" stroke-width="3" stroke-linecap="round" opacity=".6"/>' % ("".join(ring), berries, NAVY, MID),
          '<filter id="wash" x="-10%" y="-10%" width="120%" height="120%"><feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="3" seed="7"/>'
          '<feDisplacementMap in="SourceGraphic" scale="16"/><feGaussianBlur stdDeviation="1.6"/></filter>')

# v4 - retro badge
rays = "".join('<path d="M600,600 L%.1f,%.1f L%.1f,%.1f Z" fill="%s" opacity=".55"/>' % (600 + 420*math.cos(math.radians(a-4)), 600 + 420*math.sin(math.radians(a-4)),
               600 + 420*math.cos(math.radians(a+4)), 600 + 420*math.sin(math.radians(a+4)), PALE) for a in range(0, 360, 20))
scallop = "".join('<circle cx="%.1f" cy="%.1f" r="26" fill="%s"/>' % (600 + 470*math.cos(math.radians(a)), 600 + 470*math.sin(math.radians(a)), NAVY) for a in range(0, 360, 10))
v4 = page(scallop + '<circle cx="600" cy="600" r="470" fill="%s"/><circle cx="600" cy="600" r="430" fill="#ffffff"/>' % NAVY
          + '<clipPath id="in"><circle cx="600" cy="600" r="430"/></clipPath><g clip-path="url(#in)">%s</g>' % rays
          + '<circle cx="600" cy="600" r="430" fill="none" stroke="%s" stroke-width="6"/><circle cx="600" cy="600" r="400" fill="none" stroke="%s" stroke-width="4" stroke-dasharray="2 16" stroke-linecap="round"/>' % (BLUE, BLUE)
          + '<rect x="205" y="470" width="790" height="260" rx="28" fill="%s"/><rect x="223" y="488" width="754" height="224" rx="18" fill="none" stroke="#ffffff" stroke-width="4"/>' % NAVY
          + '<text x="600" y="682" font-family="\'Avenir Next Condensed\', Futura, \'Arial Narrow\', sans-serif" font-weight="800" font-size="236" text-anchor="middle" letter-spacing="22" fill="#ffffff">ALEX</text>'
          + '<g transform="rotate(-24 600 600)">%s</g><g transform="rotate(24 600 600)">%s</g>' % (sprig(600, 440, 200, pairs=4, stroke=BLUE, sw=6, fill=SKY), sprig(600, 440, 200, pairs=4, stroke=BLUE, sw=6, fill=SKY))
          + '<g transform="rotate(156 600 600)">%s</g><g transform="rotate(204 600 600)">%s</g>' % (sprig(600, 440, 200, pairs=4, stroke=BLUE, sw=6, fill=SKY), sprig(600, 440, 200, pairs=4, stroke=BLUE, sw=6, fill=SKY)))

# v5 - minimal monogram
v5 = page('<circle cx="600" cy="540" r="330" fill="none" stroke="%s" stroke-width="5"/>' % BLUE
          + '<circle cx="600" cy="540" r="306" fill="none" stroke="%s" stroke-width="2"/>' % SKY
          + '<text x="600" y="730" font-family="Didot, \'Bodoni 72\', Georgia, serif" font-size="560" text-anchor="middle" fill="%s">A</text>' % NAVY
          + '<g transform="rotate(38 760 640)">%s</g>' % sprig(760, 700, 250, pairs=5, stroke=BLUE, sw=4)
          + '<text x="600" y="1010" font-family="\'Avenir Next\', Futura, Helvetica, sans-serif" font-weight="500" font-size="76" text-anchor="middle" letter-spacing="58" fill="%s">ALEX</text>' % BLUE)

# v5, second round - the monogram redrawn without the extra initial
v5b = page('<circle cx="600" cy="600" r="400" fill="none" stroke="%s" stroke-width="5"/>' % BLUE
           + '<circle cx="600" cy="600" r="374" fill="none" stroke="%s" stroke-width="2"/>' % SKY
           + '<g transform="rotate(-62 600 600)">%s</g><g transform="rotate(62 600 600)">%s</g>' % (sprig(600, 960, 230, pairs=5, stroke=BLUE, sw=4), sprig(600, 960, 230, pairs=5, stroke=BLUE, sw=4))
           + '<text x="600" y="668" font-family="Didot, \'Bodoni 72\', Georgia, serif" font-size="206" text-anchor="middle" letter-spacing="14" fill="%s">ALEX</text>' % NAVY
           + '<path d="M470,730 H730" stroke="%s" stroke-width="3" stroke-linecap="round"/>' % SKY)

for name, svg in (("v2", v2), ("v3", v3), ("v4", v4), ("v5", v5), ("v5b", v5b)):
    (out / (name + ".svg")).write_text(svg)
print("ok")
