#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compare_to_benchmark.py — judge our render against the book's NUMERIC standard.

The book pages are scans; our renders are born-digital. Measuring CV on each
directly is NOT comparable (scan noise raises CV). So to use the book as the
standard fairly, we view our render THROUGH THE SAME LENS: downsample to the
benchmark dpi and add mild scan-like blur/noise, then measure with the identical
squint metric, and check against the book-derived band.

This implements the "对照协议": the book stays the ground truth; our work must
look as even, under the same lens, as the master's body pages.

Usage:
  python3 compare_to_benchmark.py <our_render.png> [--bench ../benchmarks/book_benchmark.json]
"""
import os, sys, json, argparse
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import measure as M
from derive_benchmark import line_pitch

def simulate_scan(png, our_dpi, target_dpi, noise=0.015):
    from scipy.ndimage import gaussian_filter, zoom
    g = np.asarray(Image.open(png).convert("L")).astype(np.float32)/255.0
    f = target_dpi/float(our_dpi)
    g = zoom(g, f, order=1)                      # downsample to scan resolution
    g = gaussian_filter(g, sigma=0.6)            # scanner softening
    rng = np.random.default_rng(7)
    g = np.clip(g + rng.normal(0, noise, g.shape), 0, 1)   # scan noise
    return g

def measure_same_lens(png, our_dpi, target_dpi, inset=0.20):
    g = simulate_scan(png, our_dpi, target_dpi)
    inv = 1.0 - g
    H,W = inv.shape
    block = inv[int(H*inset):int(H*(1-inset)), int(W*inset):int(W*(1-inset))]
    lp = line_pitch(block)
    return M.squint_cv(block, lp)

def compare(png, bench_path, our_dpi=None):
    bench = json.load(open(bench_path, encoding="utf-8"))
    tdpi = bench["dpi"]
    # our render dpi: read sibling layout.json if present
    if our_dpi is None:
        lay = png.rsplit(".",1)[0]+".layout.json"
        our_dpi = json.load(open(lay,encoding="utf-8"))["dpi"] if os.path.exists(lay) else 240
    m = measure_same_lens(png, our_dpi, tdpi)
    band = bench["derived_bands"]
    cv = m["gray_value_cv"]; dens = m["ink_density"]
    result = {
      "our_dpi": our_dpi, "benchmark_dpi": tdpi,
      "our_gray_value_cv_same_lens": cv,
      "our_ink_density_same_lens": round(dens,4),
      "book_cv_pass(<=)": band["gray_value_cv_pass"],
      "book_cv_shirai(<=)": band["gray_value_cv_shirai"],
      "book_density_band": [band["ink_density_lo"], band["ink_density_hi"]],
      "verdict": {
        "as_even_as_book": bool(cv <= band["gray_value_cv_pass"]),
        "shirai_grade_evenness": bool(cv <= band["gray_value_cv_shirai"]),
        "density_in_book_band": bool(band["ink_density_lo"]*0.7 <= dens <= band["ink_density_hi"]*1.3)
      }
    }
    result["PASS_vs_book"] = result["verdict"]["as_even_as_book"] and result["verdict"]["density_in_book_band"]
    return result

if __name__ == "__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("png"); ap.add_argument("--bench",
        default=os.path.join(os.path.dirname(__file__),"..","benchmarks","book_benchmark.json"))
    ap.add_argument("--our-dpi", type=int)
    a=ap.parse_args()
    print(json.dumps(compare(a.png, a.bench, a.our_dpi), ensure_ascii=False, indent=2))
