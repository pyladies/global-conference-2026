#!/usr/bin/env python3
"""Extract the PyLadiesCon 2026 ornament set from the Figma homepage export.

The design hand-off in design/ is a single flat SVG per comp: every ornament is
a run of sibling <path> nodes in one page-wide coordinate system, with no ids or
groups to select on. This script slices those runs back out by index into
standalone, tightly-cropped files under public/images/brand/, and records each
one's intrinsic size in src/assets/brand/manifest.json.

The files are painted flat black on purpose: components/brand/ornament.astro
applies them as a CSS mask and paints with currentColor, which is what lets one
file serve both themes.

    python3 scripts/extract_brand_assets.py      # run from the repo root

design/ is gitignored, so this only runs with the Figma hand-off checked out
locally. The generated files under public/images/brand/ are committed, so a
normal build never needs it.

The index ranges below are tied to design/02 Homepage - Desktop 1440.svg. If
that export is regenerated they will need to be re-derived; scripts/_svg_bbox.py
prints every top-level node with its bounding box to help with that.
"""
import copy
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _svg_bbox import el_bbox

NS = "http://www.w3.org/2000/svg"
NSB = "{%s}" % NS
ET.register_namespace("", NS)

SRC = "design/02 Homepage — Desktop 1440.svg"
OUT = "public/images/brand"
MANIFEST = "src/assets/brand/manifest.json"
DIMS = {}

root = ET.parse(SRC).getroot()
TOP = list(root)
DEFS = {}
for d in TOP:
    if d.tag == NSB + "defs":
        for c in d:
            DEFS[c.get("id")] = c


def collect(spec):
    """spec: list of ints or (start, end) inclusive ranges -> list of elements."""
    out = []
    for s in spec:
        if isinstance(s, tuple):
            out.extend(TOP[s[0]:s[1] + 1])
        else:
            out.append(TOP[s])
    return out


def unwrap(els):
    """Replace mask elements by their children; drop the masked solid rect."""
    res = []
    for e in els:
        tag = e.tag.replace(NSB, "")
        if tag == "mask":
            res.extend(list(e))
        elif tag == "g" and e.get("mask"):
            continue  # the solid fill rect the mask is applied to
        else:
            res.append(e)
    return res


def recolor(el, color="#000"):
    for n in el.iter():
        if n.get("fill") and n.get("fill") != "none":
            n.set("fill", color)
        if n.get("stroke") and n.get("stroke") != "none":
            n.set("stroke", color)
    return el


def strip_clip(el):
    for n in el.iter():
        n.attrib.pop("clip-path", None)
        n.attrib.pop("mask", None)
    return el


NUM_RE = re.compile(r"-?\d+\.\d+(?:[eE][-+]?\d+)?")


def _round(m, nd=2):
    v = round(float(m.group()), nd)
    if v == int(v):
        return str(int(v))
    return f"{v:g}"


def shrink(el, nd=2):
    """Figma writes 6+ significant digits; 2dp is well under a device pixel at
    the sizes these ornaments render, and roughly halves the markup."""
    for n in el.iter():
        for attr in ("d", "transform"):
            if n.get(attr):
                n.set(attr, NUM_RE.sub(lambda m: _round(m, nd), n.get(attr)))
        # drop no-op attributes Figma emits on every node
        if n.get("fill") == "none" and n.get("stroke") is None:
            n.attrib.pop("fill", None)
    return el


def emit(name, spec, pad=2, color="#000", flip=False, bbox=None,
         extra_attrs=None):
    els = [copy.deepcopy(e) for e in unwrap(collect(spec))]
    els = [shrink(strip_clip(recolor(e, color))) for e in els]

    bb = None
    for e in els:
        b = el_bbox(e)
        if b is None:
            continue
        bb = b if bb is None else (min(bb[0], b[0]), min(bb[1], b[1]),
                                   max(bb[2], b[2]), max(bb[3], b[3]))
    if bbox:
        bb = bbox
    x0, y0, x1, y1 = bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad
    w, h = x1 - x0, y1 - y0

    svg = ET.Element(NSB + "svg", {
        "viewBox": f"{x0:.2f} {y0:.2f} {w:.2f} {h:.2f}",
        "fill": "none",
        "aria-hidden": "true",
    })
    if extra_attrs:
        svg.attrib.update(extra_attrs)
    g = ET.SubElement(svg, NSB + "g")
    if flip:
        g.set("transform", f"translate({x0 + x1:.2f} 0) scale(-1 1)")
    for e in els:
        g.append(e)

    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name + ".svg")
    ET.ElementTree(svg).write(p, encoding="unicode", xml_declaration=False)
    # tidy: drop the redundant ns prefix output & pretty newline
    txt = open(p).read().replace(' xmlns:ns0="%s"' % NS, "").replace("ns0:", "")
    open(p, "w").write(txt + "\n")
    DIMS[name] = [round(w, 2), round(h, 2)]
    print(f"{p:52s} {w:7.1f}x{h:7.1f}  ({len(list(svg.iter())) - 2} nodes)")


# ---------------------------------------------------------------- hero assets
emit("hand-left", [650, 651])
emit("hand-right", [648, 649])
emit("rays-left", [(709, 714)])
emit("rays-right", [(717, 722)])
emit("pyladies-flower", [219])
emit("moon-phases", [735])
emit("moon-crescent", [737])
emit("sun-burst", [736])
emit("star-large", [220])
emit("star-small", [450])

# each hero "star" is a glyph plus a swarm of dots around it — keep them together
emit("constellation-1", [(220, 334)], pad=1)
emit("constellation-2", [(335, 449)], pad=1)
emit("constellation-3", [(450, 548)], pad=1)
emit("constellation-4", [(549, 647)], pad=1)
emit("hero-flourish", [217], pad=1)

# ------------------------------------------------------- section ornaments
EVENT = TOP[211]
EV = list(EVENT)


def emit_sub(name, group, idxs, pad=2, flip=False):
    els = [copy.deepcopy(group[i]) for i in idxs]
    els = [shrink(strip_clip(recolor(e))) for e in els]
    bb = None
    for e in els:
        b = el_bbox(e)
        if b is None:
            continue
        bb = b if bb is None else (min(bb[0], b[0]), min(bb[1], b[1]),
                                   max(bb[2], b[2]), max(bb[3], b[3]))
    x0, y0, x1, y1 = bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad
    svg = ET.Element(NSB + "svg", {
        "viewBox": f"{x0:.2f} {y0:.2f} {x1 - x0:.2f} {y1 - y0:.2f}",
        "fill": "none", "aria-hidden": "true",
    })
    g = ET.SubElement(svg, NSB + "g")
    if flip:
        g.set("transform", f"translate({x0 + x1:.2f} 0) scale(-1 1)")
    for e in els:
        g.append(e)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name + ".svg")
    ET.ElementTree(svg).write(p, encoding="unicode", xml_declaration=False)
    txt = open(p).read().replace(' xmlns:ns0="%s"' % NS, "").replace("ns0:", "")
    open(p, "w").write(txt + "\n")
    DIMS[name] = [round(x1 - x0, 2), round(y1 - y0, 2)]
    print(f"{p:52s} {x1 - x0:7.1f}x{y1 - y0:7.1f}  ({len(els)} nodes)")


emit_sub("flourish", EV, range(1, 58))           # left-facing corner flourish
emit_sub("palm-hand", EV, [453])                  # palm / hamsa above The Event
emit_sub("card-sparkle", EV, [461])               # ✦ detail-card bullet

# organizers laurel ornament + sponsors crystal ball
emit("laurel", [81], pad=2)
emit("crystal-ball", [(9, 60)], pad=2)

# tarot-card corner ornament (from an organizer card)
emit("card-corner", [93], pad=1)

# ---- the whole hero composition as one layer (frame box = 24,26 1392x659) ----
# Everything except the frame stroke, the buttons, the headline copy and navbar.
emit("hero-art", [(217, 702), (709, 737), 741],
     bbox=(24.5, 25.5, 24.5 + 1392, 25.5 + 659), pad=0)

# the ☾ ✦ ☽ rule at the foot of every organizer card
emit("card-moons", [92], pad=1)

# the compact PyLadies flower used as the navbar/footer lockup mark
emit("logo-mark", [748], pad=1)


# intrinsic sizes let the Ornament component set aspect-ratio without parsing SVG
import json
os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
with open(MANIFEST, "w") as f:
    json.dump(dict(sorted(DIMS.items())), f, indent=2)
    f.write("\n")
print(f"\n{MANIFEST}: {len(DIMS)} assets")
