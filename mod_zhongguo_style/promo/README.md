# 361 宣传视频工程

这里保存《天朝特色 361 制官员绩效考核》的宣传片脚本、分镜、实机素材需求和可复现合成入口。当前状态是
**可渲染的占位 animatic 工程**，不是正式成片；`promo-manifest.json` 中 14 个实机章节仍明确标为
`placeholder`，画面会强制显示“占位镜头·尚未实录”。

## 成片合同

- 面向中文观众，简体中文是唯一旁白和主要视觉层级；英文是画面内副字幕。
- Edge TTS 固定 `edge-tts==7.2.8` 与 `zh-CN-XiaoxiaoNeural`。
- 简中、英文字幕必须同一 cue 同时出现，并按实际字体像素宽度限制在安全区内。
- 成片必须短于 20 分钟。当前全稿离线保守估算约 `611.5s`（约 10:11）；实际时长以逐 cue MP3 的
  `ffprobe` 结果为准，超过 `1200s` 会在编码前直接 RED。
- 片头直接进入 mod 概念和玩法，禁止 CK3 启动器、启动 loading 与存档 loading 入镜。
- title card 是生成素材；其余内容只允许使用明确占位卡或已有实机素材。占位卡绝不算实机证据。
- 正式候选必须用 `--stage release` 验收；只要还有一个占位镜头就不能通过。

## 权威文件

| 文件 | 用途 |
|---|---|
| `promo-manifest.json` | 权威中文配音稿、逐 cue 英文字幕、章节顺序、主题标签、镜头需求 |
| `storyboard.md` | 约 10–12 分钟的剪辑结构与节奏说明 |
| `shot-list.md` | 14 组 CK3 实机素材的录制动作、证据要求与推荐文件名 |
| `smoke-manifest.json` | 很短的媒体流水线测试；内容明确声明“不是正式成片” |
| `../tools/build_promo_video.py` | TTS、双语 ASS、画面合成、章节拼接与 sidecar |
| `../tools/validate_promo_video.py` | 草案/正式门禁、媒体规格、时长、语言、哈希与抽帧检查 |

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

## 替换占位镜头

1. 按 `shot-list.md` 录制，原始录像直接放进一个新建的 `artifacts/zg361/promo/captures/<run-id>/raw/`
   目录；不要剪掉或覆盖原文件。
2. 另存裁切版到同一 run 的 `selects/`。剪掉 CK3 loading，但保留原始长录像。
3. 在对应章节把 `type` 从 `placeholder_card` 改为 `video_clip`（或确有必要时 `still`），把
   `material_status` 改为 `captured`，增加 `source`、`start_seconds`、`end_seconds`，并在
   `capture` 中写 `"exclude_ck3_loading": true`。
4. 同一因果链的镜头必须来自同一 acceptance run；在 `evidence_sources` 中登记该 run 的报告或 sidecar。
5. 先跑 `--validate-only`，再渲染一个新的 `--take-id`。配音稿或 take 改变后会生成新指纹文件，旧文件不会覆盖。

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

输出文件已存在时，构建默认拒绝覆盖。明确传 `--archive-existing` 时，旧 MP4 与 sidecar 会移动到输出目录的
`superseded/<timestamp>/`，不会删除。QA 抽帧目录也必须是新目录，防止旧抽检被覆盖。

## 正式验收

```powershell
& tools\.venv\Scripts\python.exe mod_zhongguo_style\tools\validate_promo_video.py `
  --manifest <captured-manifest.json> `
  --stage release `
  --video <candidate.mp4> `
  --sample-dir <new-qa-directory>
```

门禁要求：零占位、首章为生成标题卡、全部实机素材声明已排除 CK3 loading、H.264/yuv420p、AAC 48 kHz
双声道、`zho` 音轨标签、2560×1440、短于 20 分钟、Xiaoxiao voice 绑定、简中/英文双语 ASS 与视频/字幕
哈希一致。抽帧仍需人工检查字幕有没有遮住关键 GUI，以及笑点是否压住了信息。
