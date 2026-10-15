# 第4期 R06：真实补员 ADD、阶段净变化与每月补员开关

本页绑定 CK3 **1.20.0.4 / Steam25734779**，EXE SHA-256
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。
2026-10-15 离线阅读机器 `machine_id=desktop-3fevhd2-1c74096080`，源码冻结点
`1463bd9b4b89612d283dd45ac4ec9efbf22f048d`。本包按先冻结并 check/render 的有限计划
新增读取 EXE 函数709B、元数据128B，没有启动游戏/SDK、操作桌面或新增实机日；
以下为源码闭合、消费合同和离线反例，**R06 实机仍待验**。
历史文档未声明机器的安装/运行事实按 `machine_id: unknown` 阅读，不能移用为当前资格。

## 四种证据分别回答什么

| 输入 | 可以回答 | 不能据此推出 |
|---|---|---|
| 当前 native permission、fresh fraction、prepared148 | 当前查询实际读到的许可/费率/缓存 | 过去执行了多少 ADD、下一月会补多少 |
| `262C9B0` 的真实返回及 q vector | 这次请求和分支；AL=true 可以 q=0 | 请求已经写进物理 current |
| 自然 `2A98AC0` 独立 entry/return 七槽 | 该真实 callback 窗口的物理净变化 | 指令局部 ADD、正补员总量、Army 总人数变化 |
| `2A98B88` 的真实指令前后与操作数 | 被观察到的这一次物理 ADD | 全窗无漏采、每种条件都覆盖、开关效果 |
| `2633320` 进出 cached current/max | 这次 ArRg 缓存刷新 | 前面的物理 ADD 量；DATA 别名可重复贡献 |

现有 [目标采集合同](army-regular-core-subject-capture-12004.md)只到第三行。
`subject_raw_physical_delta_v1.actual_ADD_observed=false` 保持有效；没有新指令写入 producer。
全局 mapper 的 `capture_complete` 门槛继续保留，局部完整不改成全局完整。

## 已闭合的 .4 指令与整数顺序

精确来源为 [自然 regular-core 专题](army-natural-regular-core-entry-observation-12004.md)
追加引用的有限源包 `capability-lane/regular-core-writers-source-a01`。
该包 `ROOT-DELIVERY.actual.json` SHA-256
`78c24703ddff7155b333ff8db107d9a5727697024469ee2694fca59095b549d5`，
取得时间 `2026-10-15T10:54:29.251941+00:00`，来源机器同上。
它独立取得 .4 四个逻辑函数，不以 .3 地址平移作为证明。

1. `2A98AC0` 按 manager+30/+3C 的 persistent FullID **occurrence** 顺序执行。
   同一物理对象重复出现代表再次计算和写入，不能去重为一次。
2. `2A98B44` 从 persistent+148 读取 signed64 F；`2A98B53` 调用 `262C9B0`。
   F<=0 时 AL=false。F>0 时按物理七槽调用独立 `2657EF0`；许可 true 且
   scaled deficit>0 才写 q slot，并把 AL 置 true。
3. effective current 在 state3/current0 时取 maximum，其余取 signed physical current。
   `d=(int64(max)-int64(effective))*100000`；`p=wrap64(int64(max)*F)`；
   `q=wrap32(trunc0(min_signed(p,d)/100000))`。这里 maximum 是该 chunk 容量，
   不是 persistent+128 整团容量。正 F 仍可因乘法溢出得到负 q；不夹成零。
4. **先计算完整 q vector，再遍历七槽写 current**。q-index 来自 chunk 原始+C，
   与物理槽序号、DATA 选择序号分别保留。多个槽使用同一个 q-index 时，后续合资格
   q store 覆盖先前值；每个 physical ADD 读取最终共享槽，不能逐槽算完即加。
5. `2A98B88`：`01 50 F4`，`add dword ptr [rax-0xC],edx`。
   RSI=Regi，RAX=Regi+28+physical_index*24（十六进制），目标 current 为
   Regi+1C+physical_index*24。这是 DWORD 模加；**写入后没有一般性的 max/zero clamp**。
   请求计算中的 deficit cap 不能当作 ADD 后的通用 clamp。
6. 后续 `2A98BEF`：`4C 89 70 F0`，把 max/current pair 清零。所需条件为 ADD 后
   signed current>=max、raw ArRg ID=-1、exclusion byte=0、由 raw chunk+8
   解析的 owner guard138=0 且 definition magic38!=`4744624F`。
   owner 不强行替换为包含该槽的 persistent。AL=false 时整个 ADD/clear 循环跳过；
   AL=true、q=0 仍会走该循环。
7. 全 persistent loop 结束后才按 manager+50/+5C 的 Army occurrence 刷新：
   `2A98C6C -> 24E8100`，再 `24E816F -> 2633320`。
   `26338A0/26338A3` 写 ArRg+38/+3C 缓存；Character 分支可产生1/1，
   invalid DATA 也可能被移除。这些与物理 ADD、pair clear 分开记录。

以上 q 算术复用 `replenishment_numeric.same_input_chunk_q`，完整顺序复用
`army_scoped_ordered_refill_projection`。它们仍是**条件模型**，源码吻合不会变成原生执行回执。
独立 `2657EF0` 的分支没有被本次有限四函数源包展开；已跟踪
`research/ck3_1_20_0_4_army_support.json` 保留该 getter 的完整迁移证明，
不把未持有的原始 DETAIL 文件说成本包新读回。

## 每月补员开关位于准备路径

[.4 pre-date prepared 专题](native71-army-pre-date-prepared-roster-12004.md)
和 `native_bridge/src/army_pre_date_prepared_roster_12004.cpp` 已闭合实际
`262C680` 的93B函数。原始缓存摘要 SHA-256
`026599cafe4d664859c8953c5f341ccc8c355da6caf4b283136ae249fb460392`。

实际 pre-date `2A9A2C1` 测试 mask02；置位时按 persistent occurrence 调用
`2A9A31C -> 262C680`。该方法依据以下原始条件工作：

- guard138!=0，或 guard138=0 且 definition magic38=`4744624F`：要求
  `262C6E0(persistent,persistent+18)`，固定**物理 chunk0**。
  false 直接写 prepared148=0；true 取 fresh `262CAB0`，从返回 RAX 指向的值读回再写148。
- guard138=0 且 definition magic38!=`4744624F`：绕过 permission，取 fresh 并写148。
- mask02 没置位：这条 preparation 分支不执行，不能把 current fresh fraction
  代替保留下来的 prepared148。

因此，开关不能被实现为“所有 Army q 再乘 enabled”。真正能影响该轮 core 的是
这次 preparation 实际写出的 F；request 与 physical ADD 本身不直接读取一个客户端开关。
开关也不等价于 `2657EF0` 的地域/状态许可，不修改 supply stock、supply capacity，
不控制另一军入场、集结、分合军或独立损耗 writer。不要把恢复补给解释为开关补兵。

本包进一步按获准有限计划实际取得 `.4 262C6E0..262C9A5` 完整709B。
其实际 `.pdata` 是 row132720、unwind5125BA4、flags0，无 CHAININFO；
709B全部解码，span SHA 及指令摘要见[精简来源记录](evidence/episode04-refill-permission-switch-12004.json)。
取得时间 `2026-10-15T14:58:34.366325+00:00`，机器同上。新读取仅此函数709B及128B
元数据，复用已有PE映射与已验 frozen EXE 身份，不重哈希/复制整EXE、不展开外部callee。

permission 的真实局部顺序如下；其中辅助 callee 的业务名称不由本函数单独证明：

| 实际 PC/条件 | 该次 permission 的结果 | switch 会被读吗 |
|---|---|---|
| `262C6F2`：persistent dword guard138==1 | false | 否 |
| `262C705` 的真实返回对象是有效Army，且 byte1D4或1EC!=0 | false | 否 |
| `262C73A`：definition magic38!=`4744624F` | `262C743`直接true；不调用末尾chunk predicate | 否 |
| 上述未返回且 magic相等 | 解析实际补员来源Character，再进入军事组件分支 | 是 |
| `262C7E2`：来源Character+1C0组件为空 | false | 未读到有效switch |
| `262C7F2`：该组件 byte4A9==0 | false | 是；与当前玩家的switch不能混用 |
| byte4A9!=0 | 继续政府/资源raw分支；最后`262C989 -> 2657EF0(original chunk)` | 是；仍不保证true |

来源选择本身也保留原始分支：Regi+130!=-1且Regi+12C==-1时，按完整generation解析
+130对象并取该对象+128的CharacterID；Regi+130==-1且+12C!=-1时直接使用+12C；
其余组合选择-1并按原生fallback解析。Character registry比较的是对象+18完整FullID。
不能把包含玩家Army的每个persistent都当成玩家自己支付/控制补员。

toggle非零后仍可被 raw定义/资源条件拒绝：`28C2DF0`返回对象+40的bit11；
bit42、magic38和bit41组合；特殊`2BAFEF0`返回；Character+1B0所指对象+100负值、
Land对象+318负值、军事组件+4A0负值与definition+118正值组合。
这些callee、定义和资源各自业务含义未在本709B包展开，不把raw位强行命名成某种政府、
金币或其他资源。成功经过这些条件，仍调用独立chunk predicate，不在客户端人工AND两项
已经返回的permission bool。旧 .3 GUI 名称可作定位，不能作为本次实际toggle动作证据。

现在仍缺的是**普通 toggle action 的receiver/caller/validator及独立当前state reader**。
GUI 已勾选的历史静帧只证当时画面，不授本轮动作或效果，也没有可捏造的专名toggle MCP。

最小补缺分别是：

1. 复用现已闭合的 `262C6E0` 开关读取及source SHA，为实际补员来源Character建立只读
   military组件byte4A9读口；missing组件/解析fallback必须保留诊断，不伪作玩家off。
2. 绑定实际原版 GUI checkbox 的合法 native callback/command，和独立当前 state reader。
   不直接改 byte4A9，不把 Invoke/ACK 当开关已改变。动作后必须独立读回，再等下一次自然准备。
3. 在同一新 T0 两条独立正常回放中，enabled+funded 与实际 off 各覆盖相同月机会；
   完整保存 preparation/permission、真实 ADD、独立后态和其他变化。
   只完成一条真实 ADD 仍可授该事件，开关子卡继续 pending。

## 最小真实 ADD producer 与现场判定

无需把完整世界模拟作为一条真实 ADD 的前置条件。有限源码给出 `2A98B80` 开始17B的
指令 seam，结束在 `2A98B91` 分支前；但它**不是普通 C++ 函数入口**。
正确实现须保全全部 live 寄存器、flags、SIMD/XSTATE/stack，原两次 operand load、
DWORD ADD、MOV/CMP 各执行恰好一次，并把正确 flags 交回原分支。
现有函数入口 hook 的资格不能替代这种新 thunk 的独立验收。

每条写入保留 actual PC、Regi pointer+FullID、physical index、raw q-index、真实 EDX、
current/max 前态、紧随 ADD 的 current 后态及 raw bits；可选另捕获 pair-clear。
通过新 active core child TLS 关联自然父 scope、manager occurrence 和 shared event clock。
当前没有已公开的 active core child API，不能声称已接好。目标 cohort 复用当前
CArmy→ArRg→DATA 闭包，不按 persistent political owner 过滤共享物理依赖。

现场还须有实际 machine、PID/create-time、connection generation、episode、GameState、
同父日期/clock/thread、完整 FullID 身份和源/build/安装准入；每个 journal 单独取 fence，
逐日 drain ring4，记录实际 overwrite/drop/failure。缺记录、partial 或身份改变保留 unknown。
一条捕获完整的 ADD 可以作为该条事实，但“整窗补员总和”须另证整窗无漏采。
多个 Army 的 DATA 引用同一次物理写入只能留一笔 ADD，引用关系另列；
重复 manager occurrence 的多次真实 ADD 则分别保留。

## 可复用消费出口与反例

新增 `army_refill_application_qualification_12004.qualify_regular_refill_application_12004`
由现有 observed-phase consumer 发布 `refill_application_qualification_v1`。
它消费现有严格 normalizer 的结果，保留原始 source semantics，按唯一物理 token 对完整
七槽 endpoint 差做数学求和；不 wrap/clamp 净差，不把 DATA 别名重复求和。
无新 writer 合同时，它始终发布 `actual_ADD_observed=false`、
`applied_positive_refill_soldiers=null`、`no_ADD_proven=false`、
`toggle_effect_proven=false`、`continuous_window_coverage_proven=false`。
现有 schema 没有 runtime session guard 字段，因此也不伪造当前 runtime 绑定。

有意义的反例包括：90+10 后清零得到 current净差−90；整数 q=0 仍能启动整个 dispatch
并清另一槽；重复 occurrence 从80→90→100；共享 raw q-index 被后续槽覆盖，前槽甚至
可越过自身 maximum；signed wrap 后 endpoint 数学净差不等于 ADD 操作数。
这些是条件源码反例，不是声称正常游戏已经出现原始 ordinal 碰撞或溢出。
16项新聚焦测试及一个真实严格 normalizer→候选 consumer 接线检查通过；使用既有
fixture factory 只构造新输入，没有重跑旧测试或新增实机信用。

外置交付引用 `high-parallel-refill-a01/QUALIFICATION.actual.json`、相对补丁及
`CONNECTED-OUTPUT.actual.json`，机器同上。父容量准入是共享512MiB池内8MiB上限；
本包实际小于0.3MiB，按通用策略在 `2026-10-16T07:45:01.597Z` 复核，不自动续期。
Root 在运行现场退出并解除 clean-checkout 冻结后合入候选；本包未写主树、提交或推送。


Future a07 已接成来源绑定的生产查询/DTO/序列化和严格消费者候选，含原生十二例离线验证；见[补员开关观察叶子](episode04-refill-permission-switch-observation-12004.md)。尚未部署，不增加本场 toggle/action/actual ADD 业务资格。
