# 2026-08-27 阶段成果演示：CK3 原生事件窗口读取

## 一句话成果

自动玩家已经能在 CK3 `1.19.0.6` 中，通过 exact-build production native bridge、无需 OCR/鼠标/前台窗口，跨
checkpoint 与 fresh-cold CK3 进程精确读取当前事件的完整实例、canonical key、真实物化选项、禁用原因、authored native
index、cancel 和 empty typed-effect-indicator surface。

这是一项 `fixture-live` 观测里程碑，不是完整事件智能：非空 effect kinds、完整效果、scope、选择 lifecycle 与多选效用仍在
后续路线中。

## 已冻结的演示证据

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

## 推荐录屏顺序

1. 打开本页，先用上面的“一句话成果”说明这不是录制鼠标宏，而是在读取 CK3 内部原生对象。
2. 展示事件三条选项的 typed 结果：`0` 可选、`1` 禁用且有原生原因、`3` 可选且是 cancel；强调 rendered index
   与 authored native index 不可混用。
3. 展示 seed PID 与 cold PID 不同、checkpoint SHA 相同、cold query/query frame 相同，说明它能跨进程恢复而不是缓存假数据。
4. 展示最后的 `ok=true`、全部 readiness gate、cleanup 与 `NoCK3=true`。
5. 最后展示[完整路线图](../goal-and-roadmap.md)，明确下一步是完整事件效果/语义，再回到战斗 controller 和整局自治。

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
