# Project 因果律 r18：移除旧章门音效

r18 继承 r17 的全部画面、owner voice、字幕、终幕文案和 owner 选定的 No Duck 混音，只移除四段早期章门 SFX：

- 咒篇：`spell-low-bell.wav`
- 术篇：`method-page-pulse.wav`
- 道篇：`principle-dry-seal.wav`
- 辉煌愿景：`vision-five-note-rise.wav`

章门仍保留 12 秒入声延迟；这段空间现在只承载章节配乐与艺术画面，不再叠加旧合成音效。

## 构建

```bat
set XAR_PROMO_SOURCE=Z:\workspace\xar_promo_toolchain
artifacts\project-causality\private\index-tts\.venv\Scripts\python.exe tools\build_project_causality_r12.py ^
  --config promo\project_causality\r18\edit-config.json ^
  --output-dir artifacts\project-causality\2026-09-20-r16 ^
  --output artifacts\project-causality\2026-09-21-r18\project-causality-r18-owner-voice-nomusic.mp4 ^
  --plan-output artifacts\project-causality\2026-09-21-r18\project-causality-r18.build-plan.json ^
  --old-audio-dir artifacts\project-causality\2026-09-21-r17\work\generated-cues ^
  --new-audio-dir artifacts\project-causality\2026-09-21-r18\work\generated-cues ^
  --fallback-audio-dir artifacts\project-causality\2026-09-20-r16\work\generated-cues ^
  --fallback-audio-dir artifacts\project-causality\2026-09-20-r15\work\generated-cues ^
  --robert-edit promo\project_causality\r12\robert-continuous-edit.r30-main-menu.json ^
  --render --preset fast --crf 18

py tools\build_project_causality_music_preview.py ^
  --source-video artifacts\project-causality\2026-09-21-r18\project-causality-r18-owner-voice-nomusic.mp4 ^
  --music-dir artifacts\project-causality\2026-09-20-r14\music-audit\selected ^
  --output-dir artifacts\project-causality\2026-09-21-r18-music-open ^
  --output-name project-causality-r18-music-open-no-duck.mp4 ^
  --ducking-mode none
```

## 交付与核验

- 成片：`artifacts/project-causality/2026-09-21-r18-music-open/project-causality-r18-music-open-no-duck.mp4`
- OneDrive：`Project因果律/审片/Project_Causality_r18_Music_Open_No_Duck_No_Gate_SFX.*`
- 英文字幕：`Project_Causality_r18.en.srt`；从 r18 最终 MP4 的内嵌英语轨直接导出，共 274 条，覆盖 `00:00:00.200–00:47:14.232`
- OneDrive 英文字幕：`Project因果律/审片/Project_Causality_r18_Music_Open_No_Duck_No_Gate_SFX.en.srt`
- 英文字幕 SHA-256：`DB752E20A666E0913AFC96DEAA37BEBF16B99E73414A81DE836BD25B64ED40C7`
- 时长：`47:14.915`；2560×1440、H.264、AAC 48 kHz stereo
- 响度：`-16.0 LUFS integrated / 4.2 LU LRA / -1.5 dBFS true peak`
- SHA-256：`E7ACAC3C0C47655EDBB247FAF724ECDD332FE75A6D2E7674C9E8E0274BD5BA28`
- 构建计划中四个章门 `sound_effect=null`，计划策略为 `chapter_gate_sfx_policy=remove`。
- 无音乐母版的四个章门开场各抽检 11.5 秒，均为低于 `-70 dB` 的连续静音；最终成片完整解码 GREEN。
- `ducking_mode=none` 且六章节 `ducking=none`；r17 的“柴薪”“永世不熄”文案保持不变。

本版仍使用现有六首 Suno 基础母带的章节内循环；在 Whole Song 母带完成与最终人工签核前，不称为公开发布音乐母版。
