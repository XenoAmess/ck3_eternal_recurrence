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

中央 dispatcher 后续只接一个 manager-scope portfolio adapter：

```text
zg361_career_hc_open_portfolio_effect
```

调用上下文只有 `THIS = 管理者`。adapter 检查游戏规则、管理者资格、`zg361_review_serial` 与同周期
single-use marker，然后按 stewardship 排序选择**首名**满足条件的直属受评官员；`position = 0` 和单个
`ordered_vassal` 保证一次只选一人。候选人的 D/M/N/O/P/Q 旧案都必须已经关闭，且该 subject 在本周期未被
同一 portfolio 使用。

adapter 只打开 D，不会同日在同一受评者身上并发打开六案。其余五个 subject-scope open effect 与 44 个
`*_manager_apply_effect` 保留为包内 ABI，由生成的串行运行时消费，不再要求中央逐一调用。每个 open 仍使用：

```text
ROOT = 直属上司
THIS = 受评直属官员
ROOT.var:zg361_review_serial = 当前考核周期
```

PP external chain 另有两个公开但非中央 dispatcher 入口：

```text
zg361_career_hc_accept_pp_transfer_request_effect
zg361_career_hc_settle_pp_transfer_effect
```

两者只能消费本包先前生成的完整 vacancy ticket；它们不选择受评者、不授予 manager 权限，也不绕过 P 案卷来源和跨周期成熟门。

开放 effect 复用 `zg361_case_d/m/n/o/p/q_open_effect`，不会自行造另一套 owner、subject、cycle、case 或 state。调用失败只是不写 `zg361_ch_runtime_applied`，不留下半个业务案卷。

玩家管理者的首张 #019 卡在 D+1 打开。每个编号的三条选项只有在当前五元身份仍精确匹配且编号 receipt
成功写入/消费后，才把下一张卡排到 `days = 1`；D→M→N→O→P→Q 使用五个 hidden queue event，先验证
前域已经以原 owner/subject/cycle/case 和最终 state 关闭，再打开后域。领域结案回执占用中间一天，因此前域
最后一张业务卡、结案回执和后域第一张业务卡不会挤在同一天。本包自身任何游戏日最多产生一张玩家业务窗。

Q 只对同样具备天朝制公爵及以上管理资格的 subject 打开；伯爵、男爵完成 P 后直接关闭 portfolio，仍然只有
被考核权，没有经理认证或考核别人权限。授权 AI 管理者不触发 44 张业务卡，而是用相同 manager entry、五元
guard、receipt 和 consumer 在后台确定性结算；资金动作只有双账预检成功才走 A，否则走留债 C。AI 的跨域边
仍是 hidden D+1 event，不会形成可见窗口。

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

### Career/HC ↔ PP 的真实转岗空缺

P 域关闭后，`zg361_career_hc_prepare_transfer_vacancy_effect` 只从现有世界对象中冻结一个候选转岗：受评者本人、其当前 `primary_title`、原直属上司，以及另一名直属于同一上司且爵位更高的天朝制公爵以上接收经理。接收经理还必须有真实 vassal capacity，双方不得处于战争。脚本不创建人物、不复制 flag，也不把“找到经理”这一布尔值当成空缺。

空缺身份完整保存为：

```text
vacancy_id + owner + subject + source_cycle + source_case
+ receiver + title + maturity_cycle + position_kind
```

只有 #114 证据路线已经消费、P 案卷以冻结五元身份关闭，并且 title 的 holder 仍是 subject 时，才发布 `zg361_transfer_vacancy_active=1/status=1`。`maturity_cycle=source_cycle+1`，所以同周期 PP 不能消费刚生成的空缺。已有活动空缺不会被新周期覆盖：相同 ticket 返回 duplicate RED，不同来源返回 stale RED，原 ticket 与 HC 预留均保持不变。

该通道另有一单位独立 HC 账：

```text
transfer_hc_authorized
  = transfer_hc_available + transfer_hc_reserved
  + transfer_hc_settled + transfer_hc_reclaimed
```

准备时从零直接建立一张 `authorized=reserved=1` 的外部转岗票据；PP #190 接受请求会再冻结一份不可替代的 `PP owner/subject/cycle/case/vacancy/receiver` receipt，只把 vacancy `status 1→2`，不提前结清 HC。settlement 必须让 request 与 receipt 六项逐一相等。D+30 ACL audit 调用 Career/HC 的 settlement consumer；中央 phase-2 lane 仍活动时返回 external-blocked RED=6、保留预留并在 D+30 重试。lane 空闲后才使用原版 `create_title_and_vassal_change → change_liege → resolve_title_and_vassal_change` 改变真实封臣岗位，并回读 `new liege + unchanged primary-title holder`。两项后置条件都成立才写 `status=3`、`reserved→settled`；no-vacancy 或 native postcondition 失败写 typed RED 并 `reserved→reclaimed`。duplicate/stale 只返回 RED，绝不改动现存票据或 HC 账。

这里没有使用 `appoint_court_position`：原版接口明确要求受任者以任命者为 liege，而本产品的 subject 在案卷期间必须是原经理的直属有地封臣。强行调用会制造错误日志或假成功。当前可执行路径因此是正式 title/character 转封；不满足该 exact API 前置条件时保持 external blocked/RED。

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

### Q 121–128 的对象与状态权威

Q 的业务状态由本包独占；经理治理包只能读取或做 adapter，不能另写一份“经理认证结果”。每个编号的通用
`*_consume_effect` 在 operation receipt 消费后，恰好调用一次同编号
`*_business_consumer_effect`。后者再次核对 owner、subject、cycle、case、state 和当前 revision，并使用独立
`business_consumed` 锁阻止重复投递。旧 owner、旧 subject、旧 cycle、旧 case、旧 state/revision 均为 no-op。

Q 开案要求受评经理本人也是天朝制公爵及以上，而且至少有一名真实、可考核直属下属。开案时按 stewardship
确定性冻结一名实名下属，分别作为下属问卷样本与继任候选；没有合法候选时 P 域正常收口，不会留下半开的 Q。
因此 candidate 与 incumbent 是两个实际人物引用，而不是把受评经理复制两次冒充“已经有人接班”。

#124 是 vacancy / HC slot / candidate / incumbent / succession / backfill 的权威 join。每个 typed object 都保存：

```text
object_id + owner + subject + cycle + case + state + revision + route
```

succession 另存 incumbent/candidate 两端，backfill 另存 vacancy/HC 两端。#121 和 #127 复用同一本四单位
manager-HC partition；#125 使用一百小时危机 partition。两本账均先检查 available，再移动到
reserved/occupied/frozen，并在每次操作后重算：

```text
manager_hc_authorized = available + reserved + occupied + frozen + reclaimed
crisis_hours_authorized = available + delegated + manager
```

没有容量时只写本编号 capacity debt，不允许出现负数或凭空增编。A/B/C 的差异是业务状态而不只是按钮名：

| ID | A 证据路线 | B 政治路线 | C 延期路线 |
|---:|---|---|---|
| 121 | 小团队试运行，预留 1 单位管理 HC | 直接给大团队，占用 3 单位并留债 | 不建对象、不占 HC，记录延期债 |
| 122 | 70/70/70 的完整 4-3-3 样本 | 90/35/20 的短期结果偏置样本 | 不冻结记分卡 |
| 123 | 六项、三样本、可信度 100 | 单项、单样本、可信度 25 | 不伪造下属反馈 |
| 124 | 实名继任者先验收，HC/backfill 预留后放行 | 先升经理，连续性风险与冻结 HC 留账 | 不生成继任成功对象 |
| 125 | 40 小时亲自处置 + 60 小时授权 | 100 小时全由经理救火 | 不消费危机工时 |
| 126 | 双高象限及对应动作 | 高绩效低价值观“野狗”及风险动作 | 不伪造四象限判断 |
| 127 | 冻结 11 人幅度、增设一层并占 1 HC | 继续扁平直管，保存失真债 | 不改组织层级 |
| 128 | 冻结五项气候并只在下一周期生效 | 保留硬配额，同样只改下一周期 | 不创建未来政策 |

上述结论已有 Python reference model 与生成源静态测试，但仍没有 CK3/MCP 实机证据；“真实人物引用”是脚本
投影合同，必须等 native query 读回 named character、对象 tuple 和两个 partition 后才能升级 live readiness。

## 八、玩家反馈与本地化

每个编号生成简中/英文标题、业务说明及 A/B/C 路说明，既供 44 张玩家业务卡使用，也供后续考核榜职业/HC 页消费。结案时：

- AI 上司和 AI 受评者保持静默；
- 玩家上司收到领域结案事件；
- 玩家受评者也收到领域结案事件；
- 事件只概述已产生的资源、容量和下周期后果，不暴露匿名评价者或其他人的私密材料。

七种非日常开发语言仅为英文结构占位，不能称为已翻译或发布级国际化。正式发版前仍需按仓库规则完成七语发布审计。

## 九、L0 门与下一步

`test_zg361_career_hc_runtime.py` 检查：

- 44 ID、六领域、阶段分组与模型 registry 精确一致；
- 11 个生成结果可复现且均有 UTF-8 BOM；
- 唯一 manager-scope portfolio adapter、首名合格直属选择、同周期防重放和只首开 D；
- 44 张玩家业务卡逐张 D+1、五条 hidden 跨域边、关闭五元校验与同日最多一张业务窗；
- 授权 AI 只走后台 manager receipt/consumer，不触发玩家业务事件；
- 每个 open/manager/core/consumer 的权限、五元 guard、receipt 与 write→consumer；
- 所有阶段屏障、真实 delayed event、P116 的 90/150 日分支和 route C 超时；
- 七项双付款的两本共享 journal 与真实 treasury/gold 转账；
- #023 免费；N 域 HC partition 守恒；P 域隐私/延期/保护；Q 域 4-3-3/六项评价/接班门；
- Q121–128 的八个权威 business consumer、typed object 五元组、实名 candidate/incumbent 分离、manager-HC/
  crisis-hours 守恒、A/B/C、重复锁与 stale guard；
- Career/HC→PP 空缺的 title/character/owner/subject/cycle/case 冻结、跨周期成熟、duplicate/stale/no-vacancy typed RED、单单位 HC reserve/settled/reclaimed 守恒，以及真实 `change_liege` 后置条件；
- `tools/zg361_career_hc_semantic_model.py` 的 Python reference model 逐路线验证对象、容量、资源及 exact no-op，
  并明确标记为 `python-l0-reference-only`；
- 伯爵/男爵的 subject-self 路径不含任何管理入口；
- 玩家事件与 AI 静默边界；
- 简中/英文原创、七语占位结构、无宗教入口、无新增 GUI。

仍待批量完成：

1. 中央稳定 hook 已接 `zg361_career_hc_open_portfolio_effect`；PP #190 已接上述 request/settlement ABI，仍待实机验证 exact title/vassal 后果；
2. 把结案 revision、债、HC partition、释放期限、readiness、4-3-3 投影进现有考核榜内部页，不新增顶层按钮；
3. 先用 MCP/native 查询建立 named action 与变量 snapshot；OCR 不作为导航或状态真值；
4. 与 B1/B2、经理反馈等切片合并后一次 CK3 启动，批量跑成功、B 路、C 路、重复、stale、90/150 日和权限矩阵；
5. 保存 error/debug log、paused snapshot、存档和 artifact 索引。

在上述实机证据完成前，本层只允许标注 **CK3 script static-ready**，不得写成 fixture-live。
