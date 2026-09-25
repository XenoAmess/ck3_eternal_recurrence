# R7C 视觉尝试（已被用户否决）

2026-09-26。最初将“配色微妙”误解为整体棕金风格问题，因此尝试铁灰、暗红和旧金。用户随即明确纠正：系列应统一沿用第 0 期棕金风格，实际问题是 R7 底部与左上实机标签的蓝灰色。R7C 构建已停止，绝不作为交付版本；正确修正见 [R7D](../r7d-brown-gold/visual-style.md)。

R7C 曾尝试在不改原始 CombatID `16777218`、镜头秒点、数学文案、EdgeTTS 音频和主题音乐的前提下，把画面改为铁灰 `#181B1D`、暗红 `#33272A` 和旧金 `#8B7568`。该方向不符合用户要求；当时仅完成部分视觉章节，未产出整片，也未上传 OneDrive。

实现与失败 attempt 分别保留在 [R7C 合成器](../../integration/src/war_ai_promo/episode_one_r7c_same_battle.py)及外置 `episode01-r7c-muted-palette-001/`；修正后的正式制作入口是 [R7D 合成器](../../integration/src/war_ai_promo/episode_one_r7d_same_battle.py)。两版均不代表新增原生机制研究证据。
