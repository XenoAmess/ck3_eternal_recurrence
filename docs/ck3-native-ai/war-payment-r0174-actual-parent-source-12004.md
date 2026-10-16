# CK3 1.20.0.4：R0174 四输入实测与真实父链

本轮第一次实际保存了个人 ADD 的四个原始输入及其真实父栈，且沿该栈补齐了闭包到角色结算的来源链。**四字段的生产者、军事已付分量及日/月周期仍未闭合**，`maintenance_attribution=unclosed`。本轮只读已完成包与具名有限 EXE 地址；没有接游戏、SDK、桌面、重哈希整 EXE 或修改主树。旧研究见 [raw context 合同](war-payment-generic-context-12004.md) 和 [getter/cache 来源边界](war-payment-maintenance-cache-source-12004.md)，其当时未知事实保留原样。

精确游戏为 1.20.0.4 / Steam25734779，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。机器 `desktop-3fevhd2-1c74096080`；来源主树 `1463bd9b4b89612d283dd45ac4ec9efbf22f048d`。完整运行身份、实际时间、字节及 SHA 见 [FACTS](acceptance/2026-10-16-r0174-maintenance-source/FACTS.actual.json) 和原始严格 consumer 回执。

## 唯一实际 callback

R0174：PID17468/create134365505726865638/gen1，actor31254，window1/epoch1，episode `native-31254-0d067159706e`。day17 和 day21 保留的 seq12 是同一份深层类型与字节均一致的 callback，**只计一次**。day17 查询 public53/native52/date53145456；day21 public63/native62/date53145552。独立配对 before snapshot 与原始 cash 复用 [已入库原始JSON包](evidence/episode04-r0174-20261015/r0174-original-json.zip) 的四个精确成员，见 [成员字节/SHA路由](acceptance/2026-10-16-r0174-maintenance-source/RAW-ARCHIVE-MEMBERS.json)，不重复复制大回包。完整 witness 与 [day17严格原件](acceptance/2026-10-16-r0174-maintenance-source/day17/STRICT-CONSUMER.actual.json)、[day21严格原件](acceptance/2026-10-16-r0174-maintenance-source/day21/STRICT-CONSUMER.actual.json) 均为直接文件。原 consumer 未把 Root 后给的 window1/epoch1 写为独立期望；追加 verifier 显式检查这两个固定值，绝不重写旧回执。

| 实测项目 | 原始结果 |
| --- | --- |
| 类型及 caller | kind2 personal ADD；return RVA28A6D7C |
| secondary context | `*(Character+1C0)=2867562606880`；before/after identity 均相同 |
| raw signed64 `(2C0,2C8,28,30)` | `(500974,0,218610,0)`；before/after 相同，complete/stable，failed0 |
| 算式 | `500974-0-(218610+0)=282364`；与 actual ADD 参数一致 |
| 当前个人账户 | actor31254；gold `25166043→25448407`，whole callback delta282364 |
| clock/thread | identity140715344921080；sequence47976876→47976877；thread16496 |
| 实际 callback 日期 | native low32=53145456；absolute_day389394；这不是周期证明 |

公式与账户只闭合这笔带符号入账；不能将任一项或差值改名为收入、军事月费或已付维护费。kind2 没有进入 boarding qualified debit；这里没有 Army natural parent，不用通用 ADD 冒充军队事件。day17 retained12、day21 retained15，natural read_complete/no loss 只说明已保留窗口，不说明覆盖所有付款来源。

## 实际来源链

所有原始指令与 SHA 均以 [SOURCE-SPANS](acceptance/2026-10-16-r0174-maintenance-source/SOURCE-SPANS.actual.json) 为准；它提供可移机的原始 hex，不依赖本机盘符。每次离线 plan、实际 check/read/failed receipt 收于 [source archive成员索引](acceptance/2026-10-16-r0174-maintenance-source/SOURCE-ATTEMPTS-ARCHIVE-INDEX.json)，按索引中的相对路径安全提取；历史 executors 只供阅读，不作为新 run 的命令。

| 来源 | 本轮实际闭合 | 仍有边界 |
| --- | --- | --- |
| 28F7840..28F7C9E，1118B完整父函数 | RDX为Character；28F7934 `CALL28A6D10`，return28F7939；读 `*(Character+1C0)` | 无四目标字段直接 store；其他 transitive callee 没有全面展开 |
| 28A6D10..28A6F4E，既有574B | 四输入算式；正值28A6D77 `CALL285EE40`，return28A6D7C | 既有源 SHA `f2e377a5e4948042852a95bd5b4e0fe3d38159defb8eb5f823ec0fabb33fe348`；没有新命名或日期信用 |
| 3978C00..3978C53，83B | 3978C47 `CALL3978BB0`，return3978C4C | 通用16B闭包包装，无四字段生产 |
| 3978BB0..3978BFF，79B | 3978BF3 `CALL39798E0`，return3978BF8 | EDX计数的递归包装；不能把相邻栈帧当直接CALL |
| 39798E0..39798EA，10B叶+6INT3 | `mov rax,rcx; mov rcx,[rcx]; jmp [rax+8]` | 动态闭包目标须结合真实构造来源 |
| 290DC00..290DDD5，469B | task=RCX；290DC45取显式290FD20；构造闭包并于290DD41调用3978C00，return290DD46 | 任务chunk/index分发；task+68是数组描述对象指针，不能凭旧标签叫callback函数 |
| 290FD20..290FD3D，29B叶+3INT3 | 取index；RDX=描述对象首指针所指 array[index]；RCX=task+70 inline context；290FD38直接 `JMP28F7840` | 不写四字段；没有把 task context 当 secondary context |
| 3F909F0..3F90AED，253B完整上游 | 原子claim/计时；RCX=*(job+38)，3F90A6F虚调用 `[(*RCX)+10]`，return3F90A72 | 原始栈支持实际下到290DC00，但未采运行时vtable slot原值；不能伪造静态直接边 |

完整父函数在个人 ADD 之前只对 secondary context 的3E8/3F0作直接更新；这两个 offset 不属于四目标项。后面的4A0/资源4及 currentMaintenance2C13F60 分支发生在结算调用之后，不能倒算成先前 personal ADD 的军事分量。Root 另派的唯一后续 callee `28F7BDA→28A6F50` 现以 [完整110B合同](acceptance/2026-10-16-r0174-maintenance-source/CALLEE-28A6F50-FINAL-SOURCE-CONTRACT.actual.json)、[source HEX](acceptance/2026-10-16-r0174-maintenance-source/CALLEE-28A6F50-SOURCE-HEX.actual.json)、[完整asm](acceptance/2026-10-16-r0174-maintenance-source/callee28A6F50.complete.asm) 和 [原始子包索引](acceptance/2026-10-16-r0174-maintenance-source/CALLEE-ORIGINAL-ARCHIVE-INDEX.json) 落地；它使用 Character+1B8 且具有另一 wallet return28A6F94，不能把本 seq12 的值套到那笔事件。

2026-10-16来源现状补注：后段scalar现已接至[SubC合同关联角色的递归贡献](episode04-r08-contract-contributions-12004.md)，再与当前向量slot9做差。[独立语义审查](episode04-r08-semantic-attribution-audit-12004.md)确认这条静态连接仍未给本次先前NET的军事分量、付款账户或周期授值；本页唯一seq12及其历史边界保持不变。

实际18帧中11帧为同EXE。真实关键链是 `28A6D7C→28F7939→3978BF8→3978C4C→290DD46→3F90A72`；后续外层仍有调度器。这里已闭合具体闭包桥，不把同 image/OS unwind 或固定数值当作生产者语义。fixture 的 `28A1234` 从未用于此 live 链。

## 下一步可施工入口

[NEXT-PRODUCER-OBSERVATION](acceptance/2026-10-16-r0174-maintenance-source/NEXT-PRODUCER-OBSERVATION.contract.json) 是未实现方案，不是采样完成事实。[精确parent hook锚点](acceptance/2026-10-16-r0174-maintenance-source/PARENT-HOOK-SOURCE-ANCHOR.contract-a01.json) 仅为来源证据及未来方案，未实现/未ABI验收：已证16B完整指令前缀无RIP-relative；父入口原始native return预期3978BF8（两级tail jump），不能误填settlement内部return28F7939。最小现有 hook 扩展可在已证28F7840 entry保留 RCX/RDX/R8d 与 native return、同一 Character secondary context 四值及前后身份，继续使用 clock/session/TLS和 original-once 边界。entry/exit 比较只能定位刷新发生在哪个边界，不能命名 writer。

要直接找到字段生产者，下一独立 cold window 可限定为同一受控 Character 的新鲜 secondary context 四个 exact8B data-write watch，记录真正 writer PC/寄存器/旧新值/线程/日期/epoch及丢失情况，再仅对该 PC 建有限 source plan。该设计尚需观察器实现、debug状态/线程覆盖/指针失效合同和ABI冷夹具；不占用现有探针槽、不复用本session绝对指针、不凭无事件称无producer。若只有 callback thread 的观察资格，不可外推其他producer线程。

目前不能关闭的三个业务点分别是：四term的写入及失效来源；其中哪一项来自实际 military applied component；该 component 经哪个真实 payer wallet store、以什么调度周期结算。当前军事费率 getter 及数值相等不能补这三条边。

## 保真与复用

本轮四个 source scope 分别满足8192code/512metadata/48read上限，合计2050 code +1132 metadata bytes /117 reads（包括失败/partial attempt）。initial16B叶片因末条指令不完整返回rc1并原样保留；之后只读两个明确8B续片，最终29B指令+3INT3闭合。没有整image扫描或哈希。部分复用 reader 的人类 reason label 留有旧地址，receipt的数值地址、plan、原始 bytes与SHA为准；FACTS逐项记录该限制，旧回执不改写。

可复用的是原始 source hex、严格输入/拒绝合同、当时 actual packet/witness 与证据边界。绝对指针、PID、epoch、桌面和构建选项不迁移成另一机器的运行验收。本目录 verifier 用 stdlib、require/raise，在 Python `-O`下执行；只复核包完整性、实际 fixed scope 身份和 raw事实，不把机器检查写成人工签核或军事归因。

## 普通 clone 的离线复放

从仓库根目录运行（Python标准库及仓库自身模块，无CK3/SDK/本机C盘依赖）：

```text
python -B -O docs/ck3-native-ai/acceptance/2026-10-16-r0174-maintenance-source/verify_replay.py
```

校验器验证 [最小文件清单](acceptance/2026-10-16-r0174-maintenance-source/FILE-MANIFEST.json)、两个源码历史archive全部成员、四个原始JSON成员及canonical文档全部链接，并从普通仓库相对路径调用真实production normalizer复放day17/day21，明确检查Root指定window1/epoch1，最后仍输出军事归因unclosed。原始consumer回执中的C/D盘路径仅作历史来源；复放不读取它们。源码archive包含历史本地执行器，不能将其作为新现场运行命令。

若要阅读展开的原始plan/failed/read证据，可追加 `--extract-source-attempts NEW_EMPTY_DIRECTORY`；目标必须不存在，提取会保持成员路径并拒绝越界路径。无需展开原始cash大包，复放只在内存读四个具名成员。子包及parent hook均仅提供partial/future边界，未实现新hook、没有新增现场调用。
