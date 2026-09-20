# Project 因果律 r15：推荐节奏版

r15 不改 r14 的文案、画面选择、章节结构和证据边界，只重做长篇旁白的节奏。全部 119 个 cue 使用同一份已授权声线重新合成。

## 节奏参数

- IndexTTS 2.5 `duration_factor=0.90`
- 模型分段间隔 `100 ms`
- 普通 cue 结尾停顿 `0.55 s`
- 字幕尾部保持 `0.55 s`
- 普通产品卡与工程图不再继承旧版固定展示底长，镜头长度由新旁白加尾停顿决定
- 四张章节声明卡和罗贝尔连续实机仍保留各自的视觉时间权威
- 不对最终总音轨做粗暴整体倍速；参数进入每个 cue 的生成指纹和 sidecar

## 构建

```bat
Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe tools\build_project_causality_r12.py ^
  --config promo\project_causality\r15\edit-config.json ^
  --output-dir artifacts\project-causality\2026-09-20-r15 ^
  --old-audio-dir artifacts\project-causality\2026-09-20-r15\work\generated-cues ^
  --new-audio-dir artifacts\project-causality\2026-09-20-r15\work\generated-cues ^
  --robert-edit promo\project_causality\r12\robert-continuous-edit.r30-main-menu.json ^
  --synthesize --render --preset fast --crf 18
```

## 交付

- 无音乐基线：`artifacts/project-causality/2026-09-20-r15/project-causality-r15-owner-voice-nomusic.mp4`
- 现有母带循环预览：`artifacts/project-causality/2026-09-20-r15-music-preview/project-causality-r15-recommended-pace-music-preview.mp4`
- 时长：`46:51.822`（音乐版）；2560×1440、30 fps、H.264、AAC 48 kHz stereo
- 字幕与结构：简体中文烧录字幕、英语 `mov_text` 可选轨、8 个章节及 data 轨均保留
- 音乐版响度：-16.2 LUFS integrated，LRA 4.4 LU，True Peak -1.5 dBFS
- 音乐版 SHA-256：`969EF470B00899C6CBBEE8966242BEDD9CEBFFFE57BD89981AE6B7189F20FC23`
- 无音乐版 SHA-256：`21F64228E8B64E1CC943413C43C27453078B61E2E61927F01C174BF76E273D8A`
- OneDrive：`Project因果律/审片/Project_Causality_r15_Recommended_Pace_Music_Preview.*`

## 节奏验收

| 指标 | r14 | r15 | 变化 |
|---|---:|---:|---:|
| 全片时长 | 53:52 | 46:51 | -7:00 |
| 汉字/旁白秒 | 2.93 | 3.29 | +12.3% |
| TTS 内部检测静音 | 647.5 s | 530.4 s | -18.1% |
| TTS 内部停顿中位数 | 0.415 s | 0.379 s | -8.7% |
| TTS 内部 ≥1 s 停顿 | 31 | 16 | -48.4% |
| 音轨检测总静音 | 1009.3 s | 774.8 s | -23.2% |
| 普通 cue 尾停顿中位数 | 1.25 s | 0.55 s | -56.0% |

音乐版已完整解码，章节边界直接从 r15 成片读取后铺设，不复用 r14 时间点。仍然只是现有六首母带的循环预览，不是等待 Suno Whole Song 后的发布母版。
