#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
derive_benchmark.py — turn the ORIGINAL BOOK into a numeric standard.

IMPORTANT (copyright): this script reads YOUR local copy of the book and writes
out only DERIVED NUMBERS (gray-value evenness, ink density, margin ratios) plus
your own-words notes. It never copies the book's page images or annotation text
into the skill. The book stays on your machine; the skill ships only this script
and the resulting benchmarks/book_benchmark.json. Point it at clean single-column
body-text pages (essays/interview), not plates.

Usage:
  python3 derive_benchmark.py /path/to/book.pdf --pages 15,42,43,263,264 \
      --dpi 150 --out ../benchmarks/book_benchmark.json --label "Shirai body pages"
"""
import os, sys, json, argparse, subprocess, tempfile, glob
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import measure as M

def rasterize(pdf, page, dpi, tmp):
    base=os.path.join(tmp, f"p{page}")
    subprocess.run(["pdftoppm","-jpeg","-r",str(dpi),"-f",str(page),"-l",str(page),pdf,base],
                   check=True, stderr=subprocess.DEVNULL)
    fs=sorted(glob.glob(base+"*.jpg"))
    return fs[0] if fs else None

def trim_white(a_inv, thr=0.02):
    rows=np.where(a_inv.mean(axis=1)>thr)[0]; cols=np.where(a_inv.mean(axis=0)>thr)[0]
    if len(rows)==0 or len(cols)==0: return None
    return rows[0],rows[-1]+1,cols[0],cols[-1]+1

def line_pitch(block_inv):
    prof=block_inv.mean(axis=1); prof=prof-prof.mean()
    n=len(prof); ac=np.correlate(prof,prof,mode="full")[n-1:]
    lo,hi=max(6,n//60), n//3
    if hi<=lo: return max(8,n//20)
    k=lo+int(np.argmax(ac[lo:hi]))
    return k

def measure_page(png, dpi, inset=0.20):
    """Measure a clean CENTRAL crop (avoids spine shadow, edges, folio, heading).
    Returns None if the crop isn't plausible body text (density filter)."""
    g=np.asarray(Image.open(png).convert("L")).astype(np.float32)/255.0
    inv=1.0-g
    bb=trim_white(inv)
    if bb is None: return None
    r0,r1,c0,c1=bb
    page=inv[r0:r1,c0:c1]; H,W=page.shape
    # central rectangle, inset on every side
    cr0=int(H*inset); cr1=int(H*(1-inset)); cc0=int(W*inset); cc1=int(W*(1-inset))
    block=page[cr0:cr1, cc0:cc1]
    if block.size==0: return None
    lp=line_pitch(block)
    gv=M.squint_cv(block, lp)
    # density filter: keep only plausible single-column running body text
    if not (0.06 <= gv["ink_density"] <= 0.18):
        return {"_skip":True, "ink_density":gv["ink_density"]}
    if gv["gray_value_cv"] > 0.9:      # figure/diagram contaminated the crop
        return {"_skip":True, "ink_density":gv["ink_density"]}
    return {"gray_value_cv":gv["gray_value_cv"], "ink_density":gv["ink_density"],
            "line_pitch_px":lp}

def agg(vals):
    a=np.array(vals); 
    return {"median":round(float(np.median(a)),4),
            "p25":round(float(np.percentile(a,25)),4),
            "p75":round(float(np.percentile(a,75)),4),
            "min":round(float(a.min()),4),"max":round(float(a.max()),4)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("pdf"); ap.add_argument("--pages",required=True)
    ap.add_argument("--dpi",type=int,default=150); ap.add_argument("--out",required=True)
    ap.add_argument("--label",default="book body pages")
    a=ap.parse_args()
    pages=[int(x) for x in a.pages.split(",") if x.strip()]
    tmp=tempfile.mkdtemp(); rows=[]; skipped=[]
    for p in pages:
        png=rasterize(a.pdf,p,a.dpi,tmp)
        if not png: continue
        r=measure_page(png,a.dpi)
        if r is None: continue
        if r.get("_skip"): skipped.append((p, round(r["ink_density"],3))); continue
        r["_page"]=p; rows.append(r)
    if not rows: print("no measurable body pages"); sys.exit(1)
    cv=[r["gray_value_cv"] for r in rows]; dens=[r["ink_density"] for r in rows]
    bench={
      "_README":"DERIVED NUMERIC STANDARD from the original book. No page images or "
                "annotation text are stored here. Measured on a clean CENTRAL crop of "
                "single-column body pages (spine/edge/folio/heading excluded) and "
                "density-filtered to running body text. gray_value_cv is the primary "
                "transferable target (灰度均匀). Margin/canon ratios are NOT auto-derived "
                "from scans (too noisy); set canon explicitly per design. Re-run "
                "derive_benchmark.py on your local book to extend.",
      "label":a.label,"n_body_pages":len(rows),"dpi":a.dpi,
      "pages_used":[r["_page"] for r in rows],
      "pages_skipped_by_density":skipped,
      "gray_value_cv":agg(cv),
      "ink_density":agg(dens),
      "per_page":[{"page":r["_page"],"gray_value_cv":r["gray_value_cv"],
                   "ink_density":r["ink_density"]} for r in rows],
      "derived_bands":{
        "gray_value_cv_pass": round(float(np.percentile(cv,75)),4),
        "gray_value_cv_shirai": round(float(np.percentile(cv,50)),4),
        "ink_density_lo": round(float(np.percentile(dens,10)),4),
        "ink_density_hi": round(float(np.percentile(dens,90)),4)
      }
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)),exist_ok=True)
    json.dump(bench,open(a.out,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    print(json.dumps(bench,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
