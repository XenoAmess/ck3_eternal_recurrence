# R0321 / PR #502 merge ref 独立动作边界审查

审查对象：`refs/pull/502/merge` 的精确 commit `d1e65649c13b800fc4e73de217296f2aa42448d0`（head `b934dfcdd9420d262255f1c9685f675021cc4f05`，base `c9d27b1a8fd4e1edd71d82f855fde3920fc313d0`）。结论：**GREEN，仅限多守军研究结果不会从本次修改进入正式一日接战动作；R0321 qualified forecast 仍 RED。** 此结论是源码、合成测试和接收机只读离线回放，不含 CK3 实机运行。

## 两道独立门

1. `strategy.py:16926–16932`：`len(defender_army_ids)>1` 时，无论研究 `contact_admission.admitted` 是否为 true，输出状态都被改写为 `multi_defender_research_only`，且 `planner_usable=false`。R0321 两守军的完整有序集合仍可进 `forecast_fixed_contact`，但不会得到 `provisional_admissible`。
2. `strategy.py:16693–16697`：正式 ingress 只有 `len(defenders)==1` 且 `provisional.status==provisional_admissible` 才进入随后查询终战选项、短路点或一日直达接战的动作块。即使上游错误地给两守军返回 stale `provisional_admissible`，这道消费侧门也拒绝。`combat_decision_contract.py:22` 的 qualified EU activation 仍为 `False`，当前也没有生产者可令 qualified 分支 ready。

精确 merge ref 的 `test_combat_provisional_defense_canary.py` 覆盖了一日两守军场景：将试算 mock 为 512/512 模型胜、低损失，正式 `selected_step=null`、`active_attack_allowed=false`；再把 `_provisional_defense_research_assessment` 故意 mock 成 `provisional_admissible`，仍两项为 false/null。另有对有序双守军与逆序拒绝的函数级测试。使用 `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`，明确 `PYTHONPATH=D:/w/r0321merge_review/ck3_autonomous_player/src`，在 detached merge worktree 执行 canary 与 EU 合同两个模块：**27 passed**。第一次未显式设置 `PYTHONPATH` 时误导入主工作树而得 3 fail；环境修正后同一 merge ref 27/27，故未把该环境错误归于 PR。`git diff base..merge --check` 通过。

## R0321 raw 研究回放的边界

固定 WAR 接收片 `SOURCE-R0321-H3911-V3-RAW-EXCERPT-v1.json` 已独立量得 2,080,166 字节、SHA-256 `865EA7B7AC1B4A680E2BE3A1D84012C67CF9550474075E4A917EFE043CCCDD51`；正式报告 388,302 字节、SHA-256 `7A7774C59DA6099B0A1FFD650AB21A29407BD8B22B1056C7B6F5053251A5CF30`。离线审查脚本 `D:/ck3-research-artifacts/r0321-merge-review-001/verify_merge_raw.py`（SHA-256 `52CEE35E6F7612F735D6393FB82839EBFF15839C13E19CE4244F5CEDCD1A9089`）绑定 merge HEAD、两份来源哈希与 `native:23`/24/23/date raw 53219928、target 2629/entry 2630、attacker `[83886367]`、defenders `[50331920,83886484]`，再用 merge 源码只读运行 512-trial canary。外置 append-only 回执 `merge-raw-review.json` SHA-256 `8B905551ECD372F7E03634BD5CC934FBCC161FB56F5FB883CA1A5FAA315F5E44`，结果为模型胜/负/未决 `512/0/0`、`multi_defender_research_only`、`planner_usable=false`、`calibrated_win_probability_available=false`。

这一 `512/512` 是 `phase-events-disabled-envelope-v4` 对**条件固定参战集合**的模型输出，人物死亡、未来增援/离场、主动撤退、未来每日 effective stats/战宽/非掷骰优势未定量；v3 原生 `monte_carlo_ready=false`、`transition_fidelity_gate=false`、`planner_usable=false`。其 Wilson 下界只反映模拟抽样误差，不是 CK3 原版真实胜率的置信下界。

原始 46 MB H3911 driver 未转交，接收片缺原 command row 的 request/before/after、episode ID 与 connection generation；正式报告的 `first_blocker.before` 也不含 `player_armies`，因此接收机无法从这两件材料独立重建生产 `combat_simulation_encounter_scope` 再做 strict normalizer 全量同帧认证。只读审查 v2 在此处如实报 `army-strength scope requires player_armies`，没有从 payload 自身循环伪造 scope。来源侧 row 相等性、现场原生回放、概率模型保真、三行动 EU、终战和现金输入仍是独立未交付门；不得据本次 GREEN 发出 target 接战移动。
