#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
measure.py — the measurement "eye".

Turns Shirai's perceptual checks into numbers, so an AI judges by render->measure
instead of "by feeling":

  - gray_value_cv   : evenness of 灰度. Tile the type area, take ink-coverage per
                      tile, report coefficient of variation (std/mean). Lower=evener.
  - ink_density     : overall blackness of the type block (着墨率).
  - rivers          : vertical whitespace channels running down the column.
  - canon_fidelity  : do the actual margins match the intended ratio?
  - measure_chars   : echoed from layout (line length in chars; readability band).

Usage: python3 measure.py <render.png> <render.layout.json> [--out metrics.json]
"""
import json, sys, argparse
import numpy as np
from PIL import Image

def load(png, layout):
    img = np.asarray(Image.open(png).convert("L")).astype(np.float32)/255.0
    with open(layout, encoding="utf-8") as f: lay = json.load(f)
    return img, lay

def type_area_px(img, lay):
    h, w = img.shape
    dpi = lay["dpi"]; mm = dpi/25.4
    mg = lay["margins_mm"]
    # recto assumed: inner=left. (verso would swap; layout records both as in/out)
    left = mg["inner"]*mm; right = w - mg["outer"]*mm
    top = mg["top"]*mm;    bot = h - mg["bottom"]*mm
    return int(left), int(top), int(right), int(bot)

def _ink_bbox(crop, frac=0.25):
    """Bounding box of the actually-set text block (ignores empty page area)."""
    rowp = crop.mean(axis=1); colp = crop.mean(axis=0)
    rt = rowp.max()*frac; ct = colp.max()*frac
    rows = np.where(rowp > rt)[0]; cols = np.where(colp > ct)[0]
    if len(rows)==0 or len(cols)==0: return None
    return rows[0], rows[-1]+1, cols[0], cols[-1]+1

def squint_cv(crop_inv, line_step_px):
    """Shared squint metric: blur to line scale, restrict to text block, robust CV.
    crop_inv: 2D float array with ink=1, paper=0. Returns dict."""
    from scipy.ndimage import gaussian_filter
    sq = gaussian_filter(crop_inv, sigma=max(2.0, line_step_px*0.5))
    bb = _ink_bbox(sq)
    if bb is None:
        return {"ink_density":0.0,"gray_value_cv":0.0,"tile_min":0,"tile_max":0}
    r0,r1,c0,c1 = bb
    block = sq[r0:r1, c0:c1]; raw = crop_inv[r0:r1, c0:c1]
    rows = max(3, int((r1-r0)/(line_step_px*2))); cols = 8
    th, tw = (r1-r0)//rows, (c1-c0)//cols
    covs=[]
    for i in range(rows):
        for j in range(cols):
            tile = block[i*th:(i+1)*th, j*tw:(j+1)*tw]
            if tile.size: covs.append(float(tile.mean()))
    covs=np.array([c for c in covs if c==c])
    if covs.size==0:
        return {"ink_density":round(float(raw.mean()),4),"gray_value_cv":0.0,"tile_min":0,"tile_max":0}
    med=float(np.median(covs)); mad=float(np.median(np.abs(covs-med)))
    rcv=(1.4826*mad/med) if med>1e-6 else 0.0
    return {"ink_density": round(float(raw.mean()),4),
            "gray_value_cv": round(rcv,4),
            "tile_min": round(float(covs.min()),4),
            "tile_max": round(float(covs.max()),4)}

def gray_value(img, box, lay):
    l,t,r,b = box
    crop = 1.0 - img[t:b, l:r]                       # ink=1, paper=0
    dpi = lay["dpi"]
    fs_px = lay["base_text"]["size_pt"]*dpi/72.0
    line_step = fs_px*lay["base_text"].get("leading_ratio",1.8)
    return squint_cv(crop, line_step)

def rivers(img, box):
    l,t,r,b = box
    crop = 1.0 - img[t:b, l:r]
    colink = crop.mean(axis=0)                      # ink per column
    thr = colink.mean()*0.35                        # "near-empty" column
    runs, run = [], 0
    for v in colink:
        if v < thr: run += 1
        else:
            if run: runs.append(run)
            run = 0
    if run: runs.append(run)
    # a river = a wide near-empty channel inside the column (not the inter-line gaps)
    wide = [x for x in runs if x > crop.shape[1]*0.012]
    return {"river_channels": len(wide),
            "widest_river_px": int(max(runs) if runs else 0)}

def canon_fidelity(img, lay):
    """Compare actual ink bbox margins to the recorded intended margins."""
    a = 1.0 - img
    ys, xs = np.where(a > 0.25)
    if len(xs)==0: return {"canon_ratio_actual":"n/a","canon_match":False}
    h,w = img.shape; dpi=lay["dpi"]; mm=dpi/25.4
    inner = xs.min()/mm; outer = (w-1-xs.max())/mm
    top = ys.min()/mm;   bottom = (h-1-ys.max())/mm
    vals = [inner, top, outer, bottom]
    m = min(vals)
    actual = ":".join(str(round(v/m,2)) for v in vals)
    intended = lay.get("margin_ratio_in_top_out_bot","2:3:4:6")
    # tolerance: each ratio component within 25%
    def parse(s): return [float(x) for x in s.split(":")]
    try:
        ia, ii = parse(actual), parse(intended)
        ii = [x/min(ii) for x in ii]
        match = all(abs(a-b)/b < 0.30 for a,b in zip(ia, ii))
    except Exception:
        match = False
    return {"canon_ratio_actual": actual, "canon_ratio_intended": intended,
            "canon_match": bool(match)}

def measure(png, layout_path, out=None):
    img, lay = load(png, layout_path)
    box = type_area_px(img, lay)
    m = {}
    m.update(gray_value(img, box, lay))
    m.update(rivers(img, box))
    m.update(canon_fidelity(img, lay))
    m["measure_chars"] = lay.get("measure_chars")
    m["lines_per_page"] = lay.get("lines_per_page")
    m["overflow_paragraphs"] = lay.get("overflow_paragraphs", 0)
    # --- verdicts (thresholds documented in rubric/shirai-rubric.md) ---
    m["verdict"] = {
        "gray_even":   m["gray_value_cv"] < 0.28,
        "density_ok":  0.05 <= m["ink_density"] <= 0.20,
        "no_rivers":   m["river_channels"] == 0,
        "canon_ok":    m["canon_match"],
        "measure_ok":  (m["measure_chars"] is not None and 15 <= m["measure_chars"] <= 45),
        "no_overflow": m["overflow_paragraphs"] == 0,
    }
    profile = lay.get("profile","body")
    m["profile"] = profile
    if profile == "verse":
        # 诗/留白型：余白即节奏，不以正文灰度均匀为判据
        gate_keys = ["canon_ok","no_overflow"]
    else:
        gate_keys = list(m["verdict"].keys())
    m["pass_all"] = all(m["verdict"][k] for k in gate_keys)
    if out:
        with open(out,"w",encoding="utf-8") as f: json.dump(m,f,ensure_ascii=False,indent=2)
    return m

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("png"); ap.add_argument("layout"); ap.add_argument("--out")
    a = ap.parse_args()
    print(json.dumps(measure(a.png, a.layout, a.out), ensure_ascii=False, indent=2))
