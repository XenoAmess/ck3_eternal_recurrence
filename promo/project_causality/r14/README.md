# Project 因果律 r14：文案自然化审片版

r14 以 r13 的逐句人类观众审计为输入，重写 45 个 cue，覆盖其标出的 63 个需复审语义句。整改不删工程深度：每章仍按“先讲观众能得到什么、再展示直观结果、随后解释工程如何成立、最后完成价值回环”的顺序展开。

## 本轮整改

- 把 `runner`、`ACK`、`War ID`、`target ledger`、`production-live`、`RED` 等报告式口语改成自然中文，保留它们所承担的证据含义。
- 删除“这局没有事件”“影片没有规定”等会暴露制作过程的防御性说明，改为正面解释智能体如何依据真实状态决策。
- 把“宗教通用域暂缓”等内部路线图信息移出公开叙事。
- 修正 `open_kaishek` 为 `open-kashek`，并把契约原型误写的“蓄王”改回“贤王”。
- 把连续数字和过密清单改写成可听懂的关系说明，工程细节仍留在各章后半。
- 将原 46:15–49:39 的第二次开场改造成显式回望：用“把四条环路重新落回一名玩家身上”“回望整部片子”“现在再回看四层”告诉观众这是总结与升华，而不是重新立题。
- 重新合成上述 45 段授权声线，并按真实音频长度重排整片、字幕和章节。

## 构建

```bat
set XAR_PROMO_SOURCE=Z:\workspace\xar_promo_toolchain
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe tools\build_project_causality_r12.py ^
  --config promo\project_causality\r14\edit-config.json ^
  --output-dir artifacts\project-causality\2026-09-20-r14 ^
  --new-audio-dir artifacts\project-causality\2026-09-20-r14\work\generated-cues ^
  --fallback-audio-dir artifacts\project-causality\2026-09-20-r13\work\generated-cues ^
  --robert-edit promo\project_causality\r12\robert-continuous-edit.r30-main-menu.json ^
  --render --preset fast --crf 18
```

## 当前成片

- 路径：`artifacts/project-causality/2026-09-20-r14/project-causality-r14-owner-voice-nomusic.mp4`
- 时长：53:52.292
- 画面：2560×1440，H.264 High，30 fps，yuv420p
- 声音：AAC 双声道，48 kHz；综合响度 -15.9 LUFS，LRA 4.4 LU，True Peak -1.5 dBFS
- 字幕：简体中文烧录；英语 `mov_text` 可选轨
- SHA-256：`423B3506969369AF95BDA51974186955BAE802169C8496AD3344E3C2E7D99F03`
- 音乐：无；继续按项目所有者要求延后

## 验收

- 119 个 cue 全部生成并封装，其中 45 个 cue 使用本轮新文案与新旁白。
- `ffprobe` 确认视频、中文音轨、英语字幕轨和 8 个章节存在。
- 全片视频与音频完整解码，退出码为 0，未报告解码错误。
- 综合响度、动态范围和真峰值通过抽检；开场、全片、回望段和结尾 contact sheet 已目视检查。
- 英语 SRT 顺序、非重叠与成片边界由交付校验器逐条检查。
- 结尾 Steam 创意工坊卡仍列出 9 项已发布 Mod，包含《牛来》ID `3790635143`。
- 旧审计中的报告式术语、制作过程口吻、内部路线图句和第二次开场提示语均由机器合同检查为不存在。

当前文件仍是无音乐审片成片，sidecar 保持 `publication_authorized: false`，等待项目所有者连续审片与后续配乐决策。
