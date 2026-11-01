"""Eze landing illustration — v3 (structure) and v4 (palette.svg background recolour).

python3 compose3.py skin     -> eze-landing-v3-*.svg   (warm skin-tone palette throughout)
python3 compose3.py coolors  -> eze-landing-v4-*.svg   (background recoloured from palette.svg; portrait unchanged)

Geometry is identical in both; only background colours differ.
Motif size system (each motif has exactly three sizes, small : medium : large = 1 : 1.5 : 2):
  rocks     width   70 / 105 / 140 px
  pebbles   width   36 /  54 /  72 px
  leaves    length  60 /  90 / 120 px
  blobs     scale  1.0 / 1.5 / 2.0  x template (three joined circles r 16, 11, 7)
  pale back forms radius 160 / 240 / 320 px
"""
import json, math, os, random, re, sys, base64
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
import eze_trace3 as T3

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1440, 900
TEXT = (120, 280, 600, 620)

# portrait placement: chin (116,206) -> (990,650), scale 2.3
S = 2.3
TX, TY = 990 - 116 * S, 650 - 206 * S
# Eze's bubble (also the clipping mask): rounded ellipse, centre-right
BUB = dict(cx=990, cy=385, rx=335, ry=350)

SKIN = {k.lower().replace(" ", "_"): v for k, v in json.load(open(os.path.join(HERE, "skin-palette.json"))).items()}
COOL = dict(zip(["coral", "cream", "mint", "pale_blue", "slate"],
                [c.upper() for c in re.findall(r'<rect fill="(#[0-9a-fA-F]{6})"', open(os.path.join(HERE, "palette.svg")).read())]))

SIZES = {"rock": (70, 105, 140), "pebble": (36, 54, 72), "leaf": (60, 90, 120), "blob": (1.0, 1.5, 2.0), "form": (160, 240, 320)}
IDX = {"S": 0, "M": 1, "L": 2}

# ---------------------------------------------------------------- geometry helpers
def catmull_pts(pts, closed=True, t=1.0):
    n = len(pts); P = lambda i: pts[i % n] if closed else pts[max(0, min(n - 1, i))]
    segs = []
    for i in (range(n) if closed else range(n - 1)):
        p0, p1, p2, p3 = P(i - 1), P(i), P(i + 1), P(i + 2)
        c1 = (p1[0] + (p2[0] - p0[0]) / 6 * t, p1[1] + (p2[1] - p0[1]) / 6 * t)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6 * t, p2[1] - (p3[1] - p1[1]) / 6 * t)
        segs.append((p1, c1, c2, p2))
    return segs
def segs_d(segs, closed=True):
    d = f"M{segs[0][0][0]:.1f} {segs[0][0][1]:.1f}" + "".join(f" C{a[0]:.1f} {a[1]:.1f} {b[0]:.1f} {b[1]:.1f} {c[0]:.1f} {c[1]:.1f}" for _, a, b, c in segs)
    return d + (" Z" if closed else "")
def segs_poly(segs, n=10):
    pts = []
    for p0, c1, c2, p3 in segs:
        for i in range(n):
            t = i / n; mt = 1 - t
            pts.append((mt**3*p0[0] + 3*mt*mt*t*c1[0] + 3*mt*t*t*c2[0] + t**3*p3[0],
                        mt**3*p0[1] + 3*mt*mt*t*c1[1] + 3*mt*t*t*c2[1] + t**3*p3[1]))
    return pts

def rounded_pts(cx, cy, rx, ry, rot, seed, wobble=0.07, n=9, flat=0.86, facet=0.0):
    r = random.Random(seed); ph = [r.uniform(0, 6.3) for _ in range(3)]
    a0 = math.radians(rot); pts = []
    for i in range(n):
        a = i / n * 2 * math.pi
        k = 1 + wobble * (math.sin(2 * a + ph[0]) + 0.5 * math.sin(3 * a + ph[1]) + 0.25 * math.sin(4 * a + ph[2]))
        k -= facet * (abs(math.sin(2 * a)) ** 3)          # flattens towards facets (rocks)
        x, y = rx * k * math.cos(a), ry * k * math.sin(a) * (flat if math.sin(a) > 0 else 1.0)
        pts.append((cx + x * math.cos(a0) - y * math.sin(a0), cy + x * math.sin(a0) + y * math.cos(a0)))
    return pts

class Shape:
    def __init__(self, name, motif, size, d, poly, colour_role, z, extra=""):
        self.name, self.motif, self.size, self.d, self.poly, self.role, self.z, self.extra = name, motif, size, d, Polygon(poly).buffer(0), colour_role, z, extra

SHAPES = []
def add(name, motif, size, d, poly, role, z, extra=""):
    SHAPES.append(Shape(name, motif, size, d, poly, role, z, extra)); return SHAPES[-1]

def form(name, size, cx, cy, rot, seed):
    r = SIZES["form"][IDX[size]]
    segs = catmull_pts(rounded_pts(cx, cy, r, r * 0.68, rot, seed, 0.05, 10, 0.92))
    return add(name, "form", size, segs_d(segs), segs_poly(segs), "form", 0)

def rock(name, size, cx, cy, rot, seed):
    w = SIZES["rock"][IDX[size]]; rx, ry = w / 2, w / 2 * 0.62
    pts = rounded_pts(cx, cy, rx, ry, rot, seed, 0.05, 8, 0.80, facet=0.10)
    segs = catmull_pts(pts, t=0.8)                      # lower tension = slightly faceted, rock-like
    sh = add(name, "rock", size, segs_d(segs), segs_poly(segs), "rock", 1)
    # shadow shape: lower-right facet (light from upper left), clipped to the rock by construction
    a0 = math.radians(rot)
    sp = [(0.15, 0.30), (0.75, 0.05), (0.92, 0.38), (0.55, 0.78), (0.05, 0.72)]
    spts = [(cx + (u * rx) * math.cos(a0) - (v * ry) * math.sin(a0), cy + (u * rx) * math.sin(a0) + (v * ry) * math.cos(a0)) for u, v in sp]
    ssegs = catmull_pts(spts, t=0.7)
    shadow = Polygon(segs_poly(ssegs)).buffer(0).intersection(sh.poly.buffer(-3))
    if not shadow.is_empty and shadow.geom_type == "Polygon":
        sh.extra = list(shadow.exterior.coords)
    return sh

def pebble(name, size, cx, cy, rot, seed):
    w = SIZES["pebble"][IDX[size]]
    segs = catmull_pts(rounded_pts(cx, cy, w / 2, w / 2 * 0.66, rot, seed, 0.06, 8, 0.85))
    return add(name, "pebble", size, segs_d(segs), segs_poly(segs), "pebble", 2)

def leaf(name, size, bx, by, angle, bend=0.10):
    L = SIZES["leaf"][IDX[size]]; Wd = L * 0.36
    a = math.radians(angle); ca, sa = math.cos(a), math.sin(a)
    T = lambda u, v: (bx + u * ca - v * sa, by + u * sa + v * ca)
    tip = T(L, L * bend)
    c = [T(L * .22, -Wd * .62), T(L * .62, -Wd * .55 + L * bend * .4), T(L * .62, Wd * .48 + L * bend * .8), T(L * .22, Wd * .62)]
    segs = [((bx, by), c[0], c[1], tip), (tip, c[2], c[3], (bx, by))]
    v1, v2, ve = T(L * .35, L * bend * .15), T(L * .7, L * bend * .55), T(L * .88, L * bend * .82)
    vein = f"M{bx:.1f} {by:.1f} C{v1[0]:.1f} {v1[1]:.1f} {v2[0]:.1f} {v2[1]:.1f} {ve[0]:.1f} {ve[1]:.1f}"
    return add(name, "leaf", size, segs_d(segs), segs_poly(segs, 16), "leaf", 3, extra=vein)

def blob(name, size, cx, cy, rot, seed=0):
    s = SIZES["blob"][IDX[size]]; a = math.radians(rot)
    tpl = [(0, 0, 16), (22, -9, 11), (35, 6, 7)]
    circles = [(cx + s * (x * math.cos(a) - y * math.sin(a)), cy + s * (x * math.sin(a) + y * math.cos(a)), s * r) for x, y, r in tpl]
    u = unary_union([Point(x, y).buffer(r, 64) for x, y, r in circles]).buffer(6 * s, 64).buffer(-6 * s, 64)
    ring = u.exterior; pts = [ring.interpolate(i / 26, normalized=True) for i in range(26)]
    segs = catmull_pts([(p.x, p.y) for p in pts][::-1])
    return add(name, "blob", size, segs_d(segs), segs_poly(segs), "blob", 3)

# ---------------------------------------------------------------- layout (hand-placed, deliberately uneven)
# pale back forms — furthest back, spill beyond the bottom corners
form("form-bottom-left", "L", 70, 905, 8, 31)
form("form-bottom-right", "M", 1440, 880, -14, 32)
form("form-top-left", "S", 30, 20, -10, 33)
# rocks — medium-tone anchors near the lower corners
rock("rock-bl-L", "L", 168, 842, -6, 41)
rock("rock-bl-S", "S", 362, 868, 16, 42)
rock("rock-br-M", "M", 1306, 846, 9, 43)
rock("rock-tr-S", "S", 1390, 60, -18, 44)
# pebbles — small overlapping clusters riding on the rocks / spilling past the corners
pebble("pebble-bl-M", "M", 262, 792, 12, 51)
pebble("pebble-bl-S", "S", 300, 760, -20, 52)
pebble("pebble-bl-L", "L", 58, 772, 4, 53)
pebble("pebble-bl-S2", "S", 452, 880, 28, 54)
pebble("pebble-br-L", "L", 1196, 872, -8, 55)
pebble("pebble-br-S", "S", 1250, 798, 22, 56)
pebble("pebble-br-M", "M", 1405, 760, -30, 57)
# leaves — outer edges only, echoing the feathers without competing
leaf("leaf-left-M", "M", 28, 486, -38)
leaf("leaf-top-L", "L", 1412, 196, 202)
leaf("leaf-bottom-S", "S", 560, 840, -28)
leaf("leaf-top-left-S", "S", 196, 96, 24)
leaf("leaf-right-M", "M", 1418, 430, 150)
# conjoined blobs — connectors between motif groups
blob("blob-top-M", "M", 548, 112, -12)
blob("blob-lower-S", "S", 520, 744, 18)
blob("blob-right-L", "L", 1340, 300, 100)

CURVES = [("curve-lower", [(60, 690), (230, 664), (420, 672), (560, 660), (650, 640)], 4),
          ("curve-upper", [(-10, 238), (160, 214), (330, 204), (470, 182), (575, 158)], 3)]

def bubble_d():
    k = 0.5523; c = BUB
    x, y, rx, ry = c["cx"], c["cy"], c["rx"], c["ry"]
    return (f"M{x-rx} {y} C{x-rx} {y-ry*k:.1f} {x-rx*k:.1f} {y-ry} {x} {y-ry} C{x+rx*k:.1f} {y-ry} {x+rx} {y-ry*k:.1f} {x+rx} {y} "
            f"C{x+rx} {y+ry*k:.1f} {x+rx*k:.1f} {y+ry} {x} {y+ry} C{x-rx*k:.1f} {y+ry} {x-rx} {y+ry*k:.1f} {x-rx} {y} Z")

# ---------------------------------------------------------------- checks
def checks():
    bub = Point(BUB["cx"], BUB["cy"]).buffer(1, 128); bub = __import__("shapely.affinity", fromlist=["scale"]).scale(bub, BUB["rx"], BUB["ry"])
    text = Polygon([(TEXT[0], TEXT[1]), (TEXT[2], TEXT[1]), (TEXT[2], TEXT[3]), (TEXT[0], TEXT[3])])
    face = Polygon([(TX + x * S, TY + y * S) for x, y in [(30, 60), (198, 60), (198, 210), (30, 210)]])
    issues = []
    for i, a in enumerate(SHAPES):
        if a.poly.intersects(text): issues.append(f"{a.name} enters text area")
        if a.poly.intersects(face): issues.append(f"{a.name} overlaps face")
        for b in SHAPES[i + 1:]:
            if a.poly.intersects(b.poly):
                inter = a.poly.intersection(b.poly)
                depth = inter.area / max(inter.length, 1) * 2
                if depth < 6: issues.append(f"near-tangent overlap {a.name}/{b.name} (depth {depth:.1f}px)")
            else:
                dist = a.poly.distance(b.poly)
                if dist < 8: issues.append(f"near-tangent gap {a.name}/{b.name} ({dist:.1f}px)")
    return issues, bub

# ---------------------------------------------------------------- colour
def assign_colours(scheme):
    if scheme == "skin":
        K = SKIN
        base = {"form": [K["warm_ivory"]], "rock": [K["limestone"]], "pebble": [K["sand"], K["sienna"], K["almond"]],
                "leaf": [K["amber"], K["umber"]], "blob": [K["sand"], K["warm_ivory"]]}
        return dict(page=K["pale_ivory"], bubble=K["sand"], rock_shadow=K["honey"], vein=K["warm_ivory"], curve=[K["honey"], K["bronze"]],
                    accents=K["espresso"], seq=base, pebble_edge=K["pale_ivory"])
    C = COOL
    base = {"form": [C["mint"], C["mint"], C["pale_blue"]], "rock": [C["pale_blue"]], "pebble": [C["pale_blue"], C["mint"], C["coral"]],
            "leaf": [C["mint"], C["mint"], C["coral"]], "blob": [C["coral"], C["mint"], C["pale_blue"]]}
    return dict(page=C["cream"], bubble=C["pale_blue"], rock_shadow=C["slate"], vein=C["slate"], curve=[C["slate"], C["slate"]],
                accents=C["slate"], seq=base, pebble_edge=C["cream"])

def colour_of(shapes, scheme):
    """Cycle each motif's colours, but never give two overlapping shapes the same fill."""
    pal = assign_colours(scheme); out = {}; counters = {}
    order = sorted(shapes, key=lambda s: (s.z, s.name))
    for s in order:
        opts = pal["seq"][s.motif]; i = counters.get(s.motif, 0)
        for k in range(len(opts)):
            cand = opts[(i + k) % len(opts)]
            clash = any(out.get(o.name) == cand and o.poly.intersects(s.poly.buffer(4)) for o in order if o.name in out)
            if scheme == "coolors" and s.poly.intersects(BUB_POLY.buffer(4)) and cand == pal["bubble"]: clash = True
            if not clash: break
        out[s.name] = cand; counters[s.motif] = (i + k + 1) % len(opts)
    return out, pal

# ---------------------------------------------------------------- SVG
def g(id_, body, extra=""):
    return f'<g id="{id_.replace(" ", "-")}" data-name="{id_}"{extra}>{body}</g>'

def build(scheme, guides=False, reference=False):
    cols, pal = colour_of(SHAPES, scheme)
    by = lambda m: [s for s in SHAPES if s.motif in m]
    def fills(ss, edge=None):
        out = []
        for s in ss:
            st = f' stroke="{edge}" stroke-width="3" stroke-linejoin="round"' if edge else ""
            out.append(f'<path id="{s.name}" d="{s.d}" fill="{cols[s.name]}"{st}/>')
            if s.motif == "rock" and s.extra:
                out.append(f'<path id="{s.name}-shadow" d="M' + " L".join(f"{x:.1f} {y:.1f}" for x, y in s.extra[:-1]) + f' Z" fill="{pal["rock_shadow"]}"/>')
            if s.motif == "leaf":
                out.append(f'<path id="{s.name}-vein" d="{s.extra}" fill="none" stroke="{pal["vein"]}" stroke-width="{1.6 if scheme == "coolors" else 2.2}" stroke-linecap="round"/>')
        return "".join(out)
    bg = f'<rect id="page" x="0" y="0" width="{W}" height="{H}" fill="{pal["page"]}"/>' + fills(by(["form"]))
    rocks = fills(by(["rock"]))
    pebbles = fills(by(["pebble"]), edge=pal["pebble_edge"])
    leaves = fills(sorted(by(["leaf", "blob"]), key=lambda s: s.z))
    curves = "".join(f'<path id="{n}" d="{segs_d(catmull_pts(p, closed=False), closed=False)}" fill="none" stroke="{pal["curve"][i % 2]}" '
                     f'stroke-width="{w}" stroke-linecap="round"/>' for i, (n, p, w) in enumerate(CURVES))
    accents = "".join(f'<circle id="accent-{i+1}" cx="{x}" cy="{y}" r="{r}" fill="{pal["accents"]}"/>' for i, (x, y, r) in enumerate([(1236, 252, 5), (408, 790, 4.5), (1418, 640, 5)]))
    # Eze: bubble, feathers (unclipped, bases tucked behind the cap), clipped head+neck
    K = SKIN
    bubble = f'<path id="eze-bubble" d="{bubble_d()}" fill="{pal["bubble"]}"/>'
    tr = f'transform="translate({TX:.2f} {TY:.2f}) scale({S})"'
    feathers = (f'<g id="feathers" data-name="feathers" {tr}>' +
                T3.feathers_svg(vane_front=K["espresso"], vane_back=K["chocolate"], base=K["warm_ivory"], outline=K["chocolate"], splits=K["bronze"]) + "</g>")
    base = []
    for k in ("neck", "ear-left", "ear-right", "skin", "cap", "brim"):
        col = {"cap": K["amber"], "brim": K["umber"]}.get(k, K["almond"])
        base.append(f'<path id="base-{k}" d="{T3.BASES[k]}" fill="{col}"/>')
    planes = "".join(f'<path id="{k}" d="{d}" fill="{K["honey"] if k.startswith("hl") else K["espresso"]}"/>'
                     for k, d in sorted(T3.PLANES.items(), key=lambda kv: kv[0].startswith("hl")))
    planes += "".join(f'<path id="{n}" d="{T3.ellipse(x, y, r)}" fill="{K["pale_ivory"]}"/>' for n, x, y, r in (("eye-left-white", 81.5, 121.5, 9.6), ("eye-right-white", 142, 117.5, 10.3)))
    lines = "".join(T3.svg_groups(ink={"default": K["chocolate"]}, paper=K["pale_ivory"]))
    head = (f'<g id="head-clipped" data-name="head (clipped by bubble)" clip-path="url(#eze-bubble-clip)">'
            f'<g {tr}><g id="base-fills">{"".join(base)}</g><g id="facial-planes">{planes}</g>{lines}</g></g>')
    defs = f'<defs><clipPath id="eze-bubble-clip" clipPathUnits="userSpaceOnUse"><path d="{bubble_d()}"/></clipPath></defs>'
    body = [defs, g("Background", bg), g("Rocks", rocks), g("Pebbles", pebbles), g("Leaves and bubbles", leaves + accents),
            g("River currents", curves), g("Eze bubble", bubble), g("Eze portrait", feathers + head)]
    if guides:
        x0, y0, x1, y1 = TEXT
        body.append(g("Text safe area", f'<rect id="text-safe-area-guide" x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="none" stroke="#FF00B4" stroke-width="2" stroke-dasharray="10 8"/>'))
    if reference:
        img = base64.b64encode(open(os.path.join(HERE, "eze.jpg"), "rb").read()).decode()
        body.append(g("Eze reference", f'<image x="{TX:.2f}" y="{TY:.2f}" width="{200*S:.1f}" height="{200*S:.1f}" xlink:href="data:image/jpeg;base64,{img}" opacity="0.55"/>'))
    title = "Eze — landing illustration v3" if scheme == "skin" else "Eze — landing illustration v4 (palette.svg background)"
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n<title>{title}</title>\n' + "\n".join(body) + "\n</svg>\n")

issues, BUB_POLY = checks()

if __name__ == "__main__":
    scheme = sys.argv[1] if len(sys.argv) > 1 else "skin"
    v = "v3" if scheme == "skin" else "v4"
    open(os.path.join(HERE, f"eze-landing-{v}-src.svg"), "w").write(build(scheme, guides=True, reference=True))
    open(os.path.join(HERE, f"eze-landing-{v}-clean.svg"), "w").write(build(scheme))
    print(v, "written;", len(SHAPES), "background shapes")
    print("issues:", issues or "none")
    # feather tips inside bubble?
    for nm, (sil, *_r) in (("front", T3.FEATHER_FRONT), ("back", T3.FEATHER_BACK)):
        nums = list(map(float, re.findall(r"-?\d+\.?\d*", sil)))
        pts = [(TX + nums[i] * S, TY + nums[i + 1] * S) for i in range(0, len(nums) - 1, 2)]
        inside = all(BUB_POLY.buffer(-6).contains(Point(p)) for p in pts)
        print(f"feather {nm}: top y {min(p[1] for p in pts):.0f}px, fully inside bubble (6px margin): {inside}")
