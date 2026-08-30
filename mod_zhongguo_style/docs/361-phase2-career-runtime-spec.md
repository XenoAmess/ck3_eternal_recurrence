# 361 二期职业、HC、继任与晋升评审 L0 内核

状态：**Python L0 model / static-ready only**

CK3 脚本接线：**未实现**

MCP / fixture / 实机证据：**无**

权威实现：`tools/zg361_phase2_career_model.py`

逐项测试：`tools/test_zg361_phase2_career_model.py`

## 范围

本内核精确登记并逐 ID 测试 phase=2 的 68 项机制：

| 领域 | ID | 共享对象 | 本层冻结的核心规则 |
|---|---:|---|---|
| D | 019–025 | `CareerAllocationCase` | 晋升资格、晋升包、奖金/调薪、软 HC、HC 答辩、转岗与挖角；职级、封建头衔、管理权限、现金、HC 分账 |
| M | 092–097 | `CareerProfile` / `PromotionSlotBook` | 专家/经理双通道、回专家岗、有限微职级、年度权限复审、破格槽和跨团队晋升校准 |
| N | 098–105 | `HcBoard` / `SlotLedger` | 增长/补缺/项目 HC、一次结转、冻结特批、招聘梯队、零基重审、占坑审计、人才来源和 backfill 唯一归属 |
| O | 106–113 | `SuccessionPlan` | 关键岗位与关键人才分离、准备度阶梯、代理试任、高潜可见范围、潜力/绩效分会、流失分类、留任承诺和知识移交 |
| P | 114–120 | `MobilityCase` | 人才输出在真实转出后结算、匿名申请、90+60 日一次延期、一次爬坡保护、试用与正式 C 分账、招聘质量回写和 3/6/12 月导师里程碑 |
| Q | 121–128 | `ManagerCertification` | 首任经理试运行、4-3-3、可信度加权的六项下属评价、继任门槛、救火工时、绩效×价值观四象限、管理幅度和下轮气候修正 |
| U | 157–168 | `NominationBook` | 自荐/主管提名、额度守恒、雪藏到期、部门预审、陪跑、资历例外、观察窗、跨组证据、下一级试岗、撤包、sponsor 信用和难度校正命中率 |
| V | 169–180 | `PromotionPanel` | 专家/外部评委权重、可复现抽席、利益回避、冻结决策规则、盲审、答辩/辅导时数、个人归因、规模/杠杆、双证据、反馈 owner 与冷却重开 |

`MECHANISM_BEHAVIORS` 是 68 个 ID 的显式行为映射。模块导入时会拒绝缺号、多号、错领域、重复行为键或 readiness 冒进。

## 冻结身份与一次执行

所有需要跨步骤变更的案件使用：

```text
owner_id + subject_id + cycle_serial + case_serial + expected_state
```

任一字段不符返回 `stale-token`，不改变对象；同一 `action_serial` 再投递返回
`duplicate-action`，同样不改变对象。两者是合法 no-op，不冒充成功。

命令结构、值域、权限、转移条件或守恒失败则抛出带稳定 `RedCode` 的
`ModelRed`。布尔值不会被 Python 当成整数悄悄接纳。

## 守恒账

### HC / 晋升 / 提名槽

`SlotLedger` 冻结每个 slot ID，状态只能在 vacant、reserved、occupied、frozen、reclaimed
中取一项。reserve 必须先于 occupy；同一 reservation、occupant 或 departure 不可复用。
HC 类型转换只改同一 slot 的用途，不生成新 slot。内部转岗不增加角色，外招才增加角色。

提名额度满足：

```text
initial = used + returned + remaining
```

撤包只有在预审前释放一席；已投入准备工时不返还。晋升槽通过
`reserve -> occupy` 结算；一席不能晋升两人。

### 钱

`MoneyLedger` 满足：

```text
opening = available + reserved + recipient credits
```

奖金、招聘、留任付款必须先预留再实付。京察活动本身在 HC 答辩模型中强制
`treasury_delta=0` 且 `personal_gold_delta=0`。

### 不可冒充

- 抽象职级变化不创建、删除或转移 landed title。
- 专家通道待遇不授予考核他人/HC/复核席权限；经理通道才授予，并扣除个人交付容量。
- 口头 offer、称号或高潜标签不直接增加金币、改正式绩效或占晋升槽。
- 代理试任授予的权限到期收回；成功只提高 readiness，不自动生成永久任命。
- 试用失败与正式员工 3.25/C 配额分别结算。
- blind packet 在解盲前禁止姓名、角色 ID、家族、直属上司和派系字段。

## 测试合同

测试文件动态注册 **68 个独立 unittest 方法**，名称为 `test_mechanism_NNN`，每个方法调用
该 ID 的具体验证情景，而不是只检查 receipt 存在。另有合同级测试覆盖：

- 68 ID 精确集合及 D/M/N/O/P/Q/U/V 区间；
- owner/subject/cycle/case/state 五元 stale；
- action serial 幂等 no-op；
- typed RED；
- 钱、slot 和提名额度守恒；
- readiness 永远声明为 `python-l0-model` / `not-implemented`。

## 仍待 CK3 接线

本层不提供 Paradox scripted effect/event/on_action、GUI、MCP 查询或实机证据。后续接线至少需要：

1. 将 CK3 角色、天朝政府、landed rank、原版合法空缺与岗位/头衔结果映射到冻结 identity；
2. 为 slot、money、hours、packet、panel、trial 和 promise 建立可存档的变量/对象投影；
3. 用既有考核榜 dossier 展示分账、来源、期限、评委票与失败 owner，不新增奇怪的顶层 GUI 按钮；
4. 使用 MCP 命名 widget 与原生角色/头衔查询完成批量跨周期验收；OCR 不作为导航或状态真值；
5. 只有实机 paused artifact 闭环后，才能把对应项从 static-ready 提升到 fixture-live / production-live。
