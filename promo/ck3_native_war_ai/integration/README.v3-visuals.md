# V3 画面合同

`src/war_ai_promo/v3_visuals.py` 是独立的 V3 静帧绘制器，不调用旧片的 `teaching_visuals.SHOTS`。调用 `make_v3_frame(row, destination, phase, ledger_path=..., assets=...)`，其中 `phase` 为 0、1、2。每次产出 2560×1440 PNG 和返回的输入、输出 SHA-256 回执；目标文件已存在时拒绝覆盖。现已接入 `visuals.render_visual` 与当前 composer；仅 45 段准确 `S3-*` 输入走此分支，其他稿维持原路径。

绘制器逐段读取 `longform/v3/evidence-visual-ledger.json`。未知段落、镜头号不匹配、来源缺失、或状态为 `unbound` 时直接失败。当前 45 段均已有画面方案，其中 10 段从待拍因果镜头改为明确的原生规则/方法图，并未因此取得缺失的实机因果证据；边界见[逐段证据说明](../longform/v3/evidence-ledger-notes.md)。

实机背景仅支持明确给出的 CASE-R 和 CASE-W 原始抽帧 PNG。调用方必须为每个案例传 `path`、`sha256`、`case_id` 和 `evidence_role="context-only-original-frame"`；文件字节和 2560×1440 尺寸必须匹配。画面上的地图明确标作场景背景。CASE-R 数值晚于录像查询，CASE-W 军团数值由独立原生读回提供；它们均不表示视频帧中同步观察到 AI 决策。战斗和和平章节采用带来源、范围与边界的规则图卡，绝不补造 CASE-C 战斗画面。

焦点三态只改变纸面注释的强调，不重复或变速实机镜头。经过 `capture_media` 导入的 CASE-W/C 短镜头会另外生成常驻案例/边界标签，并保留未加标签的原始导入片段和整棵审计树；单个 `context` 片段不证明同步决策。接入 TTS/媒体剪辑仍不等于全片人工 1× 审阅或签核；回执中的 `human_full_film_review=false`。对来源文档和案例结果的整体哈希核对仍由 `longform/v3/build_evidence_ledger.py --check` 负责。

一次真实抽帧和一张规则图卡的检查：

```text
tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\integration\test_v3_visuals.py
tools\.venv\Scripts\python.exe promo\ck3_native_war_ai\integration\test_v3_render_integration.py --artifact-root <new-attempt-dir> --assets <v3-context-frames.json>
```

本次复核样帧保留在 `D:/workspace/ck3_war_film_research_20260923/v3-visual-preview-r1/`、`r3/`、`r4/`、`r5/` 和 `r6/`；`r2/` 是失败 attempt，原样保留。脚本每次自动选择新的 `rN` 目录，不覆盖旧输出。`r6` 的 CASE-R 实机背景与战分静态规则卡已经目视查看；这不是全片人工审阅。
