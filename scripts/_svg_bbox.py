#!/usr/bin/env python3
"""Map top-level structure + bounding boxes of a Figma-exported SVG."""
import re, sys, xml.etree.ElementTree as ET

NS = "{http://www.w3.org/2000/svg}"
NUM = re.compile(r"-?\d*\.?\d+(?:[eE][-+]?\d+)?")

def path_bbox(d):
    # crude: all numbers, alternating x,y after command letters. Good enough for grouping.
    toks = re.findall(r"[MmLlHhVvCcSsQqTtAaZz]|-?\d*\.?\d+(?:[eE][-+]?\d+)?", d)
    xs, ys = [], []
    cmd = None
    buf = []
    def flush():
        if not cmd or not buf: return
        c = cmd.upper()
        if c == "H":
            xs.extend(buf)
        elif c == "V":
            ys.extend(buf)
        elif c == "A":
            for i in range(0, len(buf) - 6, 7):
                xs.append(buf[i+5]); ys.append(buf[i+6])
        else:
            for i in range(0, len(buf) - 1, 2):
                xs.append(buf[i]); ys.append(buf[i+1])
    for t in toks:
        if t[0].isalpha():
            flush(); cmd = t; buf = []
        else:
            buf.append(float(t))
    flush()
    if not xs or not ys: return None
    return (min(xs), min(ys), max(xs), max(ys))

def merge(a, b):
    if a is None: return b
    if b is None: return a
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))

def el_bbox(el):
    tag = el.tag.replace(NS, "")
    bb = None
    if tag == "path" and el.get("d"):
        bb = path_bbox(el.get("d"))
    elif tag == "rect":
        try:
            x = float(el.get("x", 0)); y = float(el.get("y", 0))
            w = float(el.get("width", 0)); h = float(el.get("height", 0))
            bb = (x, y, x + w, y + h)
        except (TypeError, ValueError):
            bb = None
    elif tag == "circle":
        try:
            cx = float(el.get("cx", 0)); cy = float(el.get("cy", 0)); r = float(el.get("r", 0))
            bb = (cx - r, cy - r, cx + r, cy + r)
        except (TypeError, ValueError):
            bb = None
    for ch in el:
        bb = merge(bb, el_bbox(ch))
    # apply translate transform
    tr = el.get("transform") or ""
    m = re.match(r"translate\(([-\d.eE]+)[ ,]+([-\d.eE]+)\)", tr.strip())
    if m and bb:
        dx, dy = float(m.group(1)), float(m.group(2))
        bb = (bb[0] + dx, bb[1] + dy, bb[2] + dx, bb[3] + dy)
    return bb

def main(p):
    root = ET.parse(p).getroot()
    print(f"# {p}  viewBox={root.get('viewBox')}")
    for i, el in enumerate(root):
        tag = el.tag.replace(NS, "")
        bb = el_bbox(el)
        n = len(list(el.iter())) - 1
        info = f"[{i:4d}] {tag:10s} kids={n:5d}"
        if bb:
            info += f" bbox=({bb[0]:8.1f},{bb[1]:8.1f})-({bb[2]:8.1f},{bb[3]:8.1f}) w={bb[2]-bb[0]:7.1f} h={bb[3]-bb[1]:7.1f}"
        for a in ("id", "fill", "clip-path", "mask", "transform"):
            if el.get(a): info += f" {a}={el.get(a)[:40]}"
        print(info)

if __name__ == "__main__":
    main(sys.argv[1])
