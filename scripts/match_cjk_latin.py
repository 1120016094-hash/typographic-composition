#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
match_cjk_latin.py — quantify CJK+Latin optical harmony (字面/重心/灰度匹配).

Shirai's rule: when CJK and Latin sit together, their visual size, weight and
baseline-mass must match; Latin must not look "a size smaller or floating".
Latin set at the same point size as CJK is almost always optically too small,
because Latin cap-height << the CJK em.

This measures, at a given body size:
  - cjk_visual_height : ink height of a dense CJK glyph (as fraction of em)
  - latin_cap, latin_x: cap-height and x-height (as fraction of em)
  - ink ratio         : relative blackness (gray match)
and recommends a `latin_scale` so Latin cap-height lands in a target band
(default 0.66-0.74 of the CJK em — a common harmony range for Mincho+Garamond).

Usage: python3 match_cjk_latin.py [--size 64] [--target 0.70] [--scale S]
Returns JSON; also used by the engine (latin_scale) and the rubric (harmony dim).
"""
import os, json, argparse
import numpy as np
from PIL import Image, ImageFont, ImageDraw

FM = os.path.join(os.path.dirname(__file__),"..","assets","fonts","font_map.json")

def _ink_h(font, ch):
    img = Image.new("L",(int(font.size*4), int(font.size*3)),255)
    d=ImageDraw.Draw(img); d.text((font.size, font.size), ch, font=font, fill=0)
    a=255-np.asarray(img)
    ys=np.where(a.sum(axis=1)>0)[0]
    return (ys[-1]-ys[0]+1) if len(ys) else 0, float(a.mean())

def analyze(size=64, target=0.70, scale=None):
    fm=json.load(open(FM,encoding="utf-8")); base=os.path.dirname(os.path.abspath(FM))
    def res(role,w="Regular"):
        r=fm["roles"][role]
        p,i=(r["weights"][w] if "weights" in r and w in r["weights"] else (r["file"],r.get("index",0)))
        if not os.path.isabs(p): p=os.path.join(base,p)
        return p,i
    cp,ci=res("cjk_serif_body"); lp,li=res("latin_serif_body")
    cjk=ImageFont.truetype(cp,size,index=ci)
    lscale = scale if scale else 1.0
    latin=ImageFont.truetype(lp,int(round(size*lscale)),index=li)
    cjk_h,cjk_ink=_ink_h(cjk,"永")
    cap_h,cap_ink=_ink_h(latin,"H")
    x_h,_=_ink_h(latin,"x")
    em=size
    cjk_vh=cjk_h/em; cap=cap_h/em; xh=x_h/em
    # recommend scale so cap-height hits target*em
    rec_scale = round(target*em/ (cap_h/lscale), 3) if cap_h else 1.0
    out={
      "body_size_px":size,
      "latin_scale_used":round(lscale,3),
      "cjk_visual_height_em":round(cjk_vh,3),
      "latin_cap_height_em":round(cap,3),
      "latin_x_height_em":round(xh,3),
      "cap_over_cjk":round(cap/cjk_vh,3) if cjk_vh else None,
      "ink_ratio_latin_over_cjk":round(cap_ink/cjk_ink,3) if cjk_ink else None,
      "target_cap_em":target,
      "recommended_latin_scale":rec_scale,
      "verdict_harmony": bool(0.66 <= cap <= 0.74)
    }
    return out

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--size",type=int,default=64); ap.add_argument("--target",type=float,default=0.70)
    ap.add_argument("--scale",type=float)
    a=ap.parse_args()
    print(json.dumps(analyze(a.size,a.target,a.scale),ensure_ascii=False,indent=2))
