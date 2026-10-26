# M1 后继单题：角色成员写入前，谁验证当前资格？

`machine_id: xenoamess-full-tower-eb9d2c1186`；本次原件/源码回读 `2026-10-26T16:16:15Z–16:19:42Z`。机器和根映射复用本轮 capacity63 原记录，不是本岗重新认证运行中的 CK3。状态 **PREPARED_ONLY / WAITING_REA_SINGLE_BACKEND**。本卡只占 Root 授权的 ≤8 KiB 文档额，不授后端、PE 读取或运行预算；复核期限 `2026-11-02T14:11:19Z`。

机制目标沿既存 exact-build 来源：CK3 `1.20.0.4` / Steam `25734779`，image base `0x140000000`，EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。历史 native 采样缺机器 ID，仍为 `machine_id: unknown`；本轮阅读身份不倒填采样身份。没有新读 PE、启动 backend/Game/Steam/JVM。M1 十叶仅另有 Host compile88 授权的一处测试异常适配；源码自 `16:18:40.400Z` 再次静止，见独立 `resume63/m1/M1-COMPILE88-FIX01.json` 回执。

## 选择及可证伪问题

三条未闭边中，本题选 **persistent validity 的实际调用与先后**。target 重绑最直接影响继承后列表是否出现，但现有 `1B9ACC0` 是 target getter、`1C38A50` 是 targeting 列表输出投影，没有实际 setter/death caller，不能借名称或 vtable 猜入口。成员写入已有真实 26 B seed，可先解决当前成员列表能否被解释为“已经按当前 target 验证过”。loader/default 与 target 重绑继续未知。

可证伪假设 H：包含下述两次成员行写入的 native 路径，在到达写入前，必经该 faction 类型的 **持续成员资格** 检查，且检查使用当前 target、当前角色；失败路径不能写入。首先还须从上游确认 R15/R13/RBX 的实际来源。反例包括：写入的是别种对象；只检查可加入而非持续资格；某分支绕过检查；验证发生在写入后；使用旧 target；继承走另一个 writer。完整局部 body 只回答该局部路径，不能单独证明自然继承 caller、全局更新周期或首次继承后读取已收敛。

## 已有实际数据流与断边

| 边 | 原件/源码已支持的内容 | 当前断边 |
| --- | --- | --- |
| 定义→资格 | `00_factions.txt` 的类型定义使用 common validity；`00_faction_triggers.txt:30–76` 检查当前 liege/active-contract、tier、block/关系；78 起的 join gate 另加年龄、truce 等 | 哪个 native 调用者消费哪一个 gate、何时执行未知 |
| 写入→成员行 | `.4` `2603E46..2603E60` 七条完整指令：取 `[rsp+58]`、乘 `0x20`、加 `[rbx]`；把 `[r15+10]` 写到行 `+C`，再把 `[r13+18]` 写到行 `+8` | 字段角色与既采 ABI/现 reader 的 owner faction full-ID、character full-ID 对应；对象起源、调用者及触发均未在 26 B 内证明 |
| 成员行→native READ | 当前 C++ `ReadMembers:221–250` 读取 faction `+48` 的 `0x20` 行，核 owner `+C`、member `+8`、full-ID 回解；这里不执行角色 persistent validity | 本岗未发现已持原件给出该 writer 的实际自然继承 incoming caller |
| 当前 actor→风险列表 | `ReadSample:797–814` 从当前 actor `+1C0` → land `+120/+12C` targeting IDs，再读 entity `+40` 并要求 target==actor；`998–1030` 双读及前后帧一致 | 读取没有调用 target 重绑或资格刷新；相等双读不证明生命周期更新完成 |
| native→Java→规划 | `FactionReadReplay:113–117` 严格绑定 build/date/native revision/当前 actor；实际语义槽、公开编码及 WarEntry 消费见[本轮接线](2026-10-26-m1-rea-resume63.md) | 不把当前成员 ID 自动升为资格证明；缓存清除不等于 native 继承重绑完成 |

`_factions.info:305–311` 只说成员 heirs 在继承导致 liege/tier 改变时继承 membership、文档默认 yes，不是目标君主接续或 native loader 已读回。当前普通风险读取仍使用真实当前帧；不复制旧成员、不因 targeting count=0 推断旧派系全部消亡，也不把县成员与角色成员混同。

## 可复用的精确原件

以下前缀只是路径缩写，拼接即实际原件：

`F = Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261007/adopted-lifestyle-building-faction-12004/faction/`

`C = Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/shared-span-cache/`

| 相对路径 | bytes / SHA-256 | 本轮用途 |
| --- | --- | --- |
| `F/map01/character_member_add_owner-DETAIL.json` | 5142 / `472f8892bd60fcf43d4383e28c42e1987c2a69fb885e2f4eedbe936b94bef0d4` | 七条 decode 与候选 RF 元数据 |
| `C/new-02603E46-02603E60.bin` | 26 / `2a9e7f93484c4451d221ec4cff672565bf42a942e8e336531bbb42c6c265e143` | 逐条 offset/size/RVA/raw 字节回核，7/7 MATCH，无 call/分支 |
| `C/new-02603E46-02603E60.json` | 444 / `a27ca43728b87ed18449f0ad256a65cadbaf3c72083b7c24fb27c99ac612ee7e` | 历史一次26 B读取，file offset39858758 |
| `F/FACTION-SOURCE-CLOSED.json` | 9547 / `ddf5c817d4e069ffa72c81954fd1d5c0cf21996f059d764208251a8617f7c1cf` | exact-build 来源/operand closure，不是完整决策图 |

当前源码相对仓库 `ck3_autonomous_player/native_bridge/src/`：`ck3_12002_faction_alerts.cpp` 47550 B / `4c9864749fa4e8d887b3ca8d8ec2dae55a4431f184439ee2188b1c68e8f82236`；`.4` 实际绑定 `ck3_12004_faction_alerts.cpp` 4548 B / `4488ceeda98a332b262acc62fbbb5f902f7788c153b8dff73bb2c3a2fb06c5c0`（转调上述共享 reader）。

本次回读的三份原版源仍逐个匹配 [plan90](</D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/m1_research/inheritance90/plan.json>)（8536 B / `c8377df8f5636c5922c08c1795d1f39bd3fe4a87826fa7a6f71a54b332ce2e65`）中的 `info`、`classic`、`common_validity` 精确物理路径/SHA；不是当前 loaded mod 合并结果。named cache 的 `02603/02604` 文件名中只见该 26 B、war getter 和 county-add 等已持片段，未见完整候选 RF；这不是全保留库不存在的证明，REA 先查 retained/cache。

## 交唯一 REA owner 的最小取证顺序

1. 先复用 [REA 实际工作流](../rea-ck3-research/resume63-framework-workflow.md)，查已持完整 body/RF；已有则只分析，不重采。历史 map 仅 `same_ordinal_candidate_only`：ordinal132250，候选 RF `[0x2603AF0,0x26041D6)`，unwind `0x525FD10`。先核当前 exact PE 中包含 writer RVA `0x2603E46`（VA `0x142603E46`）的 **12 B RUNTIME_FUNCTION**，记录真实表项位置；不能把历史 ordinal 当 fresh RF。若边界不符，停止并回报新的包含关系，不自动扩读。
2. 只有边界确认且无已有完整原件时，补该 RF 缺失两段：`[2603AF0,2603E46)` 854 B 和 `[2603E60,26041D6)` 886 B，合计 **1740 B**；复用中间26 B。RF 总长1766 B，VA `[0x142603AF0,0x1426041D6)`。不跟 callee/global data、不重采两个 getter/targeting 谓词、不探索 vtable、不扫全 PE。若现有工具只能重取完整 body，应先明确26 B重复及理由，不能记成全新增/全复用。
3. REA 有界 Rizin 限该 RF，关闭 calls/next/jmp-after 跟随；保留原字节、完整指令/局部 CFG 与 raw Evidence。独立核对每条指令覆盖、实际相对目标及所有 memory store/call，在到达两次写入的每条已知路径追溯对象与 gate 参数。RF、正常局部 CFG、逻辑函数和异常路径分别报告；范围外边保持未知。通用 trigger evaluator 的 call 本身不足以命名为 `is_character_valid`，须有类型字段/参数来源。
4. 已持 incoming 原件若有真实 call-site，则只复用其实际传参和触发证据；本轮不追加搜索。若 body 仅证普通 add，或 caller 未定位，明确停在“局部 writer/验证先后”，不能结案为自然继承链。后续再以真实具体边单独排题。

结果到达后先更新上述数据流和反例，再决定 Java 是否缺实际输入；不预造资格 DTO 或另一套刷新器。此题没有新增游戏日、完整继承验收、性能或 token 收益信用。
