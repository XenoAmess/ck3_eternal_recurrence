# 361 职业、编制、继任与经理认证 CK3 运行时

状态：**CK3 script static-ready；尚无实机解析、MCP snapshot 或玩家操作证据**

生成器：`tools/gen_361_career_hc_runtime.py`

生成结果：

- `common/scripted_effects/zg361_career_hc_runtime_effects.txt`
- `events/zg361_career_hc_runtime_events.txt`
- `localization/*/zg361_career_hc_l_*.yml`（简中、英文原创；其余七语为日常开发期英文结构占位）

L0 合同：`tools/test_zg361_career_hc_runtime.py`

本层是 `tools/zg361_phase2_career_model.py` 的 CK3 产品投影，不修改旧考核主循环、B1/B2、考核榜 GUI 或共享案卷内核。当前没有真实 CK3 启动证据，因此不得写成 fixture-live、production-live 或“44 项已验收”。

## 一、覆盖范围

本批共接入 **44 个编号**：

| 领域 | 编号 | 案卷 | 主要闭环 |
|---|---:|---|---|
| D | 019–025 | `career_allocation` | 资格、晋升包、奖金/调薪、软 HC、免费京察答辩、转岗、反 offer |
| M | 092–097 | `career_track` | 专家/经理双通道、回专家岗、微职级、年度复审、破格槽、跨团队校准 |
| N | 098–105 | `hc_slot` | HC 分类、结转/回收、冻结特批、梯队招聘、零基重审、占坑审计、来源与 backfill |
| O | 106–113 | `succession_plan` | 关键岗位/关键人才、准备度、代理试炼、高潜可见、两会分离、流失、留任与交接 |
| P | 114–120 | `mobility_onboarding` | 输出积分、匿名申请、90+60 日放人、爬坡保护、试用分账、质量回写、3/6/12 月导师 |
| Q | 121–128 | `manager_certification` | 首任试运行、4-3-3、六项下属评价、接班门、救火工时、四象限、幅度、下轮气候 |

44 项都拥有独立的：

- `zg361_career_hc_mNNN_manager_apply_effect`：上司产品入口；
- `zg361_career_hc_mNNN_core_effect`：五元 guard 后的唯一业务写；
- `zg361_career_hc_mNNN_consume_effect`：把编号写入领域容量、状态与反馈；
- 六字段 operation receipt 加一项本案卷 single-use lock；
- A/B/C 三路：证据路线、政治路线、有期限且留债的延期路线；
- 机制语义字段，而不是只置 `choice` 或跨领域 aggregate。

## 二、入口与接线边界

根线程后续只需在稳定业务 hook 调用以下开放入口，不必修改生成文件：

```text
zg361_career_hc_open_d_case_effect
zg361_career_hc_open_m_case_effect
zg361_career_hc_open_n_case_effect
zg361_career_hc_open_o_case_effect
zg361_career_hc_open_p_case_effect
zg361_career_hc_open_q_case_effect

zg361_career_hc_mNNN_manager_apply_effect = { ROUTE = 1|2|3 }
```

开放案卷时调用上下文必须是：

```text
ROOT = 直属上司
THIS = 受评直属官员
ROOT.var:zg361_review_serial = 当前考核周期
```

开放 effect 复用 `zg361_case_d/m/n/o/p/q_open_effect`，不会自行造另一套 owner、subject、cycle、case 或 state。调用失败只是不写 `zg361_ch_runtime_applied`，不留下半个业务案卷。

本文件没有接进现有 central effects/events/interactions，也没有增加 HUD、顶层窗口或按钮。这样可以跟 B1、B2、经理反馈和考核榜投影一起合批接线、合批启动 CK3。

## 三、权限

### 管理者

所有 open 和 manager entry 都复用：

```text
root = { zg361_is_celestial_liege_trigger = yes }
zg361_is_reviewable_vassal_trigger = yes
liege = root
```

因此只有在任天朝制公爵及以上领主可以拥有/操作案件。入口不写 `is_ai = no`：这正是项目所有者授权的第二个 AI 例外；合格 AI 上司可静默调用相同 resolver，但不会收到玩家事件。

Q 域额外要求受评对象自己也通过 `zg361_is_celestial_liege_trigger`，避免把伯爵或男爵包装成可以考核他人的经理。

### 伯爵、男爵及其他受评者

18 个确需本人确认的编号提供独立 `*_subject_response_effect`。该入口只调用：

```text
zg361_case_kernel_subject_self_guard_trigger
```

它只能在 `var:subject = this` 的活动案卷上写一份自有响应，不调用 open、manager core、stage advance、HC 分配、晋升批准或经理认证。本人响应和上司裁决分别留 receipt；本人不能借响应入口消费上司的编号操作。

## 四、五元身份、幂等与阶段屏障

每项编号都检查：

```text
owner + subject + cycle_serial + case_serial + expected_state
```

并调用共享 `zg361_case_kernel_record_operation_effect` 写入：

```text
receipt_owner
receipt_subject
receipt_cycle
receipt_case
receipt_state
receipt_route
```

本域另有 `receipt_active`，用于禁止在同一状态里先走 A 再偷换 B。新案卷初始化时才把它清零。编号消费者再写 `consumed=1`；阶段屏障只有在本阶段全部编号均已消费时调用共享 `zg361_case_<domain>_advance_<stage>_effect` 一次。编号 operation 自己不能直接改共享 state。

阶段分组冻结为：

```text
D: [019,020] -> [021,022] -> [023,024] -> [025]
M: [092,093] -> [094] -> [095,096] -> [097]
N: [098,099] -> [100,101] -> [102,103] -> [104,105]
O: [106,107] -> [108,109] -> [110,111] -> [112] -> [113]
P: [114,115] -> [116] -> [117,118] -> [119] -> [120]
Q: [121,122] -> [123,124] -> [125,126] -> [127,128]
```

这使每个编号既有独立语义，又不会膨胀成 44 套互不相干的状态机。

## 五、期限

每个阶段使用独立的一组 deadline 变量，冻结相同五元身份和 expected state。手工提前完成阶段时，旧事件稍后触发会因 state 不符成为 stale no-op；它不会覆盖下一阶段的新 ticket。

超时事件均为 hidden character event：

1. 先调用 `zg361_case_kernel_expire_deadline_effect`；
2. 只有精确 ticket 被消费时才进入 timeout resolver；
3. timeout resolver 只给本阶段未完成编号写 route C；
4. route C 留下一项下周期制度债，然后由正常 stage barrier 推进。

P116 的放人窗口不是注释：

- 正常路线保存并实际调度 90 日 ticket；
- 有关键交付和交接依据的路线保存一次 extension，并实际调度 150 日 ticket；
- 两种 ticket 使用不同变量名，旧 90 日事件不能提前消费 150 日案卷。

## 六、资源与实际 CK3 后果

### 通用容量

每域初始化：

```text
authorized = available + used
```

A/B 路各消费一个可用单位，C 路不伪造消耗而增加 `debt`。每次编号消费后重新计算 partition；只有守恒才把 `conserved=1`。结案要求 `completed=authorized` 且 `conserved=1`。

### HC

N 域另有 8 个冻结单位：

```text
authorized_hc = available + reserved + occupied + frozen + reclaimed
```

098–105 每项至多移动一个单位，C 路保持空缺并留债。内部流动只改 slot 状态/来源，不生成角色；外部招募路线才写 occupied 和外部来源。当前层不直接创建 CK3 人物，避免用脚本伪造原版合法角色/职位。

### 双付款

021、025、101、104、112、114、119 是有真实资金后果的动作。A/B 路必须同时满足：

```text
上司 government treasury >= 5
上司 personal gold >= 5
受评者存在 government treasury
```

随后对 treasury 和 gold 各使用一次共享 `reserve -> settle` journal，再执行真实 CK3 转账：上司国库 -5、个人金币 -5；受评者国库 +5、个人金币 +5。两账各有实际 amount/status/settled receipt，同一编号不能二次付款。C 路不付款，只留欠账。

京察/HC 答辩 #023 明确保存：

```text
jingcha_treasury_delta = 0
jingcha_personal_delta = 0
```

其 core 不调用资金 journal，也不扣钱。京察是必须举行但活动本身免费的制度，不应被 HC 答辩偷换成收费活动。

### 结案

每域最终消费者比较证据路线与政治路线的数量，并产生真实 CK3 后果：

- 证据路线占优：受评者获得威望，上司也获得较小威望；
- 政治路线占优：受评者增加压力，上司损失威望；
- 相等：受评者获得少量威望；
- 结论、债务数、容量 partition 和 case revision 留作考核榜/MCP 后续查询。

这意味着编号写入会被后续阶段和结案真实消费，不是 debug ACK。

## 七、关键语义投影

N/O/P/Q 的首批可玩字段包括：

- N：三类 HC、一次结转/回收、冻结例外、occupied/frozen/reclaimed partition、人才来源、backfill；
- O：关键岗位与关键人才分账、四档 readiness、代理权限/容量、本人可读高潜、绩效先冻结、流失分类、留任承诺、知识覆盖；
- P：匿名到 finalist 才披露、90+60 日一次延期、一次终身爬坡保护、试用失败不吃正式 C、三方招聘质量、3/6/12 月导师；
- Q：被评经理必须同样是合格天朝公爵以上、40/30/30、六项可信度评价、接班接受后才放晋升、救火工时守恒、四象限、管理幅度、只影响下轮的气候政策。

D/M 同批提供资格/晋升包/奖金、转岗和双通道的实际案卷入口；它们与 N/O/P/Q 共用同一 receipt、期限和结案框架，后续无需重写内核。

## 八、玩家反馈与本地化

每个编号生成简中/英文名称及 A/B/C 路说明，供后续考核榜职业/HC 页直接消费。结案时：

- AI 上司和 AI 受评者保持静默；
- 玩家上司收到领域结案事件；
- 玩家受评者也收到领域结案事件；
- 事件只概述已产生的资源、容量和下周期后果，不暴露匿名评价者或其他人的私密材料。

七种非日常开发语言仅为英文结构占位，不能称为已翻译或发布级国际化。正式发版前仍需按仓库规则完成七语发布审计。

## 九、L0 门与下一步

`test_zg361_career_hc_runtime.py` 检查：

- 44 ID、六领域、阶段分组与模型 registry 精确一致；
- 11 个生成结果可复现且均有 UTF-8 BOM；
- 每个 open/manager/core/consumer 的权限、五元 guard、receipt 与 write→consumer；
- 所有阶段屏障、真实 delayed event、P116 的 90/150 日分支和 route C 超时；
- 七项双付款的两本共享 journal 与真实 treasury/gold 转账；
- #023 免费；N 域 HC partition 守恒；P 域隐私/延期/保护；Q 域 4-3-3/六项评价/接班门；
- 伯爵/男爵的 subject-self 路径不含任何管理入口；
- 玩家事件与 AI 静默边界；
- 简中/英文原创、七语占位结构、无宗教入口、无新增 GUI。

仍待批量完成：

1. 根线程在稳定 hook 接入六个 open effect 和玩家/AI 路由；
2. 把结案 revision、债、HC partition、释放期限、readiness、4-3-3 投影进现有考核榜内部页，不新增顶层按钮；
3. 先用 MCP/native 查询建立 named action 与变量 snapshot；OCR 不作为导航或状态真值；
4. 与 B1/B2、经理反馈等切片合并后一次 CK3 启动，批量跑成功、B 路、C 路、重复、stale、90/150 日和权限矩阵；
5. 保存 error/debug log、paused snapshot、存档和 artifact 索引。

在上述实机证据完成前，本层只允许标注 **CK3 script static-ready**，不得写成 fixture-live。
