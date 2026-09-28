# R0313 战局终止只读查询的条件性即时费用零值

状态：**静态门已实现，实机生产者未获准，正式现金仍为 null。**
`ck3_autonomous_player/src/xar_autoplayer/war_cash_termination_query_zero_fee_v1.py`
仅处理正式计划精确选中 `query-war-termination-options-{WarID}` 的情况，当前
Robert 对应 WarID 为 `16777231`。原生桥在
`native_bridge/src/bridge.cpp:16545-16632` 核对查询前后暂停快照，调用
`ReadWarTerminationOptions` 并返回查询结果；此分支没有 gameplay submit。
`bridge/native_driver.py:15978-16049` 把它作为内部只读查询执行，并在返回后
重查同一暂停原生帧。这些源码路径是候选逻辑依据，不能替代正在运行的精确
DLL、driver 和帧身份。

条件性生产者要求：

1. 玩家、episode、snapshot/public/native revision、游戏日期组成的六字段帧有效；
   地图暂停，仅有一个与目标 WarID 一致的活跃战争。
2. 正式计划和建设观测保持该六字段，选定 step、typed
   `read_only_query/war_termination_options/WarID` 完全一致。
3. 接收端已经完成该输出 save/driver 的官方 no-launch 配对。工具从 11 件实际
   文件逐字节流式计算 SHA：EXE、save、driver、DLL、injector、官方 no-launch
   回执、受管会话回执、二进制只读审计，以及 driver/bridge/CK3 查询源码。
   官方 no-launch 的 save/driver/日期/episode/EXE，受管会话的 loaded
   DLL/driver/EXE/injector、PID/创建时间、查询结果 WarID、前后帧与
   gameplay submit 计数，以及审计中的源文件/DLL/source commit 必须交叉一致。
   三份 JSON 均拒绝重复键。
4. 该运行回执的**完整字节 SHA**与对应 DLL 只读派发审计 SHA 均已由人工审查
   后写进模块的两个精确批准表。当前两个表为空；仅提供一份自称 `verified`
   的 JSON 无法过门。

文件哈希与 JSON 交叉一致仅是必要条件；合成测试里对两个批准表的临时注入
不证明真实进程加载关系，也不证明 DLL 由列出的源码编译。现实批准前仍须保存
独立的受管进程 loaded-module 证据、DLL 二进制派发审计与正式来源人工复核。

全部通过时，只能观察到**这一条已执行只读查询**的即时费用 Q100000 `0`。
未结战争占款、未来成本上界、风险预算和战争政策最低保留额仍是 `null`，
`formal_cash_receipt_eligible=false`。任一门不满足时，金额保持 `null` 并返回
明确 `missing_reasons`。本模块尚未接入正式 M5 收据，因为当前 formal collector
没有可信 DLL/driver 运行期身份输入，而且正式规划器尚不生产 `priced_command`
typed 查询身份；不能把计划内自报标志接成现金证明。单测里的批准表注入与
小文件都是**合成夹具**，仅覆盖条件分支，不是任何 Robert 帧的批准或实值。
若收到新的 H2743 受管查询证据，按
[H2743 接收核验清单](r0266-h2743-query-zero-fee-receiver-checklist-2026-09-28.md)
逐件核验；旧 attempt-02 不能事后补造成费用计划。

来源 R0313 H3770 与 R0314 H3774 都没有**输出检查点本身**的 receiver official
rebind/no-launch 和最终可绑定的同帧运行回执，也没有 source hold。H3766 的
输入配对不适用于 H3770/H3774；这些历史元数据不能追填即时费用为零。
普通 Python 与 `-O` 下的专项单测分别覆盖无回执/未批准、精确条件成功、
跨 step/帧、错误 DLL/driver、已发生 gameplay submit、bool 和额外帧字段。
