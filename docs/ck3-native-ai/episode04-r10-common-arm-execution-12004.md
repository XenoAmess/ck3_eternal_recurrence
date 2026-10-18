# R10 公共单 owner 的正式阶段接线

实现与实测分开：本包是 `machine_id: desktop-3fevhd2-1c74096080` 于 2026-10-18 离线施工的候选，未合入、未启动游戏、未连接 SDK、未新增构建。B 实际合格增长点仍 **0/2**，正式 ABC **0/3**。源码导入与 compound synthetic PASS 不给场次、90 日、损耗、费用或视频资格。

[CommonArmIO](../../tools/ck3_mod_acceptance_cases/r10_common_arm.py) 用正常 constructor 接收原 `CaseClient`。它读取实际 public context/frozen-argv/prepared、普通 Save 收据、prepared profile 和空 mod inventory，核同一 S0、actor/date、来源、DLL、独立进程创建 FILETIME 和 Root 原容量/期限。**公共产品 key、mod_key 和 runID 只是分配身份，不能证明或否认 vanilla 来源。** 不把 `<machine>--war-episode04-r10--R####` 改成 `vanilla`，不伪造旧 Robert identity envelope。正常来源由 `ordinary_campaign_succession/xar_off/pure-vanilla-enabled-mods-empty` 的实际 Save 与空 mod profile 证明；运行机器、PID/create/gen 和当前 actor 另取真实读回。三臂分别独立 prepare/allocate/cold run，不把同场阶段重开当新 cold。

完整 packet 复用当前 `ensure_common_full_army_client` 的同一次原始 MCP 查询和 native-wire recovery，保留 public compact 原行、原 wire proof 与 canonical derived-normalized 文件。它不制造旧 `complete-driver-army-query-result-json-v1` 或 `army_history_evidence`。旧 B 业务算法的 request/response 文件是注明来源的 **derived common-control views**，不是原 SDK transport。单份 canonical full 文件给 B packet、A/C endpoint 使用，不把 compact summary 当全量。

当前 common snapshot 不提供旧比较器的 `played_character_gold` 时，使用同一暂停 F 的 private current treasury 构造明确标记的 derived snapshot，并绑定原 snapshot/cash 回执；原 public snapshot 字节不改。每个独立 cold 调 `ck3_query_loaded_feature_manifest_v1`，以真实 `build/effective_feature_flags/script_dlc_keys/entitlements` 作为语义投影，排除日期/revision；entitlements 继续保持原查询的 provenance-unclosed。计划 baseline 应使用同一投影，不能拿旧场或编译旗标代填新 cold 的 loaded features。

`full_query_with_one_same_date_rebound` 只对现有 R05 classifier 认出的、已实际完成的 revision-drift 失败，保留原 RED 后取同日/paused/同 owner-location/lifetime 的新帧，最多再发一次只读查询。丢失结果、未知 timeout、第二次 drift 或其他错误都不重发。Move、split、merge、Arm、Resume、Save 的 once claims 保留，不能靠换 stage/attempt 复活未知动作。

[公共 arm adapter](../../tools/ck3_mod_acceptance_cases/r10_arm_adapter.py) 在同一 hold 内经现有 `root_checkpoint` 接收 Root 阶段命令：A 用既有 `admit/observe_move/update`；C 用既有 `start/propose_move/observe` 和 `common_horizon`；B 用现有 `BStages`、normal/common-horizon helper 与 R09 split/merge business functions。业务方法通过显式 current IO 组合调用，没有构造旧 Relay 实例、`__new__`、AST 重写或跳过旧 constructor。新 B `admit_cold` 接收真实 cold-start input，不再为初始 admission 编造 terminal disposition；历史完整 ARM 输入路线仍保留。

A/C 一日推进复用当前 R05 `ObservationIO.exact_day` 与 native 陌生弹窗/交互续行方法，不新造时钟。B 继续使用现有 normal/common-horizon 阶段的逐日与恢复合同，原 HOLD/未知动作不得追认为完成。到场后推进只按冻结 `hold-arrival-position-until-day90`。Root 阶段 mailbox 预留 300 秒作正常保存/退出；结束或错误时暂停、只取消确认为本 owner 的时钟、一次正常 Save；正常 GUI Quit、保留 OS0/native0 和 keeper/CAS 仍交公共入口原流程验证。

真实公共 CLI：

```text
<verified-python> -B -X utf8 tools/ck3_mod_acceptance.py plan --runtime CURRENT_RUNTIME --products tools/ck3_mod_acceptance_r10_arm_products.json --product war-episode04-r10 --case r10-common-arm
<verified-python> -B -X utf8 tools/ck3_mod_acceptance.py prepare --runtime CURRENT_RUNTIME --products tools/ck3_mod_acceptance_r10_arm_products.json --product war-episode04-r10 --case r10-common-arm --case-inputs BOUND_INPUTS --prepare-output NEW_PREPARED_DIRECTORY
```

随后沿相同公共 `allocate / preflight / run / verify`，使用实际 previous closure、当次 Steam 离线审阅和真实 frozen context；没有 `run-abc` 命令。三臂共享 frozen PLAN/S0/source/DLL，但各有自己的 current runtime、capacity 和原 hold。arm inputs 必须显式提供 `label/plan/evidence_root/capacity_admission/deadline_utc/max_runtime_total_bytes/max_evidence_file_bytes/one_day_timeout_seconds/poll_interval_seconds/maximum_modal_choices/maximum_stages`，所有 pins/时限/预算都来自当场材料。

运行产生 `case-output/r10-<A|B|C>-stage-NNNN-awaiting.json`。Root 在同目录对应 `...-root-result.json` 写原 checkpoint 的 `run_id/reviewer` 加 `machine_id/label/stage`；这是操作协调，不是用户审批或视频人审。whole-arm 阶段为 `baseline / Move-once / Move-post / advance / advance-common-horizon / finish`；B 沿现有 `baseline/split-once/post-split/rest/move-stage-once/move-stage-post/advance-stage-day/recover-stage-day/merge-once/post-merge/route/advance-common-horizon/recover-common-horizon-day`，移动传实际 `army_id`，恢复传原 `day_start_raw`，common horizon 提供真正 first-arrival arm pin。不能拿 unknown claim 重新 baseline。

资格不放宽：B constructor 先调用既有 `strategy_b_site_growth.qualify_plan_sites`，两处必须有同省、静止、完整 cohort、自然 callback Province 链和实际正库存 delta；月率/eligible 不能代替。`compare_fees=true` 时 `check_plan` 仍要求 R07/R08 资格来源，实付/payer/cadence 缺失保持 pending/null。代码能提交阶段与完整比较成功是两件事；本 adapter 不自动生成完整物理/付款账，也不自动授 `case_contract_qualified`、`formal_arm_qualified`、joint ABC 或 signoff。实际原件和后验必须进入既有比较器，缺项不能补零。

OpenK 为 `not-applicable`：本包不生成或改变 CK3 script，只有公共 DTO/IO 和现有 typed consumer 接线。唯一新增 compound synthetic 覆盖非 vanilla public ID + normal Save/empty profile 接受、fixture 来源拒绝，以及显式一次 same-date full-query rebound、未知 timeout/第二次失败不再重发。未跑旧全矩阵，未授真实 ABI/游戏日/退出/媒体信用。
