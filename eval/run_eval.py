#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_eval.py — run the pipeline over every eval/spec_*.json and report gates."""
import glob, os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__),"..","scripts"))
import run_pipeline
here=os.path.dirname(__file__); rc=0; rows=[]
for spec in sorted(glob.glob(os.path.join(here,"spec_*.json"))):
    name=os.path.splitext(os.path.basename(spec))[0]
    out=os.path.join(here,"_out",name); os.makedirs(os.path.dirname(out),exist_ok=True)
    code=run_pipeline.run(spec, out)
    rows.append((name, "PASS" if code==0 else "FAIL")); rc|=code
print("\n=== EVAL SUMMARY ==="); [print(f"  {n}: {s}") for n,s in rows]
sys.exit(rc)
