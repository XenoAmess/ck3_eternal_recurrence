# 宗族化密教：度假交接（2026-10-25）

**首发已完成，完整业务验收未完成。用户现在要求度假交接，因此停止新开发、验证和发布，已关闭 R0016、keeper、SCREEN 与容量预留。**

- 产品：`mod_dynastic_esotericism/`，key `dynastic-esotericism`，版本 0.1.0 初始公开测试版。
- Steam Workshop：**[宗族化密教 / Dynastic Esotericism — 3826991345](https://steamcommunity.com/sharedfiles/filedetails/?id=3826991345)**。后续只能更新同一物品，不能再次 CreateItem。
- 本交接的机器：`machine_id: desktop-3fevhd2-1c74096080`；闭场观察为 **2026-10-25T14:43–14:54Z**，即北京时间 **10 月 25 日 22:43–22:54**。逐项精确时间以随文快照及原回执为准。
- 当前可继续编辑的干净源码在 **`C:/ck3-dynastic-esotericism-20261024/main12`**，HEAD **`0e62073e3a1eb96cf3ade16755275d0ff5751592`**。用户 D 工作区仍是旧 HEAD，不能在那里直接接着运行新验收。
- [机器可读快照与证据索引](2026-10-25-dynastic-esotericism-vacation-snapshot.json)、[两份未推送提交的恢复补丁](2026-10-25-dynastic-esotericism-unpushed-commits.patch)。

本交接覆盖上一份 [2026-10-24 交接](2026-10-24-dynastic-esotericism-vacation-handover.md)中的“尚未发布／最新 R0003”等当时状态；旧失败和旧文件仍按原观察时间有效。它们不能作为当前最新 predecessor。本文的本机事实不能外推到其他机器。

## 1. 用户已经确定的范围与执行顺序

原任务仍是需求→测试方案→编码→实机验收→工坊发布。用户后续明确改为：**先发布到 Steam 创意工坊，再继续本地验证；发现问题后修复、验证，再提交后续更新。** 该“先发布”已经实际执行，不需要再次询问是否允许公开发布。

已确定的家族族长边界：优先让请求者卸任旧 House 族长，由真实旧家族成员接任，满足原版资格后创建新 Dynasty；旧家族只有本人或仍无合法创始人时，**生成一名真实、同礼仪的成年创始人物，保证建族**。两条实际路径均在 R0013 取得原生与存档后态。不能回到等待用户选择，也不能把全员归族缩为只处理可玩角色。

产品要求：原生 Rite 创建／编辑界面的“宗族化／无”组；绑定真实 Dynasty 与加入 House；存活同 Rite 信徒全员同步归族，含 AI、儿童、无地与生成角色。背离者保留宗族身份，原 Rite 信徒对其有一项定向 −100 意见及实际监禁／放逐／处决理由，仍遵守原版管辖与囚禁资格。回归、关闭与赦免只处理本产品来源，独立原版罪行保留；关闭不删除 Dynasty，重新启用复用原绑定。

需求、测试与操作卡应读 **Main12** 中的当前版本：

- `mod_dynastic_esotericism/docs/requirements.md`
- `mod_dynastic_esotericism/docs/test-plan.md`
- `mod_dynastic_esotericism/docs/acceptance/operator-runbook.md`
- `mod_dynastic_esotericism/docs/2026-10-25-house-head-handover.md`
- `mod_dynastic_esotericism/docs/2026-10-25-engine-house-dynasty-fix.md`

## 2. 进度口径与恢复后的时间节点

| 项目 | 实际进度 | 不能推导出的结论 |
| --- | --- | --- |
| 首版需求、实现及 Java 工具链 | 已形成可发布首版；a19 Maven 17/17、真实构建链通过 | 不能据此宣称所有玩法验收完成 |
| 历史核心实机 | R0015 前四阶段已签署，即 4/6（约 67%）；完整 core 仍失败，且原 +2 日保存有缺口 | 不合并不同场次为一次完整通过 |
| 最新 R0016 | 用户要求交接时停止，0/6、业务 INCOMPLETE；只启动并自然推进一天 | 正常退出和 host GREEN 不增加业务通过数 |
| 首次上传 | CreateItem、SubmitItemUpdate 各一次成功，ID 已取得 | Notes 网页全文、下载缓存／加载仍未验收 |
| 长期、真继承、cold、seed、old | 尚未完成 | 没有可用的最终新 head 冷载锚点 |

不再沿用旧报告的总体“60%／62%”作为当前验收百分比。上表是可核验的分项进度，没有用静态测试数量抵扣游戏结果。

度假期间没有定时续跑。下表是**用户恢复后的相对计划**，不是已预约的自然时间或完成承诺；发生真实失败即更新实际范围与估计。

| 节点 | 从恢复开始的计划时间 | 交付条件 |
| --- | --- | --- |
| 重新准入与恢复源码 | T+0–30 分钟 | 机器、源码、Steam 离线、容量及最新 predecessor 核对完成 |
| 新 core 场次进入业务 | T+30–60 分钟 | 新 profile／Prepared／分配成功；fixture_ready 与真实创建资格到位 |
| 核心长期／继承结果 | 再约 2.5–3 小时 | 在固定预算内形成实际通过或明确失败；不能保证全部场景一次通过 |
| cold／seed／old | core 产生有效锚点后再约 1–2 小时 | 精确输入与新 PID 各自取证；不从旧 Save 改标签 |
| 补公开 Notes 与缓存加载 | 依 Steam 限流、下载及离线恢复实际情况 | exact formal match＋CK3 实际加载缓存 |
| 后续工坊更新、源码整合 | 修复验证完成后 | 同一 ID 更新；普通推送与 exact SHA CI，不强推 |

## 3. 首次发布：已发生的真实结果

证据根：**`C:/ck3-dynastic-esotericism-20261024/first-publication-a01`**。

`create-receipt.json` 的 `stage=complete`；CreateItem 和 SubmitItemUpdate 均为 EResult 1，实际提交时间 **2026-10-25T13:28:15.832604Z**。`steam-native-first-create-submit-a01.actual.json` 保存原 Popen wait、退出 0 与约 24 秒耗时；不是仅有请求 ACK。

匿名官方 Steam API `anonymous-item-raw-a02.json` 已回读：item ID、公开可见性 0、consumer AppID 1158310、标题、完整描述和三个标签一致。标签为 **Religion、Gameplay、`1.20 'Crozier'`**。

- 实际上传说明：2,872 B，SHA-256 `37894010272e0ab70f22e488cedc020a7b4dc40472c7ba5ec59b248bf3eafa13`。
- 实际 Change Notes：1,753 B，SHA-256 `52e6ed1c79376d005b6c1f69e99356f9484d433e66eeae89b211062c3f6fbe9b`。
- 内容如实披露长期、真继承、cold／old 待验，包含卸任与真实 NPC 后备行为。
- **公开 Change Notes HTML 仍 HTTP 429，全文回读未通过。** a01／a02／a03 的失败原件保留；以后补读，不为 429 重复 Create／Submit。实际缺失日志时再编辑正确 owner entry 并全文核对，避免重复上传。
- **Steam 下载缓存与 CK3 缓存加载尚未执行**，不能宣称缓存验收通过。

实际上传树是 **`resume-product-a18/release-staging` 的 25 文件**，不是源码目录或 a19 fixture。原正式 manifest 为 4,496 B，SHA-256 `ddeb804cb74a0e9b7ea4f0fc15927422966beb89204670448733200cbf7c80f1`，其实际 owner 为 **`6241c6134ddb5a166f5c7228f3bf84b178487e74`**，`git_tag=null`、初次构建时 `workshop_item_id=null`。不能将 owner 倒签为 9c4 或 0e，也没有已创建的首发 Git tag。

新 a19 正式 25 文件与上述已上传 25 文件逐字节相同；本轮新改动为 fixture、操作卡与元数据，无需仅为 fixture 修复再次更新产品。

Canonical ID 只在用户目录外层：

```text
C:/Users/1/Documents/Paradox Interactive/Crusader Kings III/mod/mod_dynastic_esotericism.mod
```

该外层文件 271 B，SHA `5c354e4d848427d097004b26d9f4493b2cc879a5a1684f2454e48cc9bb457dfd`，path 指向实际上传 a18 staging，remote_file_id 为 **3826991345**。`OUTER-DESCRIPTOR-AND-POSTUPLOAD.actual.json` 已核实际正式树无内层 ID；没有修改全局启用 mod 列表。后续 launcher 上传若写入内层 ID，必须重建正式 staging 恢复无 ID；不能把 canonical ID 写进仓库 descriptor。

必要上线工作完成后已在 **13:30:38.536581Z** 恢复 Steam 离线。闭场新鲜后台观察 `operations-core-a36/VACATION-STEAM-OFFLINE.actual.json` 在 **14:50:16.742681Z** 仍为 `status=offline`、`offline_mode=true`，原生 byte 样本 1／1。

## 4. 源码、提交与不可触碰的用户文件

当前 Main12 分支为 `work/dynastic-heir-stock-input-20261025`，干净；两个本任务提交尚未推送：

1. **`9c4b1bf999471eedfeaea36dad78c80f5e5d6430`**：原生囚犯查询来源 SHA 规范化，修复 R0014 实际大写 SHA 拒绝。
2. **`0e62073e3a1eb96cf3ade16755275d0ff5751592`**：首发元数据／永久初始基线／R0015 摘要；真实继承人 fixture 输入与操作顺序修正。17 文件、256 行增加／16 行删除。

它们的父基线为 **`3ce5f5fd4d257a8383886bd10f84b2709a23555a`**。该值也是最后观察到的本地 `origin/master` 缓存，不是闭场时新鲜远端核验。本次没有 merge、push 或 tag。永久首发记录在 Main12 的 `docs/release-changelogs/dynastic-esotericism/0.1.0-initial-baseline.md`。

随文恢复补丁来自真实 `git format-patch --stdout --binary 3ce5...0e`，含且仅含上述两提交：**79,575 B**，SHA-256 **`61a3c666bed9724279791c49ec1d850128eec6acb45da46b068a7b220ef82f24`**。这是补丁包，不是包含所有祖先对象的 Git bundle。恢复到已具备 3ce5 基线的干净 checkout 后才可 `git am`；不能直接套到旧 D HEAD，也不能在已有两提交的 Main12 再应用。随后按真实远端状态线性 rebase、普通推送；禁止 force push。

Main12 的对象库仍借用 Main11，后者又引用 D 的 Git 对象库。**Main12 不是可随意搬走即自包含的 clone**。构建来源 Main11、冻结 runtime 和引用对象不得凭“已有补丁”随手删除。独立恢复需要远端基线可读，或另做经准入的对象迁移。

用户 D 工作区：`D:/workspace/ck3_eternal_recurrence`，HEAD **`3c0b5ec8fb5d5ba12724dfdc1a26222b9b768e26`**。本次仅新增本交接、快照和恢复补丁，没有把 C 新源码覆盖进 D。

**用户原脏文件继续保护，不改、不还原、不代提交：**

```text
docs/handover/2026-10-22-war-episode04-vacation-handover.md
27327 B
SHA-256 0c9be93c0e25eeefc5785187885f1eecd1244fbe342806aea314f5db31b402d2
```

## 5. 已完成的构建与共享修复

最新构建 **`resume-builder-a19`** 使用机器命令行默认 `mvn`，实际 Maven **3.10.0**；历史安装目录名仍为 `D:/apache-maven-3.9.16`，不得由目录名推断版本，也不要把绝对 Maven 路径写成执行规范。JDK 25.0.4.1。新生产工具均为 Java＋Maven＋Quarkus。

原命令完整保存在 `resume-builder-a19/maven-original-exec.actual.json`，从 Main12 执行 `mvn -o -f mod_dynastic_esotericism/tools/pom.xml ... clean verify`，原退出 **0**，71.525 秒。**17 测试、0 失败／错误／跳过**；`maven-validation.actual.json` 记录 XML、55 文件 Quarkus closure 和 15 项资源来源，不能拿旧 a18 JAR 冒充新 fixture 构建。

a19 Java 实际生产链六命令全部退出 0：validate、开发包 build／verify、正式包 build／verify、fixture emit。开发包 **18 文件**、正式九语包 **25 文件**、core fixture **13 文件／14 来源 pins／24 markers**。最终有效摘要：

```text
C:/ck3-dynastic-esotericism-20261024/resume-product-a19/SUMMARY.a02.actual.json
15266 B / SHA-256 bc27a03905e077c283244fb783fb50ae1f24ead49e077e76dd44a298a13c9187
```

它核过真实共享 manifest 消费者、ZIP 内容与前缀、实际资源字节和 a18／a19 正式包等价。**同目录 `SUMMARY.actual.json` 是序列化失败留下的不完整 JSON，不能使用。** 中途捕获脚本的 Windows 路径、ZIP 前缀、Path 序列化等失败均保留，不冒称一次无失败执行。

改动的继承决议 grammar 实际退出 0、diagnostics 空、roundTrip true；其余脚本复用字节相同的既有解析。`ck3-1.20.0.4` semantic profile 仍 UNSUPPORTED；grammar 不能授游戏语义通过。

0e 的继承 fixture 修复：实际 `primary_heir` Faith 不同时先执行 stock `set_character_faith = root.faith`，再 `set_character_rite = root.rite`；仅去掉“预先同 Faith”的输入守卫，保留真实继承人、年龄、存活、头衔及日期守卫。**不写 House／Dynasty／产品绑定、head、player 或 once flag。** 实际 emitter→AST consumer 及四个错误变体回归已通过；R0016 尚未运行这个决议。

9c4 的共享原生修复已完成 17 条实际 Python CI 命令：226 次 unittest 执行及 5 个 mypy 进程均退出 0，准确范围见 `R15-native-sha-fix-a01/TARGETED-PYTHON-CI-17-COMMANDS.a01.json`。未改变 SDK 持久化，未因此重复整个 cold／warm step。早期完整 step 的历史 NOT_EXECUTED 边界仍保留，不能说全仓 CI 全绿。

## 6. Native05 与新执行图

当前 Native05 已有实际 producer／CI／final seal，R0015 实际验证了囚犯数值来源查询。源码未变时**直接复用，不再全量编译 C++**：

| 对象 | 当前来源 |
| --- | --- |
| source | `C:/ck3-war-episode04-research-20261004-a01/native-religion-05-main-9c4-a01/source` |
| Git subtree | `ck3_autonomous_player/native_bridge`，tree `81d5ef66421f073201a7527835ee2d38a88cbfda` |
| index | `C:/w/des1025-prisoner-source-9c4-a02/evidence/final-native-index-a01/native-source-index.actual.json`，3747 B，SHA `687bbd9969ca620cca92ab7d283be05ea8188e57bba4931a8433cbafb4ea5f56` |
| DLL | `C:/w/des1025-prisoner-source-9c4-a02/build/xar_ck3_bridge.dll`，16593920 B，SHA `1f9b1fafdd2c8e5043ed2a089504ad1a7d66078b4693347a5721520a8079ec6d` |

index 的 build-only `live_qualified=false` 是原不可变事实；实际 R0015 live 另存，不能倒改 index。CI 原件含两 EXE、真实 SDK 10 checks、CTest 2/2。Native04 来源登记失败、旧 R0014 大写 SHA 失败仍保留。

最新 Java producer 实际生成：`canonical-host-a15`、`common-runtime-a15`；runtime 1,272 文件，复制 30,725,804 B，来源 Main12／0e、Native05 不变。新公共 plan／prepare 均实际退出 0，已消费的 `prepared-core-a25/prepared-case.json` 18,550 B。不要热改 a15、a25 或旧 a14。

## 7. R0015：可复用的实际范围与必须补的缺口

```text
C:/ck3-dynastic-esotericism-20261024/common-runtime-a14/runs/desktop-3fevhd2-1c74096080--dynastic-esotericism--R0015
```

`R0015-ROOT-SUMMARY.actual.json` 为 5,194 B，SHA `b016569caaee9ef23c1a56ec79a2844e0435148b079bee245ac9729148803c7b`；副本已提交至 Main12 的 `mod_dynastic_esotericism/docs/acceptance/R0015-2026-10-25.json`。

- 前四阶段签署：创建组／默认无／取消保持／无 Prophet 的真实创建；同 Faith 背离的三种产品犯罪与定向意见；跨 Faith 路径；回归清理。完整 core 仍未通过。
- 实际 Root31254、原 Faith13／Rite0→新 Rite150、Dyn12156／House12760；NPC founder／HouseHead41288，同 Rite。原生 Rite head 为 Root。
- **全量 62 名成员在 +1 和 +3 日有 Native＋独立 Save，恰好 +2 的完整保存缺失。** phase1 后 CaseClient 自动推进一天，Root 又手动一天，造成 +3；文件名含 plus2 也不能改写真实日期。
- 真实 primary_heir65836 也是旧后代负例，原 Orthodox Faith14／Rite6／House174／Dyn174。此前未执行 primary_heir_prepare，不能称其实际 NOT_READY。主动为继承改信前，保存旧后代未连带迁族的历史负例；主动改信后停止将其当作“未改信”负例。
- 原版合法囚犯控制65833 实际 custody；处决 Can=true、banish option4 Can=true、十项零成本／native5000000／would_accept=true 的真实预览已完成，**没有 Send**。Native05 数值来源修复在实际路径有效。
- Save 中唯一 −100 意见来源及四方向独立统计通过：Root→target、peer→target 各 1；outsider→target、target→Root 为 0。
- 长期 input 在回归后仅准备；没有完成第二 Rite、61 日、自然出生、真继承、开关重用、新 head 赦免或 cold anchor。

实际终止原因是 `r15-second-open-a01` 在同一 public revision 对已打开的 Decisions 重复 open，被共享 SDK 在原生分派前正确拒绝：`Decisions opener already claimed for this episode; no action retry`。**修调用顺序，查询现有 keyed tree；不清 claim，不重放，不放松 SDK 守卫。**

R0015 原进程退出 Game0／host1／public2／allocator0／keeper0，SCREEN8968；有效 preserved-failure closure 已由冻结消费者实际退出 0。`R0015-preserved-failure-close-a01/failure-close.json` 9,533 B／SHA `f9c58de37bcfe3ecb1b867b8a1dbed81b0bbb54db72e879d1b2d983b268c9684`。该失败不是最新 predecessor。

更早 R0013 的真实“卸任交接＋singleton 真实 NPC”、+1／+2 各 61 名全员 Native＋Save 仍可作未变产品的历史子集证据；不能补成 R0015 缺失的 +2。

## 8. R0016：本次交接闭场及后继接续方式

```text
C:/ck3-dynastic-esotericism-20261024/common-runtime-a15/runs/desktop-3fevhd2-1c74096080--dynastic-esotericism--R0016
C:/ck3-dynastic-esotericism-20261024/attempt-a25/state
C:/ck3-dynastic-esotericism-20261024/keeper-core-a36
C:/ck3-dynastic-esotericism-20261024/operations-core-a36/binding.game.actual.json
```

实际 Game PID26436／出生 FILETIME 字符串 `134374123550278143`。启动后从 1066.9.15／date_raw53144328 自然一天到 **1066.9.16／53144352**，actor31254；Root 完成三项只读 normal context、religion、campaign 查询。用户此时要求交接，**没有任何产品创建／取消／归族动作，没有 Root Save 或新 anchor，业务 0/6。**

Root 写入真实 `operator-evidence/USER-VACATION-STOP.actual.json` 及第一阶段结果 INCOMPLETE，六个断言均 false。共享 CaseClient 接管自动 typed normal exit，Root 没有另行 quit、finish_hold 或业务重入。

| 事实 | 实际结果 |
| --- | --- |
| 原 Game／retained OS handle | 退出 0；实际结束 14:43:33.792946Z |
| 原 host Popen | 退出 0，14:43:43.430670Z；native-report GREEN、error=null、cleanup_ok=true |
| 原 public run／verify | **均 2**，完整业务 false |
| keeper／原 allocator | 均退出 0；原工具会话已消费，不再等旧进程 |
| 正常退出 | 原结果 `normal_close_qualified=true`；**autosave_verified=false** 原样保留 |
| SCREEN | keeper 最后序号8981，实际 CAS 释放到 **8982**，资源为空 |
| 当前进程／owner | 冻结消费者实际 inventory 无 blocker，独立 bus list 无 SCREEN owner |

正常退出与业务资格分开：`case-error-preserved.json` 保存产品要求不完整，不能将 normal-close true 解释成业务 PASS，也不能因 autosave false 擅自改原 normal-close 字段。

闭场根 **`R0016-vacation-close-a01/CLOSURE.actual.json`** 保存原回执 pins。当前冻结生产消费者实际执行 `previous_session_closure`、`require_predecessor_keeper_release_v1`、`runtime_process_inventory`，原进程退出 **0**，得到 **`mode=previous-shared-managed-session`**。

恢复时：以 **R0016** 为 `--previous-live`、keeper a36 为 `--previous-keeper`、**`R0016-screen-release.actual.json`** 为 `--previous-release`；**不传 `--previous-failure-close`**，本轮走正常 managed-session cleanup 路径；不得 first-machine-bootstrap，也不能退回 R0015。若后续插入了屏幕任务，另外读取实际更晚 release。

R0016 的 profile／purpose／Prepared／single-use ledger 已消费。新运行预计 R0017，以 canonical allocator 实际分配为准；新 state、Prepared、operation／keeper 根均须重新选择未使用路径，不能复跑旧 run/context。

## 9. 恢复后业务步骤，按此避免已知误操作

1. 用户恢复后，核机器 ID、真实源码及输入、Steam 后台离线、存储新准入和最新总线 owner。只走公共 `tools/ck3_mod_acceptance.py plan/prepare/allocate/preflight/run/verify`；没有 SDK／native 变化就复用实际资格，不重复全图编译。
2. 先完成 fixture_ready 和原生创建资格。每个新操作唯一 ID，队列字段 `args`、`fresh_revision=true`；读取真实 row 的 `finished_at/ok/result/after_snapshot`。非 confirm pending 走独立观察，只有 final confirm 的真实 claim 才 collect；UNKNOWN 不重放。
3. **phase1 签字前完成恰好 +1、+2 的完整 Native 成员表＋独立 Save**，核真实日期。phase1 后 CaseClient 有自动自然日，手动下一日前先读当前 date。事件／通知先依原生界面规则处理，不能带 blocker 强推进。
4. Decisions 已可见时先 query 现有 keyed decision tree，找当前真实 key；不要在 unchanged public revision 无条件 reopen。当前操作卡已有修正，不修改 SDK once guard。
5. 回归后，先在旧 Root 完成长程：extended_start；第二 Rite 建立＋31 日；交叉 Rite／迁移、stock crime／repent、生成、合法旁支、外改 House 各真实后态；原 timer61／两次 callback；**第二 NPC founder 死亡后31日**，可与其他计时重叠。每次先读真实条件，fixture 不能替产品写绑定。
6. 自然出生必须实际孕期／出生 callback，遇出生 marker 停下，随后推进**恰好一日**并 Native＋Save 核身份、归族与可玩者知识；直接生成的人物不能冒充自然出生。
7. 再执行新真实 primary_heir_prepare，必要时 stock Faith→Rite 输入；至少一自然日后，固定实际继承人／存活成年／主头衔／Faith／Rite／House／Dynasty。继承改变或不合格就报告 NOT_READY，不能另造合格继承人或改玩家。
8. 旧 head 真实 UI 编辑 None，完整 Can／报价／五项名称、prepare／confirm 各一次、独立完成读回，固定原 Rite／Dynasty。然后只安排一次次日 stock 玩家死亡，用现有一日自然推进且 `allow_actor_change=true`；不调用 set_played_character，不强设 head，不清原版 once flag。
9. 固定旧 Root 确死、原主头衔真继承、当前 player 是 pinned living heir、原 Rite／Dynasty 保留、native Rite head 为 successor，才 successor_readback。再在新 head 上真实编辑 Dynastic，验证绑定重用。
10. 仅由**当前新 head** 执行最终 pardon_prepare→自然一日→合法 pardon 一次→observer→31日，逐项读回无三种产品理由且独立原版犯罪保留。不用旧 Root 赦免替代新 head。
11. phase6 重新核所有历史与实际新 head，生成真正新 head cold anchor，真实 Save 并独立解码。当前没有这样的有效 Save，R0015／R0016 文件不能改标签作锚点。
12. 分别新 PID 做 cold_reload（0日、精确最终新 head Save）、pre_product_seed（0日、真前产品、不挂产品，只挂2文件日志 fixture）、old_save_bootstrap（≤2日、精确 seed Save、正式一次初始化、12文件被动 fixture）。不得删产品标志伪造旧档，也不能提前 registrar。

core 固定 **9000s hold／10800s overall／1800s readiness／180s normal-exit reserve／400 自然日**。新场启动前固定，运行中不热改图或加时。安排死亡、长计时与最终赦免前检查剩余自然日和墙钟；不足就如实停，不延预算冒充完成。

离线 gate 为 **30 秒**：同一执行链顺序 probe→context→preflight，再**全新 probe→全新 context→立即 run**，后两步不跨模型回合。不要使用旧离线 receipt。Steam 状态确认后台完成，不抢焦点／截图。

存档独立读取复用 streaming projection，不落完整 melt。House→Dynasty 拓扑与 ID 分开；历史 `save_fields.stored()`／`graph()["variables"]` 仅保留 `lyd_`，必须从 raw AST variables 筛真实 `des_` 键并用 `typed()`，不能把过滤后的缺失当产品缺失。

## 10. 发布收尾与缓存验收

先修复和验证真实发现的问题，再按用户顺序更新 **3826991345**，不要创建第二物品。Main12 的产品注册表、workshop registry 与首发永久记录已写实际 ID。

缓存验收只要求 **Steam 实际下载的文件 exact match 已发布正式25文件＋CK3 实际加载该缓存**。不挂业务 fixture、不重跑事件／按钮／特质／冷却／全矩阵。尚无实际 subscribe／download callback 或缓存载荷资格；不能用本地复制 staging 冒充 Steam 下载。后续记录叶路径下载前不存在、原 worker0、实际 App／Item／Result1 及下载 callback，精确比对后新独立缓存 profile 加载、正常退出与 SCREEN 闭场。

必要联网后立即恢复 Steam 离线并后台核验。联网启动游戏前查账号是否另一机器正在游戏，不能顶号。公开 Notes 429 是补读项，不授权重复上传相同版本。

源码整合前重新准入 Git 写与容量，fresh fetch／线性 rebase／普通 fast-forward 推送，等待 exact SHA 官方 CI。当前两提交没有云端 CI 通过结果，不能引用旧 commit 的 CI 当新提交全绿。创建首发 tag 时按真实源6241与发布记录绑定，不重写旧 manifest。

## 11. 容量、已回收对象与有限保留

本机统一账本 **`D:/workspace/.codex-task-bus/e04-capacity-reservations.json`** 已由实际短 CAS 更新为 **revision1216／storage104**，任务 waiting、scope `closed-no-heavy-write-admission`；释放原 held future **C:5,398,757,712 B／D:2,097,152 B**，任务未来预留均为 **0**。这不是物理删除或磁盘增量。

闭场凭据：

```text
C:/ck3-dynastic-esotericism-20261024/capacity/VACATION-R16-FUTURE-RESERVATIONS-CLOSED-r1216.actual.json
13377 B / SHA e157b38889c9d6c4ba96956cdfc6d7bd0d1fb5e9016771ab76a49f3590d057bb
C:/ck3-dynastic-esotericism-20261024/capacity/VACATION-R16-STORAGE-CLOSED-READBACK.actual.json
```

最后完整容量 fresh check 原退出0：`capacity/FRESH-R1215-VACATION-CLOSE.actual.json`，25,325 B，SHA `9fab48837f90db3c83782359431b59f89f1c58ab32f897e273069c72bfb493e2`。约14:52Z 观察 C free42,520,276,992 B／D free21,618,937,856 B；按当时全部未消费预算、系统预留与20GiB安全计算，仅余 C83,251,816 B／D7,786,496 B。**恢复必须重新测量、准入，不能沿用这些历史小余量。** 闭场撤销本任务有限配额例外，旧21:00Z期限没有延长；没有新 Game／build／test／download／Git 写权限。

本轮为实际新图腾空间，已精确回收 Native05 的 **832 个可重建编译／链接中间文件**，实际分配量 **407,442,032 B**；不是整目录删除，没有删源、DLL、EXE、配置、日志或 Save。逐项身份／SHA／永久保留索引检查在实际回收记录：

- `capacity/Native05-static-lib-reclaim-a114/{PLAN.json,ACTUAL.json}`：一 `.lib`，157,052,928 B。
- `capacity/Native05-other-derived-reclaim-a123/{PLAN.json,ACTUAL.json}`：831 个中间物，250,389,104 B。
- `capacity/r1214-Main12-after-reclaim-a124/NATIVE05-POST-RECLAIM-BRIDGE.actual.json`：保留737文件、56,762,976 B，重建历史身份表仅追加已删 metadata，原件明确不可读。

旧 r1209 whole-tree inventory helper 对已删中间物会真实失败；不要假造同名 `.lib` 或重写旧成功回执。新容量生产路径使用明确 post-reclaim bridge。另有 r1213／1214 Game／construction 身份表示不同导致少量重叠计数的历史勘误；r1215 已排除重叠并规范 FileID，旧回执不倒改，不作为新授权。

当前必要保留到 **2026-10-31T00:00:00Z 用途复核**：首发 payload／manifest／收据、当前 Main12 与其借用对象、Native05 最小源码／DLL／index／CI、a19 Java／runtime 输入、R0013关键分支与 R0015未解决业务原件、R0016闭场。保护不等于永久保留全部旧 run，也不授权到期自动删除唯一恢复输入。执行统一 [存储策略](../storage-retention-policy.md)／[版本化参数](../storage-retention-policy.json)。

## 12. 本机约束及交接结束状态

CK3 实际安装 `.4`：`C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe`，1.20.0.4／build25734779，101,040,248 B，SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。首次临时在线后已重新核 EXE 未变。恢复仍读取实际值，不从其他机器或文件名外推。

Steam PID13256、出生 FILETIME **字符串** `134369289811819170`、版本11.12.30.7 仅为本次观察；不要用于未来 PID 绑定。64位 FileID／FILETIME 跨 JSON／JS 使用规范十进制字符串。

该机五项 Workshop 本地禁回装偏好继续有效：2291024373、2993056101、2962333032、3192256710、2224124758；不全局退订、不恢复屏障 ACL、不删除0B保护占位。新 Dynastic 物品不在五项中。Defender 仅按已有项目来源精确 EXE 登记，不新增全盘排除或重试历史 UAC。

禁止 PowerShell；新生产开发 Java／Maven／Quarkus，既有 Python 只在允许维护范围内维护。本次行政捕获脚本不是新增生产实现。没有继续运行的 CK3、keeper、队列 writer 或本任务 SCREEN owner；没有后台定时续跑。用户恢复后从本文第9节继续。
