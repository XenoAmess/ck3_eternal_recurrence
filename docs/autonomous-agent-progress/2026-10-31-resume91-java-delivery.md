# resume91 Java 交付

machine_id: `xenoamess-full-tower-eb9d2c1186`。owner `/root/java_delivery91`。用户已明确继续；本岗负责 `D:/r64d` 正式 Java 交付，运行 S/MB/Game/账本仍由 runtime91 独占。

接手时 `D:/r64d` 为干净 detached `c2acd518ab3290a74607a0b49baba045e802bf24`。本地 GUI `59a7d302`、fixture `6bc7b918`、status `c2acd518` 三个提交完整保留。Native GUI 前置已由唯一 owner 正常发表为 `b87c3ad783`，随后本岗普通 fetch/rebase/fast-forward push exit0：新祖先依次为 GUI `e1d37b1857`、fixture `543bc7e1d5`、status `c627799172`，远端 master 更新到后者。没有全树 reset/stash/stage；源码发表不代表 Native DLL 部署或 Game 新行为。

## 当前有限验证与本地模型任务

- 原 `java-json-fixture` 模型响应实际编译失败：静态方法调用 `getClass()`，以及非法 `List<byte>`。以当前 `D:/r64d` 的真实 `NativeWire.java` 和候选单测试同编，未读 MB/旧 overlay。exit1/1605ms，原始诊断位于 `D:/ck3-state/resume91-java-delivery/java-json-fixture/attempt1/compile.log`。第二个实际模型纠错已移除 `List<byte>`、采用 try-with-resources/readAllBytes，但遗漏 `InputStream` import 且仍静态调用 `getClass()`，strict javac exit1/1453ms/3errors；classloader 前导 `/` 仍不匹配其选用的 ClassLoader API。第二候选的两个 Java 字面量已逐字符核对正确；此前把外层 JSON 转义误当源码错误的审阅判断已明确撤回。两次失败候选均未采用。
- 第三项真实需求缩为 helper/import/两常量四槽：`java-json-narrow-slots03` 首次HTTP完整 stop/4.306s、1326输入+223输出token。原样四槽机械装配到第二候选，owner未改Java语义；按Native明确单槽取得后，strict真实NativeWire+测试2源 exit0/1245ms，两JUnit2P/0skip、进程0/1210ms。回执 `D:/ck3-state/resume91-java-delivery/java-json-fixture/attempt3`。测试及两canonical原golden共3叶正常发表 `eb406589f0`，Native正式fixture继续消费同字节；旧错误原件未覆盖。上下文/输出规模和任务难度均改变，不从这三个不同请求推断缓存收益或通用能力上限。
- Focus/Entry/Opening 仍是 D-only Win32 软件 peer 制作，不使用实际 Game 或旧 Game42 票。当前插入 FocusPeer 后的源码首轮缺显式测试 helper，第二轮仅 helper 的既有 try lint 警告；显式编现有 `StorageWriteGuardTestSupport`，排除 D90 全部旧 overlays，第三轮 `-Xlint:all,-try -Werror` exit0/6021ms。路径 `D:/ck3-state/resume90-java-delivery/life-entry-opening/resume91-compile03`。这只证明当前源码可编译；完整 `completeSameOwnerFocusOpeningFromActualPeer` 方法仍未实现，未执行 fixture，未完成 Focus/Opening。
- 原 Focus 两任务此前从未 POST。本轮两项各经首轮连接重置/部分流保留后，在 attempt2 完整 stop。samepeer 输出只复述任务，缺完整 Java 方法，拒绝；material 输出实际声明可对应的接口草案，但漏 authority/journal 与 installed action/replay 对象同一性、完整 Driver facts/原 effect basis 和 producer closure，未采用/未编。最初误将实际存在的 Binding/FrameLoader/Original getters 记为 API 发明的源审判断已逐声明纠正，不能计为模型 API 失败。完整连续性装配仍由 owner 负责，后继只把真实独立小 helper 交模型。原件位于 `D:/ck3-state/model-dispatch91/java-focus-{samepeer-method,material-adapter}`；没有 Focus COMPLETE 或行为验收。

复用 `revision66/build` 和已有 m2 缓存，有限 javac 只写本岗输出。没有启动 Maven、CK3、业务 worker、SAVE/RESTORE，没有本岗新游戏日。默认 `mvn -version` 实读为3.10.0、Java21.0.10（本机事实，不锁定安装绝对路径）。Root 因机械盘随机 I/O 压力对研究编译限流，MB105/worker105 安装期间暂停新研究编译；本岗没有为正式发表重跑旧绿色。JSON第二轮编译排槽时曾未等 Native owner 确认即启动，可能与其已授权 M2 短编重叠；本岗已明确纠正，后继先取得唯一研究槽再开命令，不将发送排槽通知等同已取得槽。

## 待交付队列

M6 的 `stop-public-next/STOP-PUBLIC-CONSUMER.patch` 已完成最小 diff 审阅、apply-check0，并于上述三祖先发表后 apply，本地提交 `a92f5829b0`：3 个生产叶改为 Character 角色域，1 个真实 Native packet 测试、2 个原资源；现有基线与 owner 旧红绿记录完整保留，没有重跑旧绿色场景凑验证。当前 D 三生产叶独立 `javac --release21 -Xlint:all -Werror` 必要集成编译 exit0/6.045s，输出 `D:/ck3-state/resume91-java-delivery/m6-stop-compile/classes`。首次维护 argfile 错放 `-J` JVM 参数的失败保留，随后移到 javac 命令行；没有为此改生产。未覆盖 `SwayNativeBindings.stopPreparation` 和 retained Start/完整 Finish 资格。原实际分组为 baseline 1P2F、ACK 中间结果、public 1P、negative 1P，不能合称新完整 CI。

runtime91 提供 `D:/ck3-state/resume91-runtime/sem103-regression/DELIVERY.patch`。本岗仅采用 `settledSemanticTransport` 两行：读取完整 SEM 改用 `DriverJson.object(MAX_NATIVE_BYTES)`，匹配引用解码改用 `DriverObservationEvidenceReader.reference`。其它 session/Game guard 保持。apply-check/apply0，当前 D 单 Journal 源严格编译 exit0，输出 `D:/ck3-state/resume91-java-delivery/sem103-compile`；该命令未单独计总耗时，不编造秒数。运行岗原真实 canonical102/529451B SEM baseline2F→candidate2P、MB增编0和 worker104 是运行岗结果，不是本岗新测试或 Game 动作；其现存 fixture 仍依赖原 NV CAS，不能称便携闭包。

M1 installed Context 已按 `context-consumer/DELIVERY.json` 精确采用并发表 `cebf0e9e0a`：两生产叶4hunk，Context actor 使用 NativeCharacterId，public source/binding 用严格 canonical bytes 比较消除 IntNode/BigIntegerNode 误拒。1个新测试和29个原资源保留；owner 已严格编译0，必要28P/0skip（原27+一个覆盖38个 source/binding 拒绝检查的方法）。不重跑189/202旧组；测试补丁的 dev/null header 在 Windows git apply 失败后，仅复制精确新测试并 diff0，没有改逻辑。

M1 Surrender 增量随后在 Native M1 `e2818cf865` 之后发表为 `f46dd8f3cc`：只追加已原样模型编测的新方法及9原资源/1来源 note，保留 Context 新拒绝方法。owner严格单测编译0、只选新Surrender三参数项3P/0skip；没有声称完整组合类31P或重跑Context28。正文原JSON和 packet 由 producer 保留，未用 Java 重生成。

运行岗另交付两次准确修复，均按最小 patch 正常发表、未重绿：`8611e0f227` 将 FamilyObligations source 从误比 version@SHA 改为实际 raw EXE SHA 的大小写无关比较（owner实际输入1P，含错误SHA/version/version@SHA拒绝，模型首候选case敏感被RED拒后owner纠正）；`4032ef7a61` 将 catalog 纯本地安装入口/尾端与操作 deadline 分离，新增 package-private active Game 检查，真实 RPC 的 `requireCurrent(deadline)` 仍保留原预算语义。后者 owner 两源strict0/6.911s、既有phase4P，无离线完整 catalog 正向结论，worker105同Game实装结果由 runtime91 独占记录。

Root docs01 的6叶独立提交 `7d30b58e67` 已正常发表：3个新文档及 AGENTS/README/W44 各自标题后精确插入新段，不覆盖 Z 历史 dirty；首次 push 连接 reset 保留，正常重试成功。

历史 runtime material12 已按 `SOURCE-ADOPTED.json` 和 LF 派生最小 patch 采用12生产叶，并复制 `regression/material100-durable/FILES.json` 对应3个标准JUnit源。closed v4 retained material 只在真实 live Coordinator 成功ACK/guards之后捕获一次，v1-v3构造兼容保留，pureReplay只读不可变CAS。新枚举/record公共合同的全部实际消费者已查阅，没有遗漏的穷举switch。当前D12显式生产源首次strict all/Werror编译只因未改的 Store try-resource warning失败（8.090s）；经Native明确重新授槽后，仅对该既有lint类使用 all,-try/Werror，第二次exit0/3.382s；两次原日志/argfile独立保留于 `D:/ck3-state/resume91-java-delivery/material12-compile`。没有重跑旧绿色方法或运行Maven。旧行为证据仍是archive首2P1F→只修该失败1P、capture1P、pureReplay1P各组，不能合称一次5P；标准CI的完整执行另待安排。

Root docs02 15页小快照已比较，14变化、与本岗当前逐字相同的一页跳过；独立docs提交 `9ea537867d` 正常发表，未夹带待编源码。新页保持各owner的观察时点，不外推当前Game后态。

restart/intake/ranking/episode 等仍按原交接的准确 manifest 链审阅，不能因 material12 或新 P0 两行发表便称正式 D 已包含全部运行修复。后继反向同步只接精确最小 diff，不整叶覆盖 S 或 Z。
