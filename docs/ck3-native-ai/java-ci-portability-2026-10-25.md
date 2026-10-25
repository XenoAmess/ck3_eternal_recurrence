# Java CI 可移植性修复（2026-10-25）

本地观察机器为 `desktop-3fevhd2-1c74096080`。本页记录截至 `2026-10-25T00:14:49+08:00` 的真实结果：修复候选的 build-tools 完整 Maven `verify` 已退出 `0`，JUnit 为 **623 项、0 failure、0 error、0 skipped**；新候选提交的完整 hosted 第 43 步仍待实际 CI 验证。

两个已推送提交的实际 CI 均已进入终态：

| exact commit | Official Runner CI | 产品静态 CI | Linear history |
| --- | --- | --- | --- |
| `1cdf30e5c1bb8d17bb14e39d39ffa8831eb48578` | [40104616470](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40104616470)：第 43 步失败 | [40104616421](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40104616421)：成功 | [40104616429](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40104616429)：成功 |
| `f15be2d3dcd559abe32d89f69444e43fa23d5f8b` | [40106820220](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40106820220)：第 43 步失败 | [40106820170](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40106820170)：成功 | [40106820145](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40106820145)：成功 |

逐个 exact SHA 查询只发现上表三条触发流程；两轮第 20 步资源闭场均已成功。两份原始 Java artifact 的 `bootstrap-actual.json` 均记录来源机器 `runnervmdaln5-5f47da6a04`。第 43 步的直接错误是 bootstrap 子阶段 622 项测试中的 **2 failure、4 error**，完整 reactor 和 HTTP 消费链没有因此获得通过资格。

三处原因及修复边界如下：

- `CanonicalColdWarmStageTest` 的全文件 `replaceFirst` 命中了 canonical 组之前新增的另一条 mypy 命令，原 canonical 组没有改变。现在从实际 `ParsedStep.commandLines()` 取得完整命令，精确替换唯一整行，并保留完整 30 命令、退出码检查和独立 continuation 的原断言；生产 parser 未改。
- `NativeVendorTimeoutTest` 在 fixture 创建时读取另一机器固定 VS 安装目录的 `vctip.exe`，云端缺文件，四项尚未进入消费者便报错。共享校验主体现在接收明确的 `FileRef` 上下文，测试用实际临时标记文件复用该主体；正式公共入口继续核对原固定 vendor 路径、大小、SHA 和实文件，原 terminal、manifest、deadline、raw analysis 守卫及 `Qualification.NONE` 保留。新增回归拒绝来源替换和文件漂移，标记文件从不执行。
- Windows 子 Java 的 `main` 参数经过 JDK 21 的 ANSI code page 投影，不能充当 `CreateProcessW` 的完整 Unicode 观测。本机实际 `GetACP=936`、JVM native encoding 为 GBK；原云端 XML 为 Cp1252，中文和 Ω 被替换。现有真实子进程通过 `GetCommandLineW` 和 `CommandLineToArgvW` 读回 OS 参数，同时保留 Java launcher 参数及 native encoding；完整 Unicode、唯一 Job 成员、原句柄、输出和 cleanup 断言继续执行。共享 `WindowsJobProcess` 未改。该投影行为有[上游发行说明](https://docs.redhat.com/en/documentation/red_hat_build_of_openjdk/21/pdf/release_notes_for_red_hat_build_of_openjdk_21.0.9/Red_Hat_build_of_OpenJDK-21-Release_notes_for_Red_Hat_build_of_OpenJDK_21.0.9-en-US.pdf)说明。

本地首次用默认 GraalVM 25 验证得到 623 项、5 failure、4 error；原结果保留。套件明确要求 JDK 21，另有 Java 25 告警及原生内存差异，因此没有放宽这些断言。随后在任务外置目录使用官方 SHA-256 已核验的 BellSoft JDK 21.0.12+10 Lite，仍调用命令行默认 `mvn`。该机器实际默认 Maven 为 3.10.0；历史安装目录名未变，未修改默认 Maven 或 PATH。完整 build-tools 生产及测试源码以 `--release 21`、`-Xlint:all`、`-Werror` 编译，通过全部 623 项后完成 jar 和依赖封装；原始 `Popen.wait()` 得到退出码 `0`。

原 CI profile 要求真实 isolated hosted runner、非系统卷工作根和其版本化配额；这些守卫没有修改，本机没有伪装 hosted 环境。本地通过范围仅为完整 build-tools bootstrap 子阶段。完整第 43 步以及后续流程须由新 exact commit 的真实云端结果确认。

## 2026-10-26：临时目录遍历拒绝访问

本段观察机器为`machine_id: 4-8e1c2f1861`。原`4e584e`官方run40221657946的step44在bootstrap扫描`scratch/baseline/governance-policy`时抛`AccessDeniedException`；完整reactor／HTTP尚未执行。原artifact没有内部stack，不能确认具体触发回调。确定性回归另证实：现有属性读取重试没有覆盖`visitFileFailed`／`postVisitDirectory`的目录遍历失败分支。

生产扫描现在仅对scratch的这类遍历拒绝进行最多四次完整分项遍历，每遍重新计算字节数，避免重复累计已扫描文件。必须实际完成遍历；持续拒绝、真实超限、期限和中断仍失败，既有属性读取重试次数保持。三个新回归在旧实现上实际得到2 failure／1 error；修复后的完整`CiBootstrapTest`45项通过。

本机完整build-tools `verify`实际原wait1：636项中626通过、9 failure、1 error、0 skipped。两项明确要求JDK21而当前为Java25.0.4.1；另有原生线程／G1分配失败、三项Job峰值超限、两项已失去原stderr正文的长度断言，以及原因未确认的PID就绪超时。没有把所有失败归因于JDK版本。本机有界查找未发现JDK21，没有引用上文另一机器的BellSoft安装，也未下载依赖或放宽断言。默认Maven仍为3.10.0。

本段只交付已复现分支的最小修复与45项修改范围通过，不声称完整模块或官方step通过。[本轮原始回执索引](evidence/java-ci-scratch-traversal-2026-10-26.json)保留逐项失败、源码前后身份、旧实现RED及所有原wait；对应JDK21官方结果仍须独立回读。

本机证据入口为 `C:/ck3-dynastic-esotericism-20261024/ci-1cdf30-a01/FINAL.actual.json` 和 `C:/ck3-dynastic-esotericism-20261024/official-java-step43-red-a01/FINAL.actual.json`；后者索引原始 ZIP、保真 XML、两次本地结果、实际命令、源码指纹、容量卡与工具来源。临时目录、M2 和 targets 均在 C 盘；最新 r1170 容量检查通过，新 verify 输出峰值 18,567,168 B，低于 128 MiB 限额。必要证据用途复核日期为 `2026-10-31`。

## 2026-10-26：官方工具测试通过，完整链缺实际输入

观察机器为 `machine_id: 4-8e1c2f1861`，回读时间 `2026-10-25T22:09:23Z`；本段只读 GitHub API、606335 B 的小型证据 ZIP 和当前源码，没有重新运行 Maven、测试或游戏。[exact `6d3d51` Official run40228781719](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40228781719) 在 `2026-10-25T20:59:43Z` 已终态 failure，runner 的实际 `machine_id: runnervmdaln5-5f47da6a04`。这与本机先前 Java25 的完整模块 RED 分开记录。

同一次官方 run 的 bootstrap-tools、qualified-tools 两次完整 build-tools 测试，分别均为 **87 套件、636 项通过、0 failure、0 error、0 skipped**；两次 `CiBootstrapTest` 均为 **45 项通过**。XML 记录 Java `21.0.12.1`，bootstrap 回执记录默认 Maven `3.10.0`。这证明工具阶段及修改范围通过；官方 step44 仍失败。[原 artifact](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40228781719/artifacts/12614185424) SHA-256 为 `16b0f28b48565cc9a84c988d2bdc2060423b4410ba3c2079ebf65f20ad25ab53`，当前到期时间 `2026-11-01T20:59:31Z`；本次没有在本地保存 ZIP 副本。

直接失败记录在 `logs/control-ci-actual.json`：`fixture_production_request_ref=null`、`fixture_request_ref=null`，错误为 `NOT EXECUTED: full parity requires the actual fixture-production request; fresh SDK and complete cold/warm cannot be omitted`。EXPECTED_MAVEN_RED 已 PASS；REACTOR 阶段因输入守卫为 RED，尚未调用实际 reactor build，`reactor_build_receipt_ref=null`。后续 reactor 报告闭合、HTTP/map consumers、两类 Python static、supplemental、fresh SDK 和完整 canonical cold/warm 均为 NOT_RUN。`qualified-pipeline.log` 记录真实 child exit1、Job active0、stop reason null，外层再报告 bootstrap child failed。不能把工具测试通过写成完整链通过。

当前 [workflow 第231行](https://github.com/XenoAmess/ck3_eternal_recurrence/blob/6d3d51bd81c328cfe3be6fd869136b3a4ba67b73/.github/workflows/static-ci.yml#L231) 没有传 production request；[ControlCi 第370行](https://github.com/XenoAmess/ck3_eternal_recurrence/blob/6d3d51bd81c328cfe3be6fd869136b3a4ba67b73/java/ck3-control/build-tools/src/main/java/org/xar/ck3/control/build/ControlCi.java#L370) 的原守卫在第506行先拒绝缺失输入，再于第509行准备构建仓库的 `java/ck3-control`。静态核对还发现额外输入缺口：[当前 parent POM](https://github.com/XenoAmess/ck3_eternal_recurrence/blob/6d3d51bd81c328cfe3be6fd869136b3a4ba67b73/java/ck3-control/pom.xml#L13) 仅注册9个子模块、10个 reactor projects，build-tools 独立存在；[R3 完整源图校验](https://github.com/XenoAmess/ck3_eternal_recurrence/blob/6d3d51bd81c328cfe3be6fd869136b3a4ba67b73/java/ck3-control/build-tools/src/main/java/org/xar/ck3/control/build/ControlBuild.java#L1233) 要求34子模块、35 projects。当前缺 `g2-research`、`continuity-core`、`adapters-storage`、`application`、`native-transport` 等目录，后者还承载 [R3 强制绑定的两份 army Java 源](https://github.com/XenoAmess/ck3_eternal_recurrence/blob/6d3d51bd81c328cfe3be6fd869136b3a4ba67b73/java/ck3-control/build-tools/src/main/java/org/xar/ck3/control/build/FullParityCurrentBindings.java#L21)。这是源码读回发现，不能声称官方已执行到该后续失败。

[R3 历史交接第32、86、90行](../handover/2026-10-24-java-g2-resume56-r3-progress.md#源码交付及待验边界) 说明未集成外置后继，完整树为来源机器 `machine_id: xenoamess-full-tower-eb9d2c1186` 的 `D:/codex-ck3-demos/2026-10-24-java-g2-source09-r3`。该树当时仅 SOURCE_ONLY，随后第二次编译实际 RED：22 SUCCESS、1 FAILURE、12 SKIPPED，测试未执行。此路径和历史资格只证明来源机器当时的状态，本次没有读取或搬入该树，不追认为当前本机或 hosted 的可运行输入。

后继须由原源图与 fixture owner 先集成可重建的完整源／原生产输入，解决其真实编译问题，再以 qualified-tools 生成同机、同 runtime 绑定的 typed request，继续原完整 reactor → HTTP → fresh SDK → cold/warm。SDK 输入本身要求实际 qualified-tools receipt 和原 frozen Source32／NTFS 身份，不能在缺少生产输入时手编替代请求。本支线未修改 workflow 或生产代码，未降级 full-parity、未削弱守卫、未跳过 SDK/cold-warm，**完整链尚未修复**；该缺口与 RRF 原生 review／冷载业务验收独立。[小型回读索引](evidence/java-ci-hosted-terminal-2026-10-26.json) 保留原终态、artifact／内部日志 SHA 和逐项源码行号；用途复核时间为 `2026-11-01T22:08:08Z`。
