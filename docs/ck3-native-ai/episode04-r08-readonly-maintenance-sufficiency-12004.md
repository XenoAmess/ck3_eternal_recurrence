# R08：现有只读字段足够做什么（1.20.0.4）

结论：现有 a36 接口能读费率、四 raw 和已保留的个人钱包回调，**不能单凭这些字段给出军事已付金额、军事付款人或日/月结算周期**。当前实际样本还反证了“把 c 或 c+d 直接替代当前军费率、把四 raw 算式替代当前月 NET”的数值同一假设。新增纯函数把这些快捷推断显式保持为不允许，不修改原 payment 资格。

本次审阅机器 `desktop-3fevhd2-1c74096080`，2026-10-18 22:37–22:50 UTC，源 `bc4604bed4eb8558b3f4e0e554a642aa69a4ba2f`。原游戏身份为 exact1.20.0.4/Steam25734779/EXE `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。未读取新 EXE、SDK、游戏或桌面，未构建、写主树或重跑旧矩阵。所有原片段/字段与 source blob 见[小源索引](evidence/episode04-r08-readonly-sufficiency-12004/source-index.json)，实际数值见[便携投影](evidence/episode04-r08-readonly-sufficiency-12004/actual-projection.json)。不同机器只能复用代码/来源，不能继承安装、构建或运行资格。

## 已有接口与真实反例

现有工具为 `ck3_query_war_cash_current_resources_private_v1(expected_revision, payment_sampling=None|enable|disable|query, payment_window_contract=None|same_owned_process_no_load_v1)`。注册还要求公共 host 的 `war_cash_queries=true`。普通查询没有自动 enable；`query` 只读已保留 journal，不能产生缺失的历史回调。enable 是既有显式采样控制，须另有当场准入，不是新的付款动作。

R213 原 source3661/R0208/PID27056/gen1/actor33388、date53148408/public137/native136，原 episode=null。具名现金原件仅5159B；摘要7249B。没有采样控制、自然日或 DR，journal未出现。完整 raw 子项的 admission/same-frame/complete/stable均true、failed0：

| 原字段 | 实际 raw | 数值比较的结果 |
|---|---:|---|
| secondary+2C0 / +2C8 / +28 / +30 | 359440 / 38623 / 310999 / 0 | 四项只具有 signed64 raw 合同；各项 scale/time basis未赋业务名 |
| wrap64(a-b-(c+d)) | 9818 | 不等于本帧 getter 月 NET32540；本帧没有付款callback，9818不是实付或实际入账声明 |
| gross / total expenses / NET | 469940 / 437400 / 32540 | 三项为scale100000的月率，NET=gross-expenses |
| current military gold / all-raised military gold | 386622 / 493650 | 两种独立情景的月率，不能相加；c+d310999也不等于两者 |

这仅排除该帧字面数值直接代填，不证明时间基准、单位、刷新滞后或其他数学变换，也不证明 raw term 与费率全无关系。当前 reader 的顺序是 Gold→MonthlyFlow→current military→all-raised→raw context；raw helper本身只读内存，不调用getter或创建callback。它不是 getter之前与之后的原子包，未展开getter副作用也未被本稿排除。

Agent 可在生产 `normalize_war_cash_current_resources_v1` 后调用：

```python
from xar_autoplayer.bridge.war_payment_readonly_sufficiency_v1 import assess_readonly_maintenance_sufficiency_v1
assessment = assess_readonly_maintenance_sufficiency_v1(validated_current_cash)
```

`literal_value_equal` 保留实际相等/不等/unknown；`may_substitute_c_or_c_plus_d_for_current_military`、`may_substitute_four_raw_formula_for_monthly_net`、`may_infer_paid_from_rate_or_net_or_owner` 始终false。数字碰巧相等不构成因果链；缺 raw 保留null而不是0。这是只读充分性判断，不是新业务门禁、live planner接线或付款验证器。

## 付款账户与军事付款人要分开

`current_treasury` 在该reader是 stock GetGold 的个人余额，不能与军事向量slot6的treasury混用。source读取 `*(Character+1B0)+100`；既有 personal callback读取同一个 extension+100，并核 receiver+8与它alias。真实 callback还保存Character/fullID/magic、amount、caller、entry/return余额、clock/thread/session/date。

现有四个R195/R196 terminal journals的便携typed消费只有两次ADD205712（两条独立时间线同日53148336/absolute389514，角色31254）和一次已闭登船SUB300000。两次ADD的原四项均423188/0/217476/0，真实余额25804687→26010399。它们是同日跨臂复现，不是同一时间线的重复周期。ADD角色是收款主体；不能叫付款人。

如果未来已保留的 `kind3` 真有 `caller_return_rva=28A6E05` 或 `28A6EC2`，现有 hook/DTO已经足够保存这一笔 **raw c-share或d-share的SUB参数及实际被借记账户主体**，不必为此新增hook。必须重新核同Character/fullID/extension/wrapper、whole-callback余额、原函数确实返回、完整window/session/clock及无丢失；不用窗口actor替代record主体。当前四窗这两类实际记录为0，不代表没有军费或没有其他账户路径。raw-share角色不等于军事类别，因此军事payer仍null。

负支当前确有字段缺口：`war_payment_passive_12004.cpp::Invoke` 只在personal_ADD且caller28A6D7C时捕获 `generic_wallet_context_v1`；两个personal_SUB没有这一四raw child。DTO的parent只有boarding transition/gateway，**没有 settlement parent entry token**。同日、同线程、相邻journal序号或相近QPC不能把两个SUB并成同次结算。

若以后只需补负支 raw，这个最薄接口改动位于既有 `Invoke` 的 `Capture(before)`之后及after读取处，沿原personal_SUB exact两个caller增加一个可选、明确raw-share角色的context child，并同步strict serializer/consumer；它不需要新的 detour，但需要新DLL构建/资格。它仍不能制造军事分类、原始writer或完整settlement token。本包没有实施该native扩展。只有需要同次完整结算时才考虑旧[28A6D10 entry/return合同](war-payment-net-settlement-allocation-12004.md)，不把该桥当军事来源替代品。

## Cadence 的唯一源链断点

3978BF8不是新PC。旧[完整闭包链](war-payment-r0174-actual-parent-source-12004.md)早已保留79B3978BB0（3978BF3 CALL39798E0、return3978BF8）、83B3978C00、29B290FD20、469B290DC00和253B3F909F0。此次复用，不重新读取EXE或计新source。

正常路径上 `290DC00`按task+14数量和+1C chunk原子分配index；task+68是数组descriptor指针，task+70是inline job context。`290FD20`取该index的Character，以RCX=task+70、RDX=Character、R8D=index尾跳28F7840。28F7840初段正常分支汇合到28F7934调用settlement；index不是日期，task context也不是Character secondary context。3F909F0的原子job claim/耗时计算与虚调用没有提供结算calendar门。这些是所列完整body的直接合同，不抹掉opaque helper或上游选择逻辑。

**未证的唯一调度输入是“谁按什么calendar规则构造/选择这个Character数组并将task入队”。** 当前cash/payment DTO没有task实例、selection/enqueue source或calendar predicate；保留callback日期只能证明该次发生时间，且不会记录所有零钱包结果的settlement机会。继续追相同包装器不能补出频率。现有字段不能通过改query参数读取这些缺项，也不提供任意地址读取通道。

下一份有信息量来源应是该task的真实构造/选择/入队producer PC和同代实例的来源连接；其PC当前NOTHELD，故不猜地址、不扫描text、不新增泛化审计。旧28F7840入口方案可补已选Character/context/index边界，但单独该叶仍没有array selection/enqueue calendar规则。若只做有限观察，应把“本时间线哪些日期保留了哪些callback”和“完整机会覆盖”分别记录，不把两次同日跨臂ADD升级为月结周期。

军事分量仍另缺 `context+28/+30` 的真实writer与业务来源。既有外部四槽write-watch已含c/d，不需新DLL hook；但原a07不支持ordinary null episode，维护v2仅源码/离线compound，新standalone observer EXE/SYSTEM/cold资格截至本次审阅NOTHELD。a37 bridge构建不生产该独立observer。不能把managed alias写回原null episode，也不能把四槽零命中解释成无writer。

## 给开发与视频的结论

当前可直接复用：现有cash查询与typed callbacks、原raw/NET对账、账户主体观察、新纯函数的禁止快捷替代标志。不能从当前rate/raw输出构造 `military_paid_raw/payer/cadence`；三者继续null。a36生产元数据18,411B/62375…确有cash/private/passive/generic/raw4 flags ON；a36编译源7a到本稿bc460的八个payment/cash具名文件diff为空。a37截至本次只有失败构建来源，不授新能力；具体元数据见[build status](evidence/episode04-r08-readonly-sufficiency-12004/build-status.json)。

可用旁白（两句）：同一时刻的军费月率、钱包净变和实际付款是三种证据，不能直接互换。现在能读前两者和部分钱包回调，军事分量进入哪次账户结算以及结算周期仍需来源连接。
