# 宗族化密教：度假交接（2026-10-24）

用户最新指令是“你要去度假了。写交接文档到docs。”因此暂停后续编码、构建、实机和发布，完成本交接。原“需求→测试方案→编码→验收→发布”任务尚未完成，不能标成发布成功。

**当前结论：需求和测试方案已入库，模组首版代码已实现；三轮实机均未通过完整业务验收，Workshop 尚未创建物品。当前没有 CK3 进程或屏幕 owner。**

本交接的执行机器为 `machine_id: desktop-3fevhd2-1c74096080`。现场最终观察见 `C:/ck3-dynastic-esotericism-20261024/handover-2026-10-24/closure-readback.actual.json`，该文件记录真实 UTC 时间、命令及返回码；Steam 新鲜后台观察在同目录 `steam-offline.actual.json`，结果为 offline。路径与本机事实不能外推到其他机器；接手时先运行 `tools/ck3_live_run_id.py machine`。

## 1. 需求与产品边界

- 产品目录：`mod_dynastic_esotericism/`；key：`dynastic-esotericism`；英文名：Dynastic Esotericism；目标版本 0.1.0，**无 Workshop ID**。
- 原生 Rite 创建／改革／编辑 GUI 加“宗族化”组，选择“宗族化／无”。不能把 Faith、Religion、House 或 Clan 政体当作 Rite／Dynasty。
- 宗族化 Rite 创建并绑定真实 Dynasty 与加入 House；所有存活信徒，包括创建者、AI、儿童、无地和生成角色，实际加入该宗族。
- 同宗族成员背离绑定 Rite，包括同 Faith 换 Rite，保留宗族身份。原 Rite 信徒对其有一项定向、不叠加的 `des_apostasy_opinion = -100`，并有实际监禁、放逐和处决理由，保留原版管辖／囚禁资格。不自动处罚或强迫改信。
- 回归、离开宗族、关闭选项时仅撤销本产品来源；独立原版罪行保留。持续背离不刷新已赦免／消费的理由。关闭保留 Dynasty，重新启用复用。
- 实际出生及翌日、生成、旁支、外改 House、第二 Rite 负例／交叉转换、赦免后 31 日、创建者死亡、冷重载和真实前产品母档初始化均仍须验收。
- 原生 `add_known_doctrine` 只接受 `is_playable_character`。知识断言已按 R0001 真实错误收紧；全员归族／犯罪规则没有缩减。不可玩 NPC 与新生儿不能被要求接受原版拒绝的知识写入。
- 宗族随机名称沿用原版；旧档一次性正常初始化决议；多人未验收。没有发布资格，也没有“实机全部通过”。

入口文档：[需求](../../mod_dynastic_esotericism/docs/requirements.md)、[测试方案](../../mod_dynastic_esotericism/docs/test-plan.md)、[可行性](../../mod_dynastic_esotericism/docs/feasibility-2026-10-24.md)、[状态](../../mod_dynastic_esotericism/docs/delivery-status.md)、[操作卡](../../mod_dynastic_esotericism/docs/acceptance/operator-runbook.md)。这些产品文档的已提交状态未包含本次工作树中的所有后续勘误，须同时看下节补丁。

## 2. Git、未提交改动与恢复方式

交接前最新已推送产品／共享源提交为 **`8bcff51b0d7767b69643e5ec77920c1c932abed5`**。C 干净 checkout 当时为 `C:/ck3-dynastic-esotericism-20261024/s`，该提交包含历史只读验证兼容、R0002 TTL 闭场路径与此前修复。后续文档交接提交不代表模组又完成了新一轮验收。

D 工作树交接前基线为 detached `70355cbc7b072687b03fa82dd8912c9ed85b8492`，这是上述 8bc 提交 rebase 前的本地副本。十份本次工作文件的基线 blob 已逐一证明与 8bc 相同。

**不把未验证半成品装入 master 的运行代码。** 十份自有工作树改动完整保存在随文补丁中，源文件在 D 工作树也继续保留；交接提交只收录交接文件及补丁。

- [完整工作树补丁](2026-10-24-dynastic-esotericism-working-tree.patch)：24,538 B，SHA-256 `5670d9ea7882c07fa3f0149d91ac67849f8b312d34dbe52650b655e0010a41c3`。
- [机器可读快照](2026-10-24-dynastic-esotericism-vacation-snapshot.json)：含十份文件的当前 SHA、大小、原 blob、来源提交和排除项。
- **用户原有脏文件** `docs/handover/2026-10-22-war-episode04-vacation-handover.md` 没有包含在补丁或本次提交中，未修改、撤销或代为提交。

| 工作树文件 | 当前事实 |
| --- | --- |
| `tools/ck3_mod_acceptance_allocate.py` | **未验证半成品**。增加 typed native observer 的资源闭场类型／helper／分派，尚未测试、strict 或以 R0003 原件通过消费者；不可直接执行后继分配。 |
| 四份 `acceptance-fixture` 脚本 | 修正 R0003 引擎加载发现的具体错误；语法 4/4 通过，尚未重构 JAR／fixture 或实机复验。 |
| `tools/test_product_acceptance_purpose.py` | 补齐合成 Selection 的 `case`；实际产品目的 5/5、该测试 strict、正常退出 5/5（含历史 v1/v2）通过。生产 guard 未改，尚未推送修正。 |
| `tools/ck3_mod_acceptance_cases/dynastic_esotericism_core.json` | 首 phase 改等真实 `fixture_ready`；更新下一场预算来源说明。未 prepare／allocate。 |
| `tools/ck3_mod_acceptance_products.json` | 下一场 core 固定 hold 9000 秒、timeout 10800 秒；未分配使用。 |
| 产品 `docs/test-plan.md`、`docs/acceptance/operator-runbook.md` | 同步上述下一场候选规则，补 nonconfirm pending 的正确观察方式。 |

新干净工作树恢复前先 `git apply --check --unidiff-zero docs/handover/2026-10-24-dynastic-esotericism-working-tree.patch`，再决定应用和完成半成品。**在当前 D 工作树不要重复 apply**，这些改动已经存在。远端有并发更新时先 fetch、检查差异并线性 rebase；不能 merge 或 force push。默认提交推送规则继续适用，用户原有脏文件继续排除。

## 3. 三轮实际场次及关闭事实

以下全部属于 `machine_id: desktop-3fevhd2-1c74096080`，观察日期 2026-10-24。没有任何一轮完成 Root GUI phase PASS。

| 场次 | 实际结果 | 资源结束 |
| --- | --- | --- |
| R0001，runtime a03／keeper a16 | 已启动 CK3；不可玩角色教学错误约 35,240 条，旧 R05 scope 导致日推进失败。保留 RED。 | CK3 原进程 0；host 1；public run 2；keeper 0；SCREEN CAS **8596**。当时经实际原生失败后用原版 GUI 退出。 |
| R0002，runtime a04／keeper a17 | public run 在 host／Game 启动前拒绝：离线观察已 73 秒，冻结 gate 只允许 **30 秒**。目的文件已消费，不可重放。 | host／Game 未启动，其退出码为 null；public run 2；keeper 0；CAS **8607**。 |
| R0003，runtime a05／keeper a18 | 新离线观察约 8 秒内通过启动；真实单日推进成功；fixture 加载错误，随后误对 nonconfirm open 调用 collect，host 保留错误。业务 RED。 | **原生正常退出，无 GUI／强杀**；CK3 原 Popen 0；host 原 Popen 1；public run 2；keeper 原 Popen 0；CAS **8619**。 |

R0001／R0002 小摘要已入库：[R0001](../../mod_dynastic_esotericism/docs/acceptance/R0001-2026-10-24.json)、[R0002](../../mod_dynastic_esotericism/docs/acceptance/R0002-2026-10-24.json)。

R0003 的完整 run ID：`desktop-3fevhd2-1c74096080--dynastic-esotericism--R0003`。

```text
C:/ck3-dynastic-esotericism-20261024/common-runtime-a05/runs/desktop-3fevhd2-1c74096080--dynastic-esotericism--R0003
C:/ck3-dynastic-esotericism-20261024/attempt-a06/state
C:/ck3-dynastic-esotericism-20261024/keeper-core-a18
C:/ck3-dynastic-esotericism-20261024/prepared-core-a06/prepared-case.json
C:/ck3-dynastic-esotericism-20261024/run-core-a18.actual.json
C:/ck3-dynastic-esotericism-20261024/allocate-core-a18.actual.json
C:/ck3-dynastic-esotericism-20261024/R0003-screen-release.actual.json
C:/ck3-dynastic-esotericism-20261024/R0003-screen-release-command.actual.json
```

R0003 Game PID `31096`，进程 FILETIME **字符串** `134373157160016545`；host PID `19564`。最终 native report `status=RED`，`finished_at=2026-10-24T11:58:16.984216+00:00`，`managed_session_done=true`、`managed_session_thread_finished=true`、`cleanup_ok=true`。单次合法 failure `finish_hold` 成功；最终 Game job before／final 均为 0。原 allocator 与 public run 的工具会话均已消费完成，不再等待它们。

原 `operator-normal-exit-observe-002` 保留同一 handle 的 `WAIT_OBJECT_0/exit0`，`process_identity_verified=true`、`typed_normal_exit_observed=true`。**`autosave_verified=false`、完整 normal-close 仍不合格，不能改写原结果。** 还须查清其属于未执行 disable-exit-autosave 步骤还是其他观察缺口，不能在后继业务通过时忽略。

正常退出是异步分段：首次 prepare 返回 pending 后，新 query 实际看到 stage0 主菜单已开，随后只执行未消费 stage1 的 `continue_preparation`；最终 confirm 仅一次，继续同原 handle observer 得到退出 0。不能重放已消费的 stage。首个只读 normal-exit probe 的 Root 独立快照在 run 下 `root-normal-exit-query.observed.json`。

Root 首次 CAS 释放命令缺全局 CLI SHA 参数，实际拒绝 3、无状态变更；随后附正确 SHA，以 keeper 最后序号 8618 成功释放到 8619。真实成功与先前拒绝均记录于上列 command 回执，不能冒充一次成功。

**尚未执行 R0003 public verify，尚未生成 R0003 successor closure。** 不可拿 R0002 或 R0001 继续作为最新 predecessor，不可 first-machine-bootstrap；本机 canonical 产品计数已到 R0003。

## 4. R0003 发现的问题与已准备的修正

### 4.1 引擎确认的 fixture 加载错误

完整 7,808 B 原 error.log 观察 SHA：`ecf06f36d35c6597a5bd84aa2e1e56b43a734237f4e941f8e6c463234d5f7a5a`。保全全文的小快照：

```text
C:/ck3-dynastic-esotericism-20261024/R0003-loading-script-red.actual.json
C:/ck3-dynastic-esotericism-20261024/acceptance-preparation/native-fixture-loading-fix/incremental-parser-r4.actual.json
```

后者 17,506 B，SHA `c52b62afe73f21e1f1739223b146b77f99fd0d6b16bb22fd98f497752e27b68a`，含原版参照、diff、命令与全部来源 SHA。

| 修正 | 原因与边界 |
| --- | --- |
| `events/des_acceptance_extended_events.txt:280` 的两处 `dynasty_head` 改 `dynast` | 引擎拒绝旧目标链接；原版 `81_pam_legacies.txt` 与 `00_dynasty_triggers.txt` 有同 scope 用例，保留活族长且非已死 founder 的条件。 |
| `common/scripted_effects/des_acceptance_effects.txt` 四个 `debug_log` 改裸 `$PASS$/$FAIL$` | caller 已给带引号完整字符串，旧模板再加引号使展开产生 Unknown effect TEST／NEGATIVE 等。 |
| `events/des_acceptance_events.txt` 独立 outsider 加 `location=root.location` | 没有 employer 的新角色缺地点；保持独立负例，不加 employer。 |
| `common/scripted_effects/des_acceptance_extended_effects.txt` 独立旧后代加同样 location | 保留原 Rite／House／father，不绕过后代负例。 |

四个修改文件 grammar parse 实际退出 0、diagnostics 空、roundTrip true。`ck3-1.20.0.4` semantic profile 仍未注册，validate 退出 4／UNSUPPORTED；**绝非语义或游戏通过**。22 条 unused 提示为 11 个写入证据键重复出现；没有删除这些字段或降低门槛，也不能宣称 error.log 已清零。

### 4.2 GUI 调用方误用与下一场准备门槛

R0003 baseline 为玩家 `31254`、Catholic Faith `13`、Roman Rite `0`。当时原生 piety 仍 150；fixture 计划加 100000 尚无实际完成证据。`des_acceptance.1` 由 `on_game_start_after_lobby` 以 `days=1` 排队；仅推进到第 1 日不能证明该事件已经执行。

**无需改成儒家。** exact .4 原版 CanCreateRite 开窗谓词、已改革 Faith 的 GUI 与零分歧路径支持 Catholic 基线；两个新增 doctrine 均 divergence 0、费用 0。最终能否提交仍按实际完整 `Can`、报价、名称和后态判断。先前口头“必须 Confucian”无依据，已经撤回，不能写进后续资格。

`open_create_draft` 实际 dispatch 后返回 `acknowledged_verification_pending`／`rite_creation_open_postcondition_unverified_do_not_retry`。此时不能重放 open。SDK 的 collect 文档与实现只收集 **final-confirm** claim：只有 `confirm_once` 创建 fsynced `*.claim.json`，非 confirm 仅保存原 `*.native-result.json`。本次对 open 调 collect 被拒绝“original local Rite claim is missing or ambiguous”，属于调用方误用，**不是 claim 丢失证据**。没有为此改 SDK 或 native。

下一场：先自然推进到真实 `DESAF: TEST PASS fixture_ready`，再读资源、两个知识、无 Prophet、实际 Rite；非 confirm pending 保留原 receipt，用 action context 的 `observation=draft/current_rite` 独立观察，必要时查询 groups；只有 confirm pending 调 collect，最终再独立 verify-completed。

工作树首 phase 已改成 `when_markers=["DESAF: TEST PASS fixture_ready"]`。下一场预算候选预先固定 hold **9000s**、overall timeout **10800s**，readiness 1800s、normal reserve 180s、最大 400 自然日保持。依据 R0003 实际 native 单日动作 8.566s，连后续 snapshot 约 12.315s，400 日规划估计约 82 分钟，另需 GUI。**此候选尚未 prepare／allocate，不修改 R0001–R0003 的 3600／5400s 原预算，也不允许运行中加时。**

### 4.3 尚未完成的资源闭场消费者

R0001 既有 `preserved-failure-native-process-exit-zero` 分支有 GUI window 原件要求。R0003 实际走 typed native observer，没有这些 GUI 回执，不能伪造旧形状。

`tools/ck3_mod_acceptance_allocate.py` 的工作树半成品试图为此增加显式 typed-observer 分支。它只可证明资源已结束，必须保留 normal-close／autosave／business false；目前**没有新 fixture/test、没有 strict、没有实际 R0003 consumer 通过，producer closure 也不存在**。接手第一项应审完／完成或撤销该半成品；不能直接运行它分配 R0004。

## 5. 可复用的已完成验证与工具

1. 正式开发包仍为中英 **17 文件**，与 fixture 分开。Java／Maven／Quarkus 构建、真实 manifest 消费者、ZIP、13 文件 core fixture 在固定 480ea 基线上 **14/14**，15 项打包资源逐字节核对。该旧 fixture 含本轮刚发现的错误，**不能复用于下一次业务验收**，须重构。
2. 最后旧 JAR／产物根：`C:/ck3-dynastic-esotericism-20261024/release-localization-builder-a01/final-normal-exit-builder-a01/`。runner 在 `java-build/dynastic-esotericism-tools/quarkus-app/quarkus-run.jar`；应用 JAR SHA `c0a921d21158e6fb44b4c78764df9118f83733bc34ab95e252e71ab04d10b8e8`。只做后继行政 source composer 时曾复用；四 fixture 资源变了后必须重新 Maven 构建。
3. 本机默认 `mvn` 已升级为 **3.10.0**。目录名仍含旧 3.9.16，不能用名字推断版本；不用固定旧版 EXE。来源见产品环境文档。
4. 原生 BASE：`C:/ck3-dynastic-esotericism-20261024/native-religion-01/`。DLL SHA `2ea5b48e6e8fd900ac4d1ac9e52378d16b77857201a723a9db70cc9e8d49fe4d`；native source index SHA `2e5914aa157fc104f90b2b63f59bcba80628dc1d979d233d19189f1f0b697fa3`。14 功能、三个原生测试及 Cw SYSTEM 精确路径回执已验。BASE／`C:/w/des1024-rite-tests-a01` 冻结；先前 UAC 取消 1223，**不要重试 UAC**。这不授予所有业务 PASS。
5. SDK 19 项礼仪与 4 项同 Service 注册回归已通过，五个持久名称字段及 cancel／observe-current／verify-completed 已进入冻结 API。不要重新添加平行 Service 或产品私有原生控制器。
6. Python 隔离环境：`C:/ck3-dynastic-esotericism-20261024/sdk-ci-isolated-py314-a01/venv`。固定依赖含 psutil 7.2.2；unrun strict 还需 types-psutil 7.2.2.20260906。最终小组通过使用只读复制 stubs，未改运行中的 venv。详见已有实际回执。

历史兼容／TTL／cold 验证摘要均已入库：

- [历史 normal-exit 读取兼容](../../mod_dynastic_esotericism/docs/acceptance/historical-exit-compatibility-2026-10-24.json)：缺 profile 的历史 context 可读；实际 launch 仍拒绝缺绑定。
- [R0002 TTL recovery](../../mod_dynastic_esotericism/docs/acceptance/offline-ttl-recovery-2026-10-24.json)：5/5、修改范围 strict；真实 allocator／ID writer R2→R3 回归，canonical counter 只在 admission 核对，冻结仅 immutable snapshot。
- [完整 cold 本机复测](../../mod_dynastic_esotericism/docs/acceptance/hosted-cold-recovery-2026-10-24.json)：四命令均 0，232 测试＋6 文件 strict＋8＋8。广义 pin observer 有 3 处辅助源码漂移，其原 FAIL 保留；最终 unrun 另以固定源码 5/5＋strict 通过，不倒签全图无漂移。

8bc 的 GitHub 读取结果：SDK [40090747068](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40090747068) success，cold [40090747071](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40090747071) success；产品 [40090747052](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/40090747052) **failure**，原因是 test fixture 的 `Selection.__new__` 缺 `case`，上述 D 修正已本机 5＋5＋strict 通过但未推送。全仓 Official Runner 当次最终读取仍 in_progress，不能称全仓 CI GREEN。GitHub runner 的 machine ID 未采集；这里只是本机读取远端结果，不属于本机实机验收。

产品目的 fixture 修正回执：`C:/ck3-dynastic-esotericism-20261024/sdk-ci-isolated-py314-a01/product-purpose-fixture-final-a01/SUMMARY.actual.json`，1,865 B，SHA `248f5d93e0ffe08e6e9ce5a1bef9a1ea22476da8617030d1348541ac67793af9`。

## 6. 接手后的顺序

1. 确认用户恢复开发；核机器 ID、实际安装／Steam 离线、存储新准入、任务总线最新消息与 owner。不要把本交接当成未来现场资格。
2. 读取源与补丁，保留用户原有脏文件。审完 `allocate.py` 半成品，补 R0001 旧 GUI 兼容、真实 typed observer、混合／错源／错误类型负例及修改范围 strict。用 R0003 原件实际生成并验证资源 closure；执行公共 verify，保留应有的业务失败，不伪签 GUI phase。
3. 完成清晰候选提交，fetch／线性 rebase／普通 push。用新的干净 checkout 对四项 fixture 资源重新执行默认 Maven `clean verify`、build／fixture／verify，实际检查 JAR 资源与源字节一致。不要把旧 480 产物改名充当新构建。
4. 依据公共 composer 创建全新 **common-runtime-a06**，而不是热改 a05。先前只完成 a05；a06 尚不存在。新 state 必须有新的父目录，不能复用已消费的 attempt-a06/state、purpose 或 single-use-ledger；建议接续另选 attempt-a07/state／新 prepared 名并核未消费。
5. 只走 `tools/ck3_mod_acceptance.py plan/prepare/allocate/preflight/run/verify`。真实最新 predecessor 必须是 R0003／keeper a18／释放 8619／通过验证的 R0003 closure。下一 run 预计 R0004，但以 canonical allocator 实际分配为准，不能手写 ID 或 first-machine-bootstrap。没有更晚 SCREEN 释放时 **省略 `--latest-screen-release`**；有插入任务时传严格更晚的实际释放。
6. 离线 gate 是 **30 秒**。同一执行脚本顺序：probe1→Root context1→public preflight→**全新 probe2→全新 Root context2→立即 public run**，第二 probe 与 run 中间不得跨模型回合。Root context `reviewer="/root"`，不能改 operator_delegation；保留每条原命令退出码。
7. 固定 source／argv／预算后不热改 C 源或 runtime，不在运行中加时。保留原 allocator Popen，keeper READY 不是等待其退出的信号。只有一个 native queue writer，Root 独立审实际后态并签六个 phase；UNKNOWN 不重放。
8. 稳定地图首日先 readonly normal-exit query，验证真实 profile／source inventory；后等 fixture_ready。首 UI 验默认无、两项可选、切换后取消全保持、一次真实创建确认及独立 completion，创建后另开编辑草案证明同组可见并取消。创建／编辑五名字必须独立读回，不能用 fallback 名称补空。
9. 完成六 phase 和 400 日上限内的全套既定场景。自然出生仍按真实孕期、出生日期及恰好翌日；不要跳过孕期、直接生成假新生儿或用 fixture 直接写产品绑定。保存每项意见与犯罪理由真实来源，普通交互 can_send 不能单独代替来源。
10. 再按同一共享 runtime 分别做新 PID 的 `cold_reload`、`pre_product_seed`、`old_save_bootstrap`。seed 真正不挂产品、只挂 2 文件日志 fixture；cold／bootstrap 用 12 文件被动 fixture，无提前 registrar。保存输入 `{save,bytes,sha256,player_id,date_raw}`；不删产品完成标志造旧档。每场正常退出、keeper 0 与真实 CAS 闭环。
11. 全部业务 PASS 后才进入下一节发布。当前不能发 Workshop，也不能只补标题写成已完成。

普通队列 step 用 `args`、唯一 ID／文件名、`fresh_revision=true`；读取 native report `finished_at/ok/result/after_snapshot`，不把 queue ACK 当成功。陌生事件按项目规则采原生实例／实际选项后选择第一显示项，批后离线补规则。

独立存档读取可复用 `campaign_score_save_reader.melt_projection` 的 stdout streaming（不落完整 melt），House→Dynasty 拓扑不可混淆。`i3b_checkpoint_reader.graph` 可读 Rite，但历史 `save_fields.stored()`／`graph()["variables"]` 只保留 `lyd_`，会静默过滤 `des_`；须从 raw AST 的 variables.data/list 筛真实键并用 `typed()`。旧 custody 的 64 位数在跨 JS／JSON 回执前转规范十进制字符串，不能经 Number 损失身份精度。

## 7. 发布准备与仍缺的交付

- 预览图已由 Root 看过，512×512，SHA `3a81e6c88de042dc91ca88a0388b7a811be7030cbb3308a3e4a4e1813a40c17f`。
- 七语最新候选：`C:/ck3-dynastic-esotericism-20261024/release-localization-candidates-a02/candidates.json`，18,232 B，SHA `8ef6d07d184d9191f02e24a1f66e5cc70fb07b435a913ebbbe63d8438bc17125`。105 值格式／保护 token／序列化通过；其中初始化说明 7 值已随 playable 限制重译，其余 98 值不变。未写生产目录。其他语义或外语实机未验，不能扩大。
- 真实源码仍中英开发包。业务通过后规范中英 `:0`，写七语候选，用 builder `--release-localization` 正式构建 **24 文件**。开发 CI 不强行要求七语格式；正式发布前必须跑正式格式门禁。
- 草稿：`workshop/dynastic_esotericism_description.bbcode`、`workshop/dynastic_esotericism_change_notes_0.1.0.txt`。没有 CreateItem／SubmitItemUpdate，没有 item ID、tag、公开 Notes 或缓存资格。
- 只做过只读 SteamAPI PE symbol 检查，`publishing-readiness-a01/symbols.actual.json`；这不证明 SDK 初始化、owner、账号在线或 EULA 已满足。
- 将来按既有 `ck3_workshop_mcp` steam-native publisher 完成实际创建／上传，目标 app 1158310，不能借其他产品 ID。`remote_file_id` 只能留用户目录外层 `.mod`。
- 发布冻结完整 Notes 字符数／行数／SHA，匿名精确回读目标 changelog entry 全文；核标题／描述／完整 tags 和 `1.20 'Crozier'` 兼容栏。EResult=1 不能替代公开回读。
- 真正 Steam 下载缓存逐文件核正式 staging，并证明 CK3 加载该缓存；缓存验收不重复业务测试。必要在线操作结束立即恢复并读回离线。
- 最后永久 `docs/release-changelogs/dynastic-esotericism/0.1.0.md` initial baseline＋真实 tag／commit／证据，实际提交推送 master 后才算首次发布完成。

## 8. 机器、容量与保留

本机安装：`C:/SteamLibrary/steamapps/common/Crusader Kings III`；CK3 **1.20.0.4 Crozier／Steam build 25734779**，EXE 101,040,248 B，SHA `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。这些来自本次已保全安装／实机来源，恢复仍核实际值。

公共外置根：`C:/ck3-dynastic-esotericism-20261024/`；统一账本 `D:/workspace/.codex-task-bus/e04-capacity-reservations.json`。停工前 r1156／storage44 曾在本任务 C4GiB／D32MiB 内为 a04+a05+a06 源快照共 120MiB、执行池 2GiB、builder48MiB 等分配预算，a06 未生成；旧期限为 2026-10-25T07:30Z。**度假闭场已实际更新为 r1157／storage45，本任务容量 scope 为 `closed-no-heavy-write-admission`，未来 C4GiB／D32MiB 预留归零，工作状态仍 waiting。** 未删除／移动文件，未扫描树或卷，物理回收为 0；不能沿用旧预算启动 Game／build／test。

闭场回执：`C:/ck3-dynastic-esotericism-20261024/capacity/VACATION-WAITING-FUTURE-RESERVATIONS-CLOSED-r1157.actual.json`，SHA `880f578ddf489237d54750534f98ad3541b6e59fd48fab94ef9672dfe546df27`；读回卡为同目录 `VACATION-STORAGE-CLOSED-READBACK.actual.json`。其他 claim 不变，没有延长期限；释放预留没有冒充磁盘空间回收。

当前必要基线、三轮原件、native／JAR／候选和补丁保留到 **2026-10-31 用途复核**，不承诺无限保留。按 [通用策略](../storage-retention-policy.md) 和版本化参数复核；恢复必须重新容量准入，不删除在用来源、唯一回执、个人文件或别的任务资产。

长期本机 Workshop 禁回装五项与 Steam 离线规则继续有效。未联网、未下载或恢复这些载荷，没有恢复 ACL 或重试 UAC。禁止 PowerShell；操作用 Python／cmd。没有任何当前活动代理负责继续自动推进，等待用户恢复。
