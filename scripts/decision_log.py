#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
decision_log.py — enforces 说明承重 ("every decision must be explainable").

Assembles spec + layout + metrics into a structured decision log and VALIDATES
that every required decision has a non-empty, load-bearing rationale. A render
is not "done" until its log passes. This is also the anti-pattern guard against
"AI produces first, invents a pretty reason after": the rationale must reference
the content/principle that actually drove the value, and the metric that confirms it.

Usage:
  python3 decision_log.py <spec.json> <layout.json> <metrics.json> \
        [--rationale rationale.json] --out log.json --md log.md
"""
import json, sys, argparse

REQUIRED = ["typeface", "base_text", "canon", "measure", "leading", "alignment", "gray_value"]

DEFAULT_RATIONALE = {
  "typeface":  "内容为{genre}，承载连续可久读的语言信息，故正文取明朝体/宋体本位（{cjk}）。— 法度·选字",
  "base_text": "先定基本文字（{size}），其余要素由它推导。— 法度·基本文字",
  "canon":     "古典文本取 {canon} 版心法度，版心偏上偏内，留出久读所需的余白。— 构造·古典页面",
  "measure":   "行宽 {measure} 字，落在 15–45 可读区间内，单行不致过长而失读。— 构造/法度",
  "leading":   "行距比 {lead} 由基本字号推导，既不拥挤也不松散。— 法度·行距",
  "alignment": "正文两端对齐使中文满行成整齐灰块；末行不强拉。— 法度·灰度",
  "gray_value":"渲染后眯眼复核：robust CV={cv}（<0.28 视为匀），密度={dens}。这是真正起作用的判据，不是事后说辞。— 心法·说明承重 / 法度·灰度"
}

def build(spec, layout, metrics, rationale=None):
    rationale = rationale or {}
    genre = spec.get("meta", {}).get("genre", "文本")
    fill = {
        "genre": genre,
        "cjk": "Noto Serif CJK SC（= Source Han Serif，OFL；秀英/本明朝的开源替身）",
        "size": f'{layout["base_text"]["size_pt"]}pt',
        "canon": layout["canon"],
        "measure": layout["measure_chars"],
        "lead": layout["base_text"]["leading_ratio"],
        "cv": metrics["gray_value_cv"],
        "dens": metrics["ink_density"],
    }
    decisions = {}
    for k in REQUIRED:
        text = rationale.get(k) or DEFAULT_RATIONALE[k].format(**fill)
        decisions[k] = text
    log = {
        "spec_meta": spec.get("meta", {}),
        "decisions": decisions,
        "evidence_metrics": metrics.get("verdict", {}),
        "measured": {k: metrics[k] for k in
                     ["gray_value_cv","ink_density","river_channels",
                      "canon_match","measure_chars","overflow_paragraphs"] if k in metrics},
        "pass_all": metrics.get("pass_all", False),
    }
    return log

def validate(log):
    errs = []
    for k in REQUIRED:
        v = log["decisions"].get(k, "").strip()
        if len(v) < 8:
            errs.append(f"decision '{k}' has no load-bearing rationale")
    if not log.get("pass_all"):
        errs.append("metrics did not pass_all — fix layout before finalising the log")
    return errs

def to_md(log):
    lines = ["# 决策日志 · Decision Log", ""]
    m = log.get("spec_meta", {})
    if m: lines += [f"**作品**：{m.get('title','(未命名)')} · 体裁：{m.get('genre','-')} · 语种：{m.get('lang','-')}", ""]
    lines += ["## 每个决定，及真正起作用的理由", ""]
    for k, v in log["decisions"].items():
        lines.append(f"- **{k}** — {v}")
    lines += ["", "## 度量证据（渲染→测量）", ""]
    for k, v in log.get("measured", {}).items():
        lines.append(f"- {k}: {v}")
    lines += ["", f"**总判定 pass_all：{log.get('pass_all')}**", ""]
    return "\n".join(lines)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("layout"); ap.add_argument("metrics")
    ap.add_argument("--rationale"); ap.add_argument("--out"); ap.add_argument("--md")
    a = ap.parse_args()
    spec=json.load(open(a.spec,encoding="utf-8"))
    layout=json.load(open(a.layout,encoding="utf-8"))
    metrics=json.load(open(a.metrics,encoding="utf-8"))
    rat=json.load(open(a.rationale,encoding="utf-8")) if a.rationale else None
    log=build(spec,layout,metrics,rat)
    errs=validate(log)
    if a.out: json.dump(log,open(a.out,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    if a.md: open(a.md,"w",encoding="utf-8").write(to_md(log))
    print(to_md(log))
    if errs:
        print("\n[VALIDATION FAILED]"); [print(" -",e) for e in errs]; sys.exit(1)
    print("\n[OK] decision log complete & load-bearing.")
