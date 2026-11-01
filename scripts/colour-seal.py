"""Recolour the OBINexus MMUCO seal with the palette from palette.svg (coolors ffa69e-faf3dd-b8f2e6-aed9e0-5e6472).

Only fill/stroke colours change. No path data, stroke widths, transforms or element order are touched,
so every symbol, proportion and internal space is preserved. Flat colour only: no gradients, filters
or opacity.
"""
import re, sys, os
import xml.etree.ElementTree as ET

PALETTE_SVG = sys.argv[1] if len(sys.argv) > 1 else "palette.svg"
pal = re.findall(r'<rect fill="(#[0-9a-fA-F]{6})"', open(PALETTE_SVG).read())
assert len(pal) == 5, pal
CORAL, CREAM, MINT, PALEBLUE, SLATE = [c.upper() for c in pal]

NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)

def recolour(variant):
    t = ET.parse(os.path.join(os.path.dirname(__file__), "seal.svg")); r = t.getroot()
    g = lambda i: r.find(f".//{{{NS}}}g[@id='{i}']")
    frame = g("Frame").findall(f"{{{NS}}}path")
    outer, inner = frame
    teeth = g("Teeth").findall(f"{{{NS}}}path")
    band = g("Nsibidi band")
    centre = g("Centre motif").findall(f"{{{NS}}}path")
    body, fingers, plinth = centre

    def set_(p, fill=None, stroke=None):
        if fill is not None and p.get("fill") not in (None,):
            p.set("fill", fill)
        elif fill is not None:
            p.set("fill", fill)
        if stroke is not None and p.get("stroke") is not None:
            p.set("stroke", stroke)

    v = VARIANTS[variant]
    # frame: rings stay slate linework; their (previously empty) fills carry the pale areas
    outer.set("stroke", SLATE); outer.set("fill", v["band"])
    inner.set("stroke", SLATE); inner.set("fill", v["disc"])
    for p in teeth: p.set("stroke", v["teeth"])
    for sym in band.findall(f"{{{NS}}}g"):
        name = sym.get("id").split("-")[0]
        for p in sym.findall(f".//{{{NS}}}path"):
            filled = p.get("fill") not in (None, "none")
            if filled:
                p.set("fill", v["glyph_fill"].get(name, SLATE))
                if p.get("stroke"): p.set("stroke", v["glyph_fill"].get(name, SLATE))
            else:
                p.set("stroke", SLATE)
    body.set("stroke", SLATE); body.set("fill", v["body"])
    fingers.set("stroke", SLATE)
    plinth.set("stroke", SLATE); plinth.set("fill", v["plinth"])
    t.getroot().find(f"{{{NS}}}title").text = "OBINexus MMUCO seal — colour (palette ffa69e faf3dd b8f2e6 aed9e0 5e6472)"
    return ET.tostring(r, encoding="unicode")

VARIANTS = {
    "A": dict(band=CREAM, disc=MINT, teeth=CORAL, body=PALEBLUE, plinth=CORAL, glyph_fill={}),
    "B": dict(band=CREAM, disc="#FFFFFF", teeth=SLATE, body=MINT, plinth=PALEBLUE,
              glyph_fill={"voyage": CORAL, "king": CORAL}),
    "C": dict(band=MINT, disc=CREAM, teeth=SLATE, body=PALEBLUE, plinth=CORAL,
              glyph_fill={"voyage": CORAL, "king": CORAL}),
}

if __name__ == "__main__":
    out = sys.argv[2] if len(sys.argv) > 2 else "."
    for k in (sys.argv[3].split(",") if len(sys.argv) > 3 else VARIANTS):
        open(os.path.join(out, f"seal-colour-{k}.svg"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n' + recolour(k))
    print("palette", CORAL, CREAM, MINT, PALEBLUE, SLATE)
