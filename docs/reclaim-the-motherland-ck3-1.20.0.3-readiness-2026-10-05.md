# 重整河山 0.4.1：CK3 1.20.0.3 维护准备

2026-10-05 状态：**PREPARED / RUNTIME NOT_RUN / NOT_PUBLISHED**。候选源码元数据为 `0.4.1` / CK3 `1.20.0.3`；当前公开版本仍为 `0.4.0`。本次只准备版本声明、公开文案、冻结更新说明和实际门槛界面输入，未启动 CK3、操作桌面、使用原生 Steam SDK 或上传。

产品：`mod_reclaim_the_motherland`。唯一发布目标：Workshop `3798404599`。上一公开 tag 为 `reclaim-motherland-v0.4.0`，commit 为 `23078f51d1b294b9db5dfc0a195051a48e3563a4`；候选 tag `reclaim-motherland-v0.4.1` 尚未创建。当前机器游戏为 CK3 `1.20.0.3` / build `25652598`，EXE SHA-256 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。

## 已审阅源码与旧证据

源码迁移仍为[2026-10-01 兼容专题](reclaim-the-motherland-ck3-1.20-compatibility-2026-10-01.md)记录的改动：新版提议附庸 modifier 布局与品级公式、私有后朝身份规则、三省六部预算 flag、群雄割据重组和改国号顺序，以及新版天命条件。`1.20.0.3` 的七份原版依赖与已审阅 `1.20.0.2` 完全同字节，比较记录在 `C:/workspace/ck3-upgrade-20261004/p2-rmtm-ccc-readiness-agent-01/source-12003-compare.json`，SHA-256 `657a2ce5060fca87e804dfcfa6b5239dd81cdf48b25ae805966b1d10930b6aa2`。

已通过的 `.2` 静态合同、解析和构建继续复用；本轮不重复旧业务 L0，不重新生成同字节文件，也不把它们写成 `.3` 实机 GREEN。生产机制与 GENERATED 文件没有修改。只有候选 descriptor 及相应静态版本合同从 `0.4.0` / `1.19.0.6` 改为 `0.4.1` / `1.20.0.3`。

## 核心链冷输入

原准备包入口：`C:/workspace/ck3-upgrade-20261004/p2-rmtm-ccc-readiness-agent-01/HANDOFF.md`。原 36 文件投影、14 文件原字节夹具及 `fixture-state/profile` 保留原样；原投影仍携带旧 descriptor，只代表当时输入，不能当作新 tag 的正式发布树。有效规则和初始观察计划在 `plans-02/rmtm/`，不要使用保留的错误 `inputs-01/rmtm/frontend-rules-plan.json`。

最短前台链：

1. 当次取得屏幕独占及新鲜 Steam 离线原图，启动一次新的隔离 profile。实际 Start 后在 D0 核实当前宋帝、天朝、霸权、独立及初始化标记。完整 87 个游戏规则必须以实际应用实例读回证明。
2. 逐个真实日推进，遇未知事件停止。原版 `tgp_dynastic_cycle.0081` 只有一个选项，但仍应先核对当次真实事件 definition、ROOT、instance、revision 和 shown/enabled 选项，不能按旧 ID 或固定屏幕坐标盲点。
3. 到 `RQA120: TEST READY ui_after_chaos` 停留，取空法理后朝、个人领地、忠臣封臣树、九席原任和预算控件。夹具决议【继续重整河山核心验收】描述显示两个当次真实附庸目标；分别取实际【提议附庸】的 `-50`、品级差大于一级时固定 `+10` 及其他原版理由。
4. 执行唯一夹具继续决议 `rqa120_continue_decision`，确认文本为【继续继承验收】，再自然推进到 core DONE。既有 36 marker 每个恰一次，FAIL 族为零，实际诊断须归因并保全。

该夹具先切换至继承人再杀前任，只能证明相应 title/realm 继承结果，不能算玩家原生死亡/Continue 窗口验收。定时值从生产 `1825` 日压缩为夹具 `14` 日，不能把实际压缩到期写作自然经历五年。该核心夹具在同一 effect 中连续建立 50% 和 51% 状态，因此相关 marker 不能单独证明两档实际生产决议界面。

## 独立 50% / 51% 生产决议界面 cell

额外冷输入：`C:/workspace/ck3-upgrade-20261005/rmtm-release-readiness-agent-01/threshold-ui-inputs-01/`。此输入将原夹具 14 个文件逐字保留，另加 4 个文件，总共 18 文件；profile 仍为 6 文件、只加载本产品和本夹具。原核心 profile 不修改。

新增脚本从旧夹具 threshold effect 的既有县领转移片段拆分出独立停点；不复制或调用生产复辟 effect，不改变 `rmtm_claim_restoration_decision`，不自动确认生产决议。两个新脚本单独 parser 为 `2/2`、零错误；未重扫旧产品或旧夹具。新 startup policy 已通过本轮冻结 source-04 的真实 `load_bound_fixture_start_policy`，只证明精确输入可接纳，不证明游戏结果。

实际前台步骤：

1. 同样实际 Start、自然到 Chaos，并停在 `ui_after_chaos`。
2. 选择夹具决议【验收：准备50%复辟对照】并确认。原核心驱动随之停止，实际控制状态为至少 50% 且不足原版 51%（伯爵领为离散数量，不保证比例恰好等于 0.5000）。查看真实生产【宣称复辟】的可见性、禁用状态和门槛失败理由，保存当次实际画面和 marker。
3. 选择夹具决议【验收：准备51%复辟达标】并确认。它只建立至少原版 51% 的状态，随后停留；重新查看同一个真实生产【宣称复辟】，保存实际可用性、门槛条件和原版【宣称天命】锁。
4. 主线程手动选择、确认真实生产【宣称复辟】。预算或复辟 Confirm 不能冒用白绮或 AUB 的 typed 窗口资格；鼠标兜底必须遵守原始截图、坐标映射和回执合同。
5. 选择夹具【验收：核对实际复辟结果】。该决议只读取已发生的结果，不授予头衔、不执行复辟、不推进时间。必须出现 `RQAUI: TEST PASS actual_production_restoration_effect_observed` 和 `RQAUI: TEST DONE threshold_ui`，并独立核实 `h_china` 持有者、生产 flag 与后朝销毁。该 cell 不代替核心继承、到期或预算取证。

当前状态始终为 **NOT_RUN**。计划、parser、输入 loader 或按钮 ACK 均不是业务成功。

## 本轮元数据验证与新候选投影

授权元数据修改后，专用 static validator 通过；只执行修改版本断言的单个 builder `test_manifest_identity`，通过 `1/1`，没有重跑旧业务合同测试。新的官方 builder 候选在 `C:/workspace/ck3-upgrade-20261005/rmtm-release-readiness-agent-01/production-0.4.1-candidate-01`，36 文件，严格 manifest 复核通过；相对旧 `.3` 准备投影仅 `descriptor.mod` 字节不同。

- 候选 manifest SHA-256：`8db6199d86d97eb64dd7f376d686a55973e5fc92304b60d18d2438c715a64ea0`。
- 候选 ZIP SHA-256：`ffa40557758efbcdb46b847224f48ad7ddebb6855f9f5109fd5892396100d07f`。
- 候选绑定 inspection revision `45c432f4090541ef8905bf9312f86750a95c0708` 及本轮已授权、尚未提交的元数据字节，`git_tag=null`；**不能当作正式 tag 构建**。
- 应优先使用已绑定这个新投影的 `core-0.4.1-state-01/` 与 `threshold-0.4.1-state-01/`，各 6 文件纯净 profile。前者复用原 14 文件 core 夹具，后者用 18 文件阈值 UI 变体；两个 policy 均通过冻结 source-04 的真实 load-bound 校验，均未启动。
- 本轮验证包：`.../metadata-verification-01/result.json`，含命令、退出码、stdio hashes、manifest、ZIP 与两个实际 profile。

Root 现有 `aub-core-12003-candidate-02/runtime_harness_observation240_continue_02.py` 的 policy 和 manual 两条分支都显式调用 `create_server(driver, profile_dir=args.state_dir / "profile")`，无需本产品另行修改 MCP 平台；若换用旧 harness，仍须检查实际源码，不能假定 manual 分支已绑定日志目录。

## 发布准备与剩余门禁

候选公开 description 不再沿用旧版验收声明；四张既有工坊图片明确标为 `0.4.0` / CK3 `1.19.0.6` 历史实机。完整中英更新说明为 [0.4.1.txt](../workshop/change_notes/reclaim-the-motherland/0.4.1.txt)，冻结量和 hash 在同目录 `0.4.1.freeze.json`。相对上一公开版的[永久 changelog 草稿](release-changelogs/reclaim-motherland/0.4.1.md)保持 DRAFT / NOT_PUBLISHED。

完成所需：新版核心与上述实际界面验收、原版规则对照及必要存档/命名回归；本轮最终 tag 的 36 文件正式构建；同一工坊 item 上传；匿名精确回读完整 Change Notes；实际新缓存逐文件复核及本产品要求的 fresh-cache 验收；上传后重建无 ID staging；立即恢复 Steam 离线并保存当次原图；最终 changelog 与发布证据提交并推送 `master`。任何一项缺失都不能标为 release-complete。

## 2026-10-06 R0001 实际失败、正常退出与下一候选边界

本节只追加本机事实；上文 NOT_RUN、旧输入和失败原件按原时点保留。R0001 `4-8e1c2f1861--reclaim-the-motherland--R0001` 使用新a66、Source05及 `9ea8747e50bdf8fbca23838c1061c9ae86053d4d059fe4e6a087df1f9acbb459` harness，于UTC `2026-10-05T18:23:12.956974+00:00` 实际启动，CK3 PID20392/generation1。资格状态为 **FAILED_AFTER_SINGLE_START_NO_RETRY**，没有重发Start，没有核心业务、自然日或生产UI验收信用；当前公开版本仍为0.4.0，0.4.1未发布。

首个 `ck3_query_campaign_root_context_v1` 于18:26:46.963354提交，30秒后实际返回 `timeout_cancelled_before_execution`，`executor_enter=null`，typed result/final read/frame stability均未取得。提交前原生 `native:2/revision2`（MCP revision3）实际map_ready=true、paused=true、actor31254、raw53144328、active_event=null、owner pump ready；宋帝资格两项 `exact_build_song_emperor` / `switched_to_song_emperor` 各0。owner ready和event空不等于夹具资格；此回执没有执行held-title读取，不能归因于QOL的 `county_capital_id_nonpositive`，也没有证据唯一归因于事件或frame改变。[首次准入薄证据](C:/workspace/ck3-upgrade-20261006/rmtm-r0001-failed-hold-lifecycle-agent-01/before-first-root-admission-thin-receipt.json)10259B、SHA `4942ed8248c0122921c8294fadda5caeb5e30c765826e77aee90beb6247da4f0`；[查询原始失败及分层边界](C:/workspace/ck3-upgrade-20261006/rmtm-r0001-failed-hold-lifecycle-agent-01/rootquery-and-lifecycle-thin-receipt.json)2192B、SHA `30250895342032f7ed9bf02badd3d6ac615a0b0b3a3c5fd3e1d2c5cb91b53b62`。

失败后原生状态曾显示宋帝34422和一选项intro。Root依据[原图坐标映射](C:/workspace/ck3-upgrade-20261006/rmtm-core-r1-context-failure-original-root-01/intro-confirm-once.mapping.json)只确认一次，之后原生帧event=null；这不恢复原资格。随后pure diagnostic通用queue因原 `error` 非空被守卫拒绝、未dispatch，不记录为第二次root查询或业务执行。

Root真实正常Quit Desktop一次；native于 `2026-10-05T18:33:55.704776+00:00` 以process_exit/process_exit_code0结束，shutdown.ck3_exit_code0、job0、tree_gone/cleanup_proven=true、全部进程库存[]、watchdog absent、control文件全部absent。随后[Lifecycle02唯一收口](C:/workspace/ck3-upgrade-20261006/rmtm-r0001-failed-hold-lifecycle-agent-01/actual-root-lifecycle-dispatch-receipt.json)在18:38:36只提交finish_hold、不发game action；原root error仍在，9ea退出后N/A不接纳已有失败，step及final observation的 `ck3_take_snapshot` 错误保留。完整runner **RED** 于18:38:37.718127结束，managed_session_thread_finished/cleanup_ok=true；不能用正常退出或清理成功改写为业务通过。[最终闭合薄回执](C:/workspace/ck3-upgrade-20261006/rmtm-r0001-failed-hold-lifecycle-agent-01/actual-final-closed-thin-receipt.json)2972B、SHA `5dad6d1697c6ce668fe2d6d22d03c07eccbb2857472381e690b6d5ee75f9a97f`。观察器已实际退出，harness15844/game20392/watchdog2952均gone；keeper末序3667后，[a66实际CAS释放](C:/workspace/ck3-upgrade-20261006/rmtm-core-r1-context-failure-original-root-01/actual-a66-screen-release-02.json)3668/done/resources[]，UTC18:41:36.692936（本机2026-10-06 02:41:36），3205B、SHA `cb203b2716b58745be76b8db26eadc767baacc9a1ff37f30adcad667b18d8e91`。

未来host guard候选 [runtime_harness_fixture_prequery_readiness_01.py](C:/workspace/ck3-upgrade-20261006/rmtm-fixture-prequery-readiness-agent-01/runtime_harness_fixture_prequery_readiness_01.py)113023B、SHA `81a1a36dba7845543dfc9c7131d611879aa40078e92154aa6fbce35787aa81d8`，只在首full query前等固定policy资格标记各1/FAIL0/无重复，以及两个暂停无event、同actor/PID/generation/date/native frame、owner pump递增的观察。原full DTO、exact binder、两次business pump、Start once、400秒deadline及UNKNOWN不重试保持；[16项离线边界回执](C:/workspace/ck3-upgrade-20261006/rmtm-fixture-prequery-readiness-agent-01/pure-boundary-receipt-02.json)3207B、SHA `79eb0ff207db1a9700b1710a01814088d2111723df142ba8d34fbc5358776b54` 仅为 **SOURCE/PURE PASS**，原mock缺字段失败保留。新 [operation06 freeze](C:/workspace/ck3-upgrade-20261005/rmtm-operation-card-agent-01/readyfreeze-operation06.json)15370B、SHA `ced5ba341cfe3f8003d6f8f10bd249951059fbfadd619e7ab3a5c18cab946150` 为READY/NOT_ALLOCATED/NOT_RUN，仍用同Source05/DLL70；没有采用新的原生resolver，没有实机修复或发布信用。

## 2026-10-06 R0002：真实初始化夹具失败与前台交还

R0002 `4-8e1c2f1861--reclaim-the-motherland--R0002` 实际使用 Source09/build11 DLL、HOST81及 operation08；operation08 仅把已维护变更的共享兼容规范文档移出执行输入逐文件验证，保留其原始精确 pin 和当前文档来源，operation07 及全部生产36、冷输入、规则、夹具14/18、门禁保持。a70 于03:05分配，实际 CK3 PID1852/generation1。唯一 Start 后03:10:03.641608Z 资格状态成为 **FAILED_AFTER_SINGLE_START_NO_RETRY**：两原宋资格日志各1，但 `RQA: TEST FAIL fixture_vassal_tree_prepared` 恰1。HOST81 按原 forbidden 门禁停止，首次完整根查询准入未成立，实际 native root-query 请求为0；没有业务日数、核心 UI、继承链或 threshold 验收信用，0.4.1仍未发布。后续宋玩家34422、D0日期53144328、intro实例1及正常地图不能改写失败资格。

本场完整新增 [error.log 原字节](C:/workspace/ck3-upgrade-20261006/rmtm-core-r2-front-agent-01/actual-new-error-log-complete-01.raw.log)15280B、SHA `d145163a81281bf4bc8c6994c8e4234acdead147c16b314b9d84dfe855ce0752`，在11:10:02明确报原夹具 `rqa_effects.txt:223` 的 `top_participant_group:dynastic_cycle` 返回 unset scope / Failed context switch，随后原合取 guard 的230行记录FAIL。该guard还验六个目标scope与九席任官，旧日志未独立记录其他atom及随机目标/部长的实际ID，不能据聚合FAIL认定封臣转移API失败或其余条件全成功。[窄归因回执](C:/workspace/ck3-upgrade-20261006/rmtm-r2-fixture-narrow-cause-review-agent-01/review-01.json)19036B、SHA `88a9c214708986637b8eb4806c62d57f58cd70afcef19fec9cc524c632b21c60` 保持 deeper-cause unresolved；未来只读atom日志准备不能当作已实机修复。

实际执行者 `/root/reclaim_motherland` 亲审新离线原图及nonce `44f0dfd52394`。共享旧helper硬编码的 reviewer 文本保留原件，另追加 [实际审阅人更正](C:/workspace/ck3-upgrade-20261006/rmtm-core-r2-front-agent-01/actual-operator-attribution-correction-01.json)1806B、SHA `f474a079c98b2cf9c01f3b7686366ce6b72b5d8cecdd45c19517c07a48362462`；Root没有直接审阅该次新图。执行者在失败后只为关闭而依据新原图确认intro并正常选择【退出到桌面】，没有重发Start、根查询或业务控制。唯一 native session 于03:17:54.961931Z process_exit0，shutdown.ck3_exit_code0、job0、tree_gone/cleanup_proven=true、全部库存空、原watchdog absent。lifecycle-only finish保留原错误，runner于03:19:51.117697Z **RED** 结束，managed_session_thread_finished/cleanup_ok=true；错误场死快照仍失败，不取得post-exit N/A信用。

[实际最终闭合薄包](C:/workspace/ck3-upgrade-20261006/rmtm-core-r2-front-agent-01/actual-final-closed-thin-01.json)4279B、SHA `4e09618f0225efac4029d00616dbe511bb366060b4540406b94b93c5efa4eafa` 与 [观察器退出证明](C:/workspace/ck3-upgrade-20261006/rmtm-core-r2-readonly-observer-agent-01/actual-final-observer-exit-proof-01.json)保存全部分层事实。game1852/harness11920和两个observer19140/21092及读子进程均已退出；原watchdog22028身份已native证明absent，随后同数字PID为新WmiPrvSE进程，不能按PID数字误杀。keeper session11520实际exit0/thread_exited=true、末序3934；[a70唯一实际CAS原stdout](C:/workspace/ck3-upgrade-20261006/rmtm-core-r2-front-agent-01/actual-a70-screen-release-01.json)于03:25:06.384636Z释放为3935/done/resources[]，前台交还Root。本轮未启动threshold，原失败及全部资产继续保留。


## 2026-10-06：空部院授权变量的独立生产修复（源码验证，尚无实机信用）

R0002 原始 error.log 已证明 `zz_rmtm_ministry_override.txt` 原第 13–15 行在 tooltip 计算中读取未设置的 `global_var:rmtm_ministry_entitlement_title`；同一 `AND` 内的 `exists` 未阻止该次后续访问。现只修改权威生成器 `tools/gen_reclaim_native_overrides.py`：保留原 `AND` 与外层 `exists`，将 `primary_title` 比较及该全局 title scope 内的标记检查包入 `trigger_if`，其 `limit` 再确认变量存在。原 `h_china` 持有者门禁、唯一后朝头衔及标记、天朝政体和部院预算两项 flag 均保留；缺变量时仍由外层 `exists` 保持拒绝，不能因未执行条件分支而放行。

已通过真实生成器重生 `common/scripted_triggers/zz_rmtm_ministry_override.txt`（1018 B，SHA-256 `6af4f52c0e4f41b4f66a0c2896b0bd8386aa07e897648f16b9d03746b3798130`）。另外两个 native projection 输出逐字节未变，三份反向 native contract 检查通过。当前原版 `common/decisions/dlc_decisions/03_fp2_decisions.txt` 第 790–797 行提供同类 tooltip `trigger_if(limit exists global_var)` 后访问该变量的语法例。

使用同一绝对 venv 实际执行 `-B -X utf8 -m unittest -v test_reclaim_ministry_scope_guard`，3 项定向源码测试 exit 0 / OK：缺授权变量时拒绝且不解引用、128 个原权限布尔组合保持原许可真值、旧 eager tooltip 形状重现 undefined 比较反例。这是源码 parser/有限控制流模型证据，不是 CK3 engine 实机修复证明。证据：`C:/workspace/ck3-upgrade-20261006/rmtm-participant-probes-ministry-guard-operation09-agent-01/generation-targeted-receipt-01.json` 与 `targeted-tests-actual-receipt-01.json`。

本修复与宋帝 `top_participant_group:dynastic_cycle` unset 的初始化因果仍为 **UNKNOWN**。原 R0002 qualifier FAILED / runner RED / 正常 OS-native 0 / CAS 3935 保持历史原样；0.4.1 仍 NOT_PUBLISHED。外置 operation09 仅准备三阶段同宋只读关系探针与更新后的 36 文件 staging，尚未分配或运行；不手工添加参与者、不等待猜 PASS、不改原 aggregate guard、FAIL 或业务/UI 门禁。Source09、Host81 和原正常退出闭包保持冻结，不把并入新 master 写成运行输入重建或新实机通过。
