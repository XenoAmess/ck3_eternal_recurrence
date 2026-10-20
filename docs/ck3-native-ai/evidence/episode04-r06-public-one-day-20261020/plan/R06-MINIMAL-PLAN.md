# R06 下一单日：唯一 Mar31 正常源与公共 adapter 缺口

`machine_id: desktop-3fevhd2-1c74096080`。观察时间和逐项原件 pins 见 `SOURCE-AUDIT.actual.json`。只读基于 master `93b27601aed449515b69aabed62e1af7cc61c1fc`，native tree `fee86631356f556271445157523c62abfd62951e`。本包未操作 CK3、SDK、屏幕、debugger、EXE 内容或存档内容，未改仓库。当前公共 R06 单日 actor **尚未接线**；下述合同是准确的实施清单，不能直接把 JSON 塞进现有 case 后声称会执行。

## 只用这个 S0

- 文件：`D:/workspace/ck3_native_war_ai_promo_work/e04-r214-refill-month-boundary-a01/mar31-checkpoint-preserved-a01.ck3`。
- 原始保存/保全 SHA `42dfd2c0ceb1d004ac7b34d921dee174f86b0c854237d447b173ccbebbd1f0bc`，74,273,410 B。此次只 stat，实际存在且大小相同；没有重新读或 hash 大存档，当前内容 SHA 没有独立重验。
- 来源 R214／R0209，source `191568c281bbde92feeb9f96fe40736be1b63ca8`；角色33388、1067-03-31/raw53149056、Army0/native0、Province2170，paused/map-ready，route空、不在战斗或撤退，原生 episode为null。
- 正常源 promotion：`C:/ck3-e04-resume-20261015-a01/r215-mar31-normal-source-a01/R214-MAR31-NORMAL-S0-PROMOTION.actual-a01.json`，9,210 B，SHA `5890702bcafc5f3c21418c59797ba4bca7a01bedd339d304b10dfd37941d5337`。
- 本次重新读取原 Save55,368 B、独立 after102,931 B、normal-close10,140 B、retained OS exit179 B、host wait245 B、keeper468 B及CAS6737精确保存行504 B，全部匹配 promotion 的原始 pins。normal_close_qualified=true、retained OS0、host0，CAS6737 done/resources[]。keeper旧 report 的screen_released=false保留，最终释放由后续CAS单独证明。裸原件缺机器字段时仍记unknown，由带machine_id的promotion及相同run/PID/create-time链绑定，没有改写历史原件。
- R215／R0210 的原 ready-context与prepared-case确实绑定该promotion；其真实唯一日到raw53149080，完整查询实体端点6674→6684只证明净+10。当时同Core全局subject closure为false，ADD仍false。本次仍从Mar31重载，不从Apr1后端点挑另一个存档。
- 原driver-state的`save_binding_mismatch`保留；它不是正常源依据。正常源来自原生Save、独立after与同进程后续正常关闭。普通public prepare自带的存档copy/digest校验继续执行，不由本包的stat顶替。
- R214 plain configuration四项原件此次重新核hash均匹配；直接复用 `R215 ready-context.json /case_inputs/plain_configuration` 与其 normal_checkpoint_build_receipt，不挂fixture/mod。

## 原生 producer 和线程合同已经有什么

已有真实 a37 `refill_add_hwprobe_12004.exe`：140,288 B，历史生产/SYSTEM SHA `f27826adcf3b0321614b3f8ed9dcd9bceb69da1a84f45233029245ea925ab9bf`。本次只stat EXE；重新读了a37资格48,180 B、2-case cold结果13,110 B、build1,997 B、原SYSTEM回执262,553 B与冻结source manifest8,115 B，pins均吻合，SYSTEM为verified/admin/S-1-5-18。冻结probe C++原件与当前工作树字节相同。

`refill_add_hwprobe_12004.cpp:312–328` 在每个实际debug CREATE_PROCESS/CREATE_THREAD事件上取得独占duplicate handle、核owner PID和GetThreadTimes creation FILETIME，再累计`g_total_owned_thread_generations`；达到N后拒绝下一次ownership。退出会销毁旧DR状态与handle，**不会减少累积额度**。READY必须在初始breakpoint时所有实际持有线程已arm。`--thread 0 --thread-policy carrier-owned-target --max-threads N`，生产CLI现有范围1..256，真实callback TID/creation在命中后才确定。

因此R218的64→65是实际debugger ownership事件拒绝，不能换算为“当时OS只有65条”。现在先对新PID/精确process FILETIME做三次完整OS线程metadata采样，按(TID,creation FILETIME)保留union/births/retirements，Root明确选择N及正的birth reserve，再做第四次身份/census核对。必须满足完整无错误、union+reserve≤N≤256。OS union是预算输入，不是debugger observed-generation；实际debug raw的thread_armed/retired、selected generation、terminal仍是唯一资格依据。未知结果不重arm、不重推进；超过256则在DR/day前停止，不能偷偷调大。

此次纯Python当前launcher合同7项检查PASS：N65和N256接受、N257拒绝、65个实际armed IDs在N65下接受但在N64下拒绝、重复TID和错误process FILETIME拒绝。见`PURE-CONTRACT-CHECK.actual.json`；它没有运行native或证明真实READY。

**构建边界：**a37→a39四个probe/carrier/ownership源文件相同，所以上调历史N64不要求改变producer。但当前93b的完整native tree fee866不同于a39的28dda。不得以这四文件相同冒充当前coherent native资格；Root已另行准备a40时，使用真实a40 source/flags/cold/SYSTEM/DLL/runtime回执，不把旧a37/a39资格移植过去。无需为线程预算另造第二场。

## 公共接线的最小改动（此次不实施）

1. `tools/ck3_mod_acceptance_cases/r10_prepare.json`明确增加可选`r06_refill_one_day`合同；保持默认六查询、零天的readiness行为。`r10_prepare_adapter.py`在validate/run/verify三个入口增加显式dispatch，禁止同时设置r04与r06，继续使用传入的同一个CaseClient。当前源码只识别r04，其他未识别键不会触发R06。
2. 新增一个`r06_refill_one_day.py`，对照本包`R06-ADAPTER-CONTRACT.UNIMPLEMENTED.json`严格验证：唯一S0、角色33388、Army0/native0、2170、raw53149056、普通null episode、单日上限、capacity/source pins、Root期限。复用现有`r04_county_entry.bound_saved_campaign_source`核真正公共CLI restore，复用`FullArmyResultClient`、`ObservationIO.exact_day`和modal策略；不要构造另一个CaseClient、SDK或host，也不从旧native-report读取历史队列当新场绑定。
3. 把既有外置`root_worker_month.py`的Probe/Operations边界移入该单一adapter，复用a02动态时钟保护：真实READY后仅一个原Arm/Resume，后续每次命令timeout受native30s余量约束；只有已成功paired、同PID/creation、DR清除/detach后，才允许observer退出后的readonly export。没有paired时不能继续Arm/Resume。Save以前必须独立验证实际restore/detach。
4. 完整`observed_history_full_v1`的prepare输入原有19.8MB样本超过2MiB。将已有a03“只对本次精确worker-prepare-inputs/army-packet.json允许32MiB”的reader/writer适配移入adapter，并以新Root cap授权；其他metadata、legacy Core4MiB、target proof64KiB、原full-parent line32MiB、raw128KiB上限不变。不要截断原full wire、不要改native tree去实现Python文件大小例外。
5. 用adapter内的`r06-before-observer-awaiting.json`暂停点收Root新census/owner admission与唯一camera Start；完成后返回共享entry，统一Save/正常退出。不要复用旧`worker_next.py`硬编码的a37资格、旧输出根128KiB计量、旧handoff/期限和manual-quit-awaiting条件；这些是准确来源范本，不是当前公共API。

最少focused验证：同client且未创建第二SDK；同raw日期/owner/scoped q门禁；READY拒绝时0day；一次Arm/Resume且未知不重投；唯一packet32MiB例外；paired后readonly与restore-before-Save；当前target消费者使用原parent range，不能用小摘要替代。无需重跑战争、再造月界准备或把整棵研究树变成镜头前置。

## 一场的执行顺序

1. Root完成上述公共接线及其focused验证，冻结最终source；取得真实coherent producer资格/runtime与source-bound scene cap。现有reserve仅准metadata，不代表native/game已经准入。只分配一个新run，使用唯一Mar31 source。新鲜Steam离线/屏幕独占、实际CK3版本和retained绑定由Root当场办理。
2. public正常cold load→MapReady→原六个readiness查询。原生fresh frame须仍Mar31、角色33388、Army0/native0在2170静止无战斗。校验实际saved_campaign_input/CLI restore/hash。恢复现场未知modal先采集再走既有合法native策略；不用UI查询等研究界面前置。
3. 在暂停状态采三次线程metadata、Root新N/reserve，再第四次核对；生成新的精确owner/source/cap admission，绑定当前DLL模块及carrier epoch20261018。此阶段不开30s observer。旧PID/TID/READY/相机signal全部无效。
4. 查询完整before，`ordered_refill_entry_mode=fixed_chunk0_prepare`，重新选择同帧q>0、position eligible且全部七槽/DATA别名完整的目标。历史Regi2602/slot1/ArRg82仅提示，不能固定为本场事实。下一个完整CDate64、calendar day0/month boundary均须真实ready。all OFF/clear后，仅ON regular_core，scope `regular_core_full_carmy_ids:[0]`，其余family全OFF；保存实际epoch/清零基线。
5. Root就绪后只Start一次录制并由实际fresh receipt放行。完成最后before/full/绑定检查后，prepare→唯一launch，native固定30,000ms，READY wait≤12s/observer总等待≤50s。真实READY且剩余>4s才进入一个原生exact day，目标raw53149080，单日wait≤20s且≤实际remaining−2s。所有准备/camera等待在observer启动前完成。
6. 真正exact日停后独立paused/date/actor/PID/generation核对，取得after完整query及原始full-wire-proof。等待原native actual paired/restore/detach；调用现有`consume_live_refill_add.py --raw ... --binding ... --create-target-core-proof ... --full-parent-proof ... --output ...`。producer在0x2A98B88/0x2A98B8B抓同一指令两侧252B物理七槽、真实stack q与同token carrier；消费者再从原response line重提同Core entry/return的完整目标七槽/DATA/manager alias，不能用before/after净差冒充。
7. pause/stop原sentinel（若仍armed）→observer实际restore→all OFF/clear实读→正常Save及独立after→Root正常GUI Quit→retainedOS0/native0/host0/public0/keeper退出/精确screen CAS空资源，最后settle容量。失败也沿同一闭场；不重放日步。唯一录制由Root正常Finish并消费成短插片。

成功也只先授真实目标instruction ADD及同natural Core join。现有target消费者明确`global_physical_closure_qualification_granted=false`、whole Core NET=false、full_window=false、toggle=false、业务资格false，不能直接把它标整卡GREEN。若没有命中或完整source缺失，则保留真实精确缺口，不延长新场。

## 固定容量/时间

同一Root总包3.375GiB只是reserve；scene候选2.25GiB（profile768MiB、driver1GiB、raw256MiB、other256MiB），native候选1GiB，所有线程metadata共128MiB。本包自己≤256KiB，D heavy/write均0。Root须分别取得source-bound执行subcap；本包没有授予执行。

硬界2026-10-20T08:00:00Z不自动续。MapReady还须≥2100秒，最晚07:25Z满足这条门禁；正常close转入最晚07:43Z，留900秒close+120秒cleanup。native固定30s与电影时长不同；无需把录像拖成旧191.9秒。旧save/producer仅按通用策略保护到这次接续用途复核，不无限续存。
