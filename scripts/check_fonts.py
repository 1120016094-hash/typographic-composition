#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_fonts.py — verify font_map.json points at files that exist on this host."""
import json, os, sys
fm_path = os.path.join(os.path.dirname(__file__),"..","assets","fonts","font_map.json")
fm = json.load(open(fm_path,encoding="utf-8"))
ok=True
base = os.path.dirname(os.path.abspath(fm_path))
for role, r in fm["roles"].items():
    f = r.get("file")
    fpath = f if (f and os.path.isabs(f)) else (os.path.join(base, f) if f else None)
    present = bool(fpath) and os.path.exists(fpath)
    flag = "OK " if present else "MISSING"
    if not present and r.get("status")=="present": ok=False
    gap = "  <-- GAP, user must supply" if r.get("gap") else ""
    print(f"[{flag}] {role:20s} {r.get('substitute', r.get('substitute_preferred','?'))}{gap}")
print("\nGAPS:"); [print(" -",g) for g in fm.get("gaps_summary",[])]
sys.exit(0 if ok else 1)
