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
  --output-dir artifacts\project-causality\2026-09-21-r16-music-forward ^
  --output-name project-causality-r16-music-forward-preview.mp4
```

## Music-forward v1

根据审片反馈，正式推荐审片混音不再使用全片统一 `0.24` 音乐增益和统一 `10:1` 侧链。六段音乐按叙事职责分别混音：

| 章节 | 增益 | 较旧版提升 | 侧链阈值 / 比率 |
|---|---:|---:|---:|
| 开场 | `0.33` | `+2.77 dB` | `0.020 / 8:1` |
| 咒篇 | `0.31` | `+2.22 dB` | `0.019 / 9:1` |
| 罗贝尔 | `0.35` | `+3.28 dB` | `0.022 / 7:1` |
| 术篇 | `0.33` | `+2.77 dB` | `0.019 / 9:1` |
| 道篇 | `0.38` | `+3.99 dB` | `0.019 / 9:1` |
| 辉煌愿景与 CTA | `0.36` | `+3.52 dB` | `0.022 / 7:1` |

工程讲解保持更强压低和较慢恢复，以旁白辨识度为硬边界；罗贝尔与辉煌愿景采用更轻侧链和更快恢复，让音乐在句间、战争和终幕承担叙事。

## No-duck 对比版

为直接比较“音乐始终保持力量”与“旁白优先”的差异，构建器支持 `--ducking-mode none`。该模式保留上述六章节固定增益，但完全移除人声触发的侧链压缩：

```bat
py tools\build_project_causality_music_preview.py ^
  --source-video artifacts\project-causality\2026-09-20-r16\project-causality-r16-owner-voice-nomusic.mp4 ^
  --music-dir artifacts\project-causality\2026-09-20-r14\music-audit\selected ^
  --output-dir artifacts\project-causality\2026-09-21-r16-music-open ^
  --output-name project-causality-r16-music-open-no-duck-preview.mp4 ^
  --ducking-mode none
```

这是 A/B 对比件，不自动替代当前推荐的 music-forward 侧链版。音乐在人声期间不下降，因此密集工程段也可能产生更明显的中频争夺。

## 交付

- 无音乐基线：`artifacts/project-causality/2026-09-20-r16/project-causality-r16-owner-voice-nomusic.mp4`
- 当前推荐音乐审片版：`artifacts/project-causality/2026-09-21-r16-music-forward/project-causality-r16-music-forward-preview.mp4`
- 时长：`47:15.445`；2560×1440、H.264、AAC 48 kHz stereo
- 当前推荐版响度：-15.9 LUFS integrated、4.3 LU LRA、-1.5 dBFS true peak
- 当前推荐版 SHA-256：`39EC1577326D1482F9674092A1C9886577E739D097A7FEA199BDE574C26C7429`
- No-duck 对比版：`artifacts/project-causality/2026-09-21-r16-music-open/project-causality-r16-music-open-no-duck-preview.mp4`
- No-duck 响度：-16.0 LUFS integrated、4.1 LU LRA、-1.5 dBFS true peak
- No-duck SHA-256：`F98F09CF3794FC96909C4ABD4C80B00EC5F00E03F47C29FA961C8940A217A3EE`
- 旧保守混音 SHA-256：`075413B854B01DCBA4BA48B18CA753BAB8C8AEB1E06CC189A83022C67ACE5D8A`
- 无音乐基线 SHA-256：`76A28374D8C0D9B0B2CA2B47B74890F0E87187D234C11FE1D2C4C50CCD35C9EA`
- OneDrive：`Project因果律/审片/Project_Causality_r16_Music_Forward_Preview.*`
- OneDrive 对比件：`Project因果律/审片/Project_Causality_r16_Music_Open_No_Duck_Preview.*`

音乐审片版已完成全片解码、章节/轨道检查和章门/终幕画面抽检；结尾三镜另行逐镜确认仅保留一套左上角动态标题。它仍使用现有六首 Suno 母带的章节内循环，不是完成 Whole Song
续写后的正式发布音乐母版，`publication_authorized` 继续保持 false。
