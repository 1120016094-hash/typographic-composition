#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
engine.py — deterministic typographic-composition engine.

Philosophy (from the manual): 法度=代码. Every glyph position is COMPUTED from
constants (page canon + grid), not eyeballed. The same raster it outputs is what
the measurement "eye" (measure.py) inspects, so judgement is render -> measure,
never "by feeling".

Input : a spec dict / JSON (see eval/specs for examples).
Output: <out>.png (high-DPI raster) and <out>.pdf (wrapped), plus a layout dict
        (returned + written to <out>.layout.json) used by the decision log.

This is a v1 body-text + heading engine: CJK body on an integer full-width grid,
inline Latin words, canon-derived margins, kinsoku (oidashi), justification.
Vector output and multi-column flow are roadmap items (see README).
"""
import json, os, sys, math
from PIL import Image, ImageDraw, ImageFont

MM_PT = 2.834645669            # 1 mm in pt
Q_PT  = 0.25 * MM_PT          # 1 Q (=0.25mm) in pt

# characters that may not START a line (oidashi: push previous char down to them)
KINSOKU_NO_START = set("。、，．,!?！？）)』」】〕》’”%‰°·:;：；ゝ々ぁぃぅぇぉっゃゅょゎ")
# characters that may not END a line (push them down to next line)
KINSOKU_NO_END   = set("（(『「【〔《‘“")

def pt(px_or_pt): return px_or_pt

def load_font_map(font_map_path):
    with open(font_map_path, encoding="utf-8") as f:
        fm = json.load(f)
    fm["_dir"] = os.path.dirname(os.path.abspath(font_map_path))
    return fm

def _resolve(role, weight, fm):
    r = fm["roles"][role]
    if "weights" in r and weight in r["weights"]:
        path, idx = r["weights"][weight]
    else:
        path, idx = r["file"], r.get("index", 0)
    if not os.path.isabs(path):
        base = fm.get("_dir", "")
        path = os.path.join(base, path)
    return path, idx

class FontSet:
    """Holds PIL fonts for CJK + Latin at a given pixel size."""
    def __init__(self, fm, size_px, cjk_role="cjk_serif_body", cjk_weight="Regular",
                 latin_role="latin_serif_body", latin_weight="Regular", latin_scale=1.0):
        cpath, cidx = _resolve(cjk_role, cjk_weight, fm)
        self.cjk = ImageFont.truetype(cpath, size_px, index=cidx)
        try:
            lpath, lidx = _resolve(latin_role, latin_weight, fm)
            self.latin = ImageFont.truetype(lpath, max(1,int(round(size_px*latin_scale))), index=lidx)
        except Exception:
            self.latin = self.cjk
        self.size = size_px
        self.cjk_ascent = self.cjk.getmetrics()[0]
        self.latin_ascent = self.latin.getmetrics()[0]

def is_cjk(ch):
    o = ord(ch)
    return (0x3000 <= o <= 0x9FFF) or (0xF900 <= o <= 0xFAFF) or (0xFF00 <= o <= 0xFFEF) \
           or (0x3400 <= o <= 0x4DBF)

def tokenize(text, fonts):
    """Return list of items: ('cjk', ch, advance) or ('latin', word, advance) or ('space', ' ', adv)."""
    items, i, n = [], 0, len(text)
    em = fonts.size
    while i < n:
        ch = text[i]
        if ch == " ":
            items.append(("space", " ", fonts.latin.getlength(" "))); i += 1
        elif is_cjk(ch):
            items.append(("cjk", ch, em)); i += 1            # forced full-width cell
        else:
            j = i
            while j < n and not is_cjk(text[j]) and text[j] != " ":
                j += 1
            word = text[i:j]
            items.append(("latin", word, fonts.latin.getlength(word))); i = j
    return items

def break_lines(items, measure_px, em):
    """Greedy line fill to measure_px with simple kinsoku (oidashi)."""
    lines, cur, w = [], [], 0.0
    for it in items:
        kind, val, adv = it
        if w + adv <= measure_px + 0.01:
            cur.append(it); w += adv
        else:
            # would overflow -> break. kinsoku: don't start new line with NO_START char
            if kind == "cjk" and val in KINSOKU_NO_START and cur:
                cur.append(it); w += adv               # oidashi: allow slight overflow
                lines.append(cur); cur, w = [], 0.0
            else:
                # don't end a line with a NO_END opening bracket: move it down
                if cur and cur[-1][0] == "cjk" and cur[-1][1] in KINSOKU_NO_END:
                    moved = cur.pop()
                    lines.append(cur)
                    cur, w = [moved, it], moved[2] + adv
                else:
                    lines.append(cur); cur, w = [it], adv
    if cur: lines.append(cur)
    return lines

def line_width(line): return sum(it[2] for it in line)

def render(spec, font_map_path, out_base, grid_overlay=False):
    fm = load_font_map(font_map_path)
    dpi   = spec.get("dpi", 300)
    px    = lambda p: p * dpi / 72.0          # pt -> device px

    # ---- page ----
    page = spec.get("page", {"w_mm": 148, "h_mm": 210})   # default A5 book page
    W = px(page["w_mm"] * MM_PT); H = px(page["h_mm"] * MM_PT)

    # ---- base text constants ----
    bt = spec["base_text"]
    fs_pt = bt["size_pt"] if "size_pt" in bt else bt["size_Q"] * Q_PT
    fs = px(fs_pt)
    lead_ratio = bt.get("leading_ratio", 1.75)
    lead = px(bt["leading_pt"]) if "leading_pt" in bt else fs * (lead_ratio - 1.0)
    line_step = fs + lead

    # ---- page canon (Van de Graaf 9-division == the 2:3:4:6 tradition) ----
    canon = spec.get("canon", {"type": "van_de_graaf", "page_side": "recto"})
    if canon.get("type") == "explicit":
        inner = px(canon["inner_mm"]*MM_PT); outer = px(canon["outer_mm"]*MM_PT)
        top   = px(canon["top_mm"]*MM_PT);   bottom= px(canon["bottom_mm"]*MM_PT)
    else:
        inner = W * 1/9; outer = W * 2/9; top = H * 1/9; bottom = H * 2/9
        if canon.get("page_side") == "verso":
            inner, outer = outer, inner
    taw = W - inner - outer
    tah = H - top - bottom

    # ---- snap to integer grid ----
    fonts = FontSet(fm, int(round(fs)),
                    cjk_weight=bt.get("cjk_weight", "Regular"),
                    latin_scale=bt.get("latin_scale", 1.0))
    M = max(1, int(math.floor(taw / fs)))          # measure: chars per line
    taw_snapped = M * fs
    outer += (taw - taw_snapped); taw = taw_snapped     # give slack to outer margin
    Lp = max(1, int(math.floor((tah + lead) / line_step)))   # lines per page
    tah_snapped = Lp * fs + (Lp - 1) * lead
    bottom += (tah - tah_snapped); tah = tah_snapped

    x0, y0 = inner, top

    # ---- layout body ----
    img = Image.new("RGB", (int(round(W)), int(round(H))), "white")
    d = ImageDraw.Draw(img)
    ink = tuple(spec.get("ink_rgb", [20, 18, 16]))

    # optional heading
    cursor_line = 0
    head = spec.get("heading")
    if head:
        hsize = int(round(px((head.get("size_pt") or fs_pt*1.0))))
        hfonts = FontSet(fm, hsize, cjk_weight=head.get("cjk_weight","Regular"))
        hw = sum(tokenize(head["text"], hfonts)[k][2] for k in range(len(tokenize(head["text"], hfonts))))
        hx = x0 + (taw - hw)/2 if head.get("align","center")=="center" else x0
        d.text((hx, y0), head["text"], font=hfonts.cjk, fill=ink)
        cursor_line += head.get("lines_below", 2) + 1

    # paragraphs
    paras = spec["body"] if isinstance(spec["body"], list) else [spec["body"]]
    indent = spec.get("first_line_indent_chars", 2)
    line_i = cursor_line
    overflow = []
    for p_idx, para in enumerate(paras):
        items = tokenize(para, fonts)
        if indent:
            items = [("space", " ", fs*indent)] + items
        lines = break_lines(items, taw, fs)
        for li, line in enumerate(lines):
            if line_i >= Lp:
                overflow.append(para); break
            y = y0 + line_i * line_step
            is_last = (li == len(lines)-1)
            do_justify = spec.get("justify", True) and not is_last
            _draw_line(d, line, x0, y, taw, fs, fonts, ink, justify=do_justify)
            line_i += 1
        line_i += spec.get("para_gap_lines", 0)

    # optional running head / folio
    folio = spec.get("folio")
    if folio:
        ff = FontSet(fm, int(round(px(fs_pt*0.72))))
        fx = x0 + taw - ff.latin.getlength(str(folio))
        d.text((fx, y0 + tah + lead*0.6), str(folio), font=ff.latin, fill=ink)

    if grid_overlay:
        _overlay(d, x0, y0, taw, tah, fs, line_step, Lp, M)

    png = out_base + ".png"; pdf = out_base + ".pdf"
    img.save(png, dpi=(dpi, dpi))
    img.convert("RGB").save(pdf, "PDF", resolution=dpi)

    meta = spec.get("meta", {})
    genre = meta.get("genre","")
    profile = meta.get("profile") or ("verse" if any(k in genre for k in ["诗","verse","poem","歌"]) else "body")
    layout = {
        "profile": profile,
        "page_mm": [page["w_mm"], page["h_mm"]],
        "dpi": dpi,
        "base_text": {"size_pt": round(fs_pt,3), "leading_pt": round(lead/ (dpi/72.0),3),
                       "leading_ratio": round(line_step/fs,4)},
        "canon": canon.get("type","van_de_graaf"),
        "margins_mm": {
            "inner": round(inner/px(MM_PT),2), "top": round(top/px(MM_PT),2),
            "outer": round(outer/px(MM_PT),2), "bottom": round(bottom/px(MM_PT),2)},
        "margin_ratio_in_top_out_bot": _ratio([inner, top, outer, bottom]),
        "measure_chars": M,
        "lines_per_page": Lp,
        "type_area_mm": [round(taw/px(MM_PT),2), round(tah/px(MM_PT),2)],
        "overflow_paragraphs": len(overflow),
        "outputs": {"png": os.path.basename(png), "pdf": os.path.basename(pdf)}
    }
    with open(out_base + ".layout.json", "w", encoding="utf-8") as f:
        json.dump(layout, f, ensure_ascii=False, indent=2)
    return layout

def _draw_line(d, line, x0, y, taw, fs, fonts, ink, justify):
    natural = line_width(line)
    gaps = max(0, len(line) - 1)
    extra = (taw - natural)/gaps if (justify and gaps > 0 and natural < taw) else 0.0
    x = x0
    for it in line:
        kind, val, adv = it
        if kind == "cjk":
            # center glyph in its em cell for a true grid
            gw = fonts.cjk.getlength(val)
            d.text((x + (fs-gw)/2, y), val, font=fonts.cjk, fill=ink)
        elif kind == "latin":
            dy = fonts.cjk_ascent - fonts.latin_ascent   # baseline alignment
            d.text((x, y+dy), val, font=fonts.latin, fill=ink)
        # space draws nothing
        x += adv + extra

def _overlay(d, x0, y0, taw, tah, fs, line_step, Lp, M):
    red = (200, 60, 50)
    d.rectangle([x0, y0, x0+taw, y0+tah], outline=red, width=2)
    for i in range(M+1):
        d.line([x0+i*fs, y0, x0+i*fs, y0+tah], fill=(230,200,195), width=1)
    for j in range(Lp+1):
        yy = y0 + j*line_step
        d.line([x0, yy, x0+taw, yy], fill=(230,200,195), width=1)

def _ratio(vals):
    m = min(vals)
    return ":".join(str(round(v/m,2)) for v in vals)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("out_base")
    ap.add_argument("--fonts", default=os.path.join(os.path.dirname(__file__),
                    "..","assets","fonts","font_map.json"))
    ap.add_argument("--grid", action="store_true")
    a = ap.parse_args()
    with open(a.spec, encoding="utf-8") as f: spec = json.load(f)
    lay = render(spec, a.fonts, a.out_base, grid_overlay=a.grid)
    print(json.dumps(lay, ensure_ascii=False, indent=2))
