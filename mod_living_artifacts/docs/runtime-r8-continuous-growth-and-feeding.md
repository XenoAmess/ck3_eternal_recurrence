# R8：连续成长、卸下与四档喂养通过，host RED保留

**R8已闭场：首阶段四项核心检查实际 `PASS`，七份检查点完成，CK3正常退出、屏幕释放及闭场Steam离线均有实际证据；host原始退出1、报告RED原样保留。界面经验预览存在已确认缺陷，完整业务及发布均未通过。** 核心子范围通过、正常退出、host终态与全产品资格分别记账，不能互相代替。

## 场次与来源

本场 `run_id: pc-20260924rtuf-f11af23c08--living-artifacts--R0008`，`machine_id: pc-20260924rtuf-f11af23c08`。使用冻结c11源码 `cc673f79d1198b3ac72f342f9f4636e52334c8ff`、首阶段 `core_continuous` v3；[预声明范围](feeding-shortcuts-and-core-v3.md)不因运行中的新开发扩大。host原始启动时间为 **2026-10-22T10:46:26.850656Z**，host PID9740；本场CK3 PID11500、connection generation `"1"`、实际玩家31254。这些身份只描述R8，不作为下场常数。

实际CK3为 **1.20.0.4 / Steam build25734779**；EXE为 `C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe`，101,040,248字节，SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。本场原生hello再次返回相同版本、EXE SHA及 `ck3_build_match=true`；不能用历史场次的相同路径替代这次绑定。

外置原件根目录为：

- `LIVE = D:/workspace/ck3-living-artifacts-20261022/live/pc-20260924rtuf-f11af23c08--living-artifacts--R0008`
- `OBS = D:/workspace/ck3-living-artifacts-20261022/observations/pc-20260924rtuf-f11af23c08--living-artifacts--R0008`

本页后文路径分别相对此两根目录。`LIVE/run-context-r8-a01.json`绑定本场产品、prepared及frozen argv；其SHA为 `ba4449f6b670cef5474d54911e6925fbab812c5b0dbe57cae7eff2a6973e84cd`。`LIVE/frozen-argv.json`的SHA为 `ed13a13ed1004e2f69262692d674f155657dfcfce618bd7f0509514b83d7c074`，绑定c11 adapter、合同、EXE与实际运行参数；其固定runtime manifest为 `common-manifest.cc673f79d.json`，SHA `a3f75c292b45207d7f908309c3c2fd16580d709c718074429b064bf20fc4fc8e`。原生版本与PID另见各observer所引用的 `original_native_frame_record`，实际EXE SHA见 `LIVE/native-report.json` 的identity。

启动前后台离线回执 `LIVE/steam-offline-r8-a01.json` 于 **2026-10-22T10:46:18.541460Z** 观察到本机 `status=offline / offline_mode=true`；其SHA为 `f5fa10649b90a3204255638dc80be1407e213d5c488859b8f227739efbec9744`。这是启动准入记录，不冒充闭场后的Steam状态。固定hold5400秒、外层timeout7200秒、日数72和调用420上限、正常关闭180秒预留保持；本场实际argv的readiness timeout为1800秒，不能把方案中的准备建议值写成本场已用值。

## 已取得的保存后验

以下全部为同一实际物品 **402**、同一owner **31254**。`ck3_save_checkpoint`真正保存后，Root保全原件并用官方Rakaly严格熔化，`--unknown-key error`；再由observer解析并与当次独立原生owner、库存及装备谓词交叉。它们不是当前原生物品变量查询，也不是隐藏事件动态日志。第04次离线producer的先前失败与修订来源单列于后文，不写成原版本直接通过。

| 检查点 | 实际observer UTC | 保存日期/装备 | 等级/经验/pending/成长序号 | 月度记账/共鸣/耐久 |
| --- | --- | --- | --- | --- |
| 01 | 2026-10-22T10:56:03.206827Z | 1066.9.15，未装备 | 1 / 92 / 0 / 0 | 12801 / 20 / 75.00000 |
| 02 | 2026-10-22T11:07:33.516106Z | 1066.10.1，已装备 | 2 / 0 / 0 / 1 | 12802 / 25 / 75.00000 |
| 03 | 2026-10-22T11:42:18.509030Z | 1066.11.1，未装备 | 2 / 0 / 0 / 1 | 12803 / 25 / 75.00000 |
| 04 | 2026-10-22T11:52:14.510307Z | 1066.11.1，已装备，已喂普通材料 | 2 / 80 / 0 / 1 | 12803 / 25 / 75.00000 |
| 05 | 2026-10-22T11:55:04.127456Z | 1066.11.1，已装备，已喂大师级材料 | 3 / 80 / 0 / 2 | 12803 / 25 / 75.00000 |
| 06 | 2026-10-22T11:58:15.173963Z | 1066.11.1，已装备，已喂名作级材料 | 4 / 280 / 0 / 3 | 12803 / 25 / 75.00000 |
| 07 | 2026-10-22T12:00:57.476073Z | 1066.11.1，已装备，已喂卓越级材料 | 6 / 580 / 0 / 5 | 12803 / 25 / 75.00000 |

检查点01→02对应16日的装备月结路径：初始1级92经验经生产月度+8自行成为2级0经验，成长序号只增加一次，没有升级确认。检查点02之后实际卸下，至检查点03经过完整31日，等级、经验和成长序号均保持；**`last_month`推进只是已处理该月的簿记，不是发放经验或演化。** 这份卸下证据仅覆盖经验和演化停止，不外推为全部持续修正撤销、重新装备下一月恢复或完整LW-G02通过。

前三份保存中目标名称均为 `★待测活武器`，保留原物身份；四件普通材料仍分别为403/common、404/masterwork、405/famed、406/illustrious，名称不带星号。此处证明保存名称，不替代本场库存/详情截图显示审阅；也不证明转赠、继承或冷载后不会重复加星。

检查点03→04重新装备并真实喂普通材料，日期仍为1066.11.1，目标从2级0经验变为2级80经验，pending为0、成长序号仍1。第04解析按明确剩余集合 `masterwork/famed/illustrious`校验，保存中403已经消失，404/405/406仍在；材料与目标身份没有用同名替代。因目标为甲胄食性、材料为剑，本次为非食性基础80经验，不授食性倍率验收。

检查点04→05在同一暂停日期消费大师级材料，目标 `2级80 → 3级80`，成长序号 `1→2`，对应200经验立即跨过2级门槛。403/404均已消失，405/406仍在；没有为了等待喂养冷却而推进日期，也没有升级许可步骤。

检查点05→06消费名作级材料，目标 `3级80 → 4级280`，成长序号 `2→3`；保存中只剩目标与卓越级材料406。检查点06→07消费卓越级材料，目标 `4级280 → 6级580`，成长序号 `3→5`，一次消费立即跨两级，四件材料全部消失。四次均为同一1066.11.1暂停日期，分别实际到账80/200/500/1200，共1980经验；保存和独立原生库存核对未用另一件同名材料替代。

| observer文件（`LIVE/case-output/`） | SHA-256 |
| --- | --- |
| `observer-checkpoint-01.json` | `619de2736ff44578ae6070215fd6048ea23514b9a580d71609f39147b8a18de0` |
| `observer-checkpoint-02.json` | `366513b40943fde69fe3139196342044f60fc49b069fc26d738ad1aa24d9ba71` |
| `observer-checkpoint-03.json` | `591e91a25b81cfa8f533ed94b82a9fc83e8f101012883004b985d11620c5e726` |
| `observer-checkpoint-04.json` | `3bb40b64e69dfc8271e86cc8061a45058193394be117a3660afd0d2c5f90a79d` |
| `observer-checkpoint-05.json` | `783fe87ca5b4f12c6fa13d1c917f6a52e86a093f49218499ff059eedc18fdcd9` |
| `observer-checkpoint-06.json` | `ae0e417670aa1468777ec0c4ba570ac0c28a1f4612d9a9d5d6adf8263661e63e` |
| `observer-checkpoint-07.json` | `6971c73e1660a157359c219bf0cf88dae3c18ba7d3a9f7b2cb12b7cf9db8dac9` |

每份observer内的 `readback_response` 固定实际原始存档、熔化文本、melter、command及process回执的文件Pin，`original_native_frame_record`固定独立原生帧，避免在本文复制大文件。原件位于 `OBS/checkpoint-01..07/`。对应成功process均退出0，实际完成于10:55:01.026027Z、11:06:33.856842Z、11:41:23.306833Z、11:51:10.749061Z、11:54:05.977959Z、11:57:14.665163Z、11:59:59.379504Z；observer UTC是后续解析与交叉完成时刻，不能混称为同一个时间。

## 两次中断的实际续行

两次均先保留原生上下文，再由Root按既有专用策略处理；提交后另做原生快照。原始副本保存在 `LIVE/case-output/xalw-native-interruption-0001-actual-report.json` 与 `...0002-actual-report.json`，分别由同号 `continuation-evidence.json`固定SHA、策略/意图出处、真实提交及独立post步骤。新的Root响应包含run、machine、reviewer及原实例身份，没有将R7缺字段回执改写为成功。

| 中断 | 实际选择与独立后验 |
| --- | --- |
| 交互实例16777243，`arrange_marriage_interaction` | 原生上下文的sender34232、recipient31254、婚配双方33234/38924，拒绝合法。`root-r8-interaction-reject-01` 于11:13:40.082879Z实际完成拒绝；独立 `root-r8-interaction-post-01` 于11:14:22.124999Z确认原pending消失、无active event、玩家仍31254、保持暂停及date_raw53144736。 |
| 事件实例1，`bookmark.1070` | 实际原生选项第三项为“教宗和皇帝都可以保留他们的土地……”，native index2。`root-r8-event-choice-02` 于11:33:26.537733Z完成一次option_number3提交；独立 `root-r8-event-post-02` 于11:33:55.545144Z确认事件与pending均为空，玩家仍31254、保持暂停及date_raw53145312。 |

两份continuation evidence分别记录于 **11:16:24.287673Z** 与 **11:33:58.170338Z**，都绑定本场machine/run并标记未重放。其证明范围是已处理原中断且原窗口实际消失。事件效应预览明确不完整，本文**不声称已经实际获得250名士兵**，也不把选项ACK或定义中的效果当成军队后验。事件/通知选择均通过原生MCP，没有用OCR或鼠标替代。

## 第04次离线读取与界面预览问题

第04请求已实际提交保存，其请求位于 `LIVE/case-output/checkpoint-readback-04-awaiting.json`，仍为1066.11.1的暂停日期。首次外层producer命令实际退出1：共享producer的 `validate_request` 原第163行仍将检查点编号硬编码限制为1–3，与v3全路径的七次上限不一致。原始证据仅保留在对话工具transcript **chunk `3caf68` / exit1**，没有另存stdout文件，本文不制造不存在的文件路径。该失败属于离线读取入口，不据此判定喂养是否生效，也不用修复后的成功覆盖原失败。

外置 `environment/r8-producer-limit-fix-a01/original-failure-and-resumption.json` 于 **2026-10-22T11:57:55.489258Z**追加绑定原失败、请求/spec、修订源码、回归回执及实际第04消费结果。原报错为 `ValueError: checkpoint observation number: strict bounded integer required; bool/float rejected`；记录明确 `exact_failure_time_utc=null`、原stdout/stderr文件均为null。记录时刻不是捏造的原失败时刻；其resumption证明重用了原游戏保存、未重放游戏动作，并引用实际process和observer04的Pin。

修复已进入主仓共享生产模块及回归，活动c11保持原样。`LIVE/case-output/offline-producer-source-repair.json`记录冻结producer SHA `669779f1e2093b2b57ef91635454d75a58b7c4af6fb1f664a077547e38b02925`、实际修订producer SHA `4ed0dd6195d592ceb72159b33f40fc6f37d82d51cffd53887b03635e47243261`，变更为使用共享 `CORE_CHECKPOINT_LIMIT`。修订版本仅消费已存在的同一份只读保存原件，**不重放游戏中的喂养动作，也不追认旧producer已通过**；第04修订CLI实际退出0见工具chunk `6442a6`，随后已得到上表的实际observer04。

离线验证回执为外置 `environment/r8-producer-limit-fix-a01/result.json`，本机来源/回执观察时间 **2026-10-22T11:54:02.336270Z**；原始测试工具没有绝对UTC起始时间，不能把此时间写成测试执行时刻。18项完整producer模块单测与两份完整源码的strict检查实际退出0，但其中新第04请求单测截至 `validate_request`，不单独授予完整producer→consumer链通过；本场实际修订producer、真实熔化与observer消费是另一份运行证据。

另有实际界面问题：外置 `D:/workspace/ck3-living-artifacts-20261022/media/20261022T114447451610Z-r8-four-rarity-management.png` 虽以“four-rarity-management”命名，实际画面是**普通材料消费确认页**，顶部“本次经验（已含食性）”为0，底部基础经验为80。其同名JSON sidecar记录 `machine_id: pc-20260924rtuf-f11af23c08`、观察UTC **2026-10-22T11:44:47.451610Z**、原始1920×1080和前台CK3 PID11500；PNG为2,364,287字节，SHA `b0e859b1ab02bf19d46e2167920fbdb22324200d1e035b528617ecc1222c04d7`。文件名不作为画面内容或验收结论。

只读代码定位：`living_artifacts_core.py`中顶部通过 `owner.MakeScope.ScriptValue('xalw_selected_feed_xp_value')`求值，而该公式依赖事件临时命名作用域 `scope:xalw_material`及 `scope:xalw_artifact`；底部则直接对材料求仅依赖本物稀有度的基础公式。原版 `localization/english/vassal_stances_l_english.yml:131`证明 `owner.MakeScope.ScriptValue`语法本身有效，其原版计数公式只遍历当前角色；`common/script_values/_script_values.info`说明公式使用当前作用域可用对象，支持链式求值。**当前最窄推断**是顶部重建owner求值上下文时未保留事件临时物品作用域，因而得到0；这尚不是引擎内部机制的实测定论。第04真实保存已证明这次普通材料实际发放80经验，故已确认该页有显示错误，不能拿UI的0当实际结算值。后续可在新加载源码中验证事件原上下文的 `SCOPE.ScriptValue`或预先保存的只读预览值；本场不热改c11，也不从这次非食性结果外推其他材料/食性分支。

更直接的原版先例是 `localization/english/event_localization/hold_court_events/hold_court_events_joe_l_english.yml:565`：使用 `SCOPE.ScriptValue('court_8190_county_value')`，对应 `common/script_values/00_hold_court_values.txt:134–143`的公式读取临时 `scope:other_vassal`；同一localization的592行/对应公式159–168行读取 `scope:infidel_vassal`。这为保留事件上下文的修复方向提供来源，仍不能代替修复版本的实机显示验证。

## 入库的实机图

- [中文活武器管理指引](evidence/r8-management-guidance.png)：本机2026-10-22T11:43:48.056692Z原图，显示自动成长、卸下停级及管理入口文字；只证明当时实际显示。
- [六级活武器管理页](evidence/r8-living-artifact-level-six.png)：本机2026-10-22T11:59:22.200570Z原图，显示 `★待测活武器`、6级、580/600经验及25/100共鸣。可见异能名称不证明相应触发、收益或代价已验；此图没有四档喂养选项，不能当作四档入口截图。

两图原样入库，原件、字节数、SHA、capture回执及选择范围见[图片来源清单](evidence/r8-screenshots.json)。清单保留原始capture没有独立run_id的边界，不补造该字段；本页不声称已经公开上传。普通确认页的经验0原图继续作为外置缺陷证据保留，没有制作“修正后”替代图。

## 核心结果与尚待补齐

`LIVE/case-output/living-artifacts-core-result.json` 于 **2026-10-22T12:01:20.024494Z** 实际生成，`CORE-NATIVE-EQUIP-01`、`LW-G01`、`CORE-UNEQUIP-01`、`CORE-FEED-01`四项均为PASS，`error=null`、`original_action_unknown=false`。实际47自然日、320次计入预算的公共调用，均在预声明上限内。`case_contract_qualified=true`只证明这四项首阶段合同；同份结果明确 `gui_contract_qualified=false / business_pass=false / product_release_pass=false`，生成时 `normal_close_pending=true`。不能用一处status=PASS覆盖这些字段和deferred范围。

## 正常退出、host原始终态及资源释放

以下闭场记录同属 `machine_id: pc-20260924rtuf-f11af23c08`。Root直接审阅的正常Quit原图为外置 `media/20261022T120932328900Z-r8-quit-dialog-current.png`，实际观察UTC **2026-10-22T12:09:32.328900Z**，自动保存未勾选；最终点击的统一映射回执为 `media/r8-final-quit-desktop-a01.png.json`。通过共享review CLI登记真实审阅，最终Quit没有重复点击。GUI review自身不宣称进程退出；实际退出由独立保留句柄和原生终态证明。

`LIVE/case-output/normal-close-result.json`（SHA `616b47af802c5e5f20c5898b6a040185b21b9f2c3278385c5e5af3ba2d8c039c`）实际记录 `normal_close_qualified=true`：保留句柄已signaled、`exit_code=0 / actual_retained_os0=true`；`native_zero_proof`记录原生进程退出码0、实际结束 **12:10:19.797010Z**、`cleanup_proven=true`、进程树消失及control文件清理。该原生后态的 `status=not_applicable` 明确因为进程已经正常结束，不是仍可用的游戏观察或新增业务资格。

各层原始结果分别为：

| 层 | 实际结果与出处 |
| --- | --- |
| 公共run原始工具等待 | toolsession95985实际wait0，原工具transcript chunk `be0dc9`；不能据此把内部host写成0。 |
| host原始Popen等待 | `LIVE/host-original-process-exit.json`于12:10:40.992806Z记录PID9740、`actual_original_popen_wait=true / returncode=1`。 |
| host报告 | `LIVE/native-report.json`结束于12:10:40.250950Z，`status=RED / error=null`。`final_observation_error`为游戏退出后 `ck3_take_snapshot` 遇到native DLL disconnected；预期的库存打开前置拒绝 `xalw-core-0005` 也保留原始 `ok=false`行。没有将这些记录清成全host GREEN。 |
| CK3正常退出 | 前述normal-close记录的保留句柄OS0与原生process exit0，两份独立证明成立；不从host退出1倒推CK3被强杀。 |
| keeper/allocator收尾 | 12:19:07.246053Z合作STOP后的 `runtime/keepers/living-core-a10/report.json`记录线程已退出、failure及entry_error均null、最后seq455；Root保留原始keeper/allocator退出0，原allocate toolsession8749实际wait0、工具chunk `e714dd`。停止续租之后再独立释放屏幕。 |

`environment/r8-screen-resource-close-a01/release.stdout.json`实际回读于 **12:20:35.492964Z**：CAS推进至seq456，task状态done、resources为空；它是后续资源释放证据，不能替代前述正常退出证明。

闭场新的后台 `environment/steam-offline-r8-close-a01.json` 于 **2026-10-22T12:21:18.883385Z**确认本机 `status=offline / offline_mode=true`。`environment/storage-r8-close-a01/20261022T122118634161Z-task-close.json`于12:21:18.634161Z检查统一存储策略，`deletions=0`；没有宣称自动回收器已经部署或授予新重型写入预算。

全产品63项目录、NPC自主培养、饥渴与重诅咒、12异能及4联动、转赠继承和冷载仍依各自实际证据验收。本场第一阶段即使后续通过，也不授全产品或Workshop发布完成；目前没有本场上传、订阅缓存或公开Change Notes完成事实。
