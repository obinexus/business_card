"""Eze landing illustration — version 2: refined portrait + natural motifs.

1440 x 900 px. Colours are sampled from the supplied skin-tone swatches (skin-palette.json).
Named groups (top-level, in paint order):
  Background            pale page + large pale rounded forms + pale shape behind Eze
  Pebbles               two overlapping clusters near the lower corners (sand / sienna / almond)
  River currents        long Bezier strokes (honey / bronze) that lead toward Eze
  Leaves and bubbles    tapered leaves (amber / umber) on the outer edges + a few conjoined bubbles + small accents
  Eze portrait          refined trace (eze_trace2) with base fills and facial planes
  Text safe area        non-exporting guide (rendered only with --guides)
Optional (for VectorCraft): "Eze portrait v1" (previous trace, kept for comparison) and "Eze reference".
"""
import json, math, os, random, sys, base64
from shapely.geometry import Point
from shapely.ops import unary_union
import eze_trace2 as T2
import eze_trace as T1

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1440, 900
S = 2.9
TX, TY = 1010 - 115 * S, 470 - 130 * S
TEXT = (120, 280, 600, 620)

_p = json.load(open(os.path.join(HERE, "skin-palette.json")))
K = {k.lower().replace(" ", "_"): v for k, v in _p.items()}

# ---------------------------------------------------------------- geometry helpers
def catmull(pts, closed=True, t=1.0):
    n = len(pts); P = lambda i: pts[i % n] if closed else pts[max(0, min(n - 1, i))]
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in (range(n) if closed else range(n - 1)):
        p0, p1, p2, p3 = P(i - 1), P(i), P(i + 1), P(i + 2)
        c1 = (p1[0] + (p2[0] - p0[0]) / 6 * t, p1[1] + (p2[1] - p0[1]) / 6 * t)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6 * t, p2[1] - (p3[1] - p1[1]) / 6 * t)
        d += f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d + (" Z" if closed else "")

def rounded(cx, cy, rx, ry, rot, seed, wobble=0.07, n=10):
    """Irregular but smoothly rounded closed form (pebble / soft blob)."""
    r = random.Random(seed); ph = [r.uniform(0, 6.3) for _ in range(3)]
    a0 = math.radians(rot); pts = []
    for i in range(n):
        a = i / n * 2 * math.pi
        k = 1 + wobble * (math.sin(2 * a + ph[0]) + 0.5 * math.sin(3 * a + ph[1]) + 0.25 * math.sin(4 * a + ph[2]))
        # slightly flattened underside, like a resting pebble
        x, y = rx * k * math.cos(a), ry * k * math.sin(a) * (0.86 if math.sin(a) > 0 else 1.0)
        pts.append((cx + x * math.cos(a0) - y * math.sin(a0), cy + x * math.sin(a0) + y * math.cos(a0)))
    return catmull(pts)

def conjoined(circles, fillet, npts=36):
    u = unary_union([Point(x, y).buffer(r, 64) for x, y, r in circles]).buffer(fillet, 64).buffer(-fillet, 64)
    ring = u.exterior
    pts = [ring.interpolate(i / npts, normalized=True) for i in range(npts)]
    return catmull([(p.x, p.y) for p in pts][::-1])

def leaf(bx, by, length, width, angle, bend=0.12):
    """Tapered leaf: pointed base and tip (corner nodes), curved sides, central vein."""
    a = math.radians(angle); ca, sa = math.cos(a), math.sin(a)
    T = lambda u, v: (bx + u * ca - v * sa, by + u * sa + v * ca)
    L, Wd = length, width
    tip = T(L, L * bend)
    s1a, s1b = T(L * 0.22, -Wd * 0.62), T(L * 0.62, -Wd * 0.55 + L * bend * 0.4)
    s2a, s2b = T(L * 0.62, Wd * 0.48 + L * bend * 0.8), T(L * 0.22, Wd * 0.62)
    body = (f"M{bx:.1f} {by:.1f} C{s1a[0]:.1f} {s1a[1]:.1f} {s1b[0]:.1f} {s1b[1]:.1f} {tip[0]:.1f} {tip[1]:.1f} "
            f"C{s2a[0]:.1f} {s2a[1]:.1f} {s2b[0]:.1f} {s2b[1]:.1f} {bx:.1f} {by:.1f} Z")
    v1, v2, vend = T(L * 0.35, L * bend * 0.15), T(L * 0.7, L * bend * 0.55), T(L * 0.9, L * bend * 0.85)
    stem = T(-L * 0.12, -L * 0.02)
    vein = f"M{stem[0]:.1f} {stem[1]:.1f} L{bx:.1f} {by:.1f} C{v1[0]:.1f} {v1[1]:.1f} {v2[0]:.1f} {v2[1]:.1f} {vend[0]:.1f} {vend[1]:.1f}"
    return body, vein

def circle(cx, cy, r):
    return f"M{cx-r:.1f} {cy:.1f} a{r:.1f} {r:.1f} 0 1 0 {2*r:.1f} 0 a{r:.1f} {r:.1f} 0 1 0 {-2*r:.1f} 0 Z"

def g(id_, body, extra=""):
    return f'<g id="{id_.replace(" ", "-")}" data-name="{id_}"{extra}>{body}</g>'

# ---------------------------------------------------------------- Background
BACKDROP = rounded(1000, 440, 330, 310, -8, 11, wobble=0.05, n=12)
def background():
    parts = [f'<rect id="page" x="0" y="0" width="{W}" height="{H}" fill="{K["pale_ivory"]}"/>',
             f'<path id="pale-form-top-left" d="{rounded(60, 30, 300, 210, -12, 21, 0.06)}" fill="{K["warm_ivory"]}"/>',
             f'<path id="pale-form-bottom-right" d="{rounded(1420, 900, 330, 230, -18, 22, 0.06)}" fill="{K["warm_ivory"]}"/>',
             f'<path id="pale-form-bottom-left" d="{rounded(150, 930, 360, 200, 6, 23, 0.06)}" fill="{K["warm_ivory"]}"/>',
             f'<path id="pale-shape-behind-Eze" d="{BACKDROP}" fill="{K["sand"]}"/>']
    return g("Background", "".join(parts))

# ---------------------------------------------------------------- Pebbles (lower corners, overlapping)
PEBBLES = [
    # bottom-left cluster (sits on the pale form, clear of the text area which ends at y=620)
    ("pebble-bl-1", 150, 820, 92, 58, -10, 1, "sienna"),
    ("pebble-bl-2", 252, 846, 64, 42, 14, 2, "almond"),
    ("pebble-bl-3", 74, 868, 70, 44, 8, 3, "sand"),
    ("pebble-bl-4", 318, 872, 40, 26, -16, 4, "sienna"),
    ("pebble-bl-5", 206, 770, 34, 22, 20, 5, "sand"),
    # bottom-right cluster (right of Eze's neck)
    ("pebble-br-1", 1312, 836, 82, 52, 12, 6, "almond"),
    ("pebble-br-2", 1228, 866, 58, 36, -8, 7, "sienna"),
    ("pebble-br-3", 1396, 790, 52, 34, -24, 8, "sand"),
    ("pebble-br-4", 1350, 900, 70, 40, 4, 9, "sienna"),
]
def pebbles():
    parts = []
    for name, cx, cy, rx, ry, rot, seed, col in PEBBLES:
        # a thin pale-ivory edge keeps overlapping pebbles distinguishable without an outline colour
        parts.append(f'<path id="{name}" d="{rounded(cx, cy, rx * 1.15, ry * 1.15, rot, seed)}" fill="{K[col]}" '
                     f'stroke="{K["pale_ivory"]}" stroke-width="3" stroke-linejoin="round"/>')
    return g("Pebbles", "".join(parts))

# ---------------------------------------------------------------- River currents (lead toward Eze)
CURRENTS = [
    # lower current: from the bottom-left pebbles, under the text area, rising toward Eze's chin/neck
    ("current-lower-main", "honey", 7, [(40, 700), (220, 668), (430, 676), (600, 660), (720, 628), (812, 586)]),
    ("current-lower-companion", "bronze", 3.5, [(130, 724), (330, 704), (520, 712), (660, 688), (770, 652)]),
    # upper current: across the top margin, above the heading area, toward the feather and cap
    ("current-upper-main", "honey", 6, [(-20, 250), (130, 214), (300, 196), (450, 170), (570, 138), (640, 112)]),
    ("current-upper-companion", "bronze", 3, [(60, 270), (220, 240), (380, 226), (520, 202)]),
    # right edge: a short current curling in toward the ear
    ("current-right", "honey", 5, [(1440, 610), (1380, 580), (1320, 532), (1290, 484)]),
]
def currents():
    parts = []
    for name, col, w, pts in CURRENTS:
        parts.append(f'<path id="{name}" d="{catmull(pts, closed=False)}" fill="none" stroke="{K[col]}" '
                     f'stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')
    return g("River currents", "".join(parts))

# ---------------------------------------------------------------- Leaves and bubbles
LEAVES = [
    ("leaf-top-right", 1300, 92, 132, 48, 158, "amber", "umber"),
    ("leaf-top-right-small", 1352, 160, 84, 30, 118, "umber", "amber"),
    ("leaf-left-edge", 22, 470, 110, 40, -38, "umber", "amber"),
    ("leaf-bottom-centre", 690, 862, 104, 38, -28, "amber", "umber"),
]
BUBBLES = [
    ("bubbles-top", conjoined([(560, 94, 30), (602, 78, 20), (628, 102, 12)], 12), "warm_ivory"),
    ("bubbles-lower", conjoined([(470, 770, 34), (522, 750, 22), (552, 776, 13)], 13), "sand"),
    ("bubbles-right", conjoined([(1350, 330, 26), (1330, 372, 17), (1356, 400, 10)], 10), "sand"),
]
ACCENTS = [("accent-1", 1268, 230, 5), ("accent-2", 360, 780, 4.5), ("accent-3", 1418, 690, 5)]
def leaves_bubbles():
    parts = []
    for name, d, col in BUBBLES:
        parts.append(f'<path id="{name}" d="{d}" fill="{K[col]}"/>')
    for name, bx, by, L, Wd, ang, col, vcol in LEAVES:
        body, vein = leaf(bx, by, L, Wd, ang)
        parts.append(f'<g id="{name}"><path d="{body}" fill="{K[col]}"/>'
                     f'<path d="{vein}" fill="none" stroke="{K["warm_ivory"]}" stroke-width="2.2" stroke-linecap="round"/></g>')
    for name, x, y, r in ACCENTS:
        parts.append(f'<path id="{name}" d="{circle(x, y, r)}" fill="{K["espresso"]}"/>')
    return g("Leaves and bubbles", "".join(parts))

# ---------------------------------------------------------------- Eze portrait (refined)
COL = dict(skin=K["almond"], cap=K["amber"], brim=K["umber"], feather=K["warm_ivory"],
           hl=K["honey"], sh=K["espresso"], eyewhite=K["pale_ivory"], catch=K["pale_ivory"],
           ink={"default": K["chocolate"], "facial features": K["chocolate"]})
def portrait(trace=T2, gid="Eze portrait", planes=None, mono=False):
    c = COL if not mono else dict(skin="#FFFFFF", cap="#FFFFFF", brim="#FFFFFF", feather="#FFFFFF", hl=None, sh=None,
                                  eyewhite=None, catch="#FFFFFF", ink="#111111")
    bases = trace.BASES if hasattr(trace, "BASES") else None
    base = []
    for k in ("feather", "neck", "ear-left", "ear-right", "skin", "cap", "brim"):
        col = c["skin"] if k in ("neck", "ear-left", "ear-right", "skin") else c[k]
        base.append(f'<path id="base-{k}" d="{bases[k]}" fill="{col}"/>')
    form = []
    if c.get("hl"):
        for k, d in sorted(trace.PLANES.items(), key=lambda kv: kv[0].startswith("hl")):
            form.append(f'<path id="{k}" d="{d}" fill="{c["hl"] if k.startswith("hl") else c["sh"]}"/>')
        for nm, (x, y, rx, ry) in (("eye-left-white", (81.5, 121.5, 9.6, 9.6)), ("eye-right-white", (142, 117.5, 10.3, 10.3))):
            form.append(f'<path id="{nm}" d="{T2.ellipse(x, y, rx, ry)}" fill="{c["eyewhite"]}"/>')
    lines = "".join(trace.svg_groups(ink=c["ink"], paper=c["catch"]))
    inner = (f'<g id="base-fills">{"".join(base)}</g>' + (f'<g id="facial-planes">{"".join(form)}</g>' if form else "") + lines)
    return g(gid, f'<g transform="translate({TX:.2f} {TY:.2f}) scale({S})">{inner}</g>')

def text_guide():
    x0, y0, x1, y1 = TEXT
    return g("Text safe area", f'<rect id="text-safe-area-guide" x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" '
                               f'fill="none" stroke="#FF00B4" stroke-width="2" stroke-dasharray="10 8"/>')

def build(guides=False, reference=False, before=False, mono=False):
    body = [background(), pebbles(), currents(), leaves_bubbles(), portrait(mono=mono)]
    if before:
        b = portrait_v1()
        body.append(b.replace('<g id="Eze-portrait-v1"', '<g id="Eze-portrait-v1" style="display:none"', 1))
    if guides: body.append(text_guide())
    if reference:
        img = base64.b64encode(open(os.path.join(HERE, "eze.jpg"), "rb").read()).decode()
        body.append(g("Eze reference", f'<image x="{TX:.2f}" y="{TY:.2f}" width="{200*S:.1f}" height="{200*S:.1f}" '
                                        f'xlink:href="data:image/jpeg;base64,{img}" opacity="0.55"/>'))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}">\n<title>Eze — landing illustration v2 (natural motifs)</title>\n' + "\n".join(body) + "\n</svg>\n")

def portrait_v1():
    """The previous colour portrait (eze_trace v1), built exactly as compose.py did, for before/after."""
    import compose
    svg = compose.build("colour", with_reference=False)
    start = svg.index('<g id="Eze"'); depth = 0; i = start
    while True:
        o = svg.find("<g", i + 1); cl = svg.find("</g>", i + 1)
        if o != -1 and o < cl: depth += 1; i = o
        else:
            if depth == 0: end = cl + 4; break
            depth -= 1; i = cl
    return svg[start:end].replace('<g id="Eze"', '<g id="Eze-portrait-v1" data-name="Eze portrait v1"', 1)

if __name__ == "__main__":
    open(os.path.join(HERE, "eze-landing-v2-src.svg"), "w").write(build(guides=True, reference=True, before=True))
    open(os.path.join(HERE, "eze-landing-v2-clean.svg"), "w").write(build())
    open(os.path.join(HERE, "eze-landing-v2-guides.svg"), "w").write(build(guides=True))
    print("ok")
