# Resume63 源码交付与主线状态

`machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-26T14:46:04Z 的只读观察；来源为本轮实际 `git fetch origin master`、Git refs/status、既有 SourceGraph JSON 和逐文件字节比较。源码仍由各 owner 修改，本记录不是原子 source capture，也不授构建、部署或游戏资格。

本轮接手入口为 [resume62 交接](../handover/2026-10-26-java-g2-resume62-rea-runtime-handoff.md)及其[来源索引](../handover/2026-10-26-java-g2-resume62-rea-runtime-handoff-source-index.json)。

## 当前主线与工作树

实际 fetch 后 `origin/master=c9c355ade37f42a817f63ec8f7a0d90f8e8f23a7`。`Z:/ck3_mod_rewrite` 的 `master=4a999f3ef5aa6770345832ed6a3ed47602c3c4f4`，相对远端独有 2 个提交、落后 314 个提交，观察时 489 个 status 项。根仓不能在当前用户改动上直接 rebase，也不能把这些历史改动整批提交。

唯一交付树 `D:/codex-ck3-background/i61` 为 detached `b8ddb3901f5648c3881299fd0b72a2a4d3636309`，是上述远端的祖先，落后 15 个提交；观察时有 406 个 status 项。两树共用 `Z:/ck3_mod_rewrite/.git`。resume62 的“60 unique 源码叶投影”只描述当轮新增投影，不表示 i61 总共只有 60 个改动或已经包含完整最新源码。

独立文档包从新鲜远端树构造，只纳入明确路径及必要相对链接依赖。它不改变两棵工作树的文件、索引或分支指针，不使用 merge、force push、stash 或 reset。共享索引实测 10,657,363 B，不能在 4 MiB 小包额度下创建完整临时索引；交付采用保留未修改子树的树对象构造，实际新对象增量另核。

## 完整源图恢复依据

旧完整计划为 `D:/codex-ck3-demos/2026-10-22-java-phase1/build/resume-current-20261024-r3/source_graph-complete31/plan/H/H5-repair04/SOURCE08-COMPLETE-PLAN31H5R4.json`，5,602,666 B，SHA-256 `3357ad28a5be5f1fb8628229044f19da68ba2500419d733d60cf2f852b7e9441`。

它包含 34 个模块、12 个明确组件、5,791 个互不重复的 selected target、4,476 个最终 overlay 和 87 个 relocation。组件保留集合为 COMMON 5,054，M0 36，M1 75，M2 40，M3 29，M4 37，M5 47，M6 29，M7 69，RECOVERY22 1，BUILD_TOOLS 313，HTTP_HOST 61。

其 baseline 是 `D:/codex-ck3-demos/2026-10-23-java29-source03`；原始 inventory 为 `D:/codex-ck3-demos/2026-10-22-java-phase1/scratch/resume56-20261023/java29_repair/metadata-source03/SOURCE-INVENTORY01.json.gz`，86,897 B，SHA-256 `25cd42a55a29844d9e46548f5d44a87f97ed23d27e2770c4f343227479a76379`，包含 1,524 个 literal FileRef。最终 COMMON 图必须保留这些原始身份；i61 earliest-before 或当前 mutable SRC 路径不能替代 baseline。

配套 `SOURCE08-ASSEMBLY-REQUEST31H5R4.json` 为 3,681,971 B，SHA-256 `66f3c63ccec51d072e5b78afbc3b157c1371746429e24e39ce3bf49b1a96da8d`，包含 220 个 layer、1,744 个明确 winner。后继实际 adoption 按 target 汇总为唯一最终 winner，保留各 owner 的完整 retained set，不能把时间顺序叠加包当作最终组件。

本轮从 2026-10-26T14:46:57Z 开始逐件读取旧计划引用，实际校验全部 1,524 个 baseline FileRef、5,791 个 selected source FileRef 以及 inventory/assembly 两个容器的 bytes 与 SHA-256，失败 0。该结果证明旧图原件仍完整可读；没有将后继 mutable 源码或其软件测试追认为已验收。旧 selection 去掉 87 个明确 retired target 后为 5,704 个 target，当前 SRC 比它多 132 个 target，需补齐原始 ABSENT 与 owner。

`I61-SOURCEGRAPH-OWNER-NAV11.json` 只覆盖 incremental63–70 的 148 个 target，不能替代全图。后续 73/75/76 的 collection 和 78 的单叶 adoption 可继续读回；本轮尚未形成完整新图或验收声明。旧图未选的新 target 需要明确 owner 与原始 ABSENT，不能从 M 名称猜归属。

## 一次最终投影的实际规模

复用 SRC `D:/codex-ck3-demos/2026-10-25-java-g2-complete31-h5r5/java/ck3-control` 排除 `target/.git/.idea` 后为 5,836 文件、81,768,946 B；i61 对应目录为 5,840 文件、81,608,853 B。

逐字节比较发现 178 个同路径不同内容的文件：application 10、build-tools 17、local-service 147、native-transport 3、根 POM 1。另有 16 个 SRC-only 文件、20 个 i61-only 文件。后者包括 17 个既有文档/profile 和 3 个明确测试旧位置。8 个 build-tools 差异只在末尾空白，保留原样。源图完成且必要验证形成真实结果后，可一次投影实际差异；不需要每轮重新复制约 82 MB 全源码，更不复制 BUILD、m2 或 runtime。

三个测试迁移必须按完整路径与内容身份处理：`DriverDeclarationCanonicalWriterTest`、`DriverReadHistoryWriterTest`、`ProductionAdvanceReadinessScopeTest` 从 native-transport 测试目录移到 local-service。不能按 basename 删除 adapters-storage 等其他模块合法同名类；最后一个测试的内容也有后继修复，不能仅做旧字节搬运。

| 当前文件 | bytes | SHA-256 |
| --- | ---: | --- |
| SRC `pom.xml` | 5083 | `e5234583c2cd548e59d9101c912ea145f51954f9e116a6e57263fb0bf24e5ec9` |
| i61 `pom.xml` | 4570 | `0fb46eb9c6dcf5183a1dba7f79095e697aaa4c856fd738cbeae7cb91bf04a102` |
| SRC `local-service/pom.xml` | 7102 | `63ddf5fe9fb413f3571a53e231ff0ff148db734382cea53542905b1c1e121867` |
| i61 `local-service/pom.xml` | 7135 | `998b9f51f43c9e533d5cf436ee3368255b3714f5abd1567cc0716db4a8c6785f` |
| SRC `application.properties` | 363 | `c1a51983faf3624e35d7bcc6f42b90b1ac0d6d8037e987556875145a451b80d4` |
| i61 `application.properties` | 477 | `129a4b9bafdf7820d21817a09360b00b4b745450b46b7612eebe6a326ab96342` |

LS 当前 POM 的真实来源是 `INCREMENTAL69-FINITE-POM-ADOPTED04.json` 中的 7,102 B after-image；最终唯一 winner 还须包含实际后继变更。根 POM 含诊断 profile，最终完整验收不得启用该 profile。i61 的 477 B 配置保留用户的 `%dev.quarkus.live-reload.instrumentation=true` 及注释；不得用 SRC 的 363 B 版本覆盖删除。

源码投影、Git 可追溯、Maven 局部通过、最终全图通过、SDK30 完整 step、Native 后态和真实游戏推进分别验收。本记录没有执行构建、测试、CK3、Steam 或 Defender 操作。

## 已交付的独立文档包

2026-10-26T15:03Z，49 个明确文档及必要相对链接依赖已提交并普通 fast-forward 推送为 `e735f2a0ed56e666e5f5d0977a7e532ff861f23c`，唯一 parent 为新鲜 `c9c355ade37f42a817f63ec8f7a0d90f8e8f23a7`。输入 971,205 B；严格 UTF-8、JSON 解析和相对链接闭包均通过。它不包含生产源码。根仓及 i61 的 HEAD、工作文件与索引没有因此更新；成功构造窗口内两份既有索引的 SHA-256 前后相同。

实际不创建临时索引：复用未改子树及预写相同对象，最终原始 tree/commit 输入 299,430 B，本包覆盖 63 个对象合计 562,727 B。原 256 KiB tree 子额度实际拒绝后，按实测目录输入改为 320 KiB，联合 4 MiB 总 hold 未增加。两次早先新 OID 存在性探测遇到 partial-clone promisor 查询，已仅关闭按唯一脚本指纹、父子关系及创建时刻核实的自有进程；后继本地对象检查显式 `GIT_NO_LAZY_FETCH=1` 并复用已写对象。是否新增过其他 pack 未作全 `.git` 审计，保持 UNKNOWN。

推送前实际 task bus `poll --ack` 到 9024，无新冲突；远端 fast-forward 成功。远端回显 CLA 必需状态被现账号策略 bypass，本岗未修改该策略，也不据推送成功授予 CI 信用。[Linear history](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40345540738) 已最终 SUCCESS；[Official Runner CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40345540217) 当次读回仍运行，须以后继真实终态为准。

后继 Native 软件修复交付前发现真实主线漂移：远端 configured 生产/测试为 110,409/70,433 B，旧根仓候选为 58,640/12,258 B，整文件覆盖会删除 804/875 行。已停止该覆盖，交 Native owner 从上述精确新鲜 parent 前向重放，保留远端 `dcc25e69b4` 的扩展能力。Java 则实际核过 `b8ddb3901f..e735f2a0ed` 范围的 `java/ck3-control` 无远端改动；两种情况不混同。

该 Native 维护包随后以前向两叶实际落地为 `7ecb8b1d10b88eeaed389ca76251eb5d679c652e`（parent `e735f2a0ed`），普通 fast-forward 推送成功。只采用 fresh helper 35,807 B 与测试 43,745 B；configured 两叶已有同义修复，完全保留远端版本。依据 `D:/ck3-state/ck3-java-g2-resume63-native-helper01/FRESH-READY03.json`（8,504 B，SHA-256 `e63e5598fdd95a842de174f59789453c4d8da5d2b67e7a40d33d2fdc163338ee`），fresh 四整模块 127/127、configured 两整叶 strict 与 helper 明确 AST 提取范围 strict 均实际通过；不外推为完整 helper 静态全绿。

持续 CI 只在远端既有 registration 独立 step 增加 `CI=true`、broker-client 与 MSVC-evidence 两整模块；原 configured 及三个 SDK 消费者的 step 原字节保留，未在本地执行这三个 SDK 消费者。没有为它们复制约 60 MiB SDK，也未写入此前只读查询过的两个 promisor blob 和 MCP blob。新 workflow 的 YAML 及精确 step 内容通过，源 pin、文档新增链接和 `git diff --check` 通过；两份用户索引保持原 SHA。进度 README 仅从新鲜远端插入当前入口两行，其余远端正文保留。

本包六路径的未压缩 blob 输入 535,658 B、tree 输入 102,526 B、覆盖 14 个对象 245,605 B；与首包累计 raw blob 为 1,506,863 B、对象为 808,332 B。推送前实际总线 ACK 为 9025。[该 SHA 的 Linear history](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40351720781) 已最终 SUCCESS；[Official Runner CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40351720817) 首次观察仍运行，保留待终态。Git 发布没有更新根仓的旧 helper 实体或冻结 runtime，实际运行须另绑定正确新源与资格。

## 改名后原件与唯一 POM

Root 已授权 rename63 在同一 SRC 采用 56 个 TEST 叶、182 个名称引用及 LS test-jar POM；`RENAME63-ADOPTED01.json` 为 11,252 B，SHA-256 `34a12394c1cc2fde887e8389c6d78c17d496eb74ea2d6f63204be6076a3c5484`。SRC 四个旧路径已退休，i61 四个旧投影只作采用前 witness，不能作为最终投影后仍可读的持久 donor。新的唯一 LS POM 为 7,358 B，SHA-256 `b62964c612d39d65728b7eae8c11ab4f2b0e21fc5a47911e2240aaf69460bca0`；此为真实源码采用，尚不授编测或 TEST artifact 资格。

本岗实际重读并核对以下四个持久原件，bytes/SHA 均匹配采用前像；因此无需新复制 helper。`B` 为 `D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025`。

| 旧 TEST target | 持久 donor | bytes / SHA-256 |
| --- | --- | --- |
| adapters-storage 的 `TestStorageWriteGuard.java` | `B/resume61/ledger_writer/test_guard103/TestStorageWriteGuard.java`；Incremental33 的 selected_source | 16600 / `1b3ccd1f9de19f359eb815d751ea5cec94a0e390e351f2b570a57180743a0ad9` |
| local-service 的 `TestStorageWriteGuard.java` | `D:/codex-ck3-demos/2026-10-22-java-phase1/scratch/resume-current-20261024-r3/ledger_writer/storage16/close/TestStorageWriteGuard.java`；原 COMMON selection | 16356 / `e1e742ec35abe65d04cb1771ebe61ba1a03fb9c00e4a8feb2a7f1f84d570d50b` |
| `RootWarmNativeCampaignRestoreTest.java` | `B/sources/save_restore/actual_warm41/RootWarmNativeCampaignRestoreTest.java`；原 COMMON selection | 2638 / `65240049fe3c30b8f858aa39d45f8dffcf4f0203b360cbc6a9aef8980f91cc53` |
| `RootFiniteFirstLiveResultActualTest.java` | `B/resume60/lifecycle/finite_result14/RootFiniteFirstLiveResultActualTest.java`；Incremental26 的 selected_source_ref，原始 ABSENT | 2576 / `01824a9da5e25cbe8f6ad4bda841205a63f4dc1a7e5222984fb6a45b556351b0` |

最终 SourceGraph 在退休旧 target 前，old selection 与 `Relocation.sourceRef` 须使用同一个真实 donor FileRef；新 selection 使用实际 after。adapters-storage 与 local-service 的 guard 是不同 body，不能因 FQCN 相同而合并。i61 仍未进行本轮最终 Java 投影。
