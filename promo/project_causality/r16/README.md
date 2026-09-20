# Project 因果律 r16：辉煌愿景·霸气版

r16 继承 r15 的推荐旁白节奏、完整罗贝尔实机、画面与证据边界，只重写四张章门的读法和“辉煌愿景”终章。画面主标题仍保留
`咒 / 术 / 道 / 辉煌愿景`；中文旁白在前三张章门读作“咒篇 / 术篇 / 道篇”。

## 文案结构

- 章门从解释句改为伪天司的愿景宣告。
- 四个 Loop 分别以“令欲望成为产品 / 令阻碍成为能力 / 令失败成为工具 / 令成果进入世界”统领。
- 工程事实、实机能力边界、虚实线证据规则和人类最终裁决全部保留。
- 终幕收束为“Project 因果律。因已成果，果将生因。循环既起——永不熄灭。”
- r16 共重合成 31 段旁白：三张单字章门与完整辉煌愿景终章；其余 r15 旁白按文本和 TTS 参数指纹复用。
- 结尾三镜统一改用无烙字顶栏的干净 CTA 底片，保留九项 Steam 产品、入口说明与背景主视觉，避免旧标题与动态章节标题叠层。

## 构建

```bat
py tools\build_project_causality_r12_assets.py --cta-only

set XAR_PROMO_SOURCE=Z:\workspace\xar_promo_toolchain
artifacts\project-causality\private\index-tts\.venv\Scripts\python.exe tools\build_project_causality_r12.py ^
  --config promo\project_causality\r16\edit-config.json ^
  --output-dir artifacts\project-causality\2026-09-20-r16 ^
  --old-audio-dir artifacts\project-causality\2026-09-20-r15\work\generated-cues ^
  --new-audio-dir artifacts\project-causality\2026-09-20-r16\work\generated-cues ^
  --robert-edit promo\project_causality\r12\robert-continuous-edit.r30-main-menu.json ^
  --synthesize --render --preset fast --crf 18

py tools\build_project_causality_music_preview.py ^
  --source-video artifacts\project-causality\2026-09-20-r16\project-causality-r16-owner-voice-nomusic.mp4 ^
  --music-dir artifacts\project-causality\2026-09-20-r14\music-audit\selected ^
  --output-dir artifacts\project-causality\2026-09-20-r16-music-preview ^
  --output-name project-causality-r16-imperious-vision-music-preview.mp4
```

## 交付

- 无音乐基线：`artifacts/project-causality/2026-09-20-r16/project-causality-r16-owner-voice-nomusic.mp4`
- 音乐审片版：`artifacts/project-causality/2026-09-20-r16-music-preview/project-causality-r16-imperious-vision-music-preview.mp4`
- 时长：`47:15.445`；2560×1440、H.264、AAC 48 kHz stereo
- 音乐审片版响度：-16.2 LUFS integrated、4.4 LU LRA、-1.5 dBFS true peak
- 音乐审片版 SHA-256：`075413B854B01DCBA4BA48B18CA753BAB8C8AEB1E06CC189A83022C67ACE5D8A`
- 无音乐基线 SHA-256：`76A28374D8C0D9B0B2CA2B47B74890F0E87187D234C11FE1D2C4C50CCD35C9EA`
- OneDrive：`Project因果律/审片/Project_Causality_r16_Imperious_Vision_Music_Preview.*`

音乐审片版已完成全片解码、章节/轨道检查和章门/终幕画面抽检；结尾三镜另行逐镜确认仅保留一套左上角动态标题。它仍使用现有六首 Suno 母带的章节内循环，不是完成 Whole Song
续写后的正式发布音乐母版，`publication_authorized` 继续保持 false。
