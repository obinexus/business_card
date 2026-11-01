"""Eze landing-page illustration — 1440 x 900 px artboard.

Layers (top-level groups, marked as layers for VectorCraft/Inkscape):
  Eze reference  — the supplied sketch, embedded raster, locked + hidden on export
  Background     — conjoined bubbles, blobs, squiggles, small circles (each its own path)
  Midground      — pale backdrop blob + the traced Eze portrait in named groups
  Foreground     — reserved space for heading and call-to-action (empty placeholder)

Run:  python3 compose.py mono   -> eze-landing.svg
      python3 compose.py colour -> eze-landing-colour.svg   (skin-tone palette, see PALETTES)
"""
import base64, math, random, sys, os
from shapely.geometry import Point
from shapely.ops import unary_union
import eze_trace as T

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1440, 900
# portrait placement: reference px -> artboard px
S = 2.9
TX, TY = 1010 - 115 * S, 470 - 130 * S
HEADING = (120, 280, 600, 620)          # reserved for heading + CTA (x0, y0, x1, y1)

# ---------------------------------------------------------------- curve helpers
def catmull(pts, closed=True, tension=1.0):
    """Smooth cubic Bezier path through points (Catmull-Rom -> Bezier)."""
    n = len(pts)
    P = lambda i: pts[i % n] if closed else pts[max(0, min(n - 1, i))]
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0, p1, p2, p3 = P(i - 1), P(i), P(i + 1), P(i + 2)
        c1 = (p1[0] + (p2[0] - p0[0]) / 6 * tension, p1[1] + (p2[1] - p0[1]) / 6 * tension)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6 * tension, p2[1] - (p3[1] - p1[1]) / 6 * tension)
        d += f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d + (" Z" if closed else "")

def conjoined(circles, fillet, npts=36):
    """Overlapping circles merged into one smooth droplet silhouette."""
    u = unary_union([Point(x, y).buffer(r, 64) for x, y, r in circles])
    u = u.buffer(fillet, 64).buffer(-fillet, 64)          # round the necks between bubbles
    ring = u.exterior
    pts = [ring.interpolate(i / npts, normalized=True) for i in range(npts)]
    return catmull([(p.x, p.y) for p in pts][::-1])

def blob(cx, cy, r, seed, lobes=7, wobble=0.18):
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, 6.28) for _ in range(3)]
    pts = []
    for i in range(lobes * 2):
        a = i / (lobes * 2) * 2 * math.pi
        k = 1 + wobble * (math.sin(2 * a + ph[0]) * 0.6 + math.sin(3 * a + ph[1]) * 0.3 + math.sin(5 * a + ph[2]) * 0.1)
        pts.append((cx + r * k * math.cos(a), cy + r * k * math.sin(a) * 0.92))
    return catmull(pts)

def squiggle(points):
    return catmull(points, closed=False)

def wave(x0, y0, length, amp, waves, angle_deg=0, n=None):
    n = n or int(waves * 6) + 1
    a = math.radians(angle_deg); pts = []
    for i in range(n):
        t = i / (n - 1); x = t * length; y = amp * math.sin(t * waves * 2 * math.pi)
        pts.append((x0 + x * math.cos(a) - y * math.sin(a), y0 + x * math.sin(a) + y * math.cos(a)))
    return squiggle(pts)

def loop(x0, y0, size, angle_deg=0):
    """A loose single loop: in, around, out."""
    base = [(0, 0), (0.35, -0.15), (0.6, -0.55), (0.45, -0.9), (0.15, -0.75), (0.25, -0.35), (0.65, -0.1), (1.0, -0.2)]
    a = math.radians(angle_deg)
    pts = [(x0 + size * (x * math.cos(a) - y * math.sin(a)), y0 + size * (x * math.sin(a) + y * math.cos(a))) for x, y in base]
    return squiggle(pts)

def circle(cx, cy, r):
    return f"M{cx-r:.1f} {cy:.1f} a{r:.1f} {r:.1f} 0 1 0 {2*r:.1f} 0 a{r:.1f} {r:.1f} 0 1 0 {-2*r:.1f} 0 Z"

# ---------------------------------------------------------------- background elements
# role: 'big' (outer, pale), 'mid' (conjoined / blobs), 'small' (rhythm), 'line' (squiggle), 'accent' (rare dark)
BG = [
    # large, pale blobs near the outer edges, partly off the artboard
    ("blob-top-left",        "big",  blob(70, 40, 230, 1)),
    ("blob-bottom-left",     "big",  blob(110, 900, 250, 2)),
    ("blob-top-right",       "big",  blob(1420, 60, 210, 3)),
    ("blob-bottom-right",    "big",  blob(1400, 860, 230, 4)),
    # conjoined bubbles, mid-size, stepping inward
    ("conjoined-top",        "mid",  conjoined([(540, 118, 56), (608, 96, 38), (650, 134, 24)], 20)),
    ("conjoined-lower-left", "mid",  conjoined([(330, 760, 70), (410, 742, 48), (462, 700, 30)], 24)),
    ("conjoined-right",      "mid",  conjoined([(1330, 430, 56), (1300, 500, 40), (1340, 560, 26)], 20)),
    ("blob-mid-left",        "mid2", blob(250, 180, 70, 7, lobes=5, wobble=0.22)),
    ("blob-lower-centre",    "mid2", blob(680, 820, 58, 8, lobes=5, wobble=0.25)),
    # small supporting circles leading toward Eze
    ("bubble-01", "small", circle(540, 690, 18)), ("bubble-02", "small", circle(600, 650, 12)),
    ("bubble-03", "small", circle(650, 612, 8)),  ("bubble-04", "small", circle(830, 70, 14)),
    ("bubble-05", "small", circle(880, 52, 8)),   ("bubble-06", "small", circle(1280, 300, 16)),
    ("bubble-07", "small", circle(1250, 250, 9)), ("bubble-08", "small", circle(1290, 700, 11)),
    # squiggles: flowing lines that point inward
    ("squiggle-top",         "line", wave(330, 70, 230, 12, 2.5, angle_deg=-6)),
    ("squiggle-loop-low",    "line", loop(500, 840, 110, angle_deg=-12)),
    ("squiggle-right",       "line", wave(1300, 640, 110, 10, 1.5, angle_deg=-60)),
    ("squiggle-left-arc",    "line", squiggle([(60, 560), (95, 520), (90, 470), (130, 440), (165, 455)])),
    # a few dark accents on the outer composition
    ("accent-01", "accent", circle(1372, 238, 6)), ("accent-02", "accent", circle(88, 690, 5)),
    ("accent-squiggle", "accentline", wave(1180, 840, 90, 7, 1.5, angle_deg=-18)),
    ("accent-squiggle-top-left", "accentline", wave(36, 262, 80, 6, 1.5, angle_deg=8)),
    ("accent-03", "accent", circle(1418, 520, 7)),
]

BACKDROP = blob(1000, 440, 330, 11, lobes=6, wobble=0.12)   # pale blob behind the portrait

# portrait base shapes (filled under the linework so Eze reads as a solid figure)
BASES = {
    "skin": ("M58 92 C54 104 54 118 55 132 C56 146 60 160 68 172 C74 182 80 192 88 200 C94 206 104 210 116 210 "
             "C122 211 128 210 134 208 C146 202 156 190 160 178 C164 166 168 154 172 140 C176 126 176 112 174 98 "
             "C175 92 176 87 178 82 C166 72 146 68 124 69 C98 71 74 78 54 89 C55 90 57 91 58 92 Z"),
    "ear-left":  "M52 106 C42 104 32 108 31 120 C30 132 38 142 46 148 C50 152 54 154 58 156 C56 140 55 120 56 106 Z",
    "ear-right": "M176 107 C186 103 196 109 196 121 C196 135 188 145 180 151 C176 153 172 153 170 151 C174 136 176 122 176 107 Z",
    "neck": "M80 196 C80 214 78 240 72 282 L164 282 C157 240 152 214 152 196 C140 206 128 210 116 210 C104 210 90 204 80 196 Z",
    "cap": ("M56 86 C58 62 62 36 72 26 C86 16 104 18 120 15 C140 13 156 22 166 38 C174 52 177 70 177 92 "
            "C176 88 172 84 166 80 C150 70 136 69 124 69 C98 71 74 78 54 89 Z"),
    "brim": "M62 66 C80 58 104 56 128 57 C148 58 164 62 174 70 C176 74 177 78 178 82 C166 72 146 68 124 69 C98 71 74 78 54 89 C56 80 58 72 62 66 Z",
    "feather": None,   # filled from T.GROUPS['feather'][0]
}

# form shading for the colour version: light from the upper left
FORM = {
    # highlights: forehead, nose bridge, upper cheeks
    "hl-forehead":  "M72 98 C86 90 104 86 124 86 C118 92 104 96 92 99 C84 101 77 101 72 98 Z",
    "hl-nose":      "M104 128 C106 126 110 126 112 129 C113 137 112 145 109 150 C106 147 104 139 104 128 Z",
    "hl-cheek-l":   "M60 150 C64 146 72 146 78 149 C74 153 68 156 62 156 C60 154 60 152 60 150 Z",
    "hl-cheek-r":   "M126 146 C129 144 134 144 137 146 C134 148 130 149 127 148 Z",
    # shadows: under cap, under glasses, under nose, chin, right side of face
    "sh-under-cap": "M54 89 C74 78 98 71 124 69 C146 68 166 72 178 82 C176 88 175 92 174 96 C160 84 140 79 120 80 C98 81 74 87 58 95 C57 93 55 91 54 89 Z",
    "sh-glasses-l": "M66 142 C74 148 86 149 96 145 C92 150 84 152 77 151 C71 150 68 147 66 142 Z",
    "sh-glasses-r": "M128 139 C138 145 152 145 162 138 C158 145 150 148 143 148 C136 148 131 145 128 139 Z",
    "sh-nose":      "M96 164 C104 168 114 168 124 164 C122 170 114 172 108 172 C102 172 98 169 96 164 Z",
    "sh-nose-side": "M120 126 C123 134 126 142 128 150 C126 152 123 150 121 146 C120 140 119 132 120 126 Z",
    "sh-right-face":"M174 98 C176 112 176 126 172 140 C168 154 164 166 160 178 C156 190 146 202 134 208 C142 196 150 180 154 166 C158 150 164 128 166 108 C168 102 171 99 174 98 Z",
    "sh-chin":      "M90 199 C100 206 112 209 124 208 C130 207 136 204 140 200 C136 210 124 214 114 213 C102 212 94 207 90 199 Z",
    "sh-neck":      "M84 204 C98 214 134 216 151 204 C152 208 152 212 153 216 C136 222 100 222 82 214 C83 210 83 207 84 204 Z",
}

SKIN = {  # sampled from the supplied swatches (median of label-free patches)
    "warm_ivory": "#FDE7AD", "sienna": "#D49E7A", "honey": "#CF9660", "umber": "#B36644",
    "sand": "#F9D998", "limestone": "#EDC091", "band": "#AE8A60", "golden": "#7F4422",
    "pale_ivory": "#FEE4C3", "beige": "#F2C281", "almond": "#935F37", "espresso": "#5E320F",
    "rose_beige": "#F9D3A0", "amber": "#BB6436", "bronze": "#733F17", "chocolate": "#281608",
}
K = SKIN
PALETTES = {
    "mono": dict(paper="#FFFFFF", big="#F0F0F0", mid="#E3E3E3", mid2="#E9E9E9", small="#D9D9D9", line="#A8A8A8",
                 accent="#4D4D4D", accentline="#4D4D4D", backdrop="#F4F4F4", ink="#111111",
                 skin="#FFFFFF", cap="#FFFFFF", brim="#FFFFFF", feather="#FFFFFF", lens="none",
                 hl=None, sh=None),
    "colour": dict(paper=K["pale_ivory"], big=K["warm_ivory"], mid=K["sienna"], mid2=K["sand"], small=K["honey"],
                   line=K["sienna"], accent=K["espresso"], accentline=K["espresso"], backdrop=K["sand"],
                   ink={"default": K["chocolate"], "shading": K["espresso"], "facial features": K["chocolate"]},
                   skin=K["almond"], cap=K["amber"], brim=K["umber"], feather=K["warm_ivory"], lens="none",
                   hl=K["honey"], sh=K["espresso"], catch=K["pale_ivory"], eyewhite=K["pale_ivory"],
                   override={"blob-bottom-left": K["honey"], "blob-top-left": K["sienna"], "blob-bottom-right": K["sienna"], "blob-top-right": K["sand"], "conjoined-lower-left": K["sand"],
                             "conjoined-right": K["sienna"], "blob-lower-centre": K["honey"], "bubble-02": K["almond"],
                             "bubble-06": K["sienna"], "bubble-04": K["sienna"]}),
}

def layer(id_, body, locked=False, hidden=False):
    attrs = f' id="{id_}" inkscape:groupmode="layer" inkscape:label="{id_.replace("-", " ")}"'
    if locked: attrs += ' sodipodi:insensitive="true"'
    if hidden: attrs += ' style="display:none"'
    return f"<g{attrs}>{body}</g>"

def build(pal, with_reference=True, reference_hidden=False):
    c = PALETTES[pal]
    stroke_bg = lambda role: role in ("line", "accentline")
    bg = []
    for name, role, d in BG:
        col = c.get("override", {}).get(name, c[role])
        if stroke_bg(role):
            w = 5 if role == "line" else 4
            bg.append(f'<path id="{name}" d="{d}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')
        else:
            bg.append(f'<path id="{name}" d="{d}" fill="{col}"/>')
    # midground
    m = [f'<path id="backdrop-blob" d="{BACKDROP}" fill="{c["backdrop"]}"/>']
    base = []
    feather_shape = T.GROUPS["feather"][0]["d"]
    for k, d in (("feather", feather_shape), ("neck", BASES["neck"]), ("ear-left", BASES["ear-left"]), ("ear-right", BASES["ear-right"]),
                 ("skin", BASES["skin"]), ("cap", BASES["cap"]), ("brim", BASES["brim"])):
        col = c.get(k, c["skin"]) if k not in ("neck", "ear-left", "ear-right") else c["skin"]
        base.append(f'<path id="base-{k}" d="{d}" fill="{col}"/>')
    form = []
    if c.get("hl"):
        for k, d in sorted(FORM.items(), key=lambda kv: kv[0].startswith("hl")):
            col = c["hl"] if k.startswith("hl") else c["sh"]
            form.append(f'<path id="{k}" d="{d}" fill="{col}"/>')
        ew = c.get("eyewhite")
        if ew:  # eyes: pale iris surround so the stare stays crisp against the skin
            form.append(f'<path id="eye-left-white" d="{T.circle(81, 121, 9.5, 9.5)}" fill="{ew}"/>')
            form.append(f'<path id="eye-right-white" d="{T.circle(141, 117, 11, 10)}" fill="{ew}"/>')
    lines = "".join(T.svg_groups(ink=c["ink"], paper=c["paper"] if c.get("catch") is None else c["catch"]))
    portrait = (f'<g id="Eze" transform="translate({TX:.2f} {TY:.2f}) scale({S})">'
                f'<g id="base-fills">{"".join(base)}</g>'
                + (f'<g id="form-light-shadow">{"".join(form)}</g>' if form else "")
                + lines + "</g>")
    m.append(portrait)
    fg = (f'<rect id="reserved-heading-cta" x="{HEADING[0]}" y="{HEADING[1]}" width="{HEADING[2]-HEADING[0]}" '
          f'height="{HEADING[3]-HEADING[1]}" fill="none" stroke="none"/>')
    layers = [f'<rect id="page" x="0" y="0" width="{W}" height="{H}" fill="{c["paper"]}"/>']
    if with_reference:
        img = base64.b64encode(open(os.path.join(HERE, "eze.jpg"), "rb").read()).decode()
        layers.append(layer("Eze-reference", f'<image id="eze-sketch" x="{TX:.2f}" y="{TY:.2f}" width="{200*S:.1f}" height="{200*S:.1f}" '
                                             f'xlink:href="data:image/jpeg;base64,{img}" opacity="0.6"/>', locked=True, hidden=reference_hidden))
    layers += [layer("Background", "".join(bg)), layer("Midground", "".join(m)), layer("Foreground", fg)]
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd" '
            f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n<title>Eze — landing illustration</title>\n'
            + "\n".join(layers) + "\n</svg>\n")

if __name__ == "__main__":
    pal = sys.argv[1] if len(sys.argv) > 1 else "mono"
    name = "eze-landing" + ("" if pal == "mono" else "-" + pal)
    open(os.path.join(HERE, name + "-src.svg"), "w").write(build(pal))                       # with reference layer
    open(os.path.join(HERE, name + "-noref.svg"), "w").write(build(pal, with_reference=False))
    print("wrote", name)
