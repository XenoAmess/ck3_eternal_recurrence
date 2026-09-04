# B2 首用状态、加载边界与 r20/r21 实机证据（2026-09-04）

状态：**r20 seed fixture-live GREEN；r21 focused scenario/matrix GREEN、outer harness RED；r22 待复验**

本页只固化 B2 用途分片进入完整 seed 业务链后的新证据。它不把 seed GREEN 写成 B2 四路业务 GREEN，也不把文件拆分写成这次启动问题的唯一原因。

## 冻结产品边界

- B2 runtime 保持 **25 个按用途分组的 effect 文件 / 152 个顶层 effects**；当前单文件最大 `9`，没有超过 `20` 的例外。
- first-use guard 修复后的 production projection 为 `phase2-seed-entry-production-closure-20260904-r8`，共 **252 files / 12,104,708 bytes**。
- r8 product tree SHA-256 为 `C2E3DEEC48DC31294414FBF140EAF2D0603F3F4B6A5F34AF9C3EC9BBCEBB42CD`；formal overlay SHA-256 为 `5195A306C13FA74FCC815EBEB047887F7BBA8B956D00FB7102E752135FE9EA62`。
- 既有 B1 41-effect hotfix 仍是继承例外；它不改变 B2 起“目标 1–10、原则不超过 20”的新文件门。

## r10 RED：首用未设变量，不是 loader stall

r10 artifact 位于：

`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-b2-r10-20260904-102620\artifacts-seed-live`

`02_loader_error_scan.json` 为 RED，共命中 **93 条** `parser_or_script` 运行时签名，scan SHA-256 为
`0887BD8249AE5A54108EB557B5371160BD33C13DA37EED4264DB5DA7A7C07A3E`。同轮 loader readiness 已 GREEN、bridge 已绑定、history 已完成加载；错误在进入结果业务链后出现。因此该 RED 的分类是 **product first-use runtime RED**，不是“文件太大导致 loader 停滞”。

定点归因如下：

- 57 条来自 `zg361_b2_consume_due_policy_debts_effect` 读取尚未建立的 `*_policy_debt_active`；
- 其余来自 `zg361_b2_on_result_frozen_effect` 与 business-object open/consumer 路径读取首次结果前尚不存在的 remand、metric defect、PIP state 与 `object_active` 等可选变量；
- fixture 按合同不得预先伪造 product 变量，所以这些错误同样是新局第一次 B2 result 可达的产品问题，不能靠扩充 fixture 掩盖。

提交 `05e1410bf21b6efdab1492a5919c76a047f2934f`（`Guard first-use B2 optional state`）在 generator 中加入存在性门：缺失的 active 字段按 inactive 处理，并在债务、remand、metric、PIP 和 business-object 消费/开启前检查相应变量。修复后仍是 25 文件 / 152 effects / 每文件不超过 10；没有为了修错合并回单体。

## r8 product 的后续 error scan、r14 与 r20 seed

r14 首先完成修复后的 seed GREEN：

`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-b2-r14-20260904-111017`

该轮冻结 source commit `1ae57f5609c9d2373646fb167dbceb571054919d`，加载上述 r8 product。结果：

- seed candidate `report.json` 为 **GREEN**；SHA-256
  `60D9E94CE08B6EBCF1C60DCA420D7C1AFF13A8B498E1C61F4AC2A4795F150F19`；
- 总 runner report 位于 `artifacts-live/runner-report.json`，SHA-256
  `241A521111CAB9F1FDF11847E49A88BDC4FD063BE1489225C47E37F5423BFF1F`；
- 后续 `02_loader_error_scan.json` 为 **GREEN**、`matches=[]`、quiet window `16.247 s`；scan 文件 SHA-256
  `EB517B003D216EB17D2C272F4E623E00ACE27CA1D3CE4CA7A2A7598AA5C449F1`，冻结 `error.log` SHA-256
  `04E60407EBFF593D6A0E9A0EB695228B2C25BA030F09BE120B077C30180F2D97`；
- 新 checkpoint 为 `57,377,533 bytes`，SHA-256
  `B019F9D50958D9566961E4A5EF7A414FF8A5F491F198AD9C0AE993D56532D1C2`；
- candidate contract 位于
  `artifacts-live/candidate/zg361_phase2_seed_contract.candidate.json`，SHA-256
  `5BB471378C9ED6F25430D958A38815FC0922A75C4F3F440D0EF72F3246CF1F03`。

这组证据把“首用 guard 修复后，252-file r8 product 能完成 loader、进入 seed、产出暂停 checkpoint 且项目错误扫描归零”提升为 fixture-live。它仍不证明 B2 provider 的 A/B/C 路由、四次 restore、业务 postcondition 或宣传素材已经完成。

随后最新 seed r20 位于：

`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-b2-r20-20260904-121400\artifacts-live`

r20 再次得到 **GREEN**，并冻结了供 focused B2 使用的新 checkpoint：

- candidate contract `candidate/zg361_phase2_seed_contract.candidate.json` SHA-256 为
  `FD055093617AA78858BB47F6F9F2BE4AA2E1B66ED4CABE4983B5418C6C99B7E7`；
- checkpoint 为 `57,377,533 bytes`，SHA-256
  `96D1919D569E6F3EA115BF21882B0F4372246812B1E1F630F3AED44968D49335`；
- 稳定业务身份为 date `53147016`、player `29037`、B2 owner `32904`；
- `02_loader_error_scan.json` 为 GREEN，SHA-256
  `BC6C3A21EAED4A1957AB87BED187B6D6302ADD556C508D07AE1A681DB4158D9B`；冻结完整日志 SHA-256
  `B49857293AA260148EF19431A8481A50F5FDC6D9181BA8F4CB7A45BC593A0092`，quiet window `16.232 s`、`matches=0`；
- invalid-left-value、fetch-variable、unset-variable 与 `m016` 分类均为 `0`；cleanup、source tree 和 runtime tree 保持 immutable。

r20 不改变 r14 的归因结论，只用新的稳定语义字段与 checkpoint 取代其作为当前 seed 输入；两轮都不能单独代替 focused B2 的外层验收。

## `calculated_event_id` 是进程内派生标识

同一输入存档 SHA-256
`BFC73FD9E7E80145CDF39AABC66BC2D731881122ADAB0CC0BA675FA07D1E6733` 在两个新 CK3 进程中，对同一 `zg361.4` 事件得到不同的 `calculated_event_id`：

- r11：`3030004`；artifact
  `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-b2-r11-20260904-104325\artifacts-live2\known-pre-bootstrap-event-drain.json`，SHA-256
  `CEB1E05ACCF54E7CF018DC85561C8A102FCEFBE675F7AD2D36C57235F680573D`；
- r13：`2990004`；artifact
  `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-b2-r13-20260904-110511\artifacts-live\known-pre-bootstrap-event-drain.json`，SHA-256
  `09B946CC8E7E667A3755DA5DD9A488AE27D44AB27F7014BBB988B41516DD9DFF`。

两轮的 source save、event definition key、event instance、date、root character、reviewing superior 与四个 authored options 均可稳定核对。结论是：`calculated_event_id` 不能作为跨进程 seed 身份合同字段；跨进程验收应使用这些稳定字段，computed ID 只作为本进程观测值保留。提交 `1ae57f5609c9d2373646fb167dbceb571054919d` 已从 predecessor gate 移除该跨进程等值要求。

## shader cache 准备时间与 loader 时间必须分账

后续轮次改用冻结 profile：

`Z:\ck3_mod_rewrite\_runtime\formal-ab-current-buildoff-20260903\profile`

其 lightweight shader cache 为 **4,960 files / 216,650,070 bytes**。复制、哈希和建立 isolated userdir 都发生在 CK3 进程启动前，必须记为 **profile/cache preparation**；loader 用时从 CK3 启动/loader-stage 观测开始单独计时。不得把大 cache 的递归复制时间计入 mod loader，更不得据此触发 effect 文件拆分。只有 CK3 已启动后出现 loader-stage 超时，并且没有更早 parser/material/call-graph 首错，才执行同条件文件边界 A/B。

## r21 focused B2：业务 scenario GREEN，outer harness RED

r21 artifact 位于：

`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-b2-r21-20260904-122000\focused-live`

必须分两层记录本轮结果：

- `cell/05_phase2_b2_same_checkpoint_scenario.json` 为 **GREEN**，readiness 为
  **`production-live primitive`**；A/B/C（accept / negotiate / refuse）全部 complete；
- same-checkpoint matrix 为 **GREEN**，SHA-256
  `22F8C8D07DA573457F1EBD67E70EF4CED1ACE8594210AAA562F0C02859EE49C7`；完成 4 次 restart、涉及 5 个 PID，cleanup、driver close 与 runtime locks release 均 GREEN，source/runtime trees immutable；
- 外层 `report.json` 为 **RED**，SHA-256
  `6C03CFFE91EB4BCC829F3C6B74D22B1312886161F184100DA7B395C1250ED237`。唯一阻点是 generic
  `project_diagnostics` 把初始 loader 日志中已经存在的 5,607 条静态 liveness 行判成 blocking：5,264 条
  `jomini_effect.cpp:1145` set-never-used、338 条 `jomini_effect.cpp:1161` variable used-never-set、4 条同位置
  list used-never-set，以及 1 条 orphaned event `zg361we.361`；
- 这些行在初始 loader log 中已经存在，而同轮 loader scan 为 GREEN；它们不是 focused 场景中新出现的 runtime 错误，也没有给出 loader 性能 RED。故外层 RED 分类为 **harness classification inconsistency**，不是 B2 scenario/product RED。

最小分类修复已由 `e1c020ad7ad1a8ad4cb9f2ef9676e6517fa9b906` 落盘；仍须以 r22 外层 runner 回执复验。因此本页当前只声明
“r21 scenario/matrix GREEN + outer harness RED”，**不声明 focused B2 最终 GREEN**。

## B3 文件边界延续

B3 manager 新增层已由 `4890b17998df1c5586beb36011d283c1a111f388` 按用途拆为 **7 个 effect 分片 / 43 effects**；单片最大
`10`，没有超过 `20` 的例外。该静态文件边界事实不改变 r21/r22 的 B2 实机状态，也不得用作 focused GREEN 的替代证据。
