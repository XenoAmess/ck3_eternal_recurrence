# 军事修道会借款本金：exact .4 原生源链

观察于 **2026-10-19T04:34:07.210590Z**，`machine_id: xenoamess-full-tower-eb9d2c1186`，身份来自 `tools/ck3_live_run_id.py`。[小证据](evidence/holy-order-loan-principal-static-chain-2026-10-19.json)记录仓库来源以及实际读取的14条既存 `.4` mapping、detail 和缓存原始字节 SHA。本轮没有读取 EXE、Game、RPC、桌面、活 Driver/SAVE，没有编译、测试、生产源码或 Native26/冻结 SDK/Service 修改。

具体进展是找到了可复用的 `.4` **named fixed-point 本金求值函数族**，不再把这部分笼统称为“所有 `.4` 本金 ABI 都未知”。来源是既存 Prisoner `current4-ransom/named-map01`，其 manifest 明确绑定新 EXE SHA `98702F88…DD518`，14个完整指令跨度均为 `complete_instruction_span_normalized_equal`。本轮实际核到完整393字节的 `37542D0..3754459`，而非由旧 `.3` 地址统一减偏移。

该历史 mapping/manifest 未附机器 ID，本记录将其原机器标为 **`machine_id: unknown`**。可以复用固定字节与调用语义；它不能证明当前机器安装、当前加载定义、实际 getter 执行或借款资格。本轮也未取得一份真实本金报价。

## 事前报价与变量的时点

[已绑定原版定义审计](evidence/p87-loan-actual-install-source-2026-10-18.json)中，`borrow_from_holy_order_decision` 的最终资格比较已使用**借款人 root 的 `holy_order_gold_value`**。该数值表达式可在正常当前玩家作用域中求值，不以先拥有债务或先出现 `amount_to_loan` 变量为条件。后继纯读入口应在任何 Confirm 之前求实际已加载的这个表达式，不能为看报价先借钱。

`amount_to_loan` 则是在 **`holy_order.0200` 的 immediate** 中建立的一天期限角色变量；决议已经执行并打开事件之后它才有此来源。它是 tooltip 输入，不是保存的事件 numeric scope，不是本金锁价，也不是到账。只有实际选择可用的 **`.0200.a`** 才重新求值并调用 `set_up_loan_effect`，写 owed/holder/双方身份/债权人名单，再由贷款人付款。因此事前 quote、事件 tooltip、债务建立和实际钱包到账必须分开读回。

这一时点结论复用2026-10-18、同 `machine_id` 的已安装定义审计；没有把该历史来源更新为本轮已加载定义事实。未来 getter 直接解析已加载 named definition，可以保留真实 mod/版本表达式，不能按旧公式或固定300金手算当前 quote。

## 已定位的 `.4` 调用族

| 作用 | 实际 `.4` RVA / 布局 | 来源和约束 |
| --- | --- | --- |
| named database / lookup | `A07970` / `A07830` | 两个完整跨度87/314字节；仍需固定 key、hash、类型与前后 pointer/key 一致 |
| stable key hash | `3F7E220` | 既有 `.4` named constructor `371D164` 的实际调用；不沿用 `.3` `3F7E240` |
| fixed-point wrapper | `37542D0`，393字节 | RCX=actual definition，RDX=out int64，R8=既有数值上下文，R9和stack5保持既有调用合同；返回 `RAX=out` |
| generic scope clone | `373ACF0` | 完整233字节；复制合法 scope，不接受拿任意零buffer冒充已构造 scope |
| 两个 scratch 支持体 | `3736040` / `3735F90` | 完整130/171字节；处于同一 `0x3D8` scratch，第二个在 `+0x128`，root引用在 `+0x3D0` |
| key source descriptor | `3F79B00` / `3F79DD0`，模板来源 `258BD10` | 复用现有 intern/key-view/32字节 descriptor；不能把缺失参数填成随意 metadata |
| scope / support cleanup | `889700` / `889780` / `9D7340` | 完整118/93/91字节；按现有 owner 清理本地 clone/scratch vector，allocator释放走其既有虚表 `+10` |
| named class identity | constructor `371D100`；primary/secondary `49290B0/49290C0` | constructor266字节；secondary在definition `+88`，hash `+14`、key `+18`、ObDG `+38` |
| evaluation mode / context | `5D1DADC`；context `0x28` | 复用已有 reader 的实际 root/previous/current alias 与 scratch；不能用角色ID代替 scope 指针 |
| 合法玩家 root scope | 既有 `.4` DecisionBindings `889F60` / `87E0E0` | 本地16字节对齐 `0x168` scope，构造后 kind4、零扩展 FullCharacterID；只复用来源，不在本轮执行 |

这里的数值 wrapper 分支已从**实际 `.4` 完整指令**核实：

- `3754364` 读取 definition `+70` 的 expression/provider 指针；非空时 `375438F` 调该对象 `+8` 的虚表 `+30`，随后复制临时 int64 至 out。
- 指针为空时，`375439B` 检查 byte `+7B`。非零则 `37543A1` 取 signed QWORD `+68`；零则写已初始化的真实0。
- `3754435` 返回 out 指针。已有 profiling 分支仍属于原 wrapper，本轮没有执行或修改其开关。

因此不能只移植旧 `.3` loan wrapper 的 `+7C` compiled flag 判断来决定 `.4` 路线，也不能把空 provider 一律报未知或固定非零本金。对 actual `holy_order_gold_value` 的 definition/type/provider 实例仍需未来真实查询；当前任何一条 compiled/constant 分支都没有新的实机观测。

## 角色变量入口与实际欠缺

现有 exact `.4` `BindFamilyBreakIdentifiersImage` 已提供 `variable_context=370EAF0`、identifier table `3F8A7E0`、lookup `3F8A660`、name roundtrip `3F8A6D0`。Character scope 是 kind4、零扩展完整ID；现有 Crown 读器已经使用此 dispatcher，得到 full VariableContext 的 scalar rows `+10`、count `+1C`、clock `+28`，row stride `0x20`、key `+8`、expiry `+0C`。

这些入口可用于自然出现的 `amount_to_loan`、owed/holder 等变量读取，但不能单凭有 dispatcher 就宣称完整 loan typed payload 已闭。后继仍须独立确认所需 row 的类型/payload、缺席与读取失败、期限有效性及 holder/debtor-list 关系。尤其一天 tooltip 变量不能仅因原始 row 还存在就认定有效；时间必须读其真实 expiry/clock/生命周期，不能从某个旧日期推算。现有 `.3` 的 number kind1/payload `+18` 与 holder kind4 是可定位参考，不能直接改标签取得 `.4` 资格。

这条变量路径解决的是已存在的 tooltip/债务观察。**事前本金应直接用 named expression getter**，无需等待变量出现，更不能人为建立变量、修改金币或提交决议来制造可观测输入。

## 最小后继 provider 计划

下一施工应只新增固定 `holy_order_gold_value` 的玩家 root 只读 adapter，复用已存在的 `.4` bindings 与当前 application-main capture owner。输入只需实际暂停玩家及 exact build/frame；不新增 action、任意角色或贷款人参数，不改 Native26 或共享 Service。

1. 解析并核实际玩家完整ID，使用已有原生 root constructor 准备合法 scope。root-only 的构造、clone、scratch 和销毁必须有明确单一 owner。
2. 按 actual named database/hash/lookup 取固定 key，检查已有 `.4` class/key/hash/ObDG 身份；沿已闭 wrapper 求值，保留 signed int64、Q100000 和独立 unavailable 原因，不复算 stock 公式。
3. 在同一次 owner capture 内核前后 player/frame、database/definition/key 稳定性，并按真实 ownership 释放本地 scope/scratch；不析构游戏持有的 definition，不双重清理原 root 与 clone。
4. 只输出 prospective quote。与现有成本/资格 provider 同帧聚合后，才成为后继策略输入；声明成本、债务、到账仍分别读取，quote本身从不计入可花钱包。

现有 `ReadNamedInteractionFixed12004` 的 source/tree 可复用，但其已准备 interaction scope 及角色检查**不自动证明新的 root-only 接线合法**。后继实现要明确 scope 来源与生命周期，不能通过给所有 actor/recipient 参数塞同一ID、仅改root字段或借M6的Sway资格来绕过此项。原函数族和ABI入口已定位；剩余是这个小型 root-only adapter 的具体施工、必要离线资格与后续真实读回，而非重新研究整个数据库或先执行贷款。

本轮交付两份小记录，合计硬32KiB，计原共享 research 额度；没有新增外置工作包、全局预留、测试日志或构建产物，旧 child 均保持 closed。记录按通用策略180天复核归纳；当前机器安装与运行事实不从历史 mapping 外推。
