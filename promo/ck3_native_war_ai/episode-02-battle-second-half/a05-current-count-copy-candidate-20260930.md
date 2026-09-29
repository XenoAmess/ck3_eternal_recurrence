# A05 追击人数口径：下一 run 文案候选（2026-09-30）

状态：**SOURCE_CANDIDATE_ONLY**。本页只解释本次候选旁白与英文字幕的证据和后续门槛；没有新 TTS、字幕时间轴、剪辑、clean span、人工 1× 审阅或成片签核。基线为 #451 `d921dd3a0fdf627b342959b8ec86e047a923e459`。旧 run、配置快照、TTS 请求/返回、MP3、字幕片段及媒体原件保持原字节。

## 统计对象与证据

[A05 同源追击事实回执](cards/e2-02-03-a05-pursuit-facts-20260928.json)及其 [逐团 verifier](cards/verify_e2_02_03_a05_fact_receipt.py)给三次跨日对照各 24 条 `current_fighting_raw` 稳定。独立的[四日原生 control 与孤立画面口径审计](D:/workspace/ck3_native_war_ai_promo_work/episode02-a05-current-count-audit-20260930-a01/REPORT.md)（SHA-256 `C472B84D32F105F9DE7F3AFEC64D334D8568214DA952E1BFEE9D1B7F497F3FF0`）及其 `ledger-readback.json`（SHA-256 `A03AC18190D112892C6E3C31DA04B4A57BB3D8B7888E7D9A8FD03383BA88162E`）逐团核对相同 24 团在 d28–d31 的该字段：四日均逐项为 0，三个窗口各 24/24 不变。

| A05 日期 | 败方 24 团 soft 总和（Q100000） | 除以 100000 向下取整 | 同源孤立原尺寸画面中败方红色面板整数 |
| --- | ---: | ---: | ---: |
| d28 | 82,432,227 | 824 | 824 |
| d29 | 80,361,550 | 803 | 803 |
| d30 | 78,264,077 | 782 | 782 |
| d31 | 76,137,958 | 761 | 761 |

因此原稿“当前战斗人数保持不变”只对逐团原生字段成立；若它与 824→761 的面板同屏，必须点明两者口径不同。四个面板整数与 soft 总和取整相等只是**观测吻合**，未证明 CK3 原版 UI 的内部投影公式。也不能用四张孤立画面断言原片连续 clean span 或已完成真人 1× 审片。

## 本次候选与源链

只改 [中文旁白](narration-script-draft.md)追击段第 40 行及其证据脚注、[英文字幕源](english-subtitles.json)对应句和 `pursuit.source_zh_sha256`。英文源中的其余五章文本及绑定 SHA、[九卡索引](cards/calculation-cards.json)和 [ProjectConfig](project/promo-project.json)均不改。候选句明确 24 团逐团字段稳定、面板人数下降及 UI 公式未证，不再说面板“大号人数”不变。

`script_chapters()` 提取的候选 `pursuit` 中文可听文本 SHA-256 为 `3CC4CBB4F2FCD482391F5EF67A0234B0DC5FDBA03B145ABDC54752EFF763ED9A`；旧章 SHA 为 `92367A922AF5278EA585484DDBE3BF6A73872462E875F697C4004653886B2619`。新英文源文件 SHA-256 为 `ACDE81AE16D1DB589B605EC1FEC50457EF5E6BA30FF395B86CF6F5DE31F7B559`。这两个新 SHA 只标记**文本候选**，不是音频、镜头或译文人工签核。

`render_selected_narration.py` 将 TTS 请求与源稿精确字节绑定；`prepare_subtitle_inputs.py` 校验各源组的 render/native manifest、source draft、章文本和音频边界，并要求新选定的 source-groups 绑定当前整稿 SHA。下一 run 至少需要为变动的追击章创建**新的独立 TTS attempt**，再创建新 source-groups、六章 subtitle fragments 与 readback；未改章节能否引用旧 TTS，仍须由该精确源组门逐项验证。随后按新时长重新检查追击章时轴、双语字幕、画面同步及完整真人 1× 审阅。旧追击 MP3/字幕回执不适用于新句，不能复制或改写为新准入。
