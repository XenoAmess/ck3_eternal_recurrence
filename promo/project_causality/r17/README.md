# Project 因果律 r17：终幕文案精修

r17 以 owner 选定的 r16 No Duck 混音为唯一基线，只精修两句终幕文案；结构、画面、罗贝尔实机、英语可选字幕与六章节音乐增益均保持不变。

## 文案变更

- `凡有结果，皆将成为下一轮回的燃料` → `凡有结果，皆将成为下一轮回的柴薪`
- `循环既起——永不熄灭` → `循环既起——永世不熄`

两段中文旁白由 owner voice 重新合成，中文烧录字幕同步更新。既有英文字幕语义仍准确，因此不作机械改写。

## 构建

```bat
set XAR_PROMO_SOURCE=Z:\workspace\xar_promo_toolchain
artifacts\project-causality\private\index-tts\.venv\Scripts\python.exe tools\build_project_causality_r12.py ^
  --config promo\project_causality\r17\edit-config.json ^
  --output-dir artifacts\project-causality\2026-09-20-r16 ^
  --output artifacts\project-causality\2026-09-21-r17\project-causality-r17-owner-voice-nomusic.mp4 ^
  --plan-output artifacts\project-causality\2026-09-21-r17\project-causality-r17.build-plan.json ^
  --old-audio-dir artifacts\project-causality\2026-09-20-r16\work\generated-cues ^
  --new-audio-dir artifacts\project-causality\2026-09-21-r17\work\generated-cues ^
  --fallback-audio-dir artifacts\project-causality\2026-09-20-r15\work\generated-cues ^
  --robert-edit promo\project_causality\r12\robert-continuous-edit.r30-main-menu.json ^
  --render --preset fast --crf 18

py tools\build_project_causality_music_preview.py ^
  --source-video artifacts\project-causality\2026-09-21-r17\project-causality-r17-owner-voice-nomusic.mp4 ^
  --music-dir artifacts\project-causality\2026-09-20-r14\music-audit\selected ^
  --output-dir artifacts\project-causality\2026-09-21-r17-music-open ^
  --output-name project-causality-r17-music-open-no-duck.mp4 ^
  --ducking-mode none
```

## 交付与核验

- 成片：`artifacts/project-causality/2026-09-21-r17-music-open/project-causality-r17-music-open-no-duck.mp4`
- 时长：`47:14.915`；2560×1440、H.264、AAC 48 kHz stereo
- 响度：`-16.0 LUFS integrated / 4.1 LU LRA / -1.5 dBFS true peak`
- SHA-256：`9FB98A260512B310A80F84540C190103B151D7C6C588A99021DE332D8AD95695`
- OneDrive：`Project因果律/审片/Project_Causality_r17_Music_Open_No_Duck.*`
- `ducking_mode=none`，六个 `chapter_mix[].ducking=none`；人物开口不触发音乐侧链压低。
- 两处新字幕已逐帧抽检，旧文案已从构建计划中清除；全片音视频解码 GREEN。

本版仍沿用现有六首 Suno 基础母带的章节内循环；在 Whole Song 母带完成与最终人工签核前，不称为公开发布音乐母版。
