# 02 · 选字决策表（内容 → 字族 → 可用授权替代）

字无好坏，为这份工作选对的字。下表把"内容类型"映射到角色，再由 font_map.json 落到实体文件。

| 内容类型 genre | 正文角色 | 标题角色 | 备注（白井方法） |
|---|---|---|---|
| 论说/随笔/学术 | cjk_serif_body（明朝/宋体） | cjk_serif_body 大字 或 latin_titling | 连续可久读，取静气；中轴或左齐 |
| 文学/小说 | cjk_serif_body | cjk_serif_body | 行距略宽，留呼吸 |
| 诗 | cjk_serif_body | — | 不两端对齐；按句断行，余白即节奏 |
| 画册/作品集 | cjk_sans（黑体）作图注 | cjk_sans / latin_titling | 以图为主，图注为基本文字 |
| 书信/公文 | cjk_serif_body | — | 传统样式，克制 |
| 西文为主 | latin_serif_body | latin_titling | Garamond/Sabon 气质；需补 EB Garamond |
| 双语并置 | cjk_serif_body + latin_serif_body | — | 字面/重心/灰度匹配（见 match 检查） |

## 选字三步
1. 由 genre 查角色；2. 在该角色下用**排除法**试排 2–3 个候选（含 weight），看整页表现而非字样；
3. 若标准化字体"太静谧"抹掉文本温度，可反向"依字体特征推导版式"。所有取舍写入决策日志。

## 警示
- CJK 正文不用 Bold（用 Medium/SemiBold 作强调）。
- 缺 EB Garamond 时，latin_serif_body 退回 DejaVu Serif，**须在日志标注为降级**。
