---
name: typographic-composition
description: >
  Typeset CJK (and CJK+Latin) book pages to Yoshihisa Shirai's standard. Use when
  asked to lay out / typeset / 排版 body text into a clean, classical, readable page
  or spread (essays, literature, poetry, catalogs, colophons). Drives a deterministic
  render -> measure -> explain loop: the page is COMPUTED from page-canon + grid
  constants, judged by measured gray-value/canon/river metrics (not by feeling), and
  every decision is recorded in a load-bearing decision log. Do NOT use for glyph/
  font *drawing* (this skill sets type, it does not design letterforms).
license: Built on the open manual《排版造型法度》; bundled fonts are OFL only.
---

# Typographic Composition (排版造型) — Skill

## License Notice

All rights reserved. 未经许可不得修改、分发、商用。

A non-designer runs this and gets a clean, restrained,久看-proof page whose every
decision is explainable. It encodes Shirai's method as: **法度→代码**(constants),
**眼与手→渲染后测量**(measure), **说明须承重→强制决策日志**(decision log).

## When to use / not use
- USE: "把这段文字排成一页/对开", book/essay/poem/catalog layout, CJK or CJK+Latin.
- NOT: drawing a typeface's glyphs; pure data viz; slide decks.

## Workflow (= the manual's 工序). Follow in order; do not skip step 2 or 5.
1. **采集意图**（只问必要项）：内容文件、体裁 genre、语种、成品规格（开本/单双面/用途）。
2. **解读**：先慢读内容到能"解读"为止。拦住"立刻出一版"的本能（见 reference/01）。
3. **选字**：按 `reference/02-typeface-selection.md` 由 genre→角色；用 `assets/fonts/font_map.json`
   落到实体字。先跑 `scripts/check_fonts.py` 确认字体在位（缺 EB Garamond 则标注降级）。
4. **定常数**：定基本文字（字号＋行距）→ 由它推导 measure / 版心(canon) / 网格
   （`reference/03`,`04`；预设见 `assets/page-canons`,`assets/grids`）。写出 spec（schema：`schemas/spec.schema.json`）。
5. **跑主循环（一条命令）**：
   `python3 scripts/run_pipeline.py <spec.json> <out_base>`
   它会 渲染→测量→生成并校验决策日志→给出 GATE。
6. **过闸门**：`rubric/shirai-rubric.md` 的闸门 + measure 的 `pass_all`。
   **GATE FAIL → 回到第 4 步重排**（改常数，勿微调局部）。
7. **自检反陷阱**：`reference/06-self-check.md` 的"致 AI 五问"，写入日志。
8. **交付**：`<out_base>.pdf` ＋ `<out_base>.decision.md`。

## Files map (read on demand, don't load all at once)
- 立场/硬约束 → `reference/01-principles.md`
- 选字 → `reference/02-typeface-selection.md` + `assets/fonts/font_map.json`
- 要素常数 → `reference/03-elements-constants.md`
- 网格/版心 → `reference/04-grid.md` + `assets/{page-canons,grids}`
- 花饰/装帧 → `reference/05-ornament-craft.md` + `assets/ornaments`
- 自检 → `reference/06-self-check.md`
- 评分 → `rubric/shirai-rubric.md`
- 引擎/度量/日志 → `scripts/{engine,measure,decision_log,run_pipeline,check_fonts}.py`
- 范例（输入→成品→日志）→ `examples/`  (seed: ex01)
- 评测 → `eval/`

## Hard rules
- 不得跳过测量直接交付；不得用未通过 `decision_log.validate` 的输出。
- CJK 正文不用 Bold；缺字时降级必须在日志标注。
- 每个决定的理由必须是真正起作用的原因，不得事后补。
