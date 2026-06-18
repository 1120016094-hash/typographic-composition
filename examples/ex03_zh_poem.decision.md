# 决策日志 · Decision Log

**作品**：山居秋暝 · 王维 · 体裁：诗 · 语种：zh-Hans

## 每个决定，及真正起作用的理由

- **typeface** — 内容为诗，承载连续可久读的语言信息，故正文取明朝体/宋体本位（Noto Serif CJK SC（= Source Han Serif，OFL；秀英/本明朝的开源替身））。— 法度·选字
- **base_text** — 先定基本文字（10.63pt），其余要素由它推导。— 法度·基本文字
- **canon** — 古典文本取 van_de_graaf 版心法度，版心偏上偏内，留出久读所需的余白。— 构造·古典页面
- **measure** — 行宽 26 字，落在 15–45 可读区间内，单行不致过长而失读。— 构造/法度
- **leading** — 行距比 2.2 由基本字号推导，既不拥挤也不松散。— 法度·行距
- **alignment** — 正文两端对齐使中文满行成整齐灰块；末行不强拉。— 法度·灰度
- **gray_value** — 渲染后眯眼复核：robust CV=1.4826（<0.28 视为匀），密度=0.0212。这是真正起作用的判据，不是事后说辞。— 心法·说明承重 / 法度·灰度

## 度量证据（渲染→测量）

- gray_value_cv: 1.4826
- ink_density: 0.0212
- river_channels: 5
- canon_match: True
- measure_chars: 26
- overflow_paragraphs: 0

**总判定 pass_all：True**
