from fontTools.pens.boundsPen import BoundsPen
from shapely.geometry import Polygon
from shapely.ops import unary_union
"""OBINexus MMUCO business card — FINAL (from v6 layout).
Front: colour emblem, mailto QR with a 4-module white quiet zone fully inside the 4 mm safe area, email inset,
full motto as one straight line (curved version failed the 100% readability test).
Back: brand group, Eze in the bubble (full chin and both feather tips, only the neck cropped), name,
contact block (email, website, telephone) inset from the safe edges.
---- earlier notes:
Front (emblem side): filled-disc colour emblem, mailto QR + support@obinexus.org, full motto.
Back (contact side): brand group, Eze avatar beside the name, email + website (no telephone).
Logo, QR and email are wrapped in mailto: links (clickable in SVG and PDF).
"""
import os, sys, json, re
from shapely.geometry import box, Point
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "eze"))
import card3 as C3
from card3 import G, PAL, BLACK, W, H, SAFE, BLEED, PT, pebble, leaf, circle, live, outlined
import eze_trace3 as T3, json as _j

MAILTO = "mailto:support@obinexus.org"
G.QR = json.load(open(os.path.join(HERE, "qr-mailto.json"))); G.NQ = len(G.QR)
col = open(os.path.join(HERE, "col", "seal-colour-D.svg")).read()
G.SEAL_BODY = col[col.index("</title>") + 8: col.rindex("</svg>")]
OUT = os.path.join(HERE, "out-arc"); os.makedirs(OUT, exist_ok=True)
QR = 20.5          # Vistaprint guidance: QR at least ~20 x 20 mm
BLEED = 1.5        # Vistaprint UK standard card: 88 x 58 mm with bleed (1.5 mm per side)
link = lambda body: f'<a xlink:href="{MAILTO}" href="{MAILTO}">{body}</a>'

# ---------------------------------------------------------------- front
EMB_D = 38.0
TXT_PT = 9.0      # every small text line on both sides
PITCH = 4.8       # baseline-to-baseline for every two-line group
# standard motif sizes (mm): small / medium / large  (1 : 1.5 : 2)
S_, M_, L_ = 4.0, 6.0, 8.0

def arc_text(line, cx, cy, R, phi, fill, gid, extra=40):
    """Text on a true circular path, centred at compass angle phi (deg, clockwise from 12 o'clock),
    reading clockwise (left to right over the top), glyph tops pointing away from the centre.
    Returns (live <textPath> SVG, outlined SVG, ink polygon, span_deg)."""
    _, tt, upem, gs, order = G.font(line.key)
    sc = line.size * PT / upem; L = line.adv; parts = []; polys = []
    gl = line.glyphs + [(None, L + line.tracking / 1000 * line.size * PT)]
    for (gid_, gx), (_, nx) in zip(gl, gl[1:]):
        adv = nx - gx; mid = gx + adv / 2 - L / 2; th = phi + math.degrees(mid / R)
        pen = SVGPathPen(gs); gs[order[gid_]].draw(pen); d = pen.getCommands()
        if not d: continue
        parts.append(f'<path d="{d}" transform="rotate({th:.3f} {cx:.3f} {cy:.3f}) translate({cx - adv/2:.3f} {cy - R:.3f}) scale({sc:.6f} {-sc:.6f})"/>')
        bp = BoundsPen(gs); gs[order[gid_]].draw(bp)
        if bp.bounds:
            u0, v0, u1, v1 = bp.bounds; pts = []; a = math.radians(th)
            for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1)):
                x, y = cx - adv / 2 + sc * u - cx, cy - R - sc * v - cy
                pts.append((cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))
            polys.append(Polygon(pts))
    span = math.degrees(L / R)
    a0, a1 = math.radians(phi - span / 2 - extra / 2), math.radians(phi + span / 2 + extra / 2)
    P = lambda a: (cx + R * math.sin(a), cy - R * math.cos(a))
    (x0, y0), (x1, y1) = P(a0), P(a1)
    large = 1 if (span + extra) > 180 else 0
    fam = G.FONTS[line.key][0]
    ls = line.tracking / 1000 * line.size * PT
    live = (f'<g id="{gid}"><path id="{gid}-path" d="M{x0:.3f} {y0:.3f} A{R:.3f} {R:.3f} 0 {large} 1 {x1:.3f} {y1:.3f}" fill="none" stroke="none"/>'
            f'<text font-family="{fam}" font-weight="400" font-style="normal" font-size="{line.size*PT:.4f}" letter-spacing="{ls:.4f}" fill="{fill}">'
            f'<textPath xlink:href="#{gid}-path" href="#{gid}-path" startOffset="50%" text-anchor="middle">{G.esc(line.text)}</textPath></text></g>')
    outl = f'<g id="{gid}" fill="{fill}"><title>{G.esc(line.text)}</title>{"".join(parts)}</g>'
    return live, outl, unary_union(polys), span

MOTTO_TXT = "“Spirits of Good and Evil That Bind Us in the Physical World”"
MOTTO_PT, MOTTO_TR = 9.0, 20

def front():
    INSET = 1.5
    # emblem + motto arc (bottom-left -> left -> top -> top-right, i.e. 180 deg centred on 10:30)
    mo = G.Line(MOTTO_TXT, "bubbler", MOTTO_PT, tracking=MOTTO_TR, id="Motto")
    R = mo.adv / math.pi                                      # baseline radius giving an exact 180 deg arc
    ecx = SAFE + INSET + R + mo.ink_t - 0.3                   # outer glyph edge ~1.2 mm inside the safe line
    ecy = SAFE + INSET + R + mo.ink_t - 0.3
    g, ebox, fine = G.emblem(ecx, ecy - EMB_D / 2, EMB_D)
    m_live, m_out, m_ink, m_span = arc_text(mo, ecx, ecy, R, -45, BLACK, "Motto-arc")
    gap = Point(ecx, ecy).buffer(EMB_D / 2, 128).exterior.distance(m_ink) if False else m_ink.distance(Point(ecx, ecy).buffer(EMB_D / 2, 128))
    # QR centre-right, email under it, right edges aligned
    q0 = 4 * (QR / G.NQ)
    qx = W - SAFE - q0 - QR; qy = H / 2 - QR / 2
    q, qb, mod = G.qr(qx, qy, QR); qz = 4 * mod
    em = G.Line(G.EMAIL, "bubbler", TXT_PT, tracking=25, id="Email"); em.fill_ = BLACK
    em.right(qb[2]); em.top(qb[3] + qz + 0.8)
    panel = f'<rect id="QR-quiet-zone" x="{qb[0]-qz:.3f}" y="{qb[1]-qz:.3f}" width="{QR+2*qz:.3f}" height="{QR+2*qz:.3f}" fill="#FFFFFF"/>'
    motifs = FRONT_MOTIFS()
    zones = [("emblem", Point(ecx, ecy).buffer(EMB_D / 2 + 2.5, 64)), ("motto arc", m_ink.buffer(1.5)),
             ("QR+quiet zone", box(qb[0] - qz, qb[1] - qz, qb[2] + qz, qb[3] + qz).buffer(1.0)), (em.text, box(*em.box).buffer(2))]
    items = [link(g), ("arc", m_live, m_out), panel, link(q)]
    mx0, my0, mx1, my1 = m_ink.bounds
    return dict(name="front", items=items, lines=[em], link_lines={"Email": MAILTO}, motifs=motifs, zones=zones,
                safe=[("emblem", ebox), ("motto arc", m_ink.bounds), ("qr + quiet zone", (qb[0] - qz, qb[1] - qz, qb[2] + qz, qb[3] + qz))],
                info=dict(emblem_c=(ecx, ecy), motto_R=R, motto_span=m_span, motto_arc=f"{-45 - m_span/2:.1f}..{-45 + m_span/2:.1f} deg",
                          motto_gap_to_emblem=gap, motto_bounds=m_ink.bounds, qr=qb, qr_centre_y=(qb[1]+qb[3])/2, module=mod, quiet=qz,
                          email_box=em.box, email_right_vs_qr_right=em.box[2]-qb[2]))

def FRONT_MOTIFS():
    # S/M/L = 4/6/8 mm (pebbles, leaves); blobs r = 3/4.5/6 mm. Each crosses the trim so about half shows on the card.
    m = []
    b, v, p = leaf(-1.5, -1.0, M_, 45); m.append(("leaf-M-1", b, p, PAL["teal"], v))
    b, v, p = leaf(46.0, 1.2, L_, 15); m.append(("leaf-L-2", b, p, PAL["terracotta"], v))
    d, p = circle(84.0, 1.5, 3.0); m.append(("blob-S-1", d, p, PAL["mint"], None))
    b, v, p = leaf(86.2, 8.0, S_, 165); m.append(("leaf-S-3", b, p, PAL["ochre"], v))
    d, p = circle(84.5, 54.5, 6.0); m.append(("blob-L-2", d, p, PAL["pale_blue"], None))
    d, p = pebble(63.0, 54.3, M_, 12, 11); m.append(("pebble-M-1", d, p, PAL["pale_sand"], None))
    d, p = pebble(71.0, 55.0, S_, -20, 12); m.append(("pebble-S-1", d, p, PAL["coral"], None))
    d, p = pebble(42.0, 55.0, S_, 25, 13); m.append(("pebble-S-2", d, p, PAL["mint"], None))
    d, p = pebble(1.2, 54.3, M_, -10, 3); m.append(("pebble-M-2", d, p, PAL["mint"], None))
    d, p = pebble(7.2, 55.4, S_, 18, 4); m.append(("pebble-S-3", d, p, PAL["coral"], None))
    return m

# ---------------------------------------------------------------- Eze avatar (v3 portrait, warm palette)
SK = {k.lower().replace(" ", "_"): v for k, v in _j.load(open(os.path.join(HERE, "..", "eze", "skin-palette.json"))).items()}
AV_MARGIN = 7.0
def avatar(cx, cy, d):
    # minimum enclosing circle of feathers + head + chin is centre (96.5, 83.6) r 124.9 ref units;
    # add a margin so both feather tips and the full chin stay visible, only the neck is cut
    s = (d / 2) / (124.9 + AV_MARGIN)
    tx, ty = cx - 96.5 * s, cy - 83.6 * s
    base = "".join(f'<path d="{T3.BASES[k]}" fill="{ {"cap": SK["amber"], "brim": SK["umber"]}.get(k, SK["almond"]) }"/>'
                   for k in ("neck", "ear-left", "ear-right", "skin", "cap", "brim"))
    planes = "".join(f'<path d="{dd}" fill="{SK["honey"] if k.startswith("hl") else SK["espresso"]}"/>' for k, dd in sorted(T3.PLANES.items(), key=lambda kv: kv[0].startswith("hl")))
    planes += "".join(f'<path d="{T3.ellipse(x, y, r)}" fill="{SK["pale_ivory"]}"/>' for x, y, r in ((81.5, 121.5, 9.6), (142, 117.5, 10.3)))
    lines = "".join(T3.svg_groups(ink={"default": SK["chocolate"]}, paper=SK["pale_ivory"]))
    feathers = T3.feathers_svg(vane_front=SK["espresso"], vane_back=SK["chocolate"], base=SK["warm_ivory"], outline=SK["chocolate"], splits=SK["bronze"])
    art = feathers + base + planes + lines
    # print-safe minimum stroke: nothing thinner than 0.1 mm (~0.28 pt) at this scale
    minw = 0.1 / s
    art = re.sub(r'stroke-width="([\d.]+)"', lambda m: f'stroke-width="{max(float(m.group(1)), minw):.2f}"', art)
    r = d / 2
    return (f'<g id="Eze-avatar"><defs><clipPath id="avatar-clip" clipPathUnits="userSpaceOnUse"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath></defs>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{PAL["pale_blue"]}"/>'
            f'<g clip-path="url(#avatar-clip)"><g transform="translate({tx:.3f} {ty:.3f}) scale({s:.5f})">{art}</g></g>'
            f'<circle cx="{cx}" cy="{cy}" r="{r-0.15}" fill="none" stroke="{PAL["slate"]}" stroke-width="0.3"/></g>'), (cx - r, cy - r, cx + r, cy + r), s

# ---------------------------------------------------------------- back
AV_D = 16.0; NAME_PT = 11.0; NAME_R = AV_D / 2 + 1.6          # baseline radius of the circular name
import math
from fontTools.pens.svgPathPen import SVGPathPen
def circular_name(line, cx, cy, R, fill):
    """Name set on the upper arc of a circle, centred over the top, reading left to right.
    Each glyph is a vector path from the supplied Bubbler One font (text-on-path baked to outlines)."""
    _, tt, upem, gs, order = G.font(line.key)
    sc = line.size * PT / upem
    L = line.adv; parts = []
    gl = line.glyphs + [(None, L + line.tracking / 1000 * line.size * PT)]
    for (gid, gx), (_, nx) in zip(gl, gl[1:]):
        adv = nx - gx; mid = gx + adv / 2 - L / 2; th = math.degrees(mid / R)
        pen = SVGPathPen(gs); gs[order[gid]].draw(pen); d = pen.getCommands()
        if d:
            parts.append(f'<path d="{d}" transform="rotate({th:.3f} {cx:.3f} {cy:.3f}) translate({cx - adv/2:.3f} {cy - R:.3f}) scale({sc:.6f} {-sc:.6f})"/>')
    span = math.degrees(L / R)
    return f'<g id="Name-on-circle" fill="{fill}"><title>{G.esc(line.text)}</title>{"".join(parts)}</g>', span


def bottom_arc_text(line, cx, cy, R, fill, gid):
    _, tt, upem, gs, order = G.font(line.key)
    sc = line.size * PT / upem; L = line.adv; parts = []; polys = []
    gl = line.glyphs + [(None, L + line.tracking / 1000 * line.size * PT)]
    for (gid_, gx), (_, nx) in zip(gl, gl[1:]):
        adv = nx - gx; mid = gx + adv / 2 - L / 2; th = math.degrees(mid / R)
        pen = SVGPathPen(gs); gs[order[gid_]].draw(pen); d = pen.getCommands()
        if d:
            bp = BoundsPen(gs); gs[order[gid_]].draw(bp)
            if bp.bounds:
                u0, v0, u1, v1 = bp.bounds
                pts = []
                for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1)):
                    x, y = cx - adv / 2 + sc * u, cy + R - sc * v
                    a = math.radians(-th); dx, dy = x - cx, y - cy
                    pts.append((cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a)))
                polys.append(Polygon(pts))
            parts.append(f'<path d="{d}" transform="rotate({-th:.3f} {cx:.3f} {cy:.3f}) translate({cx - adv/2:.3f} {cy + R:.3f}) scale({sc:.6f} {-sc:.6f})"/>')
    return f'<g id="{gid}" fill="{fill}"><title>{G.esc(line.text)}</title>{"".join(parts)}</g>', math.degrees(L / R), unary_union(polys)

def back():
    INSET = 1.5
    X0 = SAFE + INSET
    o = G.Line("OBINexus", "anton", C3.OBX_PT, tracking=20, id="OBINexus"); o.fill_ = PAL["slate"]
    m = G.Line("MMUCO", "anton", C3.MMUCO_PT, tracking=30, id="MMUCO"); m.fill_ = BLACK
    s = G.Line("Physical OSes", "bubbler", C3.SUB_PT, tracking=20, id="Physical-OSes"); s.fill_ = BLACK
    web = G.Line(G.WEB, "bubbler", TXT_PT, tracking=25, id="Website"); web.fill_ = BLACK
    for l in (o, m, s, web): l.left(X0)
    o.top(SAFE + INSET); m.top(o.bottom + 1.5); s.top(m.bottom + 1.5); web.base(s.oy + PITCH + 1.2)
    # Eze bubble + name on a true circular path over the top
    nm = G.Line(G.NAME, "bubbler", NAME_PT, tracking=NAME_TR, id="Name")
    r_av = AV_D / 2; R = r_av + 2.1
    half = (nm.adv / 2) / R
    reach = max(r_av, (R + nm.ink_t) * math.sin(min(half, math.pi / 2)))
    cx = W - SAFE - INSET - reach
    cy = SAFE + INSET + R + nm.ink_t + 0.6
    av_svg, av_box, av_s = avatar(cx, cy, 2 * r_av)
    n_live, n_out, n_ink, n_span = arc_text(nm, cx, cy, R, 0, BLACK, "Name-arc")
    # phone number in a speech bubble at Eze's lower-left, tail pointing up-right to him
    ph = G.Line(G.PHONE, "bubbler", TXT_PT, tracking=25, id="Phone"); ph.fill_ = BLACK
    padx, pady = 2.6, 1.9
    bw = ph.width + 2 * padx; bh = (ph.ink_t + ph.ink_b) + 2 * pady
    ang = math.radians(238)                                     # Eze's lower-left (about 8 o'clock)
    tip = (cx + (r_av + 0.9) * math.sin(ang), cy - (r_av + 0.9) * math.cos(ang))
    bx1 = tip[0] - 1.2; by1 = H - SAFE - INSET                  # bubble right / bottom
    bx0 = bx1 - bw; by0 = by1 - bh
    ph.left(bx0 + padx); ph.base(by0 + pady + ph.ink_t)
    rr = bh / 2
    t0, t1 = bx1 - rr - 5.2, bx1 - rr - 0.6                     # tail base on the top edge (wedge points up-right)
    bubble = (f'M{bx0+rr:.3f} {by0:.3f} L{t0:.3f} {by0:.3f} L{tip[0]:.3f} {tip[1]:.3f} L{t1:.3f} {by0:.3f} L{bx1-rr:.3f} {by0:.3f} '
              f'A{rr:.3f} {rr:.3f} 0 0 1 {bx1-rr:.3f} {by1:.3f} L{bx0+rr:.3f} {by1:.3f} A{rr:.3f} {rr:.3f} 0 0 1 {bx0+rr:.3f} {by0:.3f} Z')
    bub_svg = f'<path id="Speech-bubble" d="{bubble}" fill="{PAL["cream"]}" stroke="{PAL["slate"]}" stroke-width="0.3" stroke-linejoin="round"/>'
    bub_poly = box(bx0, by0, bx1, by1).union(Polygon([(t0, by0), tip, (t1, by0)]))
    motifs = BACK_MOTIFS()
    lines = [o, m, s, web, ph]
    ring = Point(cx, cy).buffer(r_av, 64).union(n_ink)
    zones = [(l.text, box(*l.box).buffer(2.0)) for l in (o, m, s, web)] + [("avatar + name arc", ring.buffer(1.5)), ("speech bubble", bub_poly.buffer(1.5))]
    safe = [("avatar", av_box), ("name arc", n_ink.bounds), ("speech bubble", bub_poly.bounds)]
    clear_txt = min(ring.distance(box(*l.box)) for l in (o, m, s, web))
    return dict(name="back", items=[av_svg, ("arc", n_live, n_out), bub_svg], lines=lines, link_lines={"Website": "https://www.mmuco.obinexus.org"},
                motifs=motifs, zones=zones, safe=safe,
                info=dict(avatar_d=2 * r_av, avatar_c=(cx, cy), avatar_scale=av_s, name_R=R, name_span=n_span, name_bounds=n_ink.bounds,
                          name_gap_to_bubble=n_ink.distance(Point(cx, cy).buffer(r_av, 128)), text_to_eze=clear_txt,
                          bubble=(bx0, by0, bx1, by1), tail_tip=tip, tip_gap=Point(tip).distance(Point(cx, cy).buffer(r_av, 128)),
                          bubble_to_eze=bub_poly.distance(Point(cx, cy).buffer(r_av, 128))))

def BACK_MOTIFS():
    m = []
    b, v, p = leaf(86.0, -0.5, L_, 140); m.append(("leaf-L-1", b, p, PAL["mint"], v))
    b, v, p = leaf(27.0, -1.0, M_, 30); m.append(("leaf-M-2", b, p, PAL["ochre"], v))
    d, p = pebble(35.5, 0.6, S_, 10, 21); m.append(("pebble-S-1", d, p, PAL["pale_sand"], None))
    b, v, p = leaf(-1.5, 30.0, M_, 20); m.append(("leaf-M-3", b, p, PAL["terracotta"], v))
    d, p = pebble(0.8, 38.5, S_, 70, 22); m.append(("pebble-S-2", d, p, PAL["mint"], None))
    d, p = circle(0.5, 54.5, 4.5); m.append(("blob-M-1", d, p, PAL["pale_blue"], None))
    d, p = pebble(56.0, 54.5, L_, -8, 7); m.append(("pebble-L-1", d, p, PAL["coral"], None))
    d, p = pebble(65.5, 55.0, M_, 18, 8); m.append(("pebble-M-1", d, p, PAL["mint"], None))
    d, p = pebble(50.0, 55.6, S_, 30, 9); m.append(("pebble-S-3", d, p, PAL["teal"], None))
    d, p = circle(84.5, 54.5, 3.0); m.append(("blob-S-2", d, p, PAL["coral"], None))
    b, v, p = leaf(86.5, 33.0, S_, 190); m.append(("leaf-S-4", b, p, PAL["teal"], v))
    return m

AV_D = 36.0; NAME_PT = 11.0; NAME_TR = 30

def write(side):
    def build(outline, bleed, links=True):
        x0, y0, w, h = (-BLEED, -BLEED, W + 2 * BLEED, H + 2 * BLEED) if bleed else (0, 0, W, H)
        mot = []
        for name, d, p, c, vein in side["motifs"]:
            mot.append(f'<path id="{name}" d="{d}" fill="{c}"/>')
            if vein: mot.append(f'<path id="{name}-vein" d="{vein}" fill="none" stroke="{PAL["slate"]}" stroke-width="0.25" stroke-linecap="round"/>')
        txt = "".join((lambda body, u=side["link_lines"].get(l.id): f'<a xlink:href="{u}" href="{u}">{body}</a>' if u and links else body)(outlined(l) if outline else live(l)) for l in side["lines"])
        body = [f'<rect id="Background" x="{-BLEED}" y="{-BLEED}" width="{W+2*BLEED}" height="{H+2*BLEED}" fill="#FFFFFF"/>',
                f'<defs><clipPath id="bleed-clip" clipPathUnits="userSpaceOnUse"><rect x="{-BLEED}" y="{-BLEED}" width="{W+2*BLEED}" height="{H+2*BLEED}"/></clipPath></defs>',
                '<g id="Natural-motifs" clip-path="url(#bleed-clip)">' + "".join(mot) + "</g>"] + [(it[2] if outline else it[1]) if isinstance(it, tuple) else it for it in side["items"]] + ['<g id="Type">' + txt + "</g>"]
        return (f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                f'width="{w:g}mm" height="{h:g}mm" viewBox="{x0:g} {y0:g} {w:g} {h:g}">\n<title>OBINexus MMUCO business card — {side["name"]}</title>\n' + "\n".join(body) + "\n</svg>\n")
    for o in (False, True):
        for b in (False, True):
            open(os.path.join(OUT, side["name"] + ("-outlined" if o else "") + ("-bleed" if b else "") + ".svg"), "w").write(build(o, b))
    # VectorCraft placement source: live text, bleed, no <a> wrappers
    s = build(False, True, links=False)
    s = re.sub(r'<a [^>]*>', '', s).replace('</a>', '')
    open(os.path.join(OUT, "src-" + side["name"] + "-final-bleed.svg"), "w").write(s)
    s = build(True, True, links=False)
    s = re.sub(r'<a [^>]*>', '', s).replace('</a>', '')
    open(os.path.join(OUT, "src-" + side["name"] + "-vistaprint-outlined.svg"), "w").write(s)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        for kv in sys.argv[1:]:
            k, v = kv.split("="); globals()[k] = type(globals()[k])(eval(v))
        OUT = os.path.join(HERE, "out6-" + "-".join(a.replace("=", "") for a in sys.argv[1:])); os.makedirs(OUT, exist_ok=True)
    for s in (front(), back()):
        write(s)
        print(s["name"], "issues:", C3.check(s) or "none", "|", {k: (tuple(round(x, 2) for x in v) if isinstance(v, tuple) else (round(v, 3) if isinstance(v, (int, float)) else v)) for k, v in s["info"].items()})
        for l in s["lines"]:
            print(f"   {l.text:38s} {G.FONTS[l.key][0]:11s} {l.size:6.3f} pt  x {l.box[0]:.2f}-{l.box[2]:.2f}  y {l.box[1]:.2f}-{l.box[3]:.2f}")
