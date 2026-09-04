# 361 二期：内部流动与学习 CK3 运行时规格（AH312–322、AI323–333）

## Readiness boundary

- Readiness: `static-ready`
- MCP evidence: `none`
- CK3 live evidence: `none`
- 精确范围：AH `312–322` 与 AI `323–333`，共 22 项。
- 本包已生成可加载的 effect/event/localization，中央 stage 9 已调用唯一 portfolio adapter；静态测试和专用 Python 语义模型证明收据、对象、期限、资源、ACL、关系、本人响应和 Career/HC 转封合同。尚无真实 CK3 paused snapshot，因此不得写成 live 或发版签核。

## 一、独立产物与唯一接缝

生成器 `tools/gen_361_career_learning_runtime.py` 只生成：

- `common/scripted_effects/zg361_career_learning_NNN_<purpose>_effects.txt`（20 个用途分片；每片 1–10 个顶层 effect）
- `events/zg361_career_learning_runtime_events.txt`
- 简中、英文和七份 English structural placeholders，共九份本地化。

测试为 `tools/test_zg361_career_learning_runtime.py`。本包不写 B1、B2、manager/governance、scoreboard、shared case kernel、中央 effects/events/interactions，也保持 no top-level GUI、没有新增 GUI 按钮。中央结算 hook 已调用的唯一 manager-scope portfolio adapter 是：

旧单体 `zg361_career_learning_runtime_effects.txt` 已删除，生成器 `--check` 会拒绝旧单体或未知旧分片。L0 边界测试逐 effect 对照原聚合渲染，证明 125 个顶层 effect 的名称、块文本和顺序保持一致；这只是静态取证，不主张文件体量已经被实机证明为加载故障根因。

```text
zg361_cl_dispatch_direct_reports_effect
```

入口冻结当前 `review_serial`，分别记录**成功打开且首个 deadline 已成功排队**的 AH/AI case 数与完成数。开案失败的受评者不进入 expected，因而不会把摘要队列永久挂死。重复调用同一轮不会重置现场；新 `review_serial` 才建立新 portfolio。本文件不另写第二个中央 caller。

每个逐项 manager callable 都显式要求 caller 传入冻结的 `TICKET_OWNER / TICKET_SUBJECT / TICKET_CYCLE / TICKET_CASE / TICKET_STATE`；绝不在执行时从当前 case 自读一组值再与自身比较。中央接线只应调用 portfolio adapter，不应另造 22 个入口。

纯 Python 权威语义层为 `tools/zg361_career_learning_semantic_model.py` 与 `tools/test_zg361_career_learning_semantic_model.py`。它逐号建模 22 种不同的 typed object、22 个不同的 named consumer、A/B/C 三路线、双付款和容量守恒、期限 resolve、ACL、岗位/导师/继任关系，以及 duplicate/stale/negative no-mutation；`InternalTransferVacancy` 另建模 #312→#314→#315→#319 的同票据、单 HC、真实 liege/title-holder 后置状态。它的诚实边界是 `python-l0-model`，不能冒充 CK3 wiring 或 live evidence。

## 二、权限与第二 AI 例外

1. portfolio owner 必须通过 `zg361_is_celestial_liege_trigger`：天朝制、在任、有地、公爵及以上。
2. 玩家与项目所有者明确授权的第二 AI 例外共用同一 manager effect。合格 AI 只走 hidden event 和 debug receipt，不弹可见事件。
3. 伯爵、男爵仍可作为 `zg361_is_reviewable_vassal_trigger` 的受评者，并可在六张真实 subject-scope 玩家事件中对 314、315、318、319、321、333 做一次本人响应；同 stage 的 314→315→318 串行出现。response effect 只用 subject-self guard，不含 open、advance、manager trigger 或 HC 权限。
4. 伯爵、男爵调用任何 `*_manager_apply_effect` 都得到 typed RED 1；不能借“本人响应”变成考核者。

## 三、两个权威状态机

AH 复用共享 kernel：

```text
posted(1):             312 + 313
  -> applied(2):       314 + 315 + 318，90 日双向试岗窗口
  -> trialed(3):       316 + 317
  -> release_decided(4): 319，一次反 Offer 与 30 日放行期限
  -> moved(5):         320 + 321
  -> alumni(6):        322
  -> closed(7)
```

AI 复用共享 kernel：

```text
budgeted(1):           323 + 324 + 325
  -> enrolled(2):      326 + 327
  -> completed(3):     328 + 329
  -> applied(4):       330 + 331
  -> measured(5):      332 + 333
  -> spread(6, closed)
```

同一 stage 的全部编号先各自形成 receipt，stage dispatcher 再推进一次。任何编号都不能单独跳状态；transition 若未返回 `case_kernel_applied=1`，同一冻结 stage 会重新排期，而不是吞掉失败后停止。

## 四、逐编号真实写入与消费者

| ID | operation | 运行时写入 | 消费/后果 |
|---:|---|---|---|
| 312 | `market.publish_real_vacancy` | 只认领 Career/HC 已成熟 P#114 vacancy，冻结 vacancy/receiver/title 与守恒的单 HC reserve | 无真实 vacancy、接收者失效、战争或 HC 不足转 typed RED 6 + 制度债且零世界变更；#319 真转封后 `hire_once` 结清 |
| 313 | `market.freeze_structured_reference` | 成果、风险、PIP、交接四栏冻结 | 遗漏重大事实进洗绩效审计；泄露/报复进反报复审计 |
| 314 | `market.offer_relocation_package` | 本人事件一次响应，同一 vacancy 的真实 receiver，10/6/4 金币分项、190 日津贴截止 | 接受才把 CL phase 推进为 accepted 并扣组织国库 15 + 经理个人 5；拒绝不收费、回收同一 HC |
| 315 | `market.run_bilateral_trial` | 同一 vacancy 的 source/target、90 日、员工/源经理/目标经理三方退出权、40/60 分功 | 接受进入 trial 但不提前改 liege；退出回收同一 HC，`failed_is_low_grade=0` |
| 316 | `market.freeze_pay_mapping` | 专业底薪 30、原/新津贴 10/5、38→36→35 分期 | 历史实付只读；强制即时降档另记 route，不回写历史 |
| 317 | `market.project_stage_acl` | stage ACL、viewer 数和每次访问日志 | 提前泄露且无新证据降评触发反报复审计 |
| 318 | `market.consume_application_slot` | 正式上限 2、撤回仍占、探索不占 | 经理超时归还名额并重新计算 remaining |
| 319 | `market.counteroffer_then_release` | 同一 vacancy 的 release authorization、counteroffer limit=1、30 日放行、90 日承诺期限 | A 的 D+30 resolver 才执行原版三段式转封并回读 liege/title/holder 后结清 HC；卡人回收 HC 并写经理人才输出 `-20` |
| 320 | `market.aggregate_exit_voice` | 实名/匿名/拒答分栏、同类最小样本 2 | 达样本才审计；匿名隐藏身份；重分类保留原始理由 |
| 321 | `market.maintain_alumni_relationship` | consent、每周期一次维护、lead 幂等、羞辱史冻结 | 同意才扣国库 4 + 经理 2；删除联系投影不删除 `talent reputation -10` |
| 322 | `market.open_returnee_case` | 两个旧案、离职原因、旧舞弊、外部证据、新 cohort | 同一人一个活动流程；洗历史尝试显式 blocked |
| 323 | `learning.allocate_dual_budget` | 金币池 40、保护工时池 20，本笔 10 金币/5 工时 | 国库 8 + 经理 2 双付款；仅结课信用为 0；两池分别守恒 |
| 324 | `learning.advance_three_stages` | completion/application/outcome 三证据与 observed delta 12 | 无 application 时 outcome 和绩效信用都归零 |
| 325 | `learning.assess_practical_competence` | 证书、实操 30、阈值 60、test validity | 证书不替代实操；题目失真追 training owner；不自动 3.25 |
| 326 | `learning.settle_conference_adoption` | 离岗 4 日、产物采用、曝光、机会成本、流失风险 | 国库 9 + 经理 3；采用产物才给组织贡献 6 |
| 327 | `learning.attribute_teaching_impact` | 授课 8/容量 40、听课/应用分栏、60/40 分功 | 份额守恒 100；无人应用时教师绩效信用为 0 |
| 328 | `learning.settle_community_adoption` | 两份产物、一名维护者、6/10 工时、采用团队 | 工时不超容量；采用后才产生跨组影响 |
| 329 | `learning.match_cross_team_mentor` | 一名活动导师、6 工时、容量付款 2、deadline 190 | 最多一次冲突换导师；换后 deadline 仍为 190；应用后才给导师信用 |
| 330 | `learning.settle_reskill_route` | 一名角色、一份目标岗、90 日、50/70 评估 | 两路线都双付款 15+5；外招写公平债；失败不自动 3.25，角色数不复制 |
| 331 | `learning.borrow_protected_time` | 总容量 100、保护 10、危机借 4、交付容量 94 | 仅受评者或冻结 owner 的 CK3 `is_at_war=yes` 事实可借；无战争事实自动走 route C 制度债，不伪造危机；下轮补 4；逾期写经理分 `-10` |
| 332 | `learning.run_safe_succession_drill` | safe simulation、40→50/42、一次 veto | 失败只写 development gap；`real_incident=0` 且不自动 3.25 |
| 333 | `learning.settle_training_commitment` | 成本 24、360 日服务期、每月递减 2、应用证据 | 国库 18 + 经理 6；D+90 自愿离开余额 18，按整除规则返还国库 13 / 经理 5 且只一次；只有 B2 #074 已实付、实际离任、释放 HC 且原因为组织裁撤的事实可豁免；无应用信用 0 |

每项都有独立 `*_core_effect`、六字段 receipt、typed object identity、`*_consume_effect`、`*_resolve_obligation_effect` 与 manager callable。A/B 创建真实业务对象并只由对应 named consumer 消费一次；C 不伪造业务成功，而是创建带 owner/subject/cycle/case/due-cycle 的治理债对象。#333 的 C 是“无绑定但仍由组织出资”的合同，因此仍原子扣国库 18 与经理个人 6，不能借 C 获得免费培训。

## 五、对象合同：不是 marker/string-only

每个 receipt 后必须冻结：`object_kind_id / object_serial`、`object_owner / subject / cycle / case / route`、`object_revision / consumer_revision / state / resolved`、typed relation fields、`acl_class`，以及 `obligation_owner / subject / cycle / case / route / days / pending / resolved`。

`OBJECT_KINDS` 精确映射 22 种对象：vacancy、reference、transfer offer、trial assignment、pay mapping、application ACL/quota、release obligation、exit signal、alumni relation、returnee case、learning budget/progress、competence assessment、conference adoption、teaching attribution、community artifact、mentor match、reskill case、protected-time loan、succession drill、training commitment。

这些对象有可消费语义：#312 不自产 HC，而是冻结 Career/HC vacancy 的 `vacancy_id/owner/subject/receiver/title/maturity` 与单单位 reserve；#314/#315/#319 的 offer、trial、release 都回链该 tuple。#319 route A 的 D+30 resolver 严格 join 四份 receipt，随后在旧 owner scope 依次执行 `create_title_and_vassal_change → change_liege → resolve_title_and_vassal_change`，并回读新 liege、原 primary title 与 holder；三项全真才 `reserved→settled`。#317 冻结 ACL class 与访问日志；#323 同时消费学习金币池与受保护工时；#324 冻结 completion/application/outcome 三阶段；#332 冻结 incumbent=owner、candidate=subject 的安全继任演练，失败仍保持 `real_incident=0` 和 `automatic_low_grade=0`。

#329 会从 owner 的其他直属受评者中选择与本人不同的真实 mentor scope；找不到时写 `mentor_missing/match_failed`，不得把 owner 或本人伪装成跨团队导师。导师信用只在应用窗口结算后产生。关系类 consumer 使用真实 CK3 opinion mutation，而不是只写字符串。#333 的提前离开追缴只在 D+90 obligation resolver 执行，不能为了关 AI stage 在同日提前追缴。

## 六、五元守卫、幂等与期限

所有 mutation 顺序固定为：

```text
frozen-ticket receipt identity -> duplicate RED
owner + subject + cycle + case + expected state against frozen ticket -> stale RED
real-time celestial owner + direct-liege relationship（#319 已结算后，尚未收口的 AH/AI 并行案只允许精确 frozen receiver/title 后置关系） -> permission RED
route/semantic invariant -> invariant RED
Career/HC vacancy/receiver/war/HC preflight（312/314/315/319） -> RED 6 + policy debt
full CK3 resource precheck -> resource RED
both shadow journals reserve/settle -> business receipt -> real CK3 debits
typed object + obligation -> domain consumer -> stage transition
```

receipt 字段为 owner、subject、cycle、case、state、choice。重复或 stale 调用发生在 `record_operation`、金币扣除和领域变量以前。旧 deadline 先走 `zg361_case_kernel_expire_deadline_effect`；过期成功后，resolver 继续携带 deadline 冻结的五元 ticket，重新验证 owner 仍为合格天朝制公爵以上领主、subject 仍为其直属可受评封臣。该 gate 位于 stage runner 最外层，因此即使同段 receipt 已由 manager callable 提前写齐、所有 core 都被跳过，也不能绕过权限直接 transition。身份、状态或实时权限任一失效都不能形成新业务 receipt 或推进 state。

typed RED 固定为：1 permission、2 stale identity/state、3 duplicate receipt、4 invariant/route、5 resource exhausted、6 external mobility blocked/policy debt。

每项还有独立的 post-receipt obligation pending latch。旧对象 unresolved 时，新 cycle 即使拿到不同 case ticket，也会在 record/payment/object mutation 以前得到 typed invariant RED，不能覆盖旧 owner/subject/deadline。到期 resolver 固定顺序为 duplicate → immutable receipt/object identity → 实时天朝制公爵以上 owner → domain resolution；错误 owner、subject、cycle 或 case 不得结算。若冻结 owner 已失去天朝制公爵以上资格，resolver 写 permission RED 与 `obligation_orphaned` 终态并释放 pending，既不替他结算业务，也不让永久失权的旧对象卡死以后所有轮次。

## 七、金币与保护工时守恒

收费编号精确为 `{314, 321, 323, 326, 330, 333}`。每笔先同时预检负责经理的政府国库与个人金币，再分别走共享 transaction journal 的 reserve→settle；**两本 journal 均 settled 后才允许生成业务 receipt**，随后才执行真实 `remove_treasury` 与个人 `add_gold = -N`。任一本 journal 失败会 refund 已 reserve/settle 的另一边；极端情况下业务 receipt 写入又失去 frozen guard，也会 refund 两本 shadow journal，而且真实金币尚未扣除。失败路径不留业务 receipt、不写消费者、不推进 state。

333 的提前离开回收额 18 不超过原 receipt 24；按 L0 `amount * treasury_share // total` 规则，受评者支付 18 后组织国库返 13、负责经理个人返 5，并把 `recovery_settled` 锁为 1。组织裁撤豁免只消费 B2 #074 的真实事实：`reason=1`、subject 相同、国库已付 50、个人已收 50、`actual_exit=1`、`hc_released=1`，且 redundancy state 为已执行/已审计（3/4）。豁免只把 outstanding 归零，不能删除原 receipt 或凭空制造工作应用信用。D+90 时个人金币不足会保持 obligation pending 并在 30 日后重试，不生成虚假的 recovered/resolved receipt。

学习金币池与保护工时池分账；结课标签不能兑换绩效。331 的借用保持 `100 = 94 delivery + 6 remaining protected` 的投影，并把补回期限固定到下一 cycle。

## 八、有序事件队列、本人响应与唯一经理摘要

AH 六段、AI 五段各自只排一个 stage hidden deadline，共 11 个 stage event。每个编号另有一个 post-receipt business/debt obligation hidden event，共 22 个；整个包合计 33 个 hidden event。另有六张真实受评人事件 `zg361cl.314/.315/.318/.319/.321/.333`：只给 `is_ai=no` 的 subject，冻结五元 prompt ticket，一次成功回应后才重跑同 stage；prompt gate 保证同一 stage 同时只排一张。AI subject 走后台默认 A。经理侧仍只有 portfolio digest `zg361cl.390`，不会收到逐下属 22 连弹。

manager-scope portfolio 在 owner 上分别冻结 `ah_expected` 与 `ai_expected`，且只在对应开案和首个 deadline 都成功后累加。每个 AH/AI case 关闭后，先在 subject scope 冻结 completion cycle，再切到 owner；只有该 cycle 等于 owner 当前 portfolio cycle 才累加 completion。至少一域 expected 非零、两域各自 completion 达到各自 expected，且本轮 `digest_shown=0`，才排 `zg361cl.390`。因此玩家每个 portfolio/review serial 最多收到一张可见摘要。合格 AI owner 永远只留后台日志。

## 九、本地化边界

简中和英文是本轮创作文案。法、德、日、韩、波、俄、西只复制 English structural placeholders，保持九语言文件可加载；这七份不是 release-grade 翻译。正式发版前再按仓库发布流程完成七语审计和实机抽检。

## 十、静态验收

```powershell
py -m py_compile tools/gen_361_career_learning_runtime.py tools/test_zg361_career_learning_runtime.py
py tools/gen_361_career_learning_runtime.py --check
py -m unittest tools/test_zg361_career_learning_runtime.py
py tools/test_zg361_career_learning_semantic_model.py
py tools/test_zg361_phase2_manager_talent_model.py
py tools/test_zg361_case_kernel.py
py tools/validate_local.py
```

测试还检查：22/22 精确覆盖、22 种对象/consumer 唯一、11 个 stage deadline + 22 个 object obligation event、仅六个合法 subject-response 读端及其真实 event setter、同 stage 串行 prompt、冻结 ticket 逐层透传、deadline 实时权限重验、pending 防覆盖、transition 同段重试、共享状态迁移、重复/stale 在业务写入前、六笔双付款 journal→receipt→真实扣款次序与 rollback、66 条 A/B/C L0 路径、容量/金币守恒、Career/HC 四 receipt join、原版三段式 change-liege 次序及后置回读、invalid receiver/war/HC 的零世界变更制度债、ACL negative、岗位一次录用、真实独立 mentor、继任关系、333 D+90 追缴与重试、成功开案分域 expected、331 战争事实、333 B2 #074 裁撤事实、伯爵/男爵只响应不管理、玩家单摘要/AI 静默、九语 key parity、UTF-8 BOM 和生成器可复现。

## 十一、后续

1. 中央生命周期继续只调用唯一 portfolio adapter；不得另开 22 个 caller。
2. MCP 尚缺 AH 四项 receipt、Career/HC vacancy/HC、subject immediate liege/primary title/holder、receiver tier/capacity/war 与 settle/reclaim 的同 paused-revision 查询；正式 live 验收必须补该只读 provider，禁止用 OCR 或脚本变量猜测冒充。
3. 一次 CK3 启动批量验证玩家公爵、授权 AI 公爵、伯爵/男爵六类本人响应、无 vacancy/战争/HC RED、真实 D+30 转封、重复、stale、存读档和完整队列。
4. 获得 paused snapshot、debug receipt 与可重复实机报告后，才逐项提升 readiness。
