"""Eze portrait — v3: simplified drawing, shorter neck, two eagle feathers.

Reference space is the sketch's 200 x 200 px. Built on eze_trace2's node helpers.
Simplification versus v2:
  * single lens rings (inner rims removed), no eyelid arcs, no nose-bridge lines,
    no nasolabial / cheek creases, no forehead line, no cap sheen mark
  * fewer nodes on the face, ears and cap; corners kept at jaw, chin, cheekbones, nostrils, lip corners
  * shading reduced to five shadow planes + three highlights
  * neck shortened and narrowed (~55 % of head width); the bubble clip hides its lower end
Stroke system: OUT 2.6 for every outer silhouette, FEAT 1.5 for features, DET 0.9 for inner details.
Feathers: elongated eagle-feather silhouettes (shape taken from the supplied photograph):
  narrow quill, widening through the upper vane, softly pointed tip, slight curve, asymmetric vanes,
  dark vane + pale downy base, one fine shaft and a few short diagonal splits.
"""
import math
from eze_trace2 import bez, ellipse

OUT, FEAT, DET = 2.6, 1.5, 0.9

# ---------------------------------------------------------------- contours (fewer nodes)
CROWN = [(56, 88, "c"), (61, 48, "s"), (88, 19, "s"), (124, 15, "s"), (164, 33, "s"), (178, 84, "c")]
BRIM_LOW = [(55, 89, "c"), (92, 73, "s"), (132, 68, "s"), (178, 80, "c")]
BRIM_TOP = [(61, 67, "c"), (104, 56, "s"), (150, 58, "s"), (174, 67, "c")]
FACE = [(57, 92, "c"), (55, 116, "s"), (56, 137, "c"), (63, 166, "c"), (86, 196, "c"), (116, 206, "s"),
        (142, 200, "c"), (160, 180, "c"), (170, 149, "c"), (175, 120, "s"), (176, 98, "c")]
EAR_L = [(56, 106, "c"), (36, 106, "s"), (34, 136, "s"), (57, 154, "c")]
EAR_R = [(176, 106, "c"), (195, 106, "s"), (194, 138, "s"), (172, 151, "c")]
EAR_L_IN = [(47, 120, "s"), (44, 131, "s"), (52, 144, "c")]
EAR_R_IN = [(184, 119, "s"), (188, 131, "s"), (181, 143, "c")]
# neck: narrower (about 55 % of head width) and it only has to reach the bubble edge
NECK_L = [(86, 197, "c"), (85, 222, "s"), (82, 246, "c")]
NECK_R = [(146, 199, "c"), (148, 222, "s"), (152, 246, "c")]
NOSE_BASE = [(95, 150, "c"), (89, 157, "s"), (94, 164, "c"), (102, 162, "c"), (110, 166, "s"), (118, 162, "c"),
             (126, 164, "c"), (131, 157, "s"), (126, 150, "c")]
UPPER_LIP = [(82, 176, "c"), (101, 169, "c"), (110, 172, "c"), (119, 168, "c"), (152, 174, "c")]
MOUTH = [(84, 179, "c"), (116, 182, "s"), (150, 176, "c")]
LOWER_LIP = [(89, 183, "c"), (117, 194, "s"), (146, 181, "c")]
BROW_L = [(64, 96, "c"), (80, 92, "s"), (98, 96, "c"), (80, 94.6, "s")]
BROW_R = [(124, 90, "c"), (142, 86, "s"), (162, 90, "c"), (142, 88.6, "s")]
LENS_L = (81.5, 121.5, 20.5, 21.5)
LENS_R = (142.0, 118.0, 21.9, 23.0)

# ---------------------------------------------------------------- feathers (from the photograph)
def feather(base, angle_deg, L, curve=0.035, skew=1.25):
    """Return (silhouette, fluff, shaft, splits) path strings for one eagle feather.
    angle_deg: tilt from vertical (negative leans to the viewer's left)."""
    a = math.radians(angle_deg)
    ux, uy = math.sin(a), -math.cos(a)          # along the feather, base -> tip
    vx, vy = -uy, ux                            # perpendicular (to the right of travel)
    def P(u, v):                                # u in 0..1 along, v in units of L across
        c = curve * math.sin(math.pi * u)       # gentle natural bow
        return (base[0] + ux * u * L + vx * (v + c) * L, base[1] + uy * u * L + vy * (v + c) * L)
    # half-widths (fraction of L) — narrow quill, widest in the upper third, soft point
    prof = [(0.00, 0.012), (0.14, 0.030), (0.32, 0.055), (0.55, 0.072), (0.76, 0.068), (0.90, 0.042), (0.975, 0.012)]
    left = [P(u, -w) for u, w in prof]
    right = [P(u, w * skew) for u, w in prof][::-1]
    tip = P(1.0, 0.004)
    pts = [(x, y, "s") for x, y in left] + [(tip[0], tip[1], "c")] + [(x, y, "s") for x, y in right]
    pts[0] = (pts[0][0], pts[0][1], "c"); pts[-1] = (pts[-1][0], pts[-1][1], "c")
    silhouette = bez(pts, closed=True, k=0.33)
    # soft downy base: three simple tufts across the lower vane
    fl = [P(0.16, -0.050), P(0.22, -0.070), P(0.27, -0.040), P(0.31, -0.060), P(0.35, 0.010),
          P(0.31, 0.075), P(0.26, 0.050), P(0.21, 0.085), P(0.15, 0.055), P(0.12, 0.0)]
    fluff = bez([(x, y, "s") for x, y in fl], closed=True, k=0.30)
    shaft = bez([(P(0.18, 0)[0], P(0.18, 0)[1], "c"), (P(0.6, 0)[0], P(0.6, 0)[1], "s"),
                 (P(0.95, 0)[0], P(0.95, 0)[1], "c")])
    splits = []
    for u, side in ((0.48, 1), (0.66, 1), (0.58, -1), (0.80, -1)):   # a few short diagonal splits
        w = 0.072 * (skew if side > 0 else 1) * side
        s0, s1 = P(u - 0.01, w * 0.95), P(u + 0.06, w * 0.35)
        splits.append(f"M{s0[0]:.2f} {s0[1]:.2f} L{s1[0]:.2f} {s1[1]:.2f}")
    return silhouette, fluff, shaft, " ".join(splits)

# existing v2 feather length (base 48,98 -> tip 18,-6) = 108 ref px; new pair: 106 and 99 (within 10 %)
FEATHER_FRONT = feather((66, 72), -8, 106)
FEATHER_BACK = feather((60, 80), -17, 99)

def feather_lengths():
    return 106, 99

# ---------------------------------------------------------------- fills and planes
BASES = {
    "skin": bez(FACE[:-1] + [(176, 98, "c"), (178, 82, "c")] + BRIM_LOW[::-1][1:], closed=True),
    "ear-left": bez(EAR_L + [(57, 130, "s")], closed=True),
    "ear-right": bez(EAR_R + [(175, 128, "s")], closed=True),
    "neck": bez([(86, 197, "c"), (85, 222, "s"), (82, 246, "c"), (152, 246, "c"), (148, 222, "s"), (146, 199, "c"),
                 (142, 200, "c"), (116, 206, "s"), (86, 196, "c")], closed=True),
    "cap": bez(CROWN + BRIM_LOW[::-1], closed=True),
    "brim": bez(BRIM_TOP + [(178, 80, "c")] + BRIM_LOW[::-1] + [(57, 78, "c")], closed=True),
}
PLANES = {
    "hl-forehead":    bez([(70, 97, "c"), (98, 87, "s"), (126, 85, "c"), (100, 96, "s")], closed=True),
    "hl-nose-bridge": bez([(105, 127, "c"), (110, 126, "c"), (109, 146, "s"), (106, 152, "c")], closed=True),
    "hl-cheekbone-l": bez([(58, 146, "c"), (72, 142, "c"), (80, 148, "c"), (64, 154, "c")], closed=True),
    "sh-under-cap":   bez([(55, 89, "c"), (92, 73, "s"), (132, 68, "s"), (178, 80, "c"), (176, 97, "c"),
                           (132, 81, "s"), (90, 85, "s"), (58, 96, "c")], closed=True),
    "sh-right-plane": bez([(176, 98, "c"), (175, 120, "s"), (170, 149, "c"), (160, 180, "c"), (142, 200, "c"),
                           (152, 172, "c"), (160, 130, "s"), (171, 104, "c")], closed=True),
    "sh-nose":        bez([(120, 127, "c"), (126, 148, "c"), (124, 152, "c"), (118, 138, "s")], closed=True),
    "sh-under-nose":  bez([(97, 164, "c"), (110, 167, "s"), (125, 164, "c"), (110, 171, "s")], closed=True),
    "sh-chin":        bez([(94, 191, "c"), (117, 197, "s"), (140, 189, "c"), (117, 202, "s")], closed=True),
    "sh-neck":        bez([(86, 203, "c"), (116, 213, "s"), (147, 205, "c"), (148, 216, "c"), (116, 224, "s"), (85, 214, "c")], closed=True),
}

def P_(d, w, fill="none", join="round", miter=None, cap="round"):
    return dict(d=d, w=w, fill=fill, join=join, miter=miter, cap=cap)

GROUPS = {
    "face outline": [P_(bez(FACE), OUT, join="miter", miter=2.2), P_(bez(EAR_L), OUT), P_(bez(EAR_R), OUT),
                     P_(bez(EAR_L_IN), DET), P_(bez(EAR_R_IN), DET), P_(bez(NECK_L), OUT), P_(bez(NECK_R), OUT)],
    "cap": [P_(bez(CROWN), OUT, join="miter", miter=2.2), P_(bez(BRIM_LOW), OUT), P_(bez(BRIM_TOP), DET)],
    "glasses": [P_(ellipse(*LENS_L), FEAT + 0.3), P_(ellipse(*LENS_R), FEAT + 0.3),
                P_(bez([(102.0, 117, "c"), (110, 112.5, "s"), (120.1, 114, "c")]), FEAT),
                P_(bez([(61.0, 117, "c"), (56, 109, "c")]), FEAT),
                P_(bez([(163.9, 113, "c"), (176, 110.5, "c")]), FEAT)],
    "facial features": [
        P_(bez(BROW_L, closed=True), 0, fill="ink"), P_(bez(BROW_R, closed=True), 0, fill="ink"),
        P_(ellipse(81.5, 121.5, 9.6), FEAT), P_(ellipse(81.5, 121.5, 3.6), 0, fill="ink"), P_(ellipse(79.2, 119.0, 1.1), 0, fill="paper"),
        P_(ellipse(142, 117.5, 10.3), FEAT), P_(ellipse(142, 117.5, 3.9), 0, fill="ink"), P_(ellipse(139.6, 114.9, 1.2), 0, fill="paper"),
        P_(bez(NOSE_BASE), FEAT, join="miter", miter=2.2),
        P_(bez(UPPER_LIP), DET, join="miter", miter=2.2), P_(bez(MOUTH), FEAT + 0.4), P_(bez(LOWER_LIP), DET),
    ],
}
ORDER = ["face outline", "cap", "glasses", "facial features"]

def svg_groups(ink="#000000", paper="#FFFFFF"):
    out = []
    for name in ORDER:
        gink = ink.get(name, ink["default"]) if isinstance(ink, dict) else ink
        parts = []
        for p in GROUPS[name]:
            fill = {"ink": gink, "paper": paper}.get(p["fill"], p["fill"])
            st = ""
            if p["w"]:
                ml = f' stroke-miterlimit="{p["miter"]}"' if p["miter"] else ""
                st = f' stroke="{gink}" stroke-width="{p["w"]}" stroke-linecap="{p["cap"]}" stroke-linejoin="{p["join"]}"{ml}'
            parts.append(f'<path d="{p["d"]}" fill="{fill}"{st}/>')
        out.append(f'<g id="{name.replace(" ", "-")}" data-name="{name}">' + "".join(parts) + "</g>")
    return out

def feathers_svg(vane_front, vane_back, base, outline, splits):
    out = []
    for gid, (sil, fluff, shaft, spl), vane in (("feather-back", FEATHER_BACK, vane_back), ("feather-front", FEATHER_FRONT, vane_front)):
        out.append(f'<g id="{gid}" data-name="{gid.replace("-", " ")}">'
                   f'<path id="{gid}-vane" d="{sil}" fill="{vane}" stroke="{outline}" stroke-width="{OUT - 0.6}" stroke-linejoin="round"/>'
                   f'<path id="{gid}-down" d="{fluff}" fill="{base}"/>'
                   f'<path id="{gid}-shaft" d="{shaft}" fill="none" stroke="{base}" stroke-width="{DET}" stroke-linecap="round"/>'
                   f'<path id="{gid}-splits" d="{spl}" fill="none" stroke="{splits}" stroke-width="{DET}" stroke-linecap="round"/></g>')
    return "".join(out)

def node_count(d):
    import re
    return len(re.findall(r"[MCL]", d))
