#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_pipeline.py — one command: spec -> render -> measure -> decision log -> GATE.
This is the loop the SKILL drives. If the gate fails, it tells you to go back to
工序 step 4 (constants) rather than fiddle locally.

  python3 run_pipeline.py <spec.json> <out_base>
"""
import json, os, sys, argparse
sys.path.insert(0, os.path.dirname(__file__))
import engine, measure, decision_log

def run(spec_path, out_base, fonts=None):
    fonts = fonts or os.path.join(os.path.dirname(__file__),"..","assets","fonts","font_map.json")
    spec = json.load(open(spec_path,encoding="utf-8"))
    lay  = engine.render(spec, fonts, out_base)
    met  = measure.measure(out_base+".png", out_base+".layout.json", out_base+".metrics.json")
    log  = decision_log.build(spec, lay, met)
    errs = decision_log.validate(log)
    json.dump(log, open(out_base+".decision.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
    open(out_base+".decision.md","w",encoding="utf-8").write(decision_log.to_md(log))
    gate = met.get("pass_all") and not errs
    # optional: judge against the book's numeric standard (same-lens), if present
    bench_path = os.path.join(os.path.dirname(__file__),"..","benchmarks","book_benchmark.json")
    bench_result = None
    if os.path.exists(bench_path) and met.get("profile","body")=="body":
        try:
            import compare_to_benchmark as C
            bench_result = C.compare(out_base+".png", bench_path)
        except Exception as e:
            bench_result = {"error": str(e)}
    print(json.dumps({"measure_pass": met.get("pass_all"),
                      "log_errors": errs,
                      "GATE": "PASS" if gate else "FAIL",
                      "metrics": met["verdict"],
                      "vs_book": (bench_result.get("PASS_vs_book") if isinstance(bench_result,dict) else None)},
                     ensure_ascii=False, indent=2))
    if bench_result and "PASS_vs_book" in bench_result and not bench_result["PASS_vs_book"]:
        print("[NOTE] 同镜对照未达书内基准：灰度/密度与原书正文页有差距，建议回第4步。")
    if not gate:
        print("\n[GATE FAIL] 回到工序第4步（定常数）重排，勿微调局部。")
        return 1
    print("\n[GATE PASS] 可交付：PDF + 决策日志" + (" + 书内基准对照通过" if (bench_result or {}).get("PASS_vs_book") else "") + "。")
    return 0

if __name__ == "__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("spec"); ap.add_argument("out_base")
    ap.add_argument("--fonts"); a=ap.parse_args()
    sys.exit(run(a.spec, a.out_base, a.fonts))
