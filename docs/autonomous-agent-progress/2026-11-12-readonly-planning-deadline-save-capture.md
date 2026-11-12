# 规划期限与已确认 SAVE 捕获接续（2026-11-12）

本单元处理两个独立的真实恢复边界。批次46的原期限为 `14:54:20.8394849Z`；1429只读发布完成后，下一次命令准备在 `RootRuntimeCommands.requireRequest` 命中过期守卫。C59此前已结算，1430中断时没有新动作 INTENT，434 observed／417 eligible／373 saved 保持。随后同局全历史恢复在旧1237捕获处拒绝：捕获 Driver 为276版，回放 retained 仍为275版。

## 最终变化

- 命令准备使用单次时钟判定的专用入口。到达同一原请求期限时产生 `PlanningDeadlineExpiry`；原公开 `RootRuntimeContext.requireCurrent`、操作期限与 Game 校验保持。Planner仅将同一请求且没有 cause／suppressed 错误的载体转成既有 DEADLINE 结果。Controller仍用原单调时钟决定批次 WALL_TIMEOUT；较早请求期限保留原 PLANNER_STOPPED 行为。
- 原发布 scope 可能把 flush 失败附加给 Controller 的内部退出异常。附带此失败时调用已有 `failIo`，保留 WRITER_UNKNOWN／不再调用失败 writer 的行为，不能以正常超时吞掉真实写入失败。
- 原1235 SAVE_CONFIRMED → 1236 BATCH_FINISHED → 1237捕获之间没有下一条 READ，而旧同步仅在后续 READ 触发。新增捕获消费者要求唯一已确认 SAVE、恰一相邻 FINISHED、同批次／session／Game、前后状态与原 reducer 一致、版本仅加1、原 pair／Driver 引用一致，再复用原 SAVE 的完整物料验证。原 READ 校验与捕获最终比较保留；不构造 READ，不修改历史原件或重发 SAVE。

旧 SAVE 物料校验体8555B完整移入私有共享方法，原 READ wrapper 与实际捕获比较区逐字保留。正式 Journal 只移植这个消费者，保留其既有 Native packet 与 coverage 顺序校验差异，不以 active 运行事实授予整个平台通过。

## 已取得的有限软件结果

实际变体66最终五个生产源首次完整编译为30类，67唯一 Journal 为21类。独立测试使用真实 OrdinaryPlanner、SessionController、共享 Clock／SessionClock 与原 `finishOriginalWork` seam；四项完整通过：policy内部过期、较早请求期限、其他／附带异常不误分类、发布失败不二次写入。未伪造 RootContext 发行或 Game 准入；测试不授完整旧1237历史恢复。

生产首编的旧 `CommandUnavailable.operation` serial／Werror失败及部分输出保留；私字段仅加 transient。新载体字段的 transient 是首编前静态修正。测试前两次编译失败分别是缺导入与错误 OperationKey 命名空间，最终只修导入；判定与输入不变。模型仅部分贡献新异常载体主体，其接线三块因双读时钟竞态、错误 trace 类型及吞附加错误而未采用，其余接线为 owner 实现。

机器软件原件：`F/context-deadline66-compile02`、`F/confirmed-save67-compile01`、`F/context-deadline66-whole4-junit01`。F 为 `D:/ck3-state/resume91-native-integration/life-postcondition-p0-20261112-01`；单元汇总 `SOURCES66-67-WHOLE4-ACTUAL-AND-145JVM-COST01.json`。两个 source Ready 和六源精确索引在交付根的 `context-deadline-p0-source66`、`confirmed-save-capture-source67`。

正式变体六个生产源独立编译通过，并复用原Test十类独立运行整4项，首次4P0FES：`F/context66-save67-formal-compile01` 于15:56:13.819740Z释放；`F/context66-save67-formal-whole4-junit01` 于16:01:09.309812Z释放。资格仅覆盖实际调用的期限／Controller／Root completion DATA 路径，不将 actual 的旧1237历史事实转授 formal Journal。

## 后到实际恢复

运行岗保持原 Game／keeper、C59及原动作1422，仅冷 Java 一次采用六源。实际完整 `readSettledSameGame` 入口已通过：1431 `SETTLED_SAME_GAME_RECOVERY` 于15:59:11.9373363Z提交，15:59:22.9131302Z进入LOOP，1432批次47于15:59:28.2742188Z开始，pending为空。原先会拒的历史入口已通过，但原1237没有独立branch flag，不能另造一次分支观测。

运行闭包为 `R/attempt67/ACTUAL-LOOP67-AND-CONTINUOUS-SOURCE64-COST01.json`（10844B／`64f38c92599510c0ca09ca7b0cb9ccc419ca65f26e0eaf8cdaee3e39c4ceb47a`），R为 `D:/ck3-state/resume91-runtime/quarkus-dev307-runtime`。434 observed／417 eligible／373 saved仍为旧C59切点；恢复没有新日或SAVE。Source66未来自然planning-expiry路径尚未发生，不由软件4P或LOOP补授。Source65小型manifest候选仍保留未混入；性能与新增确认保存日另按真实连续窗口记录。
