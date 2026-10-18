# R05 公共初始化与自然观察 case（1.20.0.4）

此增量把既有受控低补给初始化器接到同一公共 runner、同一 retained process 和原始 hold。初始化仍只运行 `subtract_supply` 一次，严格核对兵数未变。随后最多推进 30 个实际自然日，在首个完整的自然 supply callback 正常返回观测处停止，保留实际结果。代码与离线合同已验证；本 case 尚未执行 CK3/MCP，R05 实机仍未通过。

本机源码核对：`machine_id: desktop-3fevhd2-1c74096080`，2026-10-18 UTC，来源见本专题 evidence/source-index.json。准确目标是 CK3 1.20.0.4、Steam build25734779、EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。这些源码与离线包不授予另一台机器安装、native 能力或实机资格。

## 使用路线与输入

唯一入口继续为 `tools/ck3_mod_acceptance.py` 的 `plan / prepare / allocate / preflight / run / verify`，catalog 为 `tools/ck3_mod_acceptance_r05_observe_products.json`，product 为 `r05-mechanism-research`，case 为 `initialize-and-observe-supply`。它复用 a01 的公共 profile materializer、normal Save 来源核对、generic sole `mod/product.mod` 挂载和一次性初始化器，不选择另一份 host/DLL，不改旧 pure-vanilla bootstrap 的空 mods 门槛。

例如先执行公共 plan：

```text
tools/.venv/Scripts/python.exe -B -X utf8 tools/ck3_mod_acceptance.py plan --runtime <Root-bound-common-runtime.json> --products tools/ck3_mod_acceptance_r05_observe_products.json --product r05-mechanism-research --case initialize-and-observe-supply
```

prepare 所需原 normal Save、两份实际 Save/build receipt、plain configuration、OpenKaiShek 原预验绑定、province、可选期望 Army/CArmy 继续按 [a01 初始化专题](episode04-r05-controlled-low-supply-fixture-12004.md)。新增 `case_inputs.observation` 必须由 Root 明确填写下列字段，catalog 不偷偷赋予新预算：

```json
{
  "maximum_actual_days": 30,
  "maximum_modal_choices": 16,
  "speed": 5,
  "one_day_timeout_seconds": 120,
  "poll_interval_seconds": 0.25,
  "normal_close_reserve_seconds": 90,
  "cleanup_save_reserve_seconds": 60,
  "max_packet_bytes": 8388608,
  "max_retained_capture_bytes": 33554432,
  "cleanup_capture_reserve_bytes": 262144,
  "deadline_utc": "<Root 的原 UTC 截止时间>"
}
```

示例是待绑定参数，不是已预留的空间或新截止时间。未来实机须按通用存储策略把公共原件及镜像峰值纳入当场预算。`maximum_actual_days` 仅允许1..30；原 hold 不得超过显式 deadline。初始化每个请求、观察每个请求都扣除 cleanup/normal-close reserve；不得延长 hold 或重跑 initializer 来争取时间。公共 runtime 选中的 Python source 必须含合入后的本 helper、a01 initializer 及其默认兼容增量，依赖 pin 由公共 manifest 绑定，不能借 adapter 临时换 host/source/native。

## 真实原生接口与 a35 边界

只使用现有 MCP：`ck3_take_snapshot`、`ck3_query_army_strengths(profile="observed_history_full_v1")`、`ck3_execute_step`、两种 Army sampling control、既有 typed event/interaction context 与选择、`ck3_save_checkpoint`。

sampling set 的真实参数为 `enabled: bool, observer_family: "natural_phase", expected_revision: 当前 public revision`；query 为相同 family/revision。启用前须实际 OFF/clear，启用后独立 query 同 epoch。每个完成日再次 query，拒绝 family/epoch 被替换。退出前 disable，独立 query 明确 `capture_enabled=false, busy=false, clear_completed=true, retained_records=0`。已知 clear_pending 且 busy0 时允许第二个显式 disable 完成清空；未知动作不重复提交。

`natural_phase` 是现有研究记录开关。实际 supply callback/loss writer journals 在 .4 bridge 初始化中独立安装，不靠这个开关才开始捕获；因此不得把 natural-phase gate 当作供给 writer 开关。a35 CMakeCache 实际三个 parent/natural flags 为 ON：`XAR_ENABLE_ACTUAL_SUPPLY_PARENT_JOIN_12004`、`XAR_ENABLE_ACTUAL_RESIDUAL_PARENT_12004`、`XAR_NATIVE71_ARMY_NATURAL_PHASE_12004`。a35 三个决议 flags 仍 OFF，初始化能力未获准；未来 a36 须通过公共 runtime 的真实 capabilities 和一次实机 effect 后验才可用，本文不声称 a36 已构建。

逐日 route 复用真实 `ck3_execute_step`：一次 `research-arm-tactical-daily-sentinel-v1-<start>-to-<start+24>-speed-<speed>-mode-terminal-a-0`，一次 `resume-map`，随后只读 snapshot 和 `research-query-tactical-daily-sentinel-v1`。实际 arm/stop 由生产 NativeDriver 的完整 generation/date/tick validators 检查。未知 Arm/Resume 只读收敛并闭场；不重发 Arm/Resume，也不把已前进的日数伪造为已验证 exact-day。

## 观察与 R05 判定

每日期前后保存完整 structured control row：full-history strength，包括所有 retained callback、实际 writer 的 DATA 别名/唯一物理 slot、supply parent 与 residual parent；另存完整 clock、sampling、modal query/selection 和独立 snapshot。公共 CaseClient 自身保留 `.actual-results.json`；helper 在有限目录保存 gzip 镜像及 SHA。镜像耗尽时停止观察，原公共原件仍在；cleanup 可保留精确公共原件引用并继续 OFF/Save，不被镜像空间不足阻断。

按生产 normalizers、keyed parent join、periodic component classifier 和 `_physical_debit` 判断。R05 positive 必须同时满足：

- 原 owner/PID/generation/episode、同 Army/CArmy、同驻地与同物理 roster，完成原时钟 exact+24。
- 独立 callback/writer fences 无 gap/reset/unattributed failure，唯一 parent token/thread/depth/receiver/date 匹配。
- 完整自然 dispatcher callback 正常返回，写入点 stock 的真实 Q100000 operand 非负且严格 `<1000000`。
- source 已闭的 periodic supply preferred 或 residual 分支，完整 alias 覆盖且唯一物理 DATA debit `>0`。

不按 request、cache delta、Army 净兵数、callback 前后 stock、一串相邻 sequence 或 raw138 名称推因果。residual county-entry 与 siege 分支不给 R05 credit；mixed raw1380/1 可观察，保持所有原始分类与补员事实，不把 supply loss 结论外推成逐 regiment 补员规则。

初始化最低20物理兵的默认合同保持。观察阶段允许剩余19甚至0，避免把真实损失误判为初始化失败；其他身份、完整 DATA、非战斗/非退却/静止准入仍严格核对。结果分别保存 `initializer_at_zero`、无 matching callback、首个完整 callback 无 writer、物理 debit0、不满足归因、严格 physical positive。仅正常 callback 返回观测不证明 updater 的 AL；现生产 summary 明示 `updater_admission_observed=false`，本 helper 也不从 stock/date/byte 推 AL。

## 弹窗续行与清理

每个实际 modal 都重新读取当前 capabilities，再用当前 native instance 和 typed frame 查询。已分析事件先走生产 registry；未注册事件走既有第一显示可用项并保存 before/after incident，待批后离线补齐。普通 interaction 按原版 GUI 左侧拒绝，专用已知策略优先；左侧禁用时保留诊断，不改成右侧接受。API option number 按实际当前 native index+1，绝不借用旧 instance2。

选择前 checkpoint 决策并 durable once claim；一份实际 MCP 回执与独立 after snapshot 分别保留。interaction `accepted:false` 可能表示 `accept=false`，本 helper 的 `control_row_ok`、原 accepted 字段、accept 参数和独立窗口消失分列。既有 legacy incident after 若因该 accepted 字段保守记为未证，原样保留，helper 独立后验不改写它。未消失或结果未知不重选。

公开 paused=false 仍可能有 modal；helper 先做一次已知 modal 的 pause，再 typed 处理。到达 target 的 modal 复用原 generation，完成后不重新 Arm/Resume。若早期 modal 之后原 clock 仍 armed，可一次恢复这个已知暂停继续同一 clock；若原时钟已提前触发、缺失或未知，则保存 partial 并闭场，不编造整日通过。

finally 尝试暂停、核原 clock（仅匹配已知 generation 可 cancel）、sampler OFF+clear、一次 normal Save。原 Arm 结果未知时只查 clock，不冒认 generation 或取消别人的时钟。公共 runner 再执行既有正常 Quit/exit/keeper closure；`verify` 只有 initializer GUI 后验、严格 R05 predicate、OFF/clear、normal Save 和真实 normal-close 同时满足才给本 research case 的 R05 pass，不授 Workshop/product release pass。

cleanup 的 OFF/clear 初值永远为未证，包含 enable 前失败路径也须新鲜 query。若准入发现已有他人 sampling enabled，本 case 不 disable 它、不声称已清空。自身 disable 结果未知时只读 query 收敛，不重发；只有已知 disable 回执后的 clear_pending/busy0 才可发独立 clear。此边界在最终 a03 修正中有单独合同，先前 a02 seal 原件保留而由 a03 替代集成。

离线 focused checks 的原日志、精确命令与 source pins 见 [evidence](acceptance/2026-10-18-r05-initialize-observe/source-index.json)。原决议836B不变，沿用 a01 parser GREEN；旧 profile validator15 UNKNOWN_OPCODE RED 与新增 localization 未 parse 原样保留。本增量仅 Python/orchestration，无新增 CK3 DSL 待预验；不重跑旧 validator，也不把合约测试当成实机语义 GREEN。
