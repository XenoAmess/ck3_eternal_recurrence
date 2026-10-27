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

## 午夜后的实际 Git 与 CI 读回

machine_id: `xenoamess-full-tower-eb9d2c1186`。2026-10-26T16:09Z（当地 10 月 27 日）已确认第三包 `a9d621fdf19bb2914aaf3559b4f0c2bcd63196d0` 普通 fast-forward 推送到 master，parent 为 `7ecb8b1d10b88eeaed389ca76251eb5d679c652e`。仅 99 个研究、迁移状态及必要文档依赖，原始输入 965,219 B；无 Java 源码。冻结守卫曾发现 acceptance 文档从 7,440 B 变为 8,388 B，在任何对象写前拒绝；只更新该实际 ready 叶后重锁 99 叶，fingerprint 为 `c3729e926febaced`，未沿用旧 pin。

本包 tree 原始输入 303,330 B；112 个明确 loose 对象合 644,528 B。原单 cut 512 KiB 门槛曾真实拒绝，已写 partial 对象不删除、不重写；Root 与 capacity 在原联合额度内将子限调为 1 MiB 后，仅补缺失 tree。此前 raw whitespace 检查拒绝留下的未引用小 commit 保守计 1,024 B，三包对象合计上界 1,453,884 B，仍低于 2 MiB；未知 promisor pack 仍为 UNKNOWN。两份既有用户索引 SHA 前后相同，推送前真实总线 ACK 为 9027。

历史精确原件含 CRLF 和三个文件尾空行，原始 `git diff --check` 实际 exit 2；没有改写原件来制造通过。仅将 CR 识别为行尾并排除 EOF 空行后，行内空白检查实际通过；UTF-8、JSON 和相对文档依赖闭包通过。该差别不授源码或实机资格。

官方 API 实际读回如下，时间均在当地午夜以后，不倒填为 26 日截止结果：

| 读取 UTC | 精确 commit | 官方 Runner | Linear history |
| --- | --- | --- | --- |
| 16:09:01.180 | `e735f2a0ed56e666e5f5d0977a7e532ff861f23c` | [40345540217](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40345540217)，COMPLETED / FAILURE | 40345540738，SUCCESS |
| 16:09:03.336 | `7ecb8b1d10b88eeaed389ca76251eb5d679c652e` | [40351720817](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40351720817)，IN_PROGRESS | 40351720781，SUCCESS |
| 16:09:05.803 | `a9d621fdf19bb2914aaf3559b4f0c2bcd63196d0` | [40356241300](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40356241300)，IN_PROGRESS | 40356241457，IN_PROGRESS |

e735 的失败位于实际完整验证入口，不能称为 Tools 编译失败：bootstrap 与 qualified Tools 两轮各 636/636、BUILD SUCCESS；`qualified-control.stderr.log` 为 `NOT EXECUTED: full parity requires the actual fixture-production request; fresh SDK and complete cold/warm cannot be omitted`（ControlCi 595/216）。`control-ci-actual.json` 的两个 fixture request ref 均为 null；EXPECTED_MAVEN_RED 为 PASS，REACTOR 为 RED，其后七阶段为 NOT_RUN。外层 qualification child exit 1、8.6652961 秒、peak 281,006,080 B、active 0。

对应官方 [artifact 12666155214](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40345540217/artifacts/12666155214) ZIP 为 606,260 B，SHA-256 `25bba1eb715d291e19927a76dcbc5fd375176757e80557d434ed2d607e218a47`；本岗只在 RAM 解包，没有物化新 SDK 或证据副本。Host 与 launcher owner 已收到实际请求缺口，后继修复走原生产入口。7ecb 新增 registration、broker、MSVC-evidence 三完整模块的官方 step 已于 15:42:43–15:42:46 UTC SUCCESS；整 Runner 终态仍待读回，未取消或重启长 Native 编译。

## i61 用户资源的真实同图输入

Root 在恢复后明确要求 Host 将 i61 既有 477 B 用户资源作为唯一资源 delta 采用到 SRC，再进行下一 LS 编译与测试。下列 packet 由同一 Win32 只读 handle 取得原始字节与 FileBasicInfo、FileStandardInfo、FileIdInfo；读取前后身份、长度、写入时间和 change 时间相同。没有改写 i61。477 B 的 SHA 与此前用户原件一致；末尾为 LF。Host 应精确读该路径并核 bytes/SHA，采用 SRC 后记录自己的 after，后继编测和产物均绑定 477 B。

```json
{
  "schema": "xar.i61-user-application-properties-readonly/v1",
  "machine_id": "xenoamess-full-tower-eb9d2c1186",
  "observed_at_utc": "2026-10-26T16:32:30.424079+00:00",
  "path": "D:/codex-ck3-background/i61/java/ck3-control/local-service/src/main/resources/application.properties",
  "resolved_path": "\\\\?\\D:\\codex-ck3-background\\i61\\java\\ck3-control\\local-service\\src\\main\\resources\\application.properties",
  "native": {
    "volume_serial_decimal": "6505083400996699863",
    "file_id_128_hex": "f82ef800000002000000000000000000",
    "creation_filetime_decimal": "134374618564540168",
    "last_write_filetime_decimal": "134374618564551190",
    "change_filetime_decimal": "134374618564560200",
    "bytes": 477,
    "allocation_bytes": 480,
    "attributes": 32
  },
  "sha256": "129a4b9bafdf7820d21817a09360b00b4b745450b46b7612eebe6a326ab96342",
  "utf8_text": "quarkus.http.host=127.0.0.1\nquarkus.http.port=8089\n# Global HTTP framing must fit the explicit projection role; the original map route retains its own 64 KiB guard.\nquarkus.http.limits.max-body-size=8392704\nquarkus.jackson.fail-on-unknown-properties=true\nquarkus.package.jar.type=fast-jar\n%test.quarkus.http.test-port=0\n%test.xar.projection.offline.enabled=false\n\n# Redefine compatible Java method bodies during local development.\n%dev.quarkus.live-reload.instrumentation=true\n",
  "identity_stable": true,
  "authority": "Existing i61 user dev instrumentation; Root requires exact resource adoption before next LS compile/tests; no i61 write"
}
```

该 packet 只证明本次资源身份与字节，不授下一编测或产物资格。Git 也未因本次小记录写入对象或索引。

后继真实读回补记：`7ecb8b1d10b88eeaed389ca76251eb5d679c652e` 的官方 run 40351720817 于 2026-10-26T16:26:03Z 最终 FAILURE；失败 step45 于 16:19:58–16:25:51 执行，configured step48 实际 SKIPPED。16:27:19.540577Z 已独立在 RAM 读取该 run 的 artifact 12666114526：605,653 B，SHA-256 `66122e6de39805679275baf1a5c4a1b6ac8d470fb3ce2817ed591987264f5d57`。bootstrap 与 qualified Tools 均为 636/636、BUILD SUCCESS；ControlCi 595/216 仍实际报告缺少 fixture-production request 的 NOT EXECUTED，两 request ref 为 null、后七阶段 NOT_RUN。它是该 SHA 的新证据，未借用 e735 回执；不将 helper step15 成功说成整个 CI 通过。

2026-10-26T16:21:32.715Z 亦已只对本岗四个已发 commit 与被拒九叶候选 tree 的明确对象做 Win32 点测，不遍历 `.git`：去重 212 OID 的有序 LF 清单 SHA-256 为 `21929528ec0c2525e474e61587597477c4c960e303c9107b5301653d9d5e291a`。212/212 FileStandardInfo 查询成功，EndOfFile 全等逻辑长度；合计逻辑 1,568,429 B、实际 AllocationSize 1,951,536 B。未定位小 commit 另留逻辑 1,024 B、allocation 5,120 B，已知对象 allocation 上界为 1,956,656 B。该数不含未知 prior promisor pack，后继 Git 写入先按实际净峰申请，不能将逻辑剩余额度当物理余量。

## 后继研究包与官方 RED 的真实终态

REA C3/C4、两份 M5 独审与上述资源 packet 已普通 fast-forward 推送为 `0dad5eec33c7762f49bf2c8477e6ce2b7531f79e`，parent 为新鲜 `d42bb259055e62ba430675ad7e9cec684cccf493`；后者的 daily/weekly 各六行及其余四路径原样保留。八个输入原件合 94,794 B，entry 文件与主线相同，实际只改七个文档。13 个新对象逻辑 159,287 B；2026-10-26T16:43:55.390868Z 对全部 13 OID 的 Win32 点测实际 allocation 为 184,904 B。既有已知对象含孤立 commit 预留后的 steady 上界为 2,141,560 B，加入本次保守 atomic/closing 110,592 B 的峰上界为 2,252,152 B，符合 RootZ 4 MiB 内前向调整的 objects physical 2.25 MiB 子限。累计逻辑 1,728,740 B、已处理 raw 2,705,734 B；没有真实索引或全树副本。原始 whitespace 检查只报两份 M5 原件的 EOF 空行，保留原始 SHA，行内检查通过。

17:17Z 又取得两份独立官方终态：

| commit / Runner | 官方终态时间 UTC | 实际官方 artifact / bytes / SHA-256 |
| --- | --- | --- |
| `a9d621fdf19bb2914aaf3559b4f0c2bcd63196d0` / 40356241300 | 17:08:41，FAILURE；step45 在 17:07:15 失败 | 12670865474 / 606137 / `34dc7fd31f9a9742cdfccb7cf8428f2862a8bceb13f04a638c134aa6596b2def` |
| `af523899475246d62963956f4cb635cf9f614dc3` / 40357614312 | 17:16:40，FAILURE；step45 在 17:16:27 失败 | 12669659228 / 605815 / `2851f7317bde457356fec72da2df8c4d4fd624d58f85df9909b5f7790da8d09d` |

17:17:38.786245Z、17:17:42.899439Z 分别在 RAM 解包核对：两次 bootstrap 与 qualified Tools 均为 636/636；各自 actual JSON 和 inner stderr 都实际指向 ControlCi 595/216 缺 fixture-production request 的 NOT EXECUTED。两个 fixture ref 均为 null，后七阶段 NOT_RUN；原 configured step48 均为 SKIPPED。它们不是跳过后转绿，也不能替代完整 Java、SDK、Service 或 Game 验收。没有为同一结论重跑这些 CI。

## 17:59 UTC 文档交付与后继官方观察

本节 `machine_id: xenoamess-full-tower-eb9d2c1186`。2026-10-26T17:51:30.774766Z 在 RAM 独立读取 `0dad5eec33c7762f49bf2c8477e6ce2b7531f79e` 的官方 run 40361982021 artifact 12671149232：605813 B、SHA-256 `a914eb2975705f85e6be4458abe7ac8c8d1fec9706c0d7114c0ef1d554a1e160`。该 run 已于 17:38:16Z 最终 FAILURE；bootstrap 与 qualified Tools 各自 636/636、BUILD SUCCESS，但 actual 的两个 fixture ref 均为 null，ControlCi 595/216 实际返回同一缺 actual fixture-production request 的 NOT EXECUTED，REACTOR 为 RED、后七阶段 NOT_RUN。未将其称为 Tools 编译失败，未重跑或跳过后追认通过。

`d078c8123b77d572fe09d6024aacad3eab533e4c` 于 17:44Z 普通 fast-forward 推送，parent 为期间新出现的 `7f1cdcd5a73d51d90158180a9d6a3ffa9699dc37`。复用了先前候选对象，只重建三个必要祖先树；两次其他任务提交 `d42bb259...`、`7f1cdcd...` 的改动均保留。14 个冻结输入合 202251 B，两个与主线相同，实际改 12 篇文档。两份 user index 与 HEAD 均保持不动。原始 diff-check 只报 ordinary-root-production-chain 文档第 3、4 行有意的 Markdown 两空格换行，owner 已确认；保留原件，不冒报 raw check 为零。22 个明确对象的新增逻辑量 234605 B、17:45:08.203926Z Win32 点测 allocation 为 279184 B，含被旧父拒绝后保留的三个候选祖先树。

REA C6 四叶、M5 Confederation 字段来源与 24C3BE0 两页，以及缺失于主线的必要历史 planner 来源，已于 17:57:20.904Z 普通 fast-forward 推送为 `e61d061c9d48c3b8c2d1b69c42f212e76ffd76c4`，parent 为 d078；实际 bus poll/ack 为 9035。七个输入合 108710 B，UTF-8、sources JSON、11 个相对引用、实际七路径集合和 raw diff-check 均通过。两份 user index 和 HEAD 逐 SHA 保持不变，未夹带 Java 源码或改写 SRC/i61。最初缺 planner 引用的六叶候选真实拒绝，90431 B 处理量仍计入；其后每 blob 压缩预测门在第三 blob 拒绝，已写三个对象保留并复用，整包实际未超过授权 quote，没有清理或重复写入。

e61 的 12 个明确 OID 排序后以 LF 结尾清单 SHA-256 为 `2a38e03da28971a5c2aef2841c1f97e8607b006a226cb2642e29f20cb1df2629`；17:57:32.739974Z Win32 FileStandardInfo 12/12 点测成功，EndOfFile 等于各实际长度，新增逻辑 166740 B、allocation 189104 B。已知对象累计逻辑上界 2130085 B、allocation steady 上界 2609848 B；加入保守 atomic/closing 110592 B 后峰上界 2720440 B。树与 commit 只在 RAM 处理 211392 B。符合 RootZ 总 4 MiB 内前向净转配的 objects logical 2.25 MiB、physical 2.75 MiB 与 tree/commit 320 KiB 子限；raw 处理累计 3107126 B，Root 另前向授权必要 docs 的处理帽 4 MiB。未知 prior promisor pack 仍为 UNKNOWN，不计为零、不扫整 `.git`，未占用条件 24 MiB。

17:59:47.202497Z 实际 API 读回 d078 的官方 run 40371628896 仍 IN_PROGRESS；17:59:48.224149Z 读回 e61 的官方 run 40373433794 亦仍 IN_PROGRESS。两者各自 Linear history 已 SUCCESS，但官方终态尚未出现，不能据此授予整套 CI、Java 全图或实机资格。后继继续只按实际终态追加，现有源码仍等待 Host 在复用目录完成必要受影响测试和最终完整验收。

## 18:57 UTC 官方终态追加

`machine_id: xenoamess-full-tower-eb9d2c1186`。本次只读 API 与各自官方 artifact，不重跑既有 CI，不把旧运行原件替代新 SHA。

| commit / 官方 Runner | 实际最终状态 | 独立 RAM 读取时间 UTC / artifact / bytes / SHA-256 |
| --- | --- | --- |
| `d078c8123b77d572fe09d6024aacad3eab533e4c` / 40371628896 | FAILURE，18:23:29Z；step45 18:18:05–18:23:20，step15 SUCCESS、step48 SKIPPED | 18:45:56.351803Z / 12676965168 / 605897 / `55551346a15e8daa7ea6dcd33f6f96e9e8d9fbbc78be7040debe539dd4cbd9cf` |
| `e61d061c9d48c3b8c2d1b69c42f212e76ffd76c4` / 40373433794 | FAILURE，18:48:18Z；step45 18:41:56–18:48:08，step15 SUCCESS、step48 SKIPPED | 18:57:02.015642Z / 12676944762 / 605990 / `2e4bc82f156423b5aa13e39799e7fa2bc9d5ecdb12b01b806afb0f987c2f93be` |

两份 ZIP 均逐字节核对官方 digest，bootstrap 与 qualified Tools 各 636/636、BUILD SUCCESS。各自 `logs/control-ci-actual.json` 为 RED，`fixture_request_ref`、`fixture_production_request_ref` 均为 null；inner stderr 明确在 ControlCi.runQualified:595 / main:216 拒绝缺 actual fixture-production request。EXPECTED_MAVEN_RED 通过，REACTOR 为 RED，后七阶段 NOT_RUN。保持真实缺项，没有把两次结果说成 Java 编译失败、完整 SDK 验收或实机资格。

18:56Z 为下一必要文档包只读核对 remote 与现有 `origin/master`，均为 `9f191326678fea7a1cec2975478cdfaac28254f9`；相对 e61 的六个他人路径全部保留。REA C7 的五叶此前未被本岗 capture 或提交，18:45Z 已明确释放；下次仅捕获 owner 合入 C8 后的新六叶，不把旧 C7 ready 指纹冒充当前可读原件。尚未对下一文档包写入 Git 对象或 Java/Native 源码图。

## 19:44 UTC 两个后继快照的实际交付

`machine_id: xenoamess-full-tower-eb9d2c1186`。`2bf182e575aef37aa1d7bcfcde12aebcdc0649c7` 已于 19:03:00.530Z 普通 FF 推送，parent 为新鲜 9f191326；12 个冻结文档输入合 257732 B，31 个本地引用通过。实际 bus ACK 9038；两份用户 index 与 HEAD 保持不变。原始 diff-check 仅报 M1 第 210 行 EOF 空行，行内检查通过，原件 SHA 保留。19:03:40.882517Z 对 18 个明确 OID 点测：新增逻辑 250260 B、实际 AllocationSize 287480 B；排序 LF 清单 SHA-256 `450728120e44866778b6ea80b1bccef58306ef157d5771c13715731e5a9ca900`。CAS654 真实净增 RootZ 256 KiB 至 4.25 MiB，旧 19:40 review 不冒充后继有效卡。

`4dcc62e0d27cc97f86d86402fb9e5f2540b72de3` 已于 19:42:53.217Z 普通 FF 推送，parent 为新鲜 `9c687ef888dd0c387b5e791e07a152eb8df33024`，保留他人新增 game_adapter_test.cpp 提交。九个冻结文档输入 216402 B、31 个本地引用通过，实际 bus ACK 9040。原始 diff-check 仅报 M0/M2 EOF 空行，行内检查通过；两份用户 index 与 HEAD 不变。19:43:57.608493Z 对 15 个明确 OID 点测：新增逻辑 224695 B、AllocationSize 258848 B；排序 LF 清单 SHA-256 `f04b8202b3c971a8eea65c888a291d6d3e50580ea9dd6f771aa52af79d4fde4c`。

CAS658 新卡 `DELIVERY63-NINEDOCS-Z4p5MiB-AUTHORITY01.json` 为 1695 B、SHA-256 `fb4855d63861d7f1ea56b3fce6a810721f2b1b31889f3aa6ced0c7f696b9e908`，位于 `D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume63/capacity`，fresh review 为 20:40:26.824464Z。RootZ 仅再净增 256 KiB 至 4.5 MiB；已知对象累计逻辑 2605040 B、allocation 上界 3156176 B，加入保守对象 atomic/closing 110592 B 的峰为 3266768 B，低于 3342336 B 子限。raw 处理累计 3581260 B，树与 commit 本次仅 RAM 213552 B。此前未知 promisor pack 保持 UNKNOWN；没有全树扫描、实际 index 写入或源码图投影。

两次 owner freeze 均在各自真实 push/readback 后明确释放。新 Acceptance 仅授予 Full104 Tools fullVERIFY/1084 项独核范围，Runtime 七错误、SDK30、Service、Game 边界均保留。19:44Z 官方 API 读回 2bf 的 run 40383217864 正执行 step31；4dcc 的 run 40389193898 亦 IN_PROGRESS，Linear 40389193850 已 SUCCESS。二者仍待官方终态，不以等待时间或 Linear 绿追认整 CI 或实机通过。

20:03 UTC 后继读回：`bb949b1c03c597fe337ca0af7391bcb366f1fa3e` 已于 19:47:08.104Z 普通 FF 推送，三篇 status/closing 文档 79763 B、29 个本地引用与 raw diff-check 全通过；push 前实际 bus ACK 9040。19:47:41.622564Z 对七个明确 OID 点测，新增逻辑 55625 B、allocation 65728 B；已知累计逻辑 2660665 B、allocation 上界 3221904 B，本小包加入实际所需 atomic/closing 24576 B 后峰 3246480 B。CAS658 新有效窗内只把 logical 子限前向调为 2.625 MiB，physical 3342336 B、RootZ 4.5 MiB 均未增加。两份用户 index、HEAD 仍不变，无 Source 图写入；Root current/matrix 两叶已真实捕获并明确释放冻结。raw 累计 3661023 B。

`2bf182e575aef37aa1d7bcfcde12aebcdc0649c7` 官方 run 40383217864 于 20:01:36Z 最终 FAILURE；step45 实际 19:54:49–20:01:26，step15 SUCCESS、step48 SKIPPED。20:03:54.600027Z 独立 RAM 读取其 artifact 12683506526，606006 B，SHA-256 `dde40bdca76e96ffb2f13d3012bca731c8d441f436e0e761d761631bf71b4865`。各自 bootstrap 与 qualified Tools 都为 636/636、BUILD SUCCESS，但 actual 的两个 fixture ref 为 null，ControlCi 595/216 实际报告同一缺 actual fixture-production request 的 NOT EXECUTED；REACTOR RED，后七阶段 NOT_RUN。该证据只属于 2bf，不借用前版原件或外推尚在运行的 4dcc/bb 官方结果。没有重跑、取消或跳过检查。

20:44 UTC 两次官方终态已分别取原件：`4dcc62e0d27cc97f86d86402fb9e5f2540b72de3` 的 run 40389193898 于 20:42:42Z FAILURE；`bb949b1c03c597fe337ca0af7391bcb366f1fa3e` 的 run 40389831536 于 20:32:06Z FAILURE。两个 step15 均 SUCCESS、45 FAILURE、48 SKIPPED。20:44:41.209603Z / 20:44:44.874204Z 独立 RAM artifact 核验分别为 12688200314（606301 B / `1ce6b435f62495e89da044297401d64ff62533d8c4fb96be81caeb8f39d897c2`）与 12687385346（605836 B / `18b797bfdf76b85080a605586636df72d557db820ea74629e6955c112745b262`）。两者各自 bootstrap636、qualified636 均 0F/0E、BUILD SUCCESS；actual2790B 两 fixture refs 均 null，ControlCi595/main216 为缺 actual fixture-production request 的 NOT_EXECUTED。EXPECTED_MAVEN_RED PASS、REACTOR RED、后七 stage NOT_RUN；没有重跑或跳过，不能授全 Java/SDK/Service/Game。

21:00:54.548Z 只读恢复完整候选来源：SOURCE86 的 5853 叶加 SOURCE107 累计34变更（before 0fail），再六功能批及明确前向 adoption；SRC 当前5876路径、82814513 B，元数据路径/字节0missing/extra/mismatch。Snew118以325叶覆盖冻结旧Tools324后为5877叶、82880073 B；相对old104为309同版、15修改、1新增，118仅两整类9/9，ordinary119不授新Full。旧图5791是 selection，原87 relocation退休后为5704；保持原87与后继完整路径，不将 TEST 退休伪造为 TEST→MAIN relocation，不合并 adapters/LS 同名类。该来源清单仅RAM计划，未全图内容核验、capture、投影或Git源码交付；等待源STOP和实际净额授权后一次处理。Git远端78f1及此前bc8fe同事六路径增量保留，用户dirty/index与冻结old104/109未改。

2026-10-27T00:32:51.587510Z; machine_id: xenoamess-full-tower-eb9d2c1186. Official CI terminal readbacks (RAM only): fff86e9c2aebb1eb00d1151875e1266cbc5a4b24/run40403961258 FAILURE at22:10:04Z; artifact12691909739 606177B SHA2568f1aa0a4895ef9cb1946479ec75242aad50fd19880db18b22fdc850c215fc4c4. 534375b1bda095ff92846dbfbb866a30e4c0e117/run40420386291 FAILURE at00:29:38Z; artifact12699787495 605971B SHA2569cbf9749e26536c04b05bd2256b9440d545dc6c33cb92e09e514c92483f15c64. Both exact ZIP hashes verified. Each has bootstrap636PASS+qualifiedTools636PASS; control-ci-actual2790B has both fixture refs null, ControlCi595/main216 NOT_EXECUTED missing actual fixture-production request; REACTOR RED and seven downstream NOT_RUN. No javac failure, rerun or global qualification claimed. 534375 was docs-only FF onto9df; later coworker498b is preserved. Full Java source capture/delivery remains OPEN, no Source/SDK/Service/Game credit.
