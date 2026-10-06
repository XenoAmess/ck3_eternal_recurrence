# XQOL 1.20.0.3 防御资格修复与待实机输入

日期：2026-10-05。产品：XenoAmess的体验优化，Workshop item `3798133925`。本记录属于准备与修复事实，不是实机或发布通过。

源码只修改 `mod_xenoamess_quality_of_life/common/scripted_triggers/xqol_triggers.txt` 的一个反向朝贡分支，将 `tributary_contract_suzerain_guarantee_override` 改为 `tributary_contract_tributary_forced_war_override`。文件没有 GENERATED FILE 标记；没有手改生成产物。向上请求宗主保证、盟约、领主、摄政、家系和战争有效性逻辑未改。修改后 trigger 为 5301 字节，SHA-256 `b98094da6faeb2d027821f56f9c10de986e0cb119c12789a19fac9e7245265e5`。

原因是实际原版合同方向：宗主保证援助朝贡者，不表示朝贡者免费援助宗主。原逻辑会把仅有保证、没有强制参战义务且没有盟约的朝贡者直接拉进防御战争。真实 Steam .3 的防御 helper 只执行免资源加入，没有实际扣虔诚的证据；此修复针对错误资格。向下强制合同可能已由原版自动把角色加入战争，目标是否已参与或已被召仍由既有过滤器重查，避免重复。

真实原版取证来自 `C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game`。EXE 为 101039736 字节，SHA-256 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。相关来源及行号冻结在 `C:/workspace/ck3-upgrade-20261005/xqol-agent-01/defense-audit/HANDOFF.md`，原字节在其 `frozen-stock/`：

- `00_alliance.txt` 32–67：普通向下朝贡召集需法规与至少 50 虔诚；向上保证是另一分支。
- `special_contracts.txt` 804–829：宗主援助朝贡者的保证，level 1 对应 suzerain guarantee flag。
- 同文件 857–911：朝贡者强制参战义务，level 1 对应 tributary forced flag。
- `00_interaction_effects.txt` 3192–3318：先 `set_called_to`，防御分支直接 `add_defender`。

19 项原版依赖中，17 项与冻结 .2 合同 raw SHA 相同，2 项不同。防御直接依赖的 alliance、interaction effect、war on_action 相同；`pam_effects.txt` 和 `00_religious_triggers.txt` 的漂移仍需按功能边界审核，不能称全产品语义无变更。宗教审阅另确认 head_of_rite 的 -120 属于接受度修正，`ai_will_not_convert` 同时有硬门禁；百万分处罚源码存在，但旧实际行政候选窗口未展示玩家那一行，尚不能充 penalty tooltip 实机通过。

外置冷候选 `C:/workspace/ck3-upgrade-20261005/xqol-agent-01/defense-candidate-01/` 已实际创建。现有正式 builder 生成 27 文件 staging；相对 C04 staging 只有上述 trigger 和候选 descriptor 有差异。候选 descriptor 在外置 source 设置 `1.1.1` / `1.20.0.3`，仓库 canonical descriptor 尚未据此宣称发布。

- manifest SHA-256：`bf70d5975171f1804f92968336f6e01dbffdf066d047a96255ce40f79fa774e2`。
- deterministic ZIP SHA-256：`6827d7d5efd76ff9d45ad8609abca8f66f034cd4a071c799b41dcb895cc36e39`。
- 冷 profile preparation SHA-256：`5e3c2ea44fb8e4175b0b4f67367ebc6c91bc158ef6ee9e447c348c5286f82652`。
- 输入 freeze SHA-256：`64b48956e8ba993984ebeeb0293332b4a345db0b56238ed3c77f30cee232303d`。

只对改变的 trigger 与 startup scheduler 执行无版本 semantic profile 的 parser：2/2、零 diagnostics；未重复同字节旧 L0、原矩阵 parser 或整套游戏测试。cold profile 含 39 文件，只加载 product 与 fixture，logs、save games、run 为空；现有 closed fixture Start policy 对完整 mounted/config 字节执行 load_bound 检查通过。

防御原初始化 D1 hidden switch 已在这份新入口显式调整为 D0，以满足现有 policy 的实际首日宋帝/current actor 检查；初始 effect、原矩阵、开战/生产 callback/observer/replay 的相对战争时序均原样保留。首次召援仍只来自生产 on_war_started；后续 replay 只能在真实 war_days>=2、原始 count>=0 条件成立后发生。旧 operator 011 的 .2 EXE、d19 与旧 profile 锁未改，不能直接执行其 live mode。

原 regular/overlap/paid 矩阵仅提供 14 个 required marker 的待执行输入。新增反向朝贡正/负例、其他复杂关系、宗教负门禁和玩家 penalty tooltip 仍需独立真实证据。实际启动、当次 Steam 离线画面、日期推进、角色/战争身份、完整日志归因、managed cleanup、Workshop 上传、Change Notes 匿名 exact 回读、fresh-cache 核验及永久 release changelog 均尚未由本记录证明。

## 同日新增可执行输入，均 NOT_RUN

最终防御组合场为 `xqol-agent-01/defense-audit/reverse-composite-02/state`：原 14 个标记加反向朝贡合同 8 个标记，共 22 个必需标记。普通 settled 负例使用真实 guarantee=1 / forced=0，正例使用 guarantee=1 / forced=1；保留原版 forced 合同的 guarantee 前提，不以人物同名 flag 伪造合同。新增 observer 等待真实 war_days>=2、原矩阵完成且无失败、原 replay 计数为 0 后，检查负例未被错误召集、正例实际参与且重复 guard 拒绝。正例容许原版提前加入，不强求产品调用数为 1。原矩阵文件与开战/生产 callback 时序保全，新增 initializer 和两个脚本 parser3/3、零错误；policy load_bound 与所有输入 SHA 已复核。最终 freeze 为 20604 字节，SHA-256 `765bc6c8c9ec67e2fb83574d71b66d66338265a516ec83efad6058eb7fb158a5`。

主宗教补测场为 `xqol-agent-01/religion-audit/candidate-02/religion-gate/state`：在 D0 创建两名无地产 Catholic/Roman 囚犯，仅一个携带 ai_will_not_convert；检查实际 production trigger、四个含改信的 interaction validity、非改信 HR、移除和重加 flag。15 个必需标记，不执行付款、释放、改信或招募，不给接受分和 GUI 后果信用。独立 Roman 领袖诊断场从 `rite:roman_rite.head_of_rite` 取得真实人物，有 8 个标记，不囚禁、造盟或改宗该人；其 -120 处罚 tooltip 仍需真实 UI 另验。每场39文件、parser4/4零错误、policy/hash/outer path/空运行目录检查均完成；总输入索引 SHA-256 `1f5fcdad2fed1265b4ca3dd596e0b47160976a2bde938a5c1efd3fcd88b18943`。标记中的 D0 文字不能代替原生日历证明。

付款原夹具与5步计划已逐字复制至 `xqol-agent-01/payment-candidate-02`，仅重绑为同一修复后1.1.1/.3 production，未重跑 builder/parser/旧L0。其41文件 profile 与 policy load_bound 通过；输入 freeze SHA-256 `7f57ab12e583f4ae894efe5300caedee48edacbe8aad99a4935bff543de3679b`。新防御白名单不在该付款场调用路径内，付款验证仍是独立有界范围。

根入口统一见 `xqol-agent-01/HANDOFF-02.md`。上述准备没有实施向上宗主保证、摄政复杂关系、.3 行政与贤能完整任命、全部 slider、真实处罚 tooltip、存档保存/载入或发布。1.20.0.2 的行政17标记与六次实际开关仍为其原版本独立证据，不能因当前函数 SHA 相同改写成 .3 实机通过。

### 同日防御负例隔离加强

最终实际待执行入口改为 `xqol-agent-01/defense-audit/reverse-composite-03/state`，02所有历史输入保留。反向负例初始 `xqol_free_call_target_valid_trigger` 从观察值提升为必需 PASS；invalid 时明确 FAIL 并增加失败计数，避免“未参战”由无关战争资格挡住所造成的含混结果。总 required 为23（原14＋新增9）。仅改变一个外置 reverse effect 脚本，parser1/1、零错误；旧3文件 corpus 未重复，生产27文件与触发器修复字节不变。03全部输入 SHA/policy/outer path/空运行目录复核完成，freeze19926字节、SHA-256 `07602501a95e8bb4dfadb3db2a63a19ca5fff33f83fb488964db7ad5c79008ff`。统一最新入口为 `xqol-agent-01/HANDOFF-03.md`；仍NOT_RUN，没有给02或03实机信用。

### 同日 canonical 候选元数据与发布草稿

Root 授权后，canonical descriptor 已设 version=1.1.1 / supported_version=1.20.0.3，专用静态 descriptor token、README 和 Workshop 描述同步为维护候选。仅执行一次必要 metadata/asset/exact allowlist 检查，27个 canonical runtime 文件逐字节等于已冻结的外置候选；此步只有 descriptor 改变，没有 script/localization/image 漂移。没有刷新历史 .2 原版 SHA 合同，不能把该检查写作全 L0、.3 实机或发布通过。回执为 `xqol-agent-01/metadata-and-notes-validation-04.json`。

完整中英更新说明已保存 `workshop/change_notes/xenoamess-quality-of-life/1.1.1.txt` 与相邻 `1.1.1.freeze.json`，DRAFT_NOT_PUBLISHED：3991字符、33行、5469字节、LF无尾换行，SHA-256 `0cbb91ea9210dca8bdd866e1e36b76e4ea1705f58b4fdb624e7b86513601b2d6`。包含已证实的合同方向修复，没有提交或公开entry/fulltext回读事实。永久候选 changelog 位于 `docs/release-changelogs/xqol/1.1.1.md`，明确 DRAFT / NOT_PUBLISHED / .3 actual pending；正式tag/commit/发布日期、上传、缓存与最终master push均pending。所有旧历史changelog保持原样。

玩家处罚tooltip的只读源证据已完成：现有native MCP没有任命列表/tooltip语义查询或hover；宋帝持h_china霸权级，不能保证进入帝级e_minister_grand_marshal候选池。该原版部长及行政de jure近亲官职仅为合法GUI探查路线，未造强制入池夹具或改原版过滤器，实际百万分tooltip Gap继续保留。最新根交接为 `xqol-agent-01/HANDOFF-04.md`。

### 同日 R10 实际闭合：scope 资格超时，source05 诊断尚未进入

防御新冷场 `4-8e1c2f1861--xenoamess-quality-of-life--R0010` 于 07:08:12Z 开始，使用冻结 source05、held-title trace DLL `d814150496cfa031e898f39fa18417298ff4833a8bb3ea344dabd2598181a49d` 和当前 .3 EXE `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。实际 CK3 PID13004 / creation time1791184100.3526156，输入为 `reverse-selector-diagnostic-10/state`；这些是本场身份，不借用 R9 或其他旧场的宋帝/episode。

原资格最终仍为 RED：`TimeoutError: actual QOL scope actor did not crossbind and stabilize before deadline`。Root 后来实际关闭本场原版 dynasty intro once，原图、独立两轴 mapping 和 settled 原图保全；释放摘要明确资格超时先于 intro clearance。迟到关闭未补授原资格成功、immutable binding 或业务信用。最终 `steps=[]`，原 initial2、D0 pool/sample readback 和 held-root query 均未执行；完整 native wire9332行中 `query-campaign-root-context-v1` step帧、完成结果及 source05 `campaign-root-held-title-partition-failure-v1` 诊断帧均为0。此场不能证明实际 held-title 分支已定位/修复，也不能把防御23＋3、自然D1或完整QOL验收写为通过。Root 关闭后仍保留原 timeout，没有复放 Start 或把 RED 改 GREEN。

07:46:46.979862Z实际闭合：managed thread finished、cleanup_ok均true；shutdown tree_gone/cleanup_proven true、job final0、tasklist/WMI/native进程库存均空。keeper a55在3189后thread退出，07:49:47.162245Z CAS3190将任务置done/resources[]。最终 native报告128888457B，SHA-256 `0c8c15437ab1d710cf4c3cf2e1497ccf9fcabb0ca6769b2b965101c3e65110bf`；没有复制巨大报告或改写旧失败原件。

本场还暴露报告序列化开销：07:36:28Z稳定流式样本128855415B中187份同307676B BEGIN–END scope块，hex合计115070824B；资格循环每轮append完整proof后全量重写报告。未来外置候选仅把重复原块按SHA保全为immutable binary artifact，原请求/诊断/帧/绑定每条仍完整append，原query、eventnull、两个fresh pump与Start once合同保持；13项纯/source预检通过，预计单次重写少约114.96MB/89.2%，尚非运行性能实测。独审由另一线程承担；只有独审通过并绑定最终SHA后，才能在新冷输入中重绑defense adapter的BASE_PATH/BASE_SHA、输入pins和显式artifact reader，当前场与原04/source05/DLL不热换。原QOL待验与发布边界保持。

证据：[实际closed原回读](C:/workspace/ck3-upgrade-20261005/xqol-r10-root-partial-closeout-01/actual-final-readback-01.json)、[CAS3190原回执](C:/workspace/ck3-upgrade-20261005/xqol-r10-root-partial-closeout-01/screen-release-01.json)、[complete native wire与报告SHA薄核](C:/workspace/ck3-upgrade-20261005/xqol-r10-closed-doc-append-agent-01/actual-r10-closed-small-boundary-01.json)、[身份/source/keeper原收据](C:/workspace/ck3-upgrade-20261005/xqol-r10-closed-doc-append-agent-01/actual-r10-runtime-source-and-keeper-thin-02.json)、[Root intro 原图](C:/workspace/ck3-upgrade-20261005/xqol-r10-native-confirm-observed-dynasty-intro-once-01.png)/[mapping](C:/workspace/ck3-upgrade-20261005/xqol-r10-native-confirm-observed-dynasty-intro-once-01.mapping.json)/[settled](C:/workspace/ck3-upgrade-20261005/xqol-r10-native-confirm-observed-dynasty-intro-once-01-settled.png)、[未来候选 source/pure 包](C:/workspace/ck3-upgrade-20261005/qol-r10-report-rawblock-dedup-agent-01/FINAL-FUTURE-CANDIDATE-PACKET-05.json)、[未来输入接入DRAFT](C:/workspace/ck3-upgrade-20261005/xqol-r10-closed-doc-append-agent-01/future-input-intake-DRAFT-03.json)。

## 2026-10-06 R12 实际归档：原防御14项通过，反向正例联合检查仍失败

本节只追加本机 R12 的真实结果，R10/R11 及旧候选保持原记录。场次为 `4-8e1c2f1861--xenoamess-quality-of-life--R0012`，actor34422 / PID21744 / generation1；D0 raw53144328，D1 raw53144352，D5 raw53144448，共五个实际单日、120小时。实际两阶段进度见 [D1 progress](C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0012/defense-first-day-root-01/progress.json)（140795B，SHA `76d79100401221c054edc9984b2c853d812c7e6e5ef40ac1e106435591be727a`）和 [D2–D5 progress](C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0012/defense-after-d1-root-01/progress.json)（294492B，SHA `a8f0f85ee10d763af67d8a10c2aba57243bc6118b0726e22383ad72893b746e4`）。D1 的进度状态为 BOUNDED_DAY_LIMIT_INCOMPLETE；后续状态为 FIXTURE_FAIL_OR_DUPLICATE，不能改成整场通过。

D1 正例38528已有 `reverse_positive_native_prejoined` 实际观察：debug第28721行、byte2646931，源 `zqarel_reverse_effects.txt` 第143–144行只证明同一 target 战争已包含该 recipient，未区分阵营或证明由原版／mod哪个入口加入；不能写成“正例从未参战”。当日 strict_self、结义前提、解除盟约后的真实 forced flag 与非同盟检查均已有日志。到D5，原 regular/overlap/paid 防御14个必需标记各一次、对应FAIL为0；新增反向检查为5个PASS、`reverse_positive_participating` 与 `reverse_matrix_done` 两个FAIL，合计19/23必需标记，新增场没有完整通过。

D5第40566行的 `reverse_positive_participating` FAIL是四项合取失败：正例仍是root朝贡者、真实forced flag、战争primary_defender=root、正例仍为战争参与者。前一第40565行的负例 `reverse_negative_not_auto_called` PASS已在同War4/root34422覆盖primary_defender=root，且其后未改target；正例的 `is_tributary_of`、forced flag、`is_participant` 三个原子在D5仍未知。联合失败不等于最后一个参与者原子为假，也不能直接归因生产召援BUG。角色/root/recipient和War4的实际scope及原断言见 [现存日志失败观察](C:/workspace/ck3-upgrade-20261006/xqol-r12-positive-participation-failure-diagnostic-agent-01/current-log-failure-observation-01.json) 与 [源码及实际scope归属](C:/workspace/ck3-upgrade-20261006/xqol-r12-positive-participation-failure-diagnostic-agent-01/source-and-actual-scope-attribution-02.json)；两份原回执的非EOF边界保留。

实际游戏进程于 `2026-10-05T18:12:55.118117Z` 正常process_exit，process_exit_code=0且shutdown.ck3_exit_code=0；tree_gone/cleanup_proven=true、job0、全部进程库存为空、watchdog与原control文件均已消失。原95ff runner在退出后的partial finish自动调用 `ck3_take_snapshot` 仍报错，最终 `2026-10-05T18:13:44.252876Z` 为RED、cleanup/thread=true，保留原错误，不把正常退出0改写为runner GREEN或业务通过。只读observer实际exit0，回执检查PID12664、17868、21744、21172均gone，原运行计划保留。见 [实际闭合与观察器退出](C:/workspace/ck3-upgrade-20261006/xqol-r12-thin-report-observer-agent-01/actual-closed-cleanup-and-observer-exit-01.json)（4093B，SHA `92eecbec35e500ec822112d9639fe4497fde867cbdd1b6cc86b2e410d20b914b`）。

Root唯一a65释放调用的真实回执为CAS3647、done/resources=[]，UTC `2026-10-05T18:18:17.115078Z`（本机2026-10-06 02:18:17），见 [实际screen release](C:/workspace/ck3-upgrade-20261006/xqol-r12-close-current-original-root-01/actual-a65-screen-release-01.json)。本场不证明后续诊断修复、下一冷输入通过或产品正式发布；体验优化候选1.1.1仍未发布。

## 2026-10-06 R13/a67 当前实际资格失败

R13使用本轮Source08 diagnostic DLL `b1fe516b8168eca65a260882d560e25e9df22a030e2de626bcd554b310c7e017`，生产27文件与原threshold不变。首map为UTC19:11:11、宋帝34422为19:11:56；intro直到Root约19:16实际关闭（19:17:02原生观察event已空）。资格先在 `2026-10-05T19:15:55.626788Z` 失败：`TimeoutError: actual QOL scope actor did not crossbind and stabilize before deadline`。当前binding缺失、rows0；whole-query、新type_tag及D1/D5均未执行，没有业务或诊断结果信用，不能把本场认作已触发首府对象分类。见[实际薄报告004](C:/workspace/ck3-upgrade-20261006/xqol-r13-thin-report-observer-agent-01/report-state-004.json)1299B、SHA `5db0760363a03de929282ede6227727e10a8e9cd97cfff96a9830ab5bc92cb2d`。

Root真实WM_CLOSE、关闭autosave后Quit Desktop；[本场session log](C:/workspace/ck3-upgrade-20261004/live/4-8e1c2f1861--xenoamess-quality-of-life--R0013/native-report.session.log)最后native于 `2026-10-05T19:18:59.930959Z` process_exit：OS0/shutdown0、job0、tree_gone/cleanup_proven=true、库存全部[]，watchdog22492 absent。正常退出不清除原runner资格错误。本次追加时a67屏幕释放仍待Root真实回执，未写CAS完成；未来R14只使用新冷场与原门禁，400秒期限不延长，尚无实际修复或发布信用。旧R12及此前失败原件不改。

补充分层：intro关闭后检查的现存日志已含scope三标记各1/FAIL0和宋34422/`han_8052` scopeproof，不能写成scope不存在；资格截止时没有完成crossbind，binding仍null、initial rows0。已保存完整nativewire的独立扫描确认campaign root query/result/trace各0，非仅从rows0推断；该次日志与wire均为非EOF边界，见[实际非EOF失败回执](C:/workspace/ck3-upgrade-20261006/xqol-r13-thin-report-observer-agent-01/FAILURE_NON_EOF_01.json)9028B、SHA `26e96e157ea557daed8c4428f8d7eaad4d320e8fff539915e90a181a2600d3ab`。

**R13后续真实闭合（2026-10-06）：** 上述待释放为写入当时状态；runner实际于UTC19:24:40.359928以RED结束，原Timeout不变，cleanup_ok/thread_finished=true，仅finish_hold的ok=false及死后snapshot错误保留。thin/raw/harness均已实际不存在，thin observer PID3672/session62510退出0；[最终闭合薄回执](C:/workspace/ck3-upgrade-20261006/xqol-r13-thin-report-observer-agent-01/ACTUAL_NATIVE_HARNESS_OBSERVER_CLOSEOUT_02.json)3144B、SHA `82501663bc080c3861a59b2d1dcc6092721fc51771af1b971adce14c44db08bc`。keeper/session3837实际退出0、末序3688/thread=true后，Root唯一[CAS释放回执](C:/workspace/ck3-upgrade-20261006/xqol-cold13-close-current-original-root-01/actual-a67-screen-release-01.json)证明3689/done/resources[]，UTC19:25:31.764299（本机03:25:31）。正常OS0不改变本场资格或业务失败；R14已单次启动harness19988，只有启动事实，无诊断结果信用。

## 2026-10-06 R14/a68 实际首府trace与限定收口

R14资格于UTC19:34:40.278299完成，initial2+diag4共6rows全部finished/OK，只覆盖D0观察。Source08实际trace request `step-112-3221d07e7ddb`、PID20452/gen1/revision4/query_sequence1/raw53144328：title16850、held index4、held_count/capacity9/9、capital0；getter completed/nonnull=true，type-tag读取成功为 `0x4E756C6C`（Null）、stock no-province=true，whole-root仍unavailable。见[本场原生trace非EOF证据](C:/workspace/ck3-upgrade-20261006/xqol-r14-actual-native-root-trace-attribution-agent-01/ACTUAL_R14_INITIAL_ROOT_TRACE_NON_EOF_01.json)40905B、SHA `1e197f21a9d26ec18550e78ec19600551d16e496928170d83b76a0b0ecdbd189`；本场不等于首府读取已修复。

原hold于UTC20:04:45.968318自动结束，harness GREEN/error=null、cleanup/thread=true；native为stop、process_exit_code=null、shutdown.ck3_exit_code=1，绝非正常OS0或product PASS。Root于22:17:36实际D0 review后，控制器在任何新control前拒绝 `No active clean hold`；D1/D5未执行，旧review不能供新场复用。raw14784/session95401及thin14916/session2996均exit0，game/harness/watchers均gone；keeper67136 exit0/末序3864/thread=true后，Root唯一[a68实际CAS释放](C:/workspace/ck3-upgrade-20261006/xqol-cold14-firstmap-current-original-root-01/actual-a68-screen-release-01.json)3865/done/resources[]，UTC22:25:05.454799（本机06:25:05）。只保留六步观察信用，不授防御日数或业务通过；真实title/getter语义继续源码核查，尚无修复或新增正式发布，旧R13及历史不改。

R14后续EOF收据：[FINAL_EOF_THIN_01](C:/workspace/ck3-upgrade-20261006/xqol-r14-thin-report-observer-agent-01/FINAL_EOF_THIN_01.json)6919B、SHA `0bd551826d92b17eb56df362473d5b849c0c35d373050cdcda9ec4bc7068b56f`，原23项仅4/23各一次，三类FAIL与两类reject各0；真实root query/result/trace各1。engine error.log EOF为17415B、SHA `5a4aa1b2d5297c22e08b114e87ed8443f9a4231bf217b553c252f23644f238ce`，不写零错误、不先归因；无业务通过或修复信用。

## 2026-10-06 R15/a69：Source09读取修复实测，D1夹具前置失败

Source09的build11于UTC01:54:54.056463实际exit0，245.216秒；DLL SHA `916bd5a3cccacd05198b4e07d58c6883a9b8bd7dc639e691649bcec8d1029eb4`。R15唯一启动于02:15:16.679636，资格02:19:58、initial2在02:20:00完成；实际root available/readiness=true、held partition=true，family16850/heir37989/`c_nf_zhao_8d99_1` 为 `landless_noble_family_no_province` / capital=null。council_ready=false及定义flags未暴露的边界原样保留，不能写成所有DTO字段已完整。[实际首root薄证据](C:/workspace/ck3-upgrade-20261006/xqol-r15-thin-report-observer-agent-01/ACTUAL_INITIAL_ROOT_THIN_NON_EOF_01.json)19024B、SHA `f6add1d5c856bf918d7362f90a7bb88071fe7474c3b4b1a925bb6edf53c476d2`；可复用分类见[held-title专题追加](ck3-native-ai/held-title-partition-v1.md#2026-10-06-noble-family-counties-without-a-province-12003)。master五处必要回归迁移实际Python normal39/-O39、native旧16/当前17组及monthly-piety模式通过，见[11575B回归收据](C:/workspace/ck3-upgrade-20261006/held-family-master-regression-migration-agent-01/FINAL-REGRESSION-MIGRATION-RECEIPT-01.json)，SHA `703d71aeda5ce2b90c0a9c722f52f30f6dece12802f53b46894122c68f783b6e`；其native夹具复用生产renderer片段，不能冒充完整master DLL构建。

原driver04因读取正在写入的report发生PermissionError，发生于claim/output/D0前，原exit1保留。外置driver05只修文件并发读取、继承原期限及actual error fatal，在同R15恢复第一次业务动作，没有重发Start。Root唯一执行后driver05仍exit1：实际D0观察及02:43:54.097668完成的自然D1为24小时，宋34422/PID21776/gen1、raw53144328→53144352；三个FAIL为defense_fixture_setup、defense_matrix_done、reverse_initial_war_missing。原23项仅6项各一次、duplicate0，含失败后的DONE，不是6项业务PASS；D2/D5未执行，post-D1 receipt/once/output未生成。[8591B driver边界](C:/workspace/ck3-upgrade-20261006/xqol-r15-machine-driver-read-lock-recovery-agent-01/actual-r15-driver-boundary-01/actual-driver-boundary-receipt-01.json) SHA `f974c11d285f161952c71e256ea4369d97587bc49afa1e734b5a9e450a562226` 保全单次执行和停止；242处setup合取失败转376处FAIL，288–296处start_war未执行，不归因CB拒绝。

当前唯一[最终EOF薄收据03](C:/workspace/ck3-upgrade-20261006/xqol-r15-thin-report-observer-agent-01/FINAL_EOF_THIN_03.json)18950B、SHA `bec99cafb1a3c7eba50b70d28d2fcaa2a0e2064ac85b9847e11bb6e856e02b73`，纠正旧01/02按直接token或错误day-kind拼写的统计，旧原件不改。error.log EOF为17953B、SHA `3cffb99f6e55f83537c831db54da7786bc3fc2343cde1f9c18bc13be92fa4d8e`，含D1新增538B夹具错误：zqa_phase2_defense_effects:166的set_character_faith被拒，33702/al-Mustansir是宗教领袖，stack initializer44/event22；不能将全文豁免为原版court噪声。该实际拒绝影响overlap目标准备，setup其余合取原子未逐项dump，不能称唯一失败原因。完整59块/13种正文在[EOF全部正文证据](C:/workspace/ck3-upgrade-20261006/xqol-r15-thin-report-observer-agent-01/ERROR_EOF_ALL_UNIQUE_BODIES_01.json)保全。

Root真实WM_CLOSE、关闭autosave、Quit Desktop后，native于02:46:31.432661正常process_exit0/shutdown0、job0/tree_gone/cleanup、全部库存[]；[8916B正常退出证明](C:/workspace/ck3-upgrade-20261006/xqol-r15-thin-report-observer-agent-01/ACTUAL_NATIVE_NORMAL_EXIT_PROVEN_02.json) SHA `7a28254b94fe56fdfbd4064dea678043da6dc93496f0df7bda6e5e0872d3019f`。runner02:50:02.057109 GREEN/error=null、7rows全部finished/OK、cleanup/thread=true，只证明运行收口，不冲销业务FAIL3。game/harness/raw/thin四原PID全部gone，raw/thin实际exit0；原watchdog20496按原ctime已退，该数字后来被ctime1791254985.711666的conhost复用，不能认作原watchdog仍活。keeper实际exit0/末序3914后，Root唯一[a69实际CAS](C:/workspace/ck3-upgrade-20261006/xqol-r15-normal-quit-root-01/actual-a69-screen-release-01.json)3915/done/resources[]于UTC02:55:39.553874完成。首府分类读取修复已在本场实测，整个防御仍未通过，候选1.1.1未发布；旧R12–R14及失败原件不动。
