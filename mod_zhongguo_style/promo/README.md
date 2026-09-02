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
- 所有入片实机画面必须使用 CK3 书签/世界中的真实历史角色，并在素材 notes 中记录角色 ID 与开局；不使用为测试临时创建、改名或伪装的角色，考核榜可见区域也不得出现世界生成坊正的姓名。
- 最终时间线中不得出现“361制实机验收”、`ZGA`、验收规划器、演示触发器等 fixture/test-only 决议、按钮或文字。验收原始录像即使整体 GREEN，也只能截取经过污染检查且画面干净的时间段；不能因为报告通过就自动获得宣传片资格。
- title card 可以是开场/结尾，也可以是明确标注 `GENERATED EVIDENCE/BOUNDARY` 的事实边界卡；其余内容只允许使用明确占位卡或已有实机素材。生成边界卡和占位卡都不算实机镜头。
- 正式候选必须用 `--stage release` 验收；只要还有一个占位镜头就不能通过。

## 二期续篇定位

二期正式宣传片沿用一期的媒体、字幕、实录 provenance 与人工审阅门禁，但叙事按“看过一期之后的新一轮绩效折磨”组织：

- 默认观众已经知道一期的京察、361 强制分布、考核榜、3.25、PIP 与申诉，不再逐项重做新手教程；
- 开场只允许极短的旧版回顾，主体时长必须用于二期新增机制及其 CK3 决策—资源—后果闭环；
- 优先展示事实档/配额档与校准债、经理也被上司考核、晋升/HC/薪酬、项目抢功、指标口径、事故/积弊/共享官署、跨周期债和制度终局；最终镜头清单以实际完成并通过 live 的新增项为准；
- 笑点延续一期的嘲讽、诙谐和生活感，例如“不是没有 HC，是 HC 还在走流程”“背 C 不是结果，是组织能力建设”，但每个梗必须由画面中的真实机制支撑；
- 禁止把一期旧镜头重复剪成“二期新增”，禁止用配置 smoke、Python L0、测试决议或生成边界卡冒充新玩法；
- 旁白仍为 `zh-CN-XiaoxiaoNeural`，简中为主字幕、英文为副字幕，总时长短于 20 分钟，开场直接进入正题；
- 原始录屏、音频、字幕、manifest、剪辑工程、失败 take、中间导出、抽帧/OCR 与人工签核全部保留，不覆盖一期或前一版二期素材。

## 权威文件

| 文件 | 用途 |
|---|---|
| `promo-manifest.json` | 权威中文配音稿、逐 cue 英文字幕、章节顺序、主题标签、镜头需求 |
| `phase2-promo-project.json` | 二期十章 authoring 配置；章节必须从 `planned` 变为 `ready` 才能消费 capture |
| `phase2-readiness-2026-09-02.md` | 当前工具 HEAD、typed RED 与八段实录到发布的精确缺口清单 |
| 独立仓库 [`src/xar_promo/schemas/phase2-capture-contract-v1.schema.json`](https://github.com/XenoAmess/xar_promo_toolchain/blob/v0.2.1/src/xar_promo/schemas/phase2-capture-contract-v1.schema.json) | 二期 producer 的固定 mode/version/span map 合同 |
| `storyboard.md` | 约 7–8 分钟的剪辑结构与节奏说明 |
| `shot-list.md` | 一次自动集中实录的实际 marks、六张政策卡与不可夸张的产品边界 |
| `smoke-manifest.json` | 很短的媒体流水线测试；内容明确声明“不是正式成片” |
| `../tools/build_promo_video.py` | TTS、双语 ASS、画面合成、章节拼接与 sidecar |
| `../tools/build_phase2_promo_video.py` | 二期专用 adapter/preset builder；支持 `--validate-only` 与 unreviewed candidate run |
| `../tools/validate_promo_video.py` | 草案/正式门禁、媒体规格、时长、语言、哈希与抽帧检查 |
| `../tools/prepare_promo_release_manifest.py` | GREEN 集中实录 → 外部零占位正式 manifest + provenance；拒绝 RED、缺 mark、哈希漂移和覆盖旧输出 |
| `../tools/prepare_promo_visual_audit.py` | 正式 manifest → 全部实机章节的全屏 RGB24 抽帧、RapidOCR、SHA 绑定和明确 `PENDING` 的未签核 spec |
| `../tools/audit_promo_visuals.py` | 正式 manifest 的独立画面门禁：历史角色来源、全屏 PNG/OCR、测试 UI 禁词、逐章覆盖、人工签核与 SHA 复验 |

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

## 二期 builder：可执行的无启动预检

二期续篇使用项目专用入口
`mod_zhongguo_style/tools/build_phase2_promo_video.py`，而不是把二期配置交给通用
`xar-promo build`。入口默认从独立仓库的 GitHub Release `v0.2.1` wheel 加载已冻结的
adapter/preset；从仓库根目录执行前先安装：

```powershell
& tools\.venv\Scripts\python.exe -m pip install -r tools\requirements-promo-toolchain.txt
```

本地开发或验收 fixture 可设置 `XAR_PROMO_SOURCE`（兼容别名
`XAR_PROMO_TOOLCHAIN_SOURCE`）指向 `Z:\workspace\xar_promo_toolchain` 或其 `src` 目录，覆盖已安装
wheel。正式二期制作开始前还必须先 `git fetch` 独立 checkout，确认 `main == origin/main`、工作树 clean，
并把实际工具 HEAD 写进本次外部 artifact 索引；源码覆盖只允许指向该已核对 HEAD。该入口不会替你启动 CK3。
通用包在独立仓库的安装、FFmpeg/ffprobe 和可选 Edge TTS 依赖见
[`docs/installation.md`](https://github.com/XenoAmess/xar_promo_toolchain/blob/v0.2.1/docs/installation.md)。

### 先做 validate-only（不启动 CK3、不写入工作目录）

下面的预检把 stdout/stderr 和一条结果记录写到仓库外的新目录；这些是**预检日志**，不是
live capture 或宣传素材。把 `$evidence` 改成不会被 Git 跟踪的外部目录，每次重试都使用新
时间戳。故意把 capture、work、TTS、FFmpeg、ffprobe 和字体指向不存在的哨兵路径，可以直接
发现入口是否越过了 no-write 边界：

```powershell
$python = (Resolve-Path "tools\.venv\Scripts\python.exe").Path
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$evidence = Join-Path $env:TEMP "xar-phase2-preflight-$stamp"
New-Item -ItemType Directory -Path $evidence | Out-Null
$config = (Resolve-Path "mod_zhongguo_style\promo\phase2-promo-project.json").Path
$configShaBefore = (Get-FileHash -LiteralPath $config -Algorithm SHA256).Hash
$capture = Join-Path $evidence "capture-root-not-created"
$work = Join-Path $evidence "work-dir-not-created"
$tts = Join-Path $evidence "tts-cache-not-read"
$ffmpeg = Join-Path $evidence "ffmpeg-not-run.exe"
$ffprobe = Join-Path $evidence "ffprobe-not-run.exe"
$zhFont = Join-Path $evidence "zh-font-not-read.ttf"
$enFont = Join-Path $evidence "en-font-not-read.ttf"
$stdout = Join-Path $evidence "stdout.txt"
$stderr = Join-Path $evidence "stderr.txt"

& $python mod_zhongguo_style\tools\build_phase2_promo_video.py `
  --project-config $config `
  --capture-root $capture `
  --work-dir $work `
  --tts-cache $tts `
  --ffmpeg $ffmpeg `
  --ffprobe $ffprobe `
  --zh-font-file $zhFont `
  --en-font-file $enFont `
  --run-id "phase2-preflight-$stamp" `
  --validate-only 1> $stdout 2> $stderr
$exitCode = $LASTEXITCODE

$sentinels = @($capture, $work, $tts, $ffmpeg, $ffprobe, $zhFont, $enFont)
$unexpected = @($sentinels | Where-Object { Test-Path -LiteralPath $_ })
if ($unexpected.Count -ne 0) { throw "validate-only created or touched: $($unexpected -join ', ')" }
$configShaAfter = (Get-FileHash -LiteralPath $config -Algorithm SHA256).Hash
if ($configShaAfter -ne $configShaBefore) { throw "project config changed during validate-only" }
if (Select-String -LiteralPath $stderr -Pattern "Traceback") { throw "unexpected Python traceback" }
[ordered]@{
  schema_version = 1
  kind = "zhongguo-361-phase2-validate-only-preflight"
  exit_code = $exitCode
  config_sha256 = $configShaAfter
  stdout = $stdout
  stderr = $stderr
  sentinels_absent = ($unexpected.Count -eq 0)
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $evidence "result.json") -Encoding utf8
```

当前签入的 `phase2-promo-project.json` 有意把十章都标为 `planned`，因此这条命令应返回
`2`，stderr 中应出现 `RELEASE: RED` 及 `phase-two project remains planned`；这是可解释的
authoring RED，不是崩溃，也不是 live 证据。章节和 capture 都准备好后，`--validate-only`
仍只读配置及 capture 元数据，不创建 work 目录、不调用 TTS/字体/字幕渲染、媒体 probe、
FFmpeg/ffprobe 或任何外部命令，不写 run manifest、日志、partial、PNG、MP3、MP4 或 sign-off。
即使结构验证本身为 `VALIDATION: GREEN`，在 runtime claim matrix 和人工签核完成前，进程仍会
以 `RELEASE: RED`/退出码 `2` 收口；不要把这个退出码改写成“宣传片完成”。

### 二期实录入口：独立的八段 producer contract

一期的 `tools/run_zhongguo_acceptance.py --promo-capture` 继续只负责既有的
`PROMO_CLEAN_SPANS`（校准、榜单、驾驶舱、京察、告身和六张政策卡）。它不会因为配置文件
出现 `phase2_*` 章节而改变含义，也不能通过改名把一期原片伪装成二期。

二期必须显式使用：

```powershell
& $python tools\run_zhongguo_acceptance.py `
  --phase2-promo-capture `
  --artifacts-dir $phase2Capture `
  --bridge-dll $bridgeDll `
  --bridge-injector $bridgeInjector
```

该入口绑定 `phase2-capture-contract-v1.schema.json` 中固定顺序的八个 span：
`phase2_fact_quota_calibration`、`phase2_receipt_appeal_pip`、
`phase2_manager_governance`、`phase2_promotion_compensation`、`phase2_hc_workforce`、
`phase2_projects_metrics`、`phase2_incidents_operations`、
`phase2_cross_cycle_endgame`。每段必须由同一真实二期 gameplay producer 在 HUD 已出现后
调用对应的 `*_clean_begin`/`*_clean_end` gate；timeline 同时写入
`capture_mode=zhongguo-361-phase2`、contract version、producer id 和完整 span map，供
二期 preset 严格复核。

runner 已默认注册二期 managed-runtime producer adapter。它复用现有 seed install、managed
native session、loader completion、paused-map 与 loaded-seed proof 原语；不运行一期
`run_scenario`，也不把 `--phase2-live-batch` 的零视觉 MCP 场景作为素材。seed 未就绪返回
`seed_not_ready`；当前八个真实视觉 handler 未接齐时返回 `span_handlers_missing`。两条 typed RED
路径都发生在 `recorder.start()` 前，不产生可误用的录屏。静态 contract 通过不等于
`fixture-live`、`production-live` 或正式成片。

默认 producer 仍通过 runner 的 `register_phase2_promo_capture_producer(producer)` 接入；各玩法
surface 用 `register_phase2_promo_visual_primitive(producer_key, primitive)` 注册，再由共享的
`run_phase2_capture_choreography` 按冻结顺序执行。`producer` 接收
`(stream, artifacts, recorder, title_navigation_service=..., tracked_ck3_pid=...,
native_bridge=..., preflight_bridge_identity=..., seed_contract=..., seed_install=...,
native_session_binding=..., loader_gate=...)`。adapter 在真实 gameplay HUD/paused seed 可核验后调用
`recorder.start()`，解析真实历史人物，按上表顺序调用八次 `recorder.clean_hold`，并返回
一个 evidence object；runner 会再校验 recorder 生成的 hash-bound timeline。未完成这些真实
动作时不能用静态返回值或 MCP snapshot 填充 producer。

### 真实 capture 到来后的候选留存

只有所有章节变为 `ready`、每条 cue 有内容寻址的 Xiaoxiao 缓存、并且已有通过校验的 CK3
capture bundle 后，才运行普通（非 `--validate-only`）候选构建。每次尝试必须使用新的
`--work-dir`，并把该目录放在仓库外。下面的变量必须先替换成真实路径；占位字符串不会
伪造 capture，也不会绕过入口校验：

如果 capture 由天朝二期 seed runner 产生，先把同一 attempt 的
`preflight.json` 作为 `--seed-preflight-report` 传给 builder：

```powershell
$seedPreflight = "C:\captures\zhongguo-361-phase2\seed-attempt\artifacts\preflight.json"
```

builder 会只接受 `run_zg361_phase2_seed_capture.py --preflight-only` 产出的
schema-v1 `GREEN/preflight-ready` 报告，并重新核对 no-launch、MCP-only、零 OCR/图像/坐标、
projection-only 和全部 immutable checks。报告声明的 `paths.artifacts` 必须存在，且
`report_path` 必须精确指向该目录下的 `preflight.json`；它不要求后续 `--capture-root` 位于同一目录或其子树。
入口读取时记录报告 bytes/SHA-256，并在流水线结束前再次核对；若 capture timeline 提供
`source_git_commit` 或 clean-source/tree hash，则与 preflight 的 source identity 严格比对；
旧版 timeline 没有这些字段时，入口只读同一 capture root 的 GREEN `report.json`（含
`cell.runtime_tree_before_sha256`/`product_runtime_manifest.tree_sha256`）作为补充 identity，
并同样记录 bytes/SHA-256。两处 identity 只要有冲突即拒绝，全部缺少时仍保留候选但加入
`capture_identity_unbound` blocker（timeline 或补充 `report.json` 缺失时也会明确记录）。绑定报告会以
`phase2-seed-preflight` raw artifact 复制进候选 run，同时写入 `phase2-pipeline-result.json`
的 `seed_preflight` provenance。它只证明上游输入门已通过，不把 capture 变成 live、也不替代
项目 runtime matrix 或人工审阅。

没有传该参数时仍允许保留候选（便于迁移旧 capture），但结果会明确加入
`phase-two seed preflight report is not bound` blocker，因而不能成为 release-ready。

```powershell
$python = (Resolve-Path "tools\.venv\Scripts\python.exe").Path
$config = (Resolve-Path "mod_zhongguo_style\promo\phase2-promo-project.json").Path
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$greenCapture = "C:\captures\zhongguo-361-phase2\green-run"
$ttsCache = "C:\caches\xar-promo\xiaoxiao"
$ffmpegExe = "C:\tools\ffmpeg.exe"
$ffprobeExe = "C:\tools\ffprobe.exe"
$run = Join-Path $env:TEMP "xar-phase2-candidate-$stamp"
& $python mod_zhongguo_style\tools\build_phase2_promo_video.py `
  --project-config $config `
  --capture-root $greenCapture `
  --seed-preflight-report $seedPreflight `
  --work-dir (Join-Path $run "attempt") `
  --tts-cache $ttsCache `
  --ffmpeg $ffmpegExe `
  --ffprobe $ffprobeExe `
  --run-id "phase2-candidate-$stamp"
```

候选构建会在 attempt 内保留 `phase2-pipeline-result.json`、完整的成功或部分输出、命令
审计与失败诊断；失败时还会留下 `phase2-entry-failure.json`，不得复用同一目录覆盖。成功
渲染后，入口会在 `attempt\candidate-run\run-manifest.json` 建立新的、绑定精确配置字节的
unreviewed run，并保存配置声明的旁白 artifact 与最终 deliverable
（`deliverable/zhongguo-361-phase2.mp4`）。这个 run 只证明候选字节被留存，**不**记录 human sign-off，
也不代表 release GREEN；必须另外完成二期 runtime claim matrix、最终 ffprobe 时长门禁、
完整画面审阅和对同一 deliverable SHA 的明确签核。所有失败 take、原始 capture、日志和
候选 run 都应继续留在外部 artifact 目录，不能提交到 Git 或冒充正式成片。
若候选 run 在持久化过程中因 artifact/目标冲突等原因失败，入口会把
`phase=candidate-run-persistence` 写入同一份失败收据，并保留已经建立的
`candidate-run` 半成品（收据的 `retained_paths` 会标出该目录）；不得清理后在原目录重试。

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

$auditEvidence = "$capture\release\visual-audit-evidence-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
& tools\.venv\Scripts\python.exe mod_zhongguo_style\tools\prepare_promo_visual_audit.py `
  --release-manifest $release `
  --output-dir $auditEvidence `
  --sampling-interval-seconds 1.0

# 这里必须暂停自动流水线：逐章以 1× 完整观看，并检查每张 still。生成器只会产出 PENDING，绝不代签 GREEN。
$pendingSpec = "$auditEvidence\promo-visual-audit-spec.PENDING.json"
$auditSpec = "$auditEvidence\promo-visual-audit-spec.SIGNED.json"
# 人工审阅后，把 PENDING spec 另存为 $auditSpec，并填写真实 reviewer、带时区 reviewed_at_utc、
# 全部 captured chapter id 与五项 true attestation；原 PENDING 文件和所有证据保持不动。
$auditReport = "$capture\release\promo-visual-audit-report.json"
& tools\.venv\Scripts\python.exe mod_zhongguo_style\tools\audit_promo_visuals.py audit `
  --spec $auditSpec `
  --output $auditReport

$auditSha = (Get-FileHash $auditReport -Algorithm SHA256).Hash
& tools\.venv\Scripts\python.exe mod_zhongguo_style\tools\audit_promo_visuals.py verify `
  --report $auditReport `
  --expected-report-sha256 $auditSha

& tools\.venv\Scripts\python.exe mod_zhongguo_style\tools\validate_promo_video.py `
  --manifest $release `
  --stage release `
  --visual-audit-report $auditReport `
  --expected-audit-sha256 $auditSha

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$videoRoot = "$capture\release\video-$stamp"
& tools\.venv\Scripts\python.exe mod_zhongguo_style\tools\build_promo_video.py `
  --manifest $release `
  --output "$videoRoot\zg361-promo-release.mp4" `
  --work-dir "$videoRoot\work" `
  --take-id "zg361-release-$stamp" `
  --visual-audit-report $auditReport `
  --expected-audit-sha256 $auditSha

& tools\.venv\Scripts\python.exe mod_zhongguo_style\tools\validate_promo_video.py `
  --manifest $release `
  --stage release `
  --video "$videoRoot\zg361-promo-release.mp4" `
  --sample-dir "$videoRoot\qa-samples" `
  --visual-audit-report $auditReport `
  --expected-audit-sha256 $auditSha
```

投影器只接受报告与 evidence index 都为 GREEN、timeline 与报告一致、原始 MKV/六张政策图均在 index 中且
字节数和 SHA-256 完全匹配的 run。连续实机章节直接引用原始 MKV 和 marks，不先做有损中间裁切；每个 clip
都从 `recording_started_after_gameplay_hud` 之后开始。层级、同侪互动、PIP/末位等没有独立实录的章节会变成
显眼的生成证据边界卡，不能伪装成 live。输出 manifest 及同名 `.provenance.json` 使用绝对路径，默认拒绝覆盖。
正式投影还必须逐段证明所选画面没有测试专用决议/控件；若自动 OCR 不能可靠排除，就改用单独的 production-only
录制并人工抽帧签字，不能靠裁掉文字或遮罩来掩盖测试 UI。

### 独立画面内容审计

`prepare_promo_release_manifest.py` 证明一次 CK3 验收与素材哈希成立，但 **GREEN 验收录像不自动是 GREEN 宣传素材**。
投影完成后、调用正式媒体验证和渲染前，必须为该外部 manifest 建立一份
`zg361_promo_visual_audit_spec` JSON，并运行独立门禁。先让 producer 在新的外部目录提取证据：

```powershell
$auditEvidence = "$capture\release\visual-audit-evidence-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
& tools\.venv\Scripts\python.exe mod_zhongguo_style\tools\prepare_promo_visual_audit.py `
  --release-manifest $release `
  --output-dir $auditEvidence `
  --sampling-interval-seconds 1.0
```

producer 会按 source SHA 与精确时间戳合并重叠章节的相同帧，以 manifest 中每段 `start_seconds` / `end_seconds`
为端点建立不超过 1 秒的确定性采样序列；PNG 由与 consumer 相同的 FFmpeg 全屏 `rgb24` 解码结果写出，OCR
JSON 由现有 RapidOCR 生成并绑定 PNG SHA。角色 `subject_id`、history ID、显示名和 role 映射只从 manifest 的
`real_character_provenance` 派生。输出目录可在仓库外任意指定，且默认拒绝覆盖；失败留下的半成品也应保留，重试时
另开目录。

生成结果固定叫 `promo-visual-audit-spec.PENDING.json`，其中 reviewer 明示未审、章节列表为空、五项 attestation
全部为 false；因此直接交给 audit 只会得到 RED。审阅者必须以 1× 完整观看全部 captured clip、检查每张 still，
再把 PENDING 文件**另存**为新的 SIGNED spec，填入真实签核信息。之后才运行：

```powershell
$auditSpec = "$auditEvidence\promo-visual-audit-spec.SIGNED.json"
$auditReport = "$capture\release\promo-visual-audit-report.json"

& tools\.venv\Scripts\python.exe mod_zhongguo_style\tools\audit_promo_visuals.py audit `
  --spec $auditSpec `
  --output $auditReport

$auditSha = (Get-FileHash $auditReport -Algorithm SHA256).Hash
& tools\.venv\Scripts\python.exe mod_zhongguo_style\tools\audit_promo_visuals.py verify `
  --report $auditReport `
  --expected-report-sha256 $auditSha
```

spec 使用绝对路径和声明的 `bytes` / `sha256`，至少包含：

- `release_manifest`：刚生成的正式 manifest 文件记录；审计与人工签核都绑定它的 SHA-256。
- `bookmark`：CK3 书签 ID 与开局日期。
- `historical_characters`：每个主角/考核者/受评者的稳定 `subject_id`、原版 `history_id`、显示名、
  `roles`、`origin="ck3_history_database"`、`temporary_or_generated=false`，以及包含该顶层 history key 的
  exact-build 原版角色文件记录。只写一个名字或运行时数字 ID 不算历史来源证明。
- `frame_geometry` 与 `sampling_interval_seconds`：当前门禁要求间隔大于 0 且不超过 1 秒。
- `evidence`：每个入片 `video_clip` 从起点到终点连续覆盖的全屏 PNG + OCR JSON；每张 `still` 必须用 manifest
  中的原 PNG 本身。每条证据声明 `[0,0,width,height]` 全屏 OCR 区域、源素材 SHA、章节 ID、角色 subject ID
  和视频时间戳。审计器会用 ffprobe 核对真实视频、分辨率和时长，再用 ffmpeg 从该 raw 的同一时间戳自行解码
  RGB 帧，并要求它与提交 PNG 逐像素一致；不能拿旧截图或另造干净图顶替。OCR JSON 根必须为对象，包含
  `image_sha256` 绑定该 PNG，并在 `items` / `results` / `ocr` 之一保存识别数组。正常流程由
  `prepare_promo_visual_audit.py` 自动产出这些记录，不再手工抄路径或哈希。
- `manual_signoff`：逐章完整播放后的签核人、带时区时间、manifest SHA、全部实机章节，以及五项 true 证明：
  `historical_characters_only`、`no_generated_official_name_visible`、`fixture_test_ui_absent`、`full_clip_reviewed`、
  `no_crop_mask_or_redaction`。

内建禁词至少包括“361制实机验收”“开始361制实机验收”“验收上司给我的绩效”“验收免费京察规划器”
“验收规划器”“演示政策卡”“演示触发器”“切换至宋帝并开考”“打开此卡”、`FIXTURE-LIVE`、`ZGA`、`zga_` 与
`zga.`；spec 只能追加禁词，不能移除默认表。扫描会先做 Unicode/大小写/空白归一化，并把相邻 OCR 项连接，
所以测试文案被 OCR 拆成两段也会 RED。报告默认拒绝覆盖；`verify` 会重新读取 spec、manifest、原版 history、
每张 PNG 和每份 OCR，复算全部 SHA 与确定性 evaluation。正式发布记录必须保存报告绝对路径和报告 SHA-256。

自动 OCR 仍可能漏字，因此 GREEN 报告同时要求逐章人工完整观看；现有 `validate_promo_video.py --sample-dir`
生成的五张均匀抽帧只是字幕/构图抽检，不能替代该签核。命中测试 UI 的旧 take、OCR 和 RED 报告继续保留，
不得通过裁边、打码或遮罩重新声明为干净素材。

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
  --sample-dir <new-qa-directory> `
  --visual-audit-report <promo-visual-audit-report.json> `
  --expected-audit-sha256 <64-hex-report-sha256>
```

门禁要求：零占位、首章为生成标题卡、每个外部素材使用绝对路径并声明正确的 bytes/SHA-256、全部实机素材声明已排除 CK3 loading、H.264/yuv420p、AAC 48 kHz
双声道、`zho` 音轨标签、2560×1440、短于 20 分钟、Xiaoxiao voice 绑定、简中/英文双语 ASS 与视频/字幕
哈希一致，并且同一 manifest 的独立画面审计报告已通过带报告 SHA 的 `verify`。零占位只表示没有“待补”
假画面，并不表示每项都有独立实录；生成边界卡必须继续可见。抽帧仍需人工检查字幕有没有遮住关键 GUI，
以及笑点是否压住了信息。
