# 2026-08-27 阶段成果演示：CK3 原生事件窗口读取

## Canonical 双语成片

正式成片采用**英语主叙事 + 简体中文画面内副标题/字幕**；开场、阶段切换、游戏 lower-third 和最终证据卡均为双语。
纯英文首版已废弃，不作为日报交付。

| 项 | 值 |
|---|---|
| video | `Z:\ck3_mod_rewrite\artifacts\demos\2026-08-27\ck3-autonomous-agent-event-window-bilingual-20260827-004648.mp4` |
| duration / geometry | `170.700s` / `2560×1440` / ~`29.5 fps` |
| codec | H.264 `yuv420p` + silent AAC stereo |
| size / SHA-256 | `28455097` / `873498C21BD2795ED185B00C0579C118D944E5CE4BE2592B49C4E232CCDF4A81` |
| sidecar | `artifacts/demos/2026-08-27/ck3-autonomous-agent-event-window-bilingual-20260827-004648.video.json` |
| paired live artifact | `ck3-event-window-live-20260827-004648.json` / `9B560BEBD5455002642DEEDB7572BC0CCFB226186625A06EA45F87DDFAC36A21` |
| seed / cold PID | `85368` / `121352` |
| media inspection | 可解码；中文渲染正常；两次 fixture 事件窗、双语 lower-third 与最终 GREEN 卡均已全分辨率抽检 |

可复用录制命令：

```powershell
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'tools\record_event_window_demo.ps1'
```

录制器会自动启动/关闭两次 CK3、生成同次 live artifact、封装 MP4、添加 silent AAC 兼容音轨、计算哈希并删除临时 MKV。

## 一句话成果

自动玩家已经能在 CK3 `1.19.0.6` 中，通过 exact-build production native bridge、无需 OCR/鼠标/前台窗口，跨
checkpoint 与 fresh-cold CK3 进程精确读取当前事件的完整实例、canonical key、真实物化选项、禁用原因、authored native
index、cancel 和 empty typed-effect-indicator surface。

这是一项 `fixture-live` 观测里程碑，不是完整事件智能：非空 effect kinds、完整效果、scope、选择 lifecycle 与多选效用仍在
后续路线中。

## 已冻结的演示证据

下表是最初冻结并回写 machine ABI 的 Attempt4。上面的正式视频又独立复跑了一次同一能力；两者不能混用 PID/哈希，
但都得到 `fixture-scoped-live-confirmed`。

| 项 | 值 |
|---|---|
| artifact | `C:\Users\xenoa\AppData\Local\Temp\xar-current-event-window-context-cea30a0-live-attempt4.json` |
| size / SHA-256 | `130779` / `690EB5EA188B0903281E5F5DFDA343DA795117EE0FB1C83C3FCDC7F572170B7B` |
| seed / cold PID | `22976` / `43140` |
| full instance / key | `17` / `xar_event_window_live_fixture.1` |
| native option indices | `[0,1,3]`；index `3 cancel=true` |
| cold double query | frame 严格相等；只有 query sequence `1→2` |
| 命令边界 | seed 仅 query/save；cold 仅 query/query；零 option selection |
| 清理 | 两个进程、driver、process tree、nonce root 全部回收；`NoCK3=true` |

## 成片结构

1. 英语主标题 + 中文副标题说明目标与无 OCR/鼠标/前台窗口依赖边界。
2. seed CK3 全程实机画面；双语 lower-third 标明只读 native query 与 checkpoint save，不选择事件选项。
3. 双语 checkpoint 交接卡明确第一 PID 结束并即将启动全新进程。
4. fresh-cold CK3 实机恢复同一 fixture 事件；lower-third 切换为 cold recovery/repeat verification。
5. 双语 GREEN 卡展示 instance/key、`[0,1,3]`、cancel `[3]`、两组 PID、double-query、source unchanged 与 cleanup。

## 30 秒读取既有 artifact

在仓库根目录打开 PowerShell：

```powershell
$artifact = 'C:\Users\xenoa\AppData\Local\Temp\xar-current-event-window-context-cea30a0-live-attempt4.json'
$j = Get-Content -LiteralPath $artifact -Raw | ConvertFrom-Json
$frame = $j.cold_stage.sequence.first_query.current_event_window_context
[pscustomobject]@{
  ok = $j.ok
  evidence = $j.evidence_classification
  seed_pid = $j.cross_stage_proof.seed_bridge_pid
  cold_pid = $j.cross_stage_proof.cold_bridge_pid
  instance = $j.cross_stage_proof.current_event_instance_id
  key = $j.cross_stage_proof.event_definition_key
  native_indices = (@($frame.options.native_option_index) -join ',')
  cancel_flags = (@($frame.options.cancel) -join ',')
  cold_double_query_equal = $j.cold_stage.sequence.checks.adjacent_context_frames_strictly_equal
  cleanup = $j.disposable_cleanup.ok
  no_ck3_after = $j.no_ck3_processes_after
}
```

随后展示每条 option：

```powershell
$frame.options | Select-Object rendered_index,native_option_index,shown,enabled,resolved_name,unavailable_reason,cancel,fallback
```

## 完整实机复跑

完整复跑会自动启动并关闭两个 CK3 进程，约需 3 分钟。录制期间不要手动操作 CK3；runner 会保持暂停并且不选择任何
事件选项。每次必须使用全新的 pipe/output 名：

```powershell
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$demoOutput = Join-Path $env:TEMP "xar-current-event-window-context-demo-$stamp.json"
$demoPipe = "\\.\pipe\xar-event-window-context-demo-$stamp"
$env:XAR_EVENT_WINDOW_ISOLATED_SOURCE_ROOT = 'C:\Users\xenoa\AppData\Local\Temp\xar-event-window-cea30a0-source'
& 'tools\.venv\Scripts\python.exe' 'ck3_autonomous_player\native_bridge\research\run_current_event_window_context_live_acceptance.py' `
  --game-dir 'Crusader Kings III' `
  --bridge-pipe $demoPipe `
  --bridge-dll 'ck3_autonomous_player\native_bridge\.build-event-window-cea30a0-msvc2\xar_ck3_bridge.dll' `
  --expected-bridge-dll-sha256 '52398435F8AA5177D6D507BFAA38CD2578EB988F0629F1C5E13360CC91FB3BB0' `
  --bridge-injector 'ck3_autonomous_player\native_bridge\.build-event-window-cea30a0-msvc2\xar_ck3_bridge_injector.exe' `
  --output $demoOutput
```

成功摘要应包含 `ok: true`、完整 instance/key、seed/cold 两组 process-local 数值和 `error: null`。不要为了视频修改
fixture 预期；若新 run RED，保留 artifact 并按 harness/capability 分类排查。

## 诚实边界

- 这是 generic 非宗教 definition/localization fixture + production bridge，不是 stock/production-only event coverage。
- empty indicator rows 不等于选项无效果；只是 GUI 有损 typed 子集在该夹具中为空。
- 当前没有自动选择本事件。多选事件仍因完整 effects/scopes 未闭合而保持 `semantic_decision_ready=false`。
- 宗教域没有被本演示触碰；圣战与婚姻必要 faith 判定两项窄例外也没有使用。
