# 本机第一次公共运行时分配

2026-10-10：当前机器此前只有已关闭的历史 profile-MCP 诊断现场，没有公共 host 的前场 `native-report.json`。`allocate` 增加显式 `--first-machine-bootstrap <bundle.json>`，消费旧现场的真实闭场证据，仅解决第一次公共分配的前场准入。它不把 R38 追认为公共运行时验收，不改变旧失败记录，也不赋予任何产品功能通过。

后续每次公共分配继续要求真实上一公共现场的 session/thread/native job/tree/control/inventory 清理、keeper 退出和屏幕释放。不能重复使用 bootstrap，也不能用更早的已闭场 run 绕过最新 RED 或未完成 run。

## 首次准入边界

本机实际 OS MachineGuid（其他受支持系统为 machine-id）经现有 ID allocator 派生 machine ID。仅 hostname 不足以准入。拒绝 `XAR_CK3_MACHINE_ID` 或 `XAR_CK3_LIVE_RUN_STATE_ROOT` 环境覆盖，并核对 bundle 的 machine、既有 canonical ID-state、当前公共 runtime config/manifest 和 checkout 实际路径及字节。这是当前机器/配置的实际检查，不是一个 `first_run=true` 布尔开关。

canonical ID-state 的 machine 子目录保存 `.shared-runtime-admissions-v1`。它是全产品、全公共 runtime 版本共用的链，不在产品 state、artifact root 或 runtime 目录中。首次准入创建不可覆盖的 `intent.json`，然后记录实际分配出的 `allocation.json`；失败、RED 和未启动 attempt 均保留。任何已消费 intent 都使 bootstrap 永久拒绝，换空输出目录或换公共 runtime 版本无效。后续常规准入还要求 `--previous-live` 正是链的最新 allocation，不能选择更早的 GREEN/closed 现场。

首次准入同时读取本机既有 task-bus durable register 历史，存在任何旧 `shared runtime acceptance` 注册就拒绝 bootstrap，后续修改 task summary 不会清除历史。它核对当前独立 bus list 中不存在任何 `ck3-screen:acquired`，包括 stale/unsafe 的占用，并保留该次真实回读。实际进程 inventory 必须没有 CK3、原 injector/watchdog 或 Python keeper/controller，lease anchor 必须 clean。进程不存在只用于证明当前现场无占用，永远不推导正常退出或 exit0。

所有普通 prepare pins、冷输入单次 ledger、唯一实际 run ID、任务注册、fresh CAS、keeper READY、Steam 新鲜原图直接审核和正常关闭门禁继续保留。bootstrap 不启动 CK3、不领屏；只有整个公共 `allocate` 在全部门禁通过后按原流程注册现场。

## 显式 bundle

Root 在最终公共本机配置和 manifest 固定后，使用实际文件字节创建新的外置 bundle。下列示例只有 schema，不是实际回执；`bytes: 0` 和所有占位字段必须替换，不能原样提交。

```json
{
  "schema": "ck3-mod-acceptance-first-machine-bootstrap-v1",
  "machine": {
    "machine_id": "<actual OS-derived allocator machine ID>",
    "state_root": "<actual canonical local live-run-ids-v1 directory>",
    "admission_root": "<state_root>/<machine_id>/.shared-runtime-admissions-v1"
  },
  "runtime_config": {"path": "<actual common runtime.local.json>", "bytes": 0, "sha256": "<actual SHA-256>"},
  "runtime_manifest": {"path": "<actual common manifest.json>", "bytes": 0, "sha256": "<actual SHA-256>"},
  "repo_root": "<actual checkout>",
  "legacy_archive_index": {"path": "<tracked original archive INDEX.json>", "bytes": 0, "sha256": "<actual SHA-256>"},
  "legacy_profile_mcp_closure": {
    "identity": {"path": "<original live-run-id.json>", "bytes": 0, "sha256": "<actual SHA-256>"},
    "launch": {"path": "<original launch.json>", "bytes": 0, "sha256": "<actual SHA-256>"},
    "profile": {"path": "<original native-profile-with-exit-inventory.json>", "bytes": 0, "sha256": "<actual SHA-256>"},
    "typed_normal_exit": {"path": "<original successful normal-exit-observe SDK result>", "bytes": 0, "sha256": "<actual SHA-256>"},
    "original_handle_exit": {"path": "<original game-original-handle-final.json>", "bytes": 0, "sha256": "<actual SHA-256>"},
    "keeper_final": {"path": "<original keeper FINAL.json>", "bytes": 0, "sha256": "<actual SHA-256>"},
    "client_final": {"path": "<original client final.json>", "bytes": 0, "sha256": "<actual SHA-256>"},
    "closeout_task": {"path": "<original actual task closeout snapshot>", "bytes": 0, "sha256": "<actual SHA-256>"}
  }
}
```

八份旧证据必须全部出现在当前 checkout 已跟踪的 archive index 的 `evidence_entries[].source` 中，源文件 SHA/字节必须仍一致。identity 必须全文存在于该机器既有 canonical ID history，launch 的 run/execution/PID/creation 必须精确对应同一原始现场。SDK 必须证明 `typed_normal_exit_observed=true / process_exit_observed_zero / exit_code=0`，其 profile SHA、原生 PID、retained token 和 creation FILETIME 必须绑定原 launch；独立原始父进程句柄回执也必须是同一 PID 的真实 exit0。单独的 SDK ACK、父进程 exit0 或当前进程消失均不够。

历史 `autosave_verified=false` 原样保存；它不否定已取得的 typed normal0 和独立父句柄0，也不能被改写为自动保存通过。client 必须 terminal CLOSED，keeper 必须真实 thread_exited 且无 failure。`closeout_task` 必须 done/waiting、resources=[]、sequence 超过 keeper 最终 sequence，并与当次新鲜独立 bus list 一致；本机 durable bus journal 还必须保留 keeper 最后确实持屏、随后实际释放的事件链。

canonical machine ID history 中如有晚于该旧现场闭场时间的任何新 live ID，就拒绝使用它首次准入，避免选择较早的旧闭场绕开后来的现场。仅“新公共 artifact root 是空的”不能证明首次运行。

## 当前 R38 的原始来源

以下是已存在的历史文件位置，使用前仍需 Root 按实际字节冻结；本页不提供伪造的新验收回执。

- archive index：`docs/li-yu-dao/acceptance/2026-10-09-r0038-transaction-control-guard-red/INDEX.json`。
- 历史根：`C:/workspace/ck3_lyd_runtime_20261004/live-attempt-038`；其中 `live-run-id.json`、`launch.json`、`native-profile-with-exit-inventory.json`、`game-original-handle-final.json` 和 `R38-CLOSEOUT-TASK.actual.json`。
- SDK：上述根下 `diagnostic-mcp-client-001/0017-r38-exit-observe-002.sdk-result.json`；client 闭场为同目录 `final.json`。
- keeper：`C:/workspace/ck3_lyd_runtime_20261004/r38-root-screen-keeper-20261009-001/FINAL.json`。
- 本机 bus 原始 heartbeat 4188 仍持有 screen；实际 completed 4189 释放；最终 closeout snapshot 为 4190。独立 list 和 durable journal 核对由 allocator 当次执行，不能只相信本页旧叙述。

本轮公共配置目标是 `C:/workspace/ck3-common-runtime/20261010-002/runtime.local.json`；真实 manifest、Source02/native build 与最终 Python delta 由 Root 固定。此路径不存在或尚未固定时，不能构造已通过的 bundle。

## 命令和记录

首次模式仍需 `--previous-release`，其值必须是 bundle 的 `closeout_task.path`。它与 `--previous-live / --previous-keeper` 明确互斥。Root 按已存在公共 entry 参数执行：

```text
<verified-python> -B -X utf8 tools/ck3_mod_acceptance.py allocate --runtime C:/workspace/ck3-common-runtime/20261010-002/runtime.local.json --products tools/ck3_mod_acceptance_products.json --product <actual-product> --case <actual-case> --prepared-case <actual-prepared-case.json> --attempt <unused-aNN> --keeper-output <new-keeper-dir> --first-machine-bootstrap <actual-frozen-bootstrap-bundle.json> --previous-release C:/workspace/ck3_lyd_runtime_20261004/live-attempt-038/R38-CLOSEOUT-TASK.actual.json
```

新现场保存 `predecessor-admission.json`，明确 `mode=first-machine-legacy-profile-mcp-closure`、`legacy_shared_runtime_qualified=false`，同时保全实际进程 inventory、当次无持屏者的 bus list 和 machine-chain 路径。旧 bundle/index/八份旧原始文件与新 predecessor receipt 都加入冻结 pins。历史 ID journal 的快照 SHA 只作准入时证据，因为真正分配新 ID 会合法追加该 journal，不能把这份可变 journal 错当成 launch 的不可变输入。

这份变更的离线回归为：

```text
<verified-python> -B -X utf8 -m unittest discover -s tools -p test_ck3_mod_acceptance_bootstrap.py -v
```

十项测试覆盖旧原始双重0、跨机器/换配置拒绝、缺失 typed normal0、实际 bus 未释放、后续 ID、全机器 intent 重复、选择旧 closed 绕最新 RED、machine/state override、注册历史保留和新 keeper/controller 进程识别。全部使用临时合成证据，无 CK3/Steam/任务总线调用，无屏幕或真实 ID 分配。
