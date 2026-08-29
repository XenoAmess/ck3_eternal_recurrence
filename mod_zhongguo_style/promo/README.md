# 361 宣传视频工程

这里保存《天朝特色 361 制官员绩效考核》的宣传片脚本、分镜、实机素材需求和可复现合成入口。仓库内
`promo-manifest.json` 始终是**可渲染的作者版占位 animatic**；正式候选 manifest 不反写仓库，而是由一次
GREEN 集中实录投影到该 run 的外部 artifact 目录。这样既保留 8 个待补镜头的原始计划，也不会把失败 take
或尚未单拍的功能悄悄包装成实机。

## 成片合同

- 面向中文观众，简体中文是唯一旁白和主要视觉层级；英文是画面内副字幕。
- Edge TTS 固定 `edge-tts==7.2.8` 与 `zh-CN-XiaoxiaoNeural`。
- 简中、英文字幕必须同一 cue 同时出现，并按实际字体像素宽度限制在安全区内。
- 成片必须短于 20 分钟。当前全稿离线保守估算约 `432s`（约 7:12）；实际时长以逐 cue MP3 的
  `ffprobe` 结果为准，超过 `1200s` 会在编码前直接 RED。
- 片头直接进入 mod 概念和玩法，禁止 CK3 启动器、启动 loading 与存档 loading 入镜。
- title card 可以是开场/结尾，也可以是明确标注 `GENERATED EVIDENCE/BOUNDARY` 的事实边界卡；其余内容只允许使用明确占位卡或已有实机素材。生成边界卡和占位卡都不算实机镜头。
- 正式候选必须用 `--stage release` 验收；只要还有一个占位镜头就不能通过。

## 权威文件

| 文件 | 用途 |
|---|---|
| `promo-manifest.json` | 权威中文配音稿、逐 cue 英文字幕、章节顺序、主题标签、镜头需求 |
| `storyboard.md` | 约 7–8 分钟的剪辑结构与节奏说明 |
| `shot-list.md` | 一次自动集中实录的实际 marks、六张政策卡与不可夸张的产品边界 |
| `smoke-manifest.json` | 很短的媒体流水线测试；内容明确声明“不是正式成片” |
| `../tools/build_promo_video.py` | TTS、双语 ASS、画面合成、章节拼接与 sidecar |
| `../tools/validate_promo_video.py` | 草案/正式门禁、媒体规格、时长、语言、哈希与抽帧检查 |
| `../tools/prepare_promo_release_manifest.py` | GREEN 集中实录 → 外部零占位正式 manifest + provenance；拒绝 RED、缺 mark、哈希漂移和覆盖旧输出 |

## 无联网静态前置

在仓库根目录运行：

```powershell
& tools\.venv\Scripts\python.exe mod_zhongguo_style\tools\build_promo_video.py `
  --manifest mod_zhongguo_style\promo\promo-manifest.json `
  --output artifacts\zg361\promo\draft-animatic.mp4 `
  --work-dir artifacts\zg361\promo\work `
  --validate-only

& tools\.venv\Scripts\python.exe mod_zhongguo_style\tools\validate_promo_video.py `
  --manifest mod_zhongguo_style\promo\promo-manifest.json `
  --stage draft
```

`--validate-only` 不创建目录、不调用 Edge TTS、不编码视频。它会检查 13 项核心主题、中文/英文关键词、
配音 voice、字幕像素布局、素材存在性、loading 开场禁令和离线时长预算。

## 媒体 smoke

这一步需要联网调用 Edge TTS，但只生成一章很短的流水线测试：

```powershell
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$run = "artifacts\zg361\promo\smoke-$stamp"

& tools\.venv\Scripts\python.exe mod_zhongguo_style\tools\build_promo_video.py `
  --manifest mod_zhongguo_style\promo\smoke-manifest.json `
  --output "$run\zg361-promo-pipeline-smoke.mp4" `
  --work-dir "$run\work" `
  --take-id "xiaoxiao-smoke-$stamp"

& tools\.venv\Scripts\python.exe mod_zhongguo_style\tools\validate_promo_video.py `
  --manifest mod_zhongguo_style\promo\smoke-manifest.json `
  --stage draft `
  --video "$run\zg361-promo-pipeline-smoke.mp4" `
  --sample-dir "$run\qa-samples"
```

smoke 只能证明中文配音、双语字幕和媒体流水线能工作，不能证明 mod 玩法或正式宣传片完成。

## 从一次 GREEN 集中实录生成正式 manifest

集中录制 runner 在进入真实 gameplay HUD 后才启动 FFmpeg，一次保存连续原始 MKV、timeline marks、报告、
evidence index，以及实际打开的六张政策卡 `#001/#007/#020/#022/#026/#361`。它不声称录到了
`#002/#015/#035`。拿到 GREEN run 后执行：

```powershell
$capture = "Z:\ck3_mod_rewrite_process_assets\zg361\promo\captures\<green-run>"
$release = "$capture\release\zg361-promo-release-manifest.json"

& tools\.venv\Scripts\python.exe mod_zhongguo_style\tools\prepare_promo_release_manifest.py `
  --artifact-root $capture `
  --output $release

& tools\.venv\Scripts\python.exe mod_zhongguo_style\tools\validate_promo_video.py `
  --manifest $release `
  --stage release

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$videoRoot = "$capture\release\video-$stamp"
& tools\.venv\Scripts\python.exe mod_zhongguo_style\tools\build_promo_video.py `
  --manifest $release `
  --output "$videoRoot\zg361-promo-release.mp4" `
  --work-dir "$videoRoot\work" `
  --take-id "zg361-release-$stamp"

& tools\.venv\Scripts\python.exe mod_zhongguo_style\tools\validate_promo_video.py `
  --manifest $release `
  --stage release `
  --video "$videoRoot\zg361-promo-release.mp4" `
  --sample-dir "$videoRoot\qa-samples"
```

投影器只接受报告与 evidence index 都为 GREEN、timeline 与报告一致、原始 MKV/六张政策图均在 index 中且
字节数和 SHA-256 完全匹配的 run。连续实机章节直接引用原始 MKV 和 marks，不先做有损中间裁切；每个 clip
都从 `recording_started_after_gameplay_hud` 之后开始。层级、同侪互动、PIP/末位等没有独立实录的章节会变成
显眼的生成证据边界卡，不能伪装成 live。输出 manifest 及同名 `.provenance.json` 使用绝对路径，默认拒绝覆盖。

## 过程素材保留

构建目录按 manifest SHA 与 `take-id` 分开。每一条旁白 cue 会保留：

- `cue-*.zh-CN.txt`
- `cue-*.zh-CN.mp3`
- `cue-*.edge-tts.json`
- 合并旁白 MP3 与 concat 清单
- 双语 ASS
- 生成/叠加帧
- 每章 MP4 与构建指纹
- 全片 concat 清单、MP4 和 `.video.json`

正式 manifest 与 provenance 保存在 capture run 的外部 artifact 目录，不进 Git；原始 MKV、失败 take、
OCR、静帧、报告和 timeline 都原样保留。输出文件已存在时，manifest 投影器直接拒绝覆盖；视频构建明确传
`--archive-existing` 时，旧 MP4 与 sidecar 会移动到输出目录的
`superseded/<timestamp>/`，不会删除。QA 抽帧目录也必须是新目录，防止旧抽检被覆盖。

## 正式验收

```powershell
& tools\.venv\Scripts\python.exe mod_zhongguo_style\tools\validate_promo_video.py `
  --manifest <external-capture-run>\release\zg361-promo-release-manifest.json `
  --stage release `
  --video <candidate.mp4> `
  --sample-dir <new-qa-directory>
```

门禁要求：零占位、首章为生成标题卡、每个外部素材使用绝对路径并声明正确的 bytes/SHA-256、全部实机素材声明已排除 CK3 loading、H.264/yuv420p、AAC 48 kHz
双声道、`zho` 音轨标签、2560×1440、短于 20 分钟、Xiaoxiao voice 绑定、简中/英文双语 ASS 与视频/字幕
哈希一致。零占位只表示没有“待补”假画面，并不表示每项都有独立实录；生成边界卡必须继续可见。抽帧仍需
人工检查字幕有没有遮住关键 GUI，以及笑点是否压住了信息。
