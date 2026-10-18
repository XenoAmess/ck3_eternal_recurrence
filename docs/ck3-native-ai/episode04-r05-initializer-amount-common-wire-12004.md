# R05：R207 的实际减量单位与公共 full 查询修复

R207 已执行一次真实决议确认，但没有准备成低补给。输入 `subtract_supply = 0.999`，独立原生读数从 `11651751` 降到 `11551851`，精确减少 `99900`（Q100000，即0.999单位）；逐 physical DATA 的 current/max/state、别名和持久分类不变。不能把这个输入解释为减少99.9%。本次只证明这个实际输入点，其他减量及归零/clamp行为仍待实机验证。

来源机器 `machine_id: desktop-3fevhd2-1c74096080`，2026-10-18 05:35:35 UTC；源 HEAD `6a5a42eb563aa12951f9a0d16141146a9fdeec1d`，exact CK3 1.20.0.4，EXE SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。玩家33388，PID27284，Army0/CArmy0，province1506，paused date53147376。机器事实不得外推；下面的代码和便携原件可在其他机器离线重放。

[来源索引](acceptance/2026-10-18-r207-r05-initializer-units/source-index.actual.json)保存一次 claim、原生确认、独立库存/physical后验和失败回执。确认实际完成且详情窗独立关闭；`assessment.status=supply_changed_not_low_stock`。观察器按严格前置停止，未启用采样、未推进自然日，也没有该阶段的正常 Save。因此没有自然 updater、实际饥饿扣兵、R05正例或影片信用。一次 claim 已消耗，本场没有换 key/prefix 重投。

## 明确的 amount 参数

新配置使用 `supply_loss_amount`：显式十进制正值，最多5位小数，换算Q100000须在正int64范围，不再限制小于1。它只渲染一条 `subtract_supply`，不调用 whole natural-disaster effect，不调用 deplete/spawn，不改兵数，不强制日步或 updater。

```text
python -B -X utf8 tools/prepare_r05_low_supply_fixture.py --output <new-external-package> --province-id 1506 --supply-loss-amount 116.51751
```

公共 `initialize-ordinary-low-supply` / `initialize-and-observe-supply` 的 `case_inputs` 同样接受 `"supply_loss_amount":"116.51751"`。`supply_loss_fraction` 和旧 CLI `--supply-loss-fraction` 仅保留为**绝对减量的历史别名**，保持旧config和已生成决议字节；它不是百分比，不能和新参数并存。缺省旧0.999仍是兼容行为，不是低库存承诺。原件不追改。

下一独立 fixture 的计划：从同一早期正常 S0 重新冷载后，fresh typed snapshot/full 确认唯一 Army0@1506、库存仍为11651751，使用减量116.51751，算术目标raw0。这个新减量尚未实机执行；实际前后读数仍须确认归零且 physical 守恒，不能只凭算术/ACK授资格。stock0起点只代表受控初始化，不是拍到自然正库存耗尽。冷载后身份、库存或位置变化时重新绑定新fixture，不复用旧场 claim。

[新生成预览](acceptance/2026-10-18-r207-r05-initializer-units/next-fixture-preview/fixture-manifest.json)绑定全部4文件。新840B决议已单独执行真实 OpenKaiShek `parse --file`，exit0、PARSED、零诊断、roundTrip=true，见[新语法回执](acceptance/2026-10-18-r207-r05-initializer-units/script-preflight-amount116.51751.actual.json)。这仅证明该决议的语法；descriptor/localization仅绑定SHA。原15项UNKNOWN_OPCODE语义RED保留，未重跑或转授新corpus，仍无1.20.0.4语义profile，不宣称新amount的native效果已验证。

## 公共 full 结果不再依赖外置路径

原自动公共case在首个查询收到 `compact_mcp_summary` 后，把它误当完整Strength，因而在任何初始化前失败。共享host默认sidecar quota为0；本修复不重建host、不开第二个SDK，也不把compact改称full。

`tools/ck3_mod_acceptance_full_army.py` 在两个R05公共adapter入口包装实际 `CaseClient`，从现存同host `native-report.native-wire.jsonl` 取回这一次查询已经收到的原生完整结果。`tools/ck3_mod_acceptance_army_wire.py` 请求前记录fileID/EOF，在请求后只读取新增≤32MiB；绑定实际request_id、query_sequence、profile、Army IDs和native expected revision，并保存原始请求/结果行offset/SHA。不会补发查询。原compact控制回执保持原样。

随后复用生产 `expand_army_strengths_manager_inputs`、profile coverage、`normalize_army_strengths` 与scope/status检查。两侧真实host frame必须同paused date、actor、PID、generation、public/native revision和scope。派生结果中的 `queried_*` 明确是给既有消费者的绑定，不能冒充完整Driver原件。完整结果只另存一次，并保原wire来源证明。

若完整结果的两侧帧漂移，原公共accepted行和两帧仍保留，包装器另标`derived_full_result_error`，以既有精确错误交给R05 readonly恢复逻辑。只有同日、paused、同身份时最多一次fresh snapshot与新request重取；不重天数或动作，再漂移就停。包装器本身不重试，其他错误也不自动变成可重试错误。

公共snapshot实际提供 `managed_campaign_run_binding.run_id`，没有顶层 `episode_run_id`。包装器验证它等于当前Selection的run ID，再给消费者创建带来源说明的dict副本；若已有顶层episode与绑定冲突则拒绝。原snapshot不改。这个值是托管run绑定，不是新读到的原生episode字段。控制ID缺省保留原值；热续行可显式给新prefix，逻辑ID与物理控制ID分别保留。

R207同owned进程的完整查询已真实运行成功，且实际seq1原件先完成生产normalize/target/initializer首个UI动作前的离线回放。此次修复的单个便携focused case复用封存R207原始JSONL结果、public前后帧和负例，验证生产展开、目标、旧字节、amount边界及run冲突拒绝；无SDK。运行 `python -B -O -X utf8 tools/test_r05_amount_common_wire.py --receipt <new-external-receipt>`。该检查不授新公共冷启动、其他机器运行环境或新amount实机资格。

本修复不改变原生flags、DLL、EXE、原a36资格或原自动case的RED。下一实际运行仍走同一公共 prepare/allocate/preflight/run 与正常Save/退出；原始失败、一次确认和独立后验分别保留。历史native-wire原件可在来源机器读取；本专题已压缩携带所需确切原始JSONL行和关键JSON，因此离线回放不依赖来源机器的C/D路径。源码/小回执按通用策略180天复核，可重建预览48小时复核，活跃下一场输入到闭场再复核。
