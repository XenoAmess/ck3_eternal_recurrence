# Workforce probation/PIP 结局事实 CK3 运行合同

状态：**CK3 script static-ready；#274 arm、三代有界 ledger、signed attribution 普通 result 与 B2 PIP settlement 均已接入；尚无变更后的 loader / paused snapshot / 实机证据**。
生成器常量固定为 `ck3-script-static-ready-not-live`；本包不得写成 fixture-live、production-live 或完整 #269。

## 1. 独立文件与责任边界

本包只拥有：

- `tools/gen_zg361_workforce_probation_fact.py`；
- `tools/test_zg361_workforce_probation_fact.py`；
- `common/scripted_effects/zg361_workforce_probation_fact_effects.txt`；
- `events/zg361_workforce_probation_fact_events.txt`；
- `localization/*/zg361_workforce_probation_fact_l_*.yml`；
- 本规格。

它不修改 Workforce、B1、B2、Career/HC、中央 dispatcher、native provider、runner 或 case kernel。简中、英文为本轮
创作文案；法、德、日、韩、波、俄、西只是英文结构占位，不算发布翻译。

本包保留旧 Workforce #269 曾等待的 12 个 probation outcome compatibility alias：

```text
zg361_we_ad_external_attribution_bps_2
zg361_we_ad_external_attribution_bps_3
zg361_we_ad_external_outcome_dimension_1
zg361_we_ad_external_outcome_dimension_2
zg361_we_ad_external_outcome_dimension_3
zg361_we_ad_external_outcome_evidence_count
zg361_we_ad_external_outcome_evidence_hash
zg361_we_ad_external_outcome_evidence_id
zg361_we_ad_external_outcome_exclusion_reason
zg361_we_ad_external_outcome_id
zg361_we_ad_external_outcome_observed_cycle
zg361_we_ad_external_outcome_quality
```

这些名字不是新的权威事实槽。当前 generation 继续通过 subject 上无后缀的
`zg361_workforce_probation_fact_*` 活动投影向 B2、attribution、rehire 与共享 core 保持 ABI；此前已完整消费的 generation
在接受下一份真实 #274 receipt 前追加到两个 immutable archive。活动投影 + 两个 append-only archive 构成三代有界
ledger。普通 #269 consumer 现直接 join 当前 probation + attribution detailed receipt，不再读取这 12 个名字。probation 包仍可在
调用 core 前短暂物化 compatibility alias，并在 D+1 consume receipt 后删除；alias 只用于旧包的碰撞/清理兼容，不能授权结算。

## 2. 真实对象与状态机

每个 generation 的事实状态只有五种：

| state | 含义 | 是否允许出现 12 alias |
|---:|---|---|
| 0 / missing | 未建立真实录用事实 | 否 |
| 1 | 已由真实 #274 任命/岗位回执 armed；尚无后续结局 | 否 |
| 2 | 后续正式结果是 3.25；冻结原结果与归因，等待唯一 B2 PIP settlement | 否 |
| 3 | canonical outcome 已发布、等待 Workforce #269 消费 | 仅在 exact consumer ready 后短暂出现 |
| 4 | #269 已 ACK，独立消费回执已写 | 否 |

arm 必须命中 subject 上已经成功的 #274：`write owner/subject/cycle/case/state=4`、`hired=1`、真实
`position_receipt_id/hash`、`native_appointment_confirmed=1` 和严格更晚的 `probation_due_cycle`。因此它不会把候选人、
未录用对象或一个布尔 sentinel 变成试用期事实。

canonical outcome 同时保留：

```text
owner + subject + hire cycle/case + position receipt
+ result owner/subject/cycle/case/state/settlement receipt/grade/reason/KPI/rank
+ 三份 #267 sealed vote evidence + 三份 attribution bps + attribution receipt
+ 可选 PIP owner/subject/cycle/case/state/policy route/task/settlement/outcome/result + B2 case/closure receipt
+ source kind + quality + observed cycle + evidence id/hash/count + publication id/hash
```

消费成功后另写 `consume_owner/subject/hire_cycle/hire_case/result_cycle/result_case/outcome_id`、Workforce route choice、
owner 单调消费序号和消费 fingerprint。ACK、canonical source 与消费回执三者缺一，state 不得变成 4。

### 2.1 三代有界 ledger

三个 generation 的物理布局固定为：

| generation | 物理位置 | 写入规则 |
|---:|---|---|
| 1 | 初始活动投影；第二次 arm 前归档至 `ledger_slot_1_*` | archive `active=1` 最后提交，此后只读 |
| 2 | 第二次活动投影；第三次 arm 前归档至 `ledger_slot_2_*` | archive `active=1` 最后提交，此后只读 |
| 3 | 当前活动投影 | 不再接受第四份不同 arm receipt |

这是闭合“旧 owner → 不同 owner → 回旧 owner” #276 provenance 的最小容量：generation 1 保留旧 owner 的完整 consumed
tombstone；generation 2 保存不同 owner 的真实 probation/result/consume receipt，并先由 rehire fact 捕获 growth；generation 3
允许回到旧 owner 建立当前案。archive 对每个实际存在的 source、PIP、outcome 与 consume 字段逐项复制，同时固定
`generation / archive_receipt_id / archive_receipt_hash / owner / subject / cycle / case / state / arm receipt identity`。

所有 ledger 字段都是 subject character 上的普通 `set_variable`，随 CK3 存读档持久化；temporary scope/value 只计算当前调用的
expected receipt，不承载账本真值。既有单槽存档第一次再 arm 时只补 `ledger_version=1,generation=1` 元数据，不改写原 receipt。
归档成功后可以退休无后缀活动投影以复用既有 ABI，但不删除任何 `ledger_slot_1_*` 或 `ledger_slot_2_*`。

有界语义明确区分：

- 当前或 archive 的完整 arm identity 重放：status 2，活动投影不切换；
- owner/subject/hire cycle/case 相同但 due、position receipt 或 arm receipt 不同：RED 1002 collision/stale；
- 当前 generation 尚未 state 4/consumed：RED 1004 active collision；
- 元数据或 archive commit marker 矛盾：RED 1005；
- 三代已满后的第四份不同 arm：RED 1003，不覆盖最旧历史。

未命中 ledger 的任意新 tuple 仍必须先通过当前真实 #274 business object 与 native position receipt guard；ledger 不接受 caller
自报 owner、case 或 hash，也不清洗旧 receipt 来伪造容量。

## 3. 三个 ABI 与 scope 约定

所有 public hook 的**当前 scope (`this`) 必须是真实 hired subject**；`OWNER` 参数必须是真实 #274 owner。`ROOT` 被明确
忽略，不参与身份、权限或幂等键。消费 legacy #269 前，本包通过 subject 上的 hidden character event 重新建立
`ROOT=this=subject`，以满足旧 consumer 内部的 `root.var:*` 读取；外部 caller 的 ROOT 不会泄漏进消费语义。

### 3.1 已接 #274 arm adapter

共享 core 已在 #274 A 成功、业务对象和 native position receipt 已消费后，通过 D+1 post-consume seam 接入：

```text
# current scope = hired subject
zg361_workforce_probation_fact_arm_hire_effect = {
    OWNER = <exact #274 owner>
}
```

幂等键：

```text
owner / subject / m274_write_cycle / m274_write_case
+ m274_probation_due_cycle / m274_position_receipt_id / m274_position_receipt_hash
```

完全相同的当前或 archive identity 重放为 status 2。新的真实 #274 只有在当前 state 4 且完整消费回执存在时才追加；第二、第三代
分别先把当前 tombstone 写入 slot 1、slot 2，再退休活动投影。相同逻辑案但 receipt 不同为 RED 1002；未完成当前案为 RED 1004；
第四代为 RED 1003。invalid source 仍为 RED 1001，任何 RED 都不覆盖旧案。

### 3.2 已接 hook 1：普通 result settlement

B1/通用结果的两个 canonical settlement 写点现只排 D+1 relay；relay 不直接调用本 ABI，而是调用 signed attribution adapter，
后者从已签 receipt 提取 bps 并以本包的内部 ABI 发布：

```text
# current scope = result subject = hired subject
zg361_workforce_probation_fact_publish_from_result_effect = {
    OWNER = <zg361_result_case_owner>
    ATTRIBUTION_BPS_2 = <真实第二 evidence dimension 的归因 bps>
    ATTRIBUTION_BPS_3 = <真实第三 evidence dimension 的归因 bps>
}
```

第一份 bps 固定从 `10000-bps_2-bps_3` 推导，并在任何写入前拒绝负数。三个 dimension 不由 caller 自报，直接取同一
hire case 已封存且互异的 `m267_vote_evidence_1..3`；三位 interviewer 也必须存在且互异。唯一合法 caller 是 attribution
fact 包：玩家明确签署哪一席主责，或 AI 依冻结原票与公开 tie rule 产生 `6000/2000/2000`，并留下 actor/evidence/receipt。
共享 core 不传 3333/3333、全零、随机值或从档位反推的伪值。

结果 guard 要求：result owner/subject 匹配；cycle 不早于 probation due 且严格晚于 hire cycle；case/settlement receipt
相等；state 为 3 或 5；grade/reason/KPI/rank 完整；owner 的权威 review serial 已到 observed cycle；Workforce #269
仍以同一 owner/subject/hire cycle/case/state=5 等待。

幂等键：

```text
owner / subject / hire cycle / hire case
+ result cycle / case / state / settlement receipt / grade / reason / KPI / rank
+ m267 vote_evidence_1..3 / attribution_bps_1..3
```

同键重放不发新 outcome ID；任何字段变化都 RED 2001，不能覆盖已冻结结果。

### 3.3 已接 hook 2：B2 PIP settlement

`zg361_b2_publish_workforce_pip_settlement_effect` 现已接入。完整提交链分成四个 D+1 边界：`zg361b2.101` 只在
`outcome_code` 已提交后执行 terminal settlement；`zg361b2.102` 只在 terminal tuple 已提交后发布/守恒 B2 source；`zg361b2.103` 只在
source 已提交后首读并调用：

```text
# current scope = PIP subject = hired subject
zg361_workforce_probation_fact_publish_from_pip_settlement_effect = {
    OWNER = <zg361_b2_pip_owner>
}
```

不能在 resolver / terminal writer / source writer 的同一 effect 链里读取各自刚写入的字段；CK3 对这种读后写顺序没有可靠提交
边界。`zg361b2.103` 完成首读并安排 `zg361b2.104`；后者是一个有界且真实可达的次日重放 caller，只重放同一 handoff，
不重新调用 B2 publisher、不补字段，也不重签 B2 receipt。若 #277 已消费 source，`pending=1/consumed=0` guard 使重放静默
失效；若 source 仍被守恒，probation adapter 只接受相同完整幂等键，不能签发第二个 outcome。两次 delayed event 还分别冻结并
复核 owner/subject/cycle/case；`.101` 另冻结 state=2。旧票据不能在新 PIP 上借壳执行。closure hash 直接从已提交的 underlying
PIP tuple 重算，不读取 source writer 同链刚写的 case hash。

它只接受 state 2 中已经冻结的同 owner/subject 3.25 result，并严格 join B2 的 underlying PIP 五元组、policy route、task kind、
唯一 settlement、`outcome_result_cycle/case/grade`，以及尚未被 #277 消费的 Workforce PIP case/closure ID/hash。四个 receipt
字段不只要求为正：case ID/hash 与 closure ID/hash 必须逐项等于 B2 writer 的公式结果，连同 route/task/state/result tuple 一起
证明它们确由该 settlement 产生。PIP cycle 必须等于已冻结 3.25 result cycle，结局 result cycle 必须更晚；毕业要求 grade 2/3，
失败要求 grade 1。此 hook 不重新接收归因，沿用 3.25 时已经冻结的三维证据与 bps。

幂等键：

```text
完整 frozen result key
+ pip owner / subject / cycle / case / state / policy route / task kind / settlement receipt / outcome code
+ pip outcome result cycle / case / grade
+ B2 Workforce pip case receipt ID/hash / closure receipt ID/hash
```

完全相同重放不发第二个 outcome；普通 result 已经发布后调用 PIP hook，或 PIP tuple 改写，均 RED 3001。

## 4. 结局映射与诚实缺口

| 真实来源 | canonical quality | 说明 |
|---|---:|---|
| settled result grade 2（3.5）或 3（3.75） | 1 / pass | 后续正式结果已经证明试用通过 |
| settled result grade 1（3.25） | 不发布 | 只进入 state 2；不能把 3.25 默认解释为失败或成功 |
| B2 `outcome_code=1,state=3` | 1 / pass | 唯一 D+365 PIP settlement 明确毕业 |
| B2 `outcome_code=2,state=4` | 2 / mismatch | 唯一 D+365 PIP settlement 明确失败；失败本身仍不是离职 |

本包没有真实 attrition 或岗位/战略失效 producer，所以不发布 quality 3/4，也不借 PIP failure 伪造离职。对本包真实发布的
pass/mismatch，`outcome_exclusion_reason=0` 是经过 source-kind guard 的 typed “not excluded” 结论，不是默认成功。
未来若要发布 attrition/excluded，必须另接 Career/HC/native 的真实退出或岗位失效 case、receipt 与 owner/subject/cycle/case
join；在该生产点出现前继续 fail-closed。

## 5. Alias 物化、消费与双结算屏障

只有 state 3 且下列全部成立时才物化 12 alias：

1. owner/subject/hire cycle/case 与 #269 write/receipt 完全相等；
2. #274 hired、formal HC lineage、#267 candidate 均仍指向本 subject/case；
3. owner review serial 已到 probation due 与 observed cycle；
4. 12 alias 要么全不存在，要么全都等于 canonical fact；部分残留或不同值拒绝；
5. canonical outcome 还没有消费。

随后调用 `zg361_we_m269_future_consume_effect`；compatibility alias 不参与该 consumer 的成功 guard。consumer 直接核对
本槽与 signed attribution receipt，只有核到
`outcome_settled=1,pending=0,last_outcome_id=canonical outcome_id,consumed_hire_case/candidate/evidence/quality`，并存在有效
`receipt_choice` 后，才允许发独立消费回执、state 3→4 并删除 12 alias。若 probation 的 D+1 consumer 先于 attribution ACK
到达，core 只返回 WAIT；attribution ACK 完成后由 #269 watchdog 精确重试，core settle 后的 D+1 post-settlement seam 再调用
本包 finalizer，避免事件队列先后顺序留下未消费事实。无论是本次调用后的即时 ACK，还是重放时观察到的既有 ACK，
删除前都再次要求 12 alias 全不存在或全等于 canonical；部分/外来 envelope 永远不会被本包清除。consumer 未 ACK 时 canonical
source 保留、state 不推进；hidden event 只重试消费，不发布或补全任何事实。

普通 result 与 PIP 不会二次结算：新 result 只允许当前活动投影 state 1，PIP 只允许 state 2；canonical commit 要求 outcome ID
尚未签发；state 3/4 只接受完整幂等键重放。owner outcome serial 与 consume serial 分开单调增加。archive 不参与 alias
物化或再次结算，只服务历史重放判定与 rehire provenance 审计。

## 6. 已接线与待验收

三个入口现均为 core-wired static-ready：#274 post-consume D+1 arm；canonical result → attribution adapter → 本包 result ABI；
B2 PIP 的四段跨事件 handoff。第二和第三份 #274 可在不清洗旧 tombstone 的情况下自然 arm，因此 rehire 的不同 owner growth
caller 不再被旧 owner 单槽挡住。ordinary #269 直接消费 detailed facts，WAIT/RED 不推进；route C 不发布 outcome，而由独立
attribution cancel receipt 清槽。没有先冻结普通 3.25 result 与真实三维签署归因时，PIP handoff 仍只会 no-op，不能凭 B2
settlement 反向制造试用期事实。

正常离职的独立 HC partition 单元已于 2026-09-01 补齐：#075 在真实 funded/native poststate 后执行
`occupied -> frozen`，并在 D+1 重新读取六分区、formal HC 与 lineage；只有守恒成立才签发
`hc_ledger_settled=1 / hc_conservation_verified=1` receipt。该逻辑不属于 probation 多代 ledger，本包只保留其
immutable provenance；仍须 MCP-first paused snapshot、存读档和自然多周期实机验收，不能把 static-ready 写成 live。

下一步仍必须用新 loader 证明旧 12 个 `used but never set` 告警归零，再做 MCP-first paused snapshot：普通 pass、3.25 等待、PIP graduation、PIP failure、
重放幂等、错 tuple RED、一次消费和 alias 清理。本文没有替代这些 live 证据。

L0 命令：

```powershell
py tools/gen_zg361_workforce_probation_fact.py --check
py tools/test_zg361_workforce_probation_fact.py -v
py -O tools/test_zg361_workforce_probation_fact.py -v
py tools/test_zg361_workforce_attribution_fact.py -v
py tools/test_zg361_workforce_endgame_runtime.py -v
py tools/validate_local.py
```
