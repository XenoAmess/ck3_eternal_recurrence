# 四期 R04：县 residual 触发、修正取整与零样本边界（1.20.0.4）

县进入并不保证调用 residual allocator。actual `.4` 县 callback 先保存
`R = s32(B - min_signed(B,S_pref))`，只有 `R>0` 才以 flags0 调用
`2A957E0`。因此普通首选人数已覆盖预算时，应观察 county primary
`24E25EE`；等待县 residual token 不会增加信息。这里的 `B` 和
`S_pref` 已可从同帧的当前原生输入读取，无需新增 DTO 或 hook。

本专题是 exact-build 静态源码结论及下一现场 recipe。没有执行 EXE、
启动/连接游戏、SDK、桌面、构建或复测已验收的 TLS/serializer。自然
actual4 正证据仍由单独现场回执证明。

## 本次来源

来源机器为 `machine_id: desktop-3fevhd2-1c74096080`，任务开始观测
`2026-10-15T17:08:21.558697+00:00`，研究源码 HEAD
`dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb`。本机 EXE 身份复用
`frozen-game-12004/IDENTITY.actual.json`：CK3 `1.20.0.4`、Steam25734779、
SHA256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。
每次窄读前后核同一冻结文件 size/mtime，未重新 hash 整个 EXE。

本次 packet 为 `C:/ck3-e04-resume-20261015-a01/high-parallel-county-a04/`。
`START.actual.json`、各 `SOURCE-FIRST-*.json` 和最终
`SOURCE-FACTS.actual.json` 保存机器、观察时间、argv、原件与指令 pin。
预算和两 getter 的精确 `.4` extent 来自已有独立迁移 ledger；不由
`.3` 减20推算。逻辑 count helper 的第一 pdata 仅32B，保留该 prefix
原件，再按其实际 fallthrough `2A95740`、JE target `2A957D3` 与最小
CHAININFO 完成187B；没有将 prefix 当完整函数或读取相邻函数。

| Source | 完整范围 | 本次新增 code |
|---|---|---:|
| 县 callback | `24E23E0..24E2A6F` | 0；复用1679B |
| residual allocator | `2A957E0..2A95941` | 0；复用353B |
| 县预算 | `24E6650..24E691C` | 716B |
| 有效比例 | `24E6570..24E6646` | 214B |
| 修正倍率 | `24DD9A0..24DDA67` | 199B |
| ordered filtered current count | `2A95720..2A957DB`，三个 pdata fragment | 187B |
| **Total** | 只沿具名实际 CALL/控制流 | **1316B** |

精确新增 metadata、read 次数、source SHA 见最终 source receipt。缓存
PE section map 和已读 pdata row 复用；新 header/full pdata scan、save/raw
读取、whole EXE hash 和 native EXE 执行均0。旧 Z raw 原件本机不可读，
仅其 tracked 独立迁移 ledger 作为范围来源，未冒称仍持有 raw。

## 什么时候县 callback 才启动 residual

到达调用者在首次 `Unit+20=target` 前调用 county callback。其原生上游
准入仍要求旧、目标 Province definition `+1B`、实际特殊 `R9B` 分支和
`24E2230(actor,old,target,mode)`。当前 route condition 是预选输入，
不能观察未来 special flag，也不证明 callback 实际执行。

通过准入后，`24E24B3` 调 `24E6650(CArmy,nullptr)` 得 signed32 `B`。
`B==0` 在 `24E24CA` 直接绕过首选和 residual 分配。非零时，原始
`Army+38/+44` roster 按 occurrence 累加有效 FullID/magic ArRg、且
definition `+2A0<=0` 的 current38 为 signed32 `S_pref`。不得先去重。
其语义预选直接使用现有 `loss_application_inputs_v1.definition_le_zero_soldiers`；
不凭兵种中文名假定该值。

`24E254F..255C` 以 signed32 比较取 `P=min(B,S_pref)`，立即保存
`R=s32(B-P)`。首选的 ordered writer 请求随后才执行，且剩余请求减
`q`，并不减实际物理 debit。首选 writer skip、别名或原始 physical
变化不会重新计算这个已保存的 R。首选完成后，`24E261E..2630` 仅在
`R>0` 时执行：`RCX=actual CArmy+38`、`EDX=R`、`R8D=0`，
CALL `24E262B`、实际 return `24E2630`。

这也区分两个不同的零分支：**县 R<=0 根本不调用 allocator**；
generic allocator 若被其他 caller 以 EDX0 调用，才会在入口
`2A957E0 TEST EDX / 2A957E2 JE RET` 绕过位于 `2A957E8` 的 detour。
不能把县缺 token 写成“观察到了 allocator 的 zero-budget 调用”。

## 县修正参与哪些原生值，在哪些地方取整

`24DD9A0(out,CArmy)` 生产 Q100000 multiplier M。它先调用实际
predicate `24DD830(CArmy)`；true 时直接写 M0 并返回。这一 predicate
的游戏语义未在本包展开，不称为任何特质、免疫或地形。

false 路径以 property ID `0x1A7` 调 `24DFBB0(CArmy,out,id)`，加100000
后按 loaded qword slot `5C68F68` 做 signed lower-bound 选择。
仅当 `CArmy+1D4!=0`，它再加一次 Army property `0x1A8` 和一次
`23036E0(CArmy+1D8 所指对象+280,out,0x1A8)`，随后按 loaded slot
`5C69118` 再作 signed lower-bound。对象+1D8的业务类型、两个下界的
当前值、property ID 的本地化名称以及 getter 内部 owner 选择均保留
unknown。原生指令没有在这里加入100%上界。

`24E6570(CArmy,out)` 从 loaded qword `5C699F0` 取得 base fraction C，
再调用上述 multiplier getter，生产有效比例 F。常见安全整数域中
`F=trunc0(C*M/100000)`，这已经发生一次取整。两原值绝对值都不超过
3037000499时直接乘；其他值走实际有符号 min/max、商余分解分支。
该分支的各乘加保留64位机器结果，不能用 Python 任意精度乘法覆盖。

`24E6650` 按原始有效 ArRg occurrences 以 signed32 ADD 求 W，之后：

1. `24E6702..6728`：`low64(s64(W)*F)` 再 signed trunc0 `/100000`。
2. `24E6735` **另一次调用** multiplier getter；`24E673A` 从 loaded
   signed32 slot `5C68C64` 读 minimum N，`low64(s64(N)*M2)` 再 trunc0
   `/100000`。本包不把两次 multiplier 调用追认为一次实际观测。
3. `24E6759..6762`：两个商先按低32位 signed 值比较取较大，再与 W
   作 signed min。普通非溢出域才简写为
   `B=min(W,max(trunc0(W*F/100000),trunc0(N*M2/100000)))`。

实际县调用传 detail=null；`24E6768` 后的明细字符串构造分支被跳过。
这些预算是整军级，和首选 `S_pref` 是不同集合。最终逐团分配又在
`24E25D7..25DC`、`2A958D1..D6` 做 **signed32 低积 + CDQ/IDIV**，不能
把整军比例分别乘每个团后取整，也不能把 fraction/minimum 的多层
取整合并。

新算术反例仅为 source-shaped 输入：W3001、C5000、M=M2=33339、
N100。先取 F1666，比例人数49，minimum33，最终 B49。将修正和
whole fraction 合并到最后才取整会得到50。它不是本场的 modifier
或兵数观测；`ARITHMETIC-EXAMPLES.actual.json` 保留输入和计算。

## 完整353B allocator 的分支

令当前 pass 输入 signed32 budget Q、flags byte f。`2A95826` 调完整
`2A95720(actual array,f)` 得 M：valid FullID/magic/非-1的原始 roster
current38按 signed32 ADD 累加。bit0要求 definition+2A0<=0；bit1要求
`2A956B0(ArRg)` true。县 flags0 两种额外条件都不启用，故不会调用
`2A956B0`；本包无需展开它。

| 指令/分支 | 实际行为 |
|---|---|
| `2A957E0..E2` | Q==0直接 RET；不分配 token、不保存 scope、不调用 count/writer |
| `2A9582B..3E` | 保存原始 roster count；A=min_signed(Q,M)，D=M，先算下一 pass 候选 `Q_next=s32(Q-A)` |
| `2A95841/51/5A` | count<=0、A<=0或D<=0，跳到 pass 尾，不调用 writer |
| `2A95863..A3` | 按原始 occurrence FullID/generation、storage fallback、magic/非-1 校验；非法项跳过 |
| `2A958A5..C6` | bit0与bit1资格与 count helper一致；不合格项跳过 |
| `2A958C8..E3` | 读取调用前 current C；`q=idiv(s32(C*A),D)`；请求 signed64 `q*100000`，writer return2A958E8 |
| `2A958EF..F9` | A减请求q，D减调用前C；不看 writer 的 physical debit，也不在这里退还 skip 请求 |
| `2A9590D..1A` | 仅 bit0置位且 Q_next>0 时清 bit0、保留 bit1，再从 count helper重算；不是对剩余A或实际未扣人数重试 |
| `2A9591F..40` | restore/RET；县 f0必到此，不再fallback |

q0 **仍调用 writer**；例如当前数 `[1,149]`、Q100，ordered 请求为
`[0,100]`。因此“有 source_complete residual context”只证明进入了这次
source-proved writer 调用；raw request0不是缺采样，且不能替代该调用
的 physical debit。负 q、alias、writer skip 或 state3等特殊效果均以
实际 physical raw before/after 为准，不从预算推得。

## 当前 detour 看不到哪些负例

现有 scope 只借 writer ring 发布上下文，没有新增 allocator-entry ring。

| 现场实际情况 | 现有 ring 能证明什么 |
|---|---|
| 从未到达 callback、上游准入 false、special flag 绕过 | 缺 county writer 不区分这几项 |
| 当前 B0，或县 R<=0 | 无县 residual 事件；不是 observed residual zero |
| generic EDX0调用 | 在 detour前返回，连 scope都没有 |
| 非零 allocator scope，但 count/A/D分支无 writer，或全部项跳过 | scope正常结束但 ring无事件，不能以空ring证明未调用 |
| 首选 physical debit0、或某次 q0 writer | 有 writer row 时可保留本次原始零值；不证明整次县进入总额0 |
| query时相关 ArRg已离开当前 roster、ring已覆盖、capture failure基线变 | 窗口不完整，缺失事件不能补零 |
| writer installed，但 residual flag OFF/未绑定精确 DLL startup | writer布尔本身不证明 residual 可见 |

精确 flagON DLL 的实际 PrepareStartup成功可补上最后一项安装返回证据：
`bridge.cpp` 在 `InstallActualResidualParentHook12004` false时返回FALSE。
仍不能据安装成功排除前述无调用/无writer负例。没有必要为本次现场新增
全局基础设施、负例ring或依赖日期相邻关系。

## 给现场、视频和 agent 的最小 recipe

1. Root唯一现场 owner确认同机 fresh exact EXE/session、a06 DLL及实际
   startup返回，冻结 `XAR_ENABLE_ACTUAL_RESIDUAL_PARENT_12004=ON`；做
   periodic对比时同时用现有 supply-parent flagON。无额外 runtime setter。
   a06构建开关只是来源资格，不冒充本场安装或业务通过。
2. 在开录前的暂停帧保存同一 CArmy/native/public FullID、date/revision、
   当前/第一站 Province、完整 roster，以及 native
   `county_entry_inputs_v1` 和 `loss_application_inputs_v1`。要求 family
   available、同帧 W一致、当前 condition available/true、合法 B>0。
   直接取 native B，不用 GUI5%重算。
3. **county residual 候选**再要求 `B>S_pref`，预期 R=B-S_pref>0；若
   S_pref>=B，选择 primary case，期待实际 raw return24E25EE。两者
   都只是预选；实际 special flag、未来条件和输入变化仍 unknown。
   没有当前合适输入时不反复推进/等待同一无信息 case。
4. 保存 writer sequence及unattributed failure baseline。按已批准的现
   场窗口仅到第一站实际到达；45秒动态拍摄中不插 county query，开录
   前或45秒后取证。Root已有R12/R13镜头调度优先，不由此增开游戏。
5. 同 session暂停后，以未改写的生产 strict normalizer和
   `classify_retained_loss_writer_window_v1` 消费窗口。positive residual
   需 raw inner return2A958E8、`source_complete=true`、outer24E2630、
   flags0、source county_entry、CArmy双ID及实际array FullID匹配，并有
   同一 writer 的完整 unique physical-slot raw before-minus-after>0。
   日期相同、预算相等、军队净少人或 parent token相邻不补因果。
6. periodic仍保留现 strict主标签 `periodic_callback_residual`；用已经
   发布的 outerreturn与flags单列 supply/combined对比，不改schema。
   actual supply outer24E3638/flags2、combined siege/raid outer24E37B3/
   flags0，均与县24E2630独立。共同callback parenttoken不代表同分量。
7. 视频只可说“这次县来源 writer 原始物理槽减少X”；零值明确限定到
   被观察的这一次writer。无事件写 unavailable/unknown；不说“县损耗0”，
   不补整个县/周期总额，不把兵员损失全部叫死亡。agent可把上述同帧
   阈值作采样候选规则，不能把当前预算当已执行账本。

发生身份/路线/编成、combat/event、journal覆盖或失败基线变化时保存
真实窗口并降级，不追认单一原因。所有未知边保留；现有 consumer 的
`county_total_debit`、`periodic_total_debit` 继续为null。
