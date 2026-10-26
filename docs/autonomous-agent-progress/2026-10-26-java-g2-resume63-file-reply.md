# resume63：同 Prepared 的 FILE_REPLY 接点

`machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-26T14:54:57Z 观察；身份来源为本轮 `py tools/ck3_live_run_id.py machine` 实际输出。本文记录源码采用与待验收合同，不授予 SERVICE、SDK、运行环境、财务容量或 Game 资格。

## 问题与范围

resume62 的直接 `RootProfileBootstrapCommand.phase` 在同一 child、同一 `Prepared` 中发出阶段 quote，再从 `System.in` 接独立 issuer 的 binding。Shared 普通 Windows 子进程的 stdin 为 NUL，因此该接点会在收到 binding 前失败。不能改成每阶段重新 prepare：ENV 含真实 observed 时间；NormalExit 私有 projection 必须在创建 guard 后继续复用。

本次在原 Command 中增加显式 FILE_REPLY 传输；原四参数 stdin 路由与完整 SERVICE Session 路由保留。没有构造 Session PID、nonce、Arrival 或 WriteReceipt，没有改变 SERVICE/mandatory-tests 门禁，没有新增 runner，没有启动游戏。

截至本记录，五个 main 和一个新测试叶已写入可复用 SRC：

`D:/codex-ck3-demos/2026-10-25-java-g2-complete31-h5r5/java/ck3-control/local-service/src/`。

| 叶 | 改动 |
| --- | --- |
| `main/java/org/xar/ck3/control/service/root/RootProfileBootstrapCommand.java` | 原 phase 仅替换 binding 来源；新增原 issuer mode `ISSUER_FILE_REPLY` 与有限 typed request |
| `main/java/org/xar/ck3/control/service/root/RootBootstrapProtocol.java` | 单一 channel/reply 字段合同、Command 各模式固定 phase 顺序、canonical LF quote 编码 |
| `main/java/org/xar/ck3/control/service/root/RootBootstrapFileReply.java` | 只读 channel/reply consumer，逐 byte 比较本次内存 quote，保留全部真实 witnesses |
| `main/java/org/xar/ck3/control/service/root/RootBootstrapOutputGuard.java` | 窄 metadata staging API，原锁内核完整控制峰值并经原 Native writer/readback |
| `main/java/org/xar/ck3/control/service/root/RootBootstrapRuntime.java` | 原 Session 完整 required-class/source closure 纳入新 consumer |
| `test/java/org/xar/ck3/control/service/root/RootBootstrapFileReplyTest.java` | 九个真实文件与原 Guard 回归方法；独立财务卡仅为明确的软件夹具 |

源码增量与本文使用 Root 本轮已批准 D 盘小源池；未新增 C 盘构建、缓存或证据根。BUILD/m2/TMP 仍由 Host 唯一管理；本岗没有执行编译。

## 字段与路由

旧入口为 `MODE REQUEST_PATH REQUEST_BYTES REQUEST_SHA256`。

新入口严格为 `MODE REQUEST_PATH REQUEST_BYTES REQUEST_SHA256 FILE_REPLY CHANNEL_PATH CHANNEL_BYTES CHANNEL_SHA256`。长度只接受 4 或 8；8 参数必须带 literal `FILE_REPLY`，channel bytes 必须为规范十进制；issuer/census mode 不能消费 binding channel。

channel 为 `xar.java-root-bootstrap-file-reply-channel/v1`，包含 `machine_id`、`deadline`、Command `mode`、exact `bootstrap_request`、`issuer_reply_root` 与实际 `issuer_reply_directory`。所有 FileRef 都保留 path/bytes/SHA-256；Native 64 位及 128 位身份仍使用既有规范十进制字符串合同。

每阶段外部只把该次 stdout 的完整 canonical LF quote 原字节保存为 `issuer_reply_root/phase-N-quote.jsonl`，不 trim、重排字段或重新投影。由原 `ISSUER_DECLARE` → 实际 census → 独立财务 issuer release → 原 `ISSUER_BINDING` 取得真实 binding。

`ISSUER_FILE_REPLY` 使用 `xar.java-root-bootstrap-issuer-file-reply-request/v1`：`machine_id`、`review_at_utc`、channel exact FileRef、`phase_index`、`actual_phase_quote` exact FileRef、binding exact FileRef。它不生成 release，也不把调用成功当成独立容量。

最终 reply 为 `xar.java-root-bootstrap-file-reply/v1`，固定路径 `issuer_reply_root/phase-N-reply.json`；字段为 channel、bootstrap_request、mode、phase、phase_index、deadline、quote、quote_native_file、binding，加 schema。child 核 exact outer/channel、固定模式/顺序/窗口、实际目录 Native identity，重开 quote 并核实际 native witness、完整 LF、canonical bytes，最后逐 byte 对比当前同 Prepared 内存 quote。接到的 binding 仍需原 `RootBootstrapOutputGuard.readExact` 与 `Prepared.createNew` 的完整计划核验、CREATE_NEW 和 readback。

原件 witnesses 在 Guard 打开前、创建前及创建后重新核验。缺字段、null、额外字段、错误 enum/数值类型、错误 quote/Native identity、顺序及过期窗口均拒绝。channel deadline 不得超过实际阶段 quote/outer request 的 review；同时保留 open 时实际剩余窗口的 monotonic 上限，系统时钟回拨不能延长轮询。任何拒绝均不能触发新 prepare 或自动重投。

## 发布可见性与计费

issuer 在原 Guard 锁内先 `requirePlan`，要求 binding 的实际完整计划等于 quote，然后在该 binding 声明的 control root 中经原 `NativeCheckpointFiles` 创建 `.phase-N-reply.pending` 并完整 readback。

窄 Guard API 在写前核两个 metadata 名额，以及 `2 × fileQuote(encoded_reply_bytes, control_root)` 的保守控制/joint 峰值。这覆盖原 Native writer 的 private/pending 区间和稍后的 pending/final 区间；沿用实际 cluster geometry、原 control ceiling、joint ceiling、volume safety/quota/other holds，没有借 metadata 新增容量。

原 Guard 锁关闭后才用 `Files.createLink(final, pending)` 发布 final。此原语与既有 `NativeCheckpointFiles.createNew` 相同，目标已存在时失败。Windows `ATOMIC_MOVE` 即使不传 REPLACE_EXISTING 也可能替换现有目标，所以这里不使用该方案。

final 发布后先核实际 final/pending Native identity 和完整内容，成功才移除本次 pending 名，再重新 observe final 的真实 FileRef/Native witness 并 readback；不把 pending witness 改 path 冒充 final。child 只接受 final 的单链接 witness，遇到两名 finalization 区间在有限窗口内等待，因此不会在 issuer 仍持原 Guard 锁时取得 binding，也不读取半包。

pending 或 final 已存在时不能再 stage/重投。链接、readback、身份或窗口失败保留实际失败状态；不会清除 final 或制造同名成功原件。本文不把源码采用外推为这些 OS 行为已经实际跑通。

## 验收状态

截至本记录，编译、静态检查、九个新测试及原消费者回归全部 **NOT_RUN**。已给 Host 请求：在同 SRC/BUILD/m2/TMP 增量编译后执行完整 `RootBootstrapFileReplyTest`，以及既有 `RootBootstrapIssuerCommandTest`、`RootBootstrapDuplexTest`、`RootProfileBootstrapExplicitRequestTest`、`RootBootstrapOutputGuardTest`。保留 lint/Werror，不新建 Maven 构建目录，不把依赖出现在 reactor 说成全部重编。

新测试正例消费原 phase 实际 stdout LF frame，经真实 declaration/census、明确标为软件夹具的独立 release、原 binding publisher、新生产 reply publisher，再回到同 Prepared 的原 Guard 创建/重开，并交实际 DATA consumer。反例覆盖 phase/outer/native/quote/canonical/deadline、字段和类型、目录身份、超期与延窗、quote 原件替换、不可重投、错误 binding 计划，以及双名 metadata 峰值不足。

已新增跨进程 Windows Job stdin=NUL 软件回归，但尚未执行；没有完整 Shared 实际受管入口、SERVICE 验收或实机推进信用；后继必须消费 Host 真实结果，再完成原受管 launcher/发行入口的运行验证。首场已存在 Genesis 不因本接点再次初始化。
