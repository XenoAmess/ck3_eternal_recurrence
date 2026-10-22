# 军事 Java 迁移休假交接（2026-10-22）

观察时间：2026-10-22T15:04:26Z。`machine_id: xenoamess-full-tower-eb9d2c1186`。仓库 `Z:/ck3_mod_rewrite`；本机有限工作包 `D:/codex-ck3-demos/2026-10-22-java-phase1`，下文简称 `J`。这些本机路径和执行结果不能外推其他机器。

用户最后指令为停止后续工作、保存 WIP 并交接。此前“56 并发”“自然后继自主续项”均已被停开新迁移任务及休假指令覆盖。不要将本文件当作自动恢复或启动采样的授权。军事域已经通知全部 19 位 owner 停止源码、测试、资源、文档续写和采样；只汇总现有状态，不为交接补跑。Root 通知 `java11` 尚未启动且已停止、storage 所有 Job active=0；此处记录 Root 的当前调度事实，不追认为执行者独立重验。

## 当前真实验收边界

- `java07`：原九模块整组 458 PASS；本域原 `military-policy/declarationpriority` 的 10 JUnit 真 PASS。此前 `java06` 的 float token 真实 RED 保留；修复为 capture/JUnit 直接保留并提交原 token，没有放宽生产整数守卫。
- `java08`：上游 governance 三项断言失败，军事 SKIPPED，未编译未测。
- `java09`：`--fail-at-end` 真执行独立模块，但 replenishment 必需 golden 缺失使军事依赖链仍 SKIPPED，未编译未测。
- `java10`：首次实际编译完整 `wave2-military` 的 main/test，执行 **393 tests：220 PASS、84 failures、89 errors、0 skipped**。大量失败为必需 golden 尚未进入该 snapshot，不能据统计判定每叶有业务缺陷；各 owner 必须读自己的实际报告。
- `java10` Maven 最终 exit=1、Job active=0，**compiled snapshot 后验 MATCH，原 Z 来源后验 MISMATCH**。不能把局部 PASS 或之后采用的新资源追认为这轮全图来源一致、全组通过或当前树已通过。后续要用 fresh snapshot 真验。

实际证据：`J/logs/build-java10.json`、`J/logs/build-java10-verify.stdout.log`；每类 XML 和文本在 `J/build/java10/wave2-military/surefire-reports/`。来源漂移的事后只读观察为 `J/logs/JAVA10-SOURCE-DIFFERENCE-OBSERVATION01.json`，观察时间 `15:00:09.679555600Z`。它明确不能替代构建原始 postcheck，也不能倒推漂移的确切发生时刻。

原 replenishment 在 `java10` 实际 8/8 PASS，landstock 实际 7/7 PASS；updaterwrites 的 7 errors 为缺 mandatory golden。此前“replenishment 缺 golden 阻断军事编译”的问题在 `java10` 已解除，不能继续描述为当前编译阻点。

## 393 项的实际类报告

以下均绑定 `java10` compiled snapshot，列为“运行 / failures / errors / skipped”。当前资源后续采用不能改变该表。

| 包 | 实际结果 |
|---|---:|
| actualcontact | 9 / 0 / 8 / 0 |
| armyinventory | 89 / 0 / 0 / 0 |
| armyqueue | 6 / 0 / 4 / 0 |
| armyselector | 7 / 7 / 0 / 0 |
| armytransfer | 5 / 0 / 4 / 0 |
| callbackrisk | 7 / 0 / 7 / 0 |
| coalition | 3 / 0 / 0 / 0 |
| coalitionreceipt | 3 / 3 / 0 / 0 |
| combatroles | 6 / 6 / 0 / 0 |
| commander | 5 / 5 / 0 / 0 |
| countyentry | 5 / 4 / 0 / 0 |
| declarationcontract | 2 / 1 / 0 / 0 |
| dejureexitterms | 5 / 0 / 5 / 0 |
| exitcomparison | 10 / 0 / 9 / 0 |
| exitresult | 12 / 0 / 11 / 0 |
| disembark | 7 / 3 / 0 / 0 |
| fleetsupply | 3 / 3 / 0 / 0 |
| holycost | 2 / 2 / 0 / 0 |
| holyhirecontract | 4 / 3 / 0 / 0 |
| holyreinf | 6 / 6 / 0 / 0 |
| landstock | 7 / 0 / 0 / 0 |
| losssequence | 6 / 6 / 0 / 0 |
| monthlyloss | 4 / 3 / 0 / 0 |
| prewaradmission | 10 / 0 / 0 / 0 |
| prestore | 6 / 6 / 0 / 0 |
| realmsiege | 38 / 0 / 0 / 0 |
| refuge | 7 / 7 / 0 / 0 |
| reliefrelevance | 6 / 5 / 0 / 0 |
| routewindow | 9 / 0 / 4 / 0 |
| routewindowstep | 7 / 0 / 1 / 0 |
| sharedwire | 5 / 5 / 0 / 0 |
| stocksupply | 10 / 0 / 10 / 0 |
| supplyschedule | 6 / 6 / 0 / 0 |
| updaterwrites | 8 / 0 / 7 / 0 |
| wardeclaredoverview | 5 / 0 / 5 / 0 |
| warexitterms | 8 / 0 / 7 / 0 |
| warresults | 45 / 0 / 0 / 0 |
| warresultssource | 7 / 0 / 7 / 0 |
| zerostockclock | 3 / 3 / 0 / 0 |

`armyinventory`、`coalition`、`landstock`、`prewaradmission`、`realmsiege`、`warresults` 的整类报告为零 fail/error。其余类的具体原因仍以原 XML/文本为准；不能把资源错误、测试采样故障、合同不一致和业务计算差异混成一种失败。

## 有限源码与 owner 清单

当前 `wave2-military` 共上表 39 个已启动包，下面按唯一 owner 列出，不再增加新包。域 POM owner 为 `java_declaration_priority`；Root 独占 parent POM、Git、Game、账本和实机调度。`g2_m7` 是唯一 Maven writer，`storage_resume` 是唯一受管 capture 调度 owner，任何恢复应重新核当前准入而非自行启动 JVM/Python。

| owner（`/root/` 下） | 已启动 wave2 包 | 已写 wave3 / D 草稿 |
|---|---|---|
| java_declaration_priority | prewaradmission；原 military-policy/declarationpriority 已真验 | prewarprior 仅 D 两个 main，未 ready |
| wave2_coalition | coalition、coalitionreceipt、declarationcontract、holycost | 无新开发 |
| java_replenishment | landstock、updaterwrites；另 replenishment-policy 原模块 | landcontext：11 main、capture、9 JUnit 方法及说明已于 java10 RELEASE 后入 Z，89,842 B；未编译/采样 |
| wave2_monthly_loss | monthlyloss、losssequence | 无新项 |
| wave2_stock_supply | stocksupply、callbackrisk | 无新项 |
| wave2_fleet_supply | fleetsupply、zerostockclock | 无新项 |
| wave2_supply_schedule | supplyschedule | 已启动的完整 derivedframe 后继若有 D 草稿，只按其最终说明收尾；不得新领取 |
| wave2_army_queue | armyqueue、armytransfer | 无新项 |
| wave2_army_selector | armyselector | orderedaudit：D 中 6 main、3 test/capture 与说明；另同一 shared runner/trace 最小重构 D 草稿，尚未采用 |
| wave2_county_entry | countyentry | 无新项 |
| wave2_disembark | disembark、prestore；共享完整 CurrentMovement codec | 无新项 |
| wave2_combat_roles | combatroles、sharedwire | currentflag31 旧候选不算交付；不得新增 |
| java_projected_contact | armyinventory、routewindow、routewindowstep、actualcontact | 无 wave3 新包；D 仅既有 actualcontact 草稿 |
| java_battle_retreat | realmsiege、refuge、reliefrelevance | siegecontribution 已完整迁 wave3；siegepresence 候选撤销，不继续 |
| java_defender_risk | exitcomparison、exitresult；原 military-policy/defenderrisk 保持 | holyobservation 的 2 个 child DTO/codec 已在 wave3，完整 observer/consumer/capture/测试尚未交付 |
| java_war_query_cadence | warresults、wardeclaredoverview、warresultssource；原 planning-runtime/warquerycadence | warresultstop 3 Java D 草稿明确 NOT READY，停止扩展，不入当前 reactor |
| wave2_war_exit_terms | warexitterms、dejureexitterms | 无新项 |
| wave2_holy_reinforcement | holyreinf、holyhirecontract | 无新项 |
| wave2_commander_quality | commander | commanderreadback 仅按 owner 最终 WIP 记录；不能把只读设计当源码已完成 |

`wave3-military/pom.xml` 已创建，仅单向依赖 `wave2-military`、contracts、Jackson/JUnit；未由本域修改 parent 登记，不承诺已经入统一 reactor 或编译。停工后只读 `rg --files` 确认 Z 中该 family 只有 landcontext、siegecontribution、holyobservation 这三个已启动包及域 POM；prewarprior、orderedaudit、warresultstop 均未入 Z。新旧 family 不得形成循环依赖。半成品移出 wave2 的历史 snapshot 原件不改写。

## 资源、采样与实际阻点

休假指令后的禁止事项包括启动新 capture 或为了交接补跑。下列均为已有请求与原件，恢复时先查文件是否仍存在及 SHA，保留旧 RED、不覆盖同名证据、只采用真实原 producer 字节。

- 原 declarationpriority：golden 50,899 B，SHA-256 `2a7ad28778ff5c6505dbcf61465523c014e2068c148f37aaef27ae5ff2dfac83`；`J/logs/DECLARATION-PRIORITY-SOURCE-FREEZE02.json`。包含 raw_request_json 的真实 float token 负例。默认 JUnit 不依赖未跟踪 Python。
- prewaradmission：golden 45,824 B，SHA-256 `3f7d6cec6ac9e12923293c7ae4aa98e9175faf6cdad7f3156e3a5203a7c01a3d` 已采用；原完整 pytest 41 PASS/0 skip，58 原 producer 向量。`J/logs/CAPTURE-prewaradmission01-ACTUAL01.json`、`PREWARADMISSION-SOURCE-FREEZE01.json`。java10 本类 10/10 真 PASS，生产与 golden 无后续修改；MIGRATION 已记录局部 PASS 及全域 RED/source MISMATCH。
- replenishment05 原完整 5 tests 真实 capture PASS，真 golden 已纳 java10，8 Java 真 PASS；landstock01 capture PASS、7 Java PASS。`J/logs/REPLENISHMENT-LANDSTOCK-UPDATER-CAPTURE-BATCH01.json` 保留。updater01 的 RED 为 test-only Windows inline mutation 引号丢失，fresh02 已排，不能移除非空突变检查来求绿。
- coalition 的 123 原 producer 向量已采用且 3 Java PASS。coalitionreceipt01 原件 18,019 B / `7b90bd8ca10faea6d70d687f803ebc2883ebb55c74820cc6104132d2dd42b703`，declarationcontract01 原件 26,513 B / `743b471e9ed39c1853fbf5bbf06f9262f14c4db91a03d2384ea57966493c1935`，已在 java10 终态 RELEASE 后逐字节采用，未重新 Java 验证。`J/logs/COALITION-CHAIN-CAPTURE-BATCH01.json` 是原三请求有限合并。holycost01 RED 为 capture base 中 selected 对象别名，须三个来源分别 deepcopy，fresh02 仅修捕获夹具，不冒称生产 normalizer 有同一故障。
- armyinventory 的 81 原 producer 向量已采用，本类 89 Java PASS。routewindow02、routewindowstep01、actualcontact02 的真实 capture 均 PASS，分别 63/73/69 cases、41,504/15,035/27,831 B；owner 已在明确 java10 RELEASE 后按原字节采用并核 SHA。默认测试的旧 4/1/8 errors 来自 snapshot 缺资源，后续仍须 fresh Java。NativeDriver 全文来源漂移时保留旧01，fresh02 绑定真实新 SHA，没有绕来源守卫。
- realmsiege：原 capture01 因 70 KiB 上限真实 RED；fresh02 无损 gzip 保留全部 32 expected，raw 89,594 B SHA `cf3cc5d927dd4afb4db1d3970dd4671eaa6794ba96bed76eb55479e3ec50bf52`，gzip 2,774 B SHA `1023c72eba68a625ad88ab211e1eeba18c766b6b9ae4312eece08acd60851692`。resource 已采用，38 Java PASS。refuge02、reliefrelevance01、siegecontribution01 为现存待采请求，未采不能授 golden/Java PASS。
- exitcomparison01 / exitresult01 原 producer capture 双实际 PASS，exit=0/Job0。java10 RELEASE 后采用 exitcomparison 41,509 B / `e844f4977ec73b566c250a2b67ae0de0bbd40ba3439abdf03594f5d965e1f444`，exitresult 37,833 B / `91784812f661318013c96d2130c817b764feb407e66f8d5d95a577e17c9db7a3`，4096-target sidecar 22,716 B / `8829b000bac2490a96cdce4ba372346fa522d784a4ddaf88f4c0507428f798ec`；本轮 9/11 errors 为 snapshot 缺 golden。`J/logs/EXITCOMPARISON-CAPTURE-REQUEST01.json`、`EXITRESULT-CAPTURE-REQUEST01.json` 已执行完成，保留勿重复采样。
- warresults：38 向量+原 4 pytest 实际 PASS，46,406 B / `126e8c8d856b39ee6b6e1b268bd08360f17e0efdbdfcc0ce7c9c20ab1dad6da2` 已采用，45 Java PASS。warresultssource：29 向量+原 10 pytest 实际 PASS，57,796 B / `e58d50ae5281a8cfcf099eb1f0379b117111b3de7b61407778dfb5e52c9ea407` 已采用，但 java10 snapshot 未纳入，7 errors 不能被事后采用改写。overview01 原 15 主测试+15 子测试均 PASS，capture 计数器混算成30导致真实 RED；D-only fresh02 须分别严格计数，旧01原件保留。已有请求 `SHARED-GOLDEN-BATCH-WAR-WINDOWS01.json`、`SHARED-GOLDEN-BATCH-WAR-OVERVIEW01.json`，以 storage 最终 D 队列及 fresh02 为准。
- disembark/prestore 已有请求分别 `J/disembark-capture-request01.json`、`J/prestore-capture-request01.json`。CurrentMovement 的完整 normalizer 唯一归 prestore，县入口风险归 countyentry，不能另复制。java09 RELEASE 后 added provenance declared-type guard/public CUnit guard 与新增两项回归不在 java10 老7项 snapshot 中，须 fresh 验证；不是用旧局部结果追认新代码。
- monthlyloss/losssequence、stocksupply/callbackrisk、fleetsupply/zerostockclock、supplyschedule、armyqueue/armytransfer、armyselector、countyentry、sharedwire/combatroles、holy 两包、commander、退出条款两包的具体 capture 请求保存在各 `MIGRATION-*.md` 和 storage D 队列。已写默认 JUnit 必须继续缺样本即失败，禁止改 skip/放宽守卫。这里没有新的采样授权。

停工前的最终请求补注：`J/logs/UPDATERWRITES-CAPTURE-BATCH02.json` 尚无 fresh02 实际通过结论；`J/logs/LANDCONTEXT-CAPTURE-BATCH01.json` 含18个真实来源引用，golden帽72,000 B、尚未执行，Z capture 是最新 canonical，D 的 landcontext 旧 capture 仍85k帽不可误用。overview fresh02 为 `J/logs/SHARED-GOLDEN-BATCH-WAR-OVERVIEW02.json`，D 修复源 7,019 B / `bc04a0f6bf166694b1a3db316404a1b069d6d81d971d6ea276ea788902139768` 未采用；旧01源保全，后续通过后同步 source/测试/golden。holycost fresh02 `J/logs/HOLYCOST-CAPTURE-REQUEST02.json` 已明确暂停，修复后的 Z/D 等价 capture 12,116 B / `cb32590ea4aa123cd6330fde2afe6e510cfef990a550c0000854410c9b47667c`，没有输出资格。

routewindow/step/actualcontact 的最终小型冻结清单于15:04:03Z保存为 `J/logs/ROUTEWINDOW-SOURCE-FREEZE01.json`、`ROUTEWINDOWSTEP-SOURCE-FREEZE01.json`、`ACTUALCONTACT-SOURCE-FREEZE01.json`，总大小分别78,498 / 35,515 / 70,406 B；这些是 source/resource 清单，不替代 fresh Java。realmsiege 停工前仅说明与 `REALMSIEGE-SOURCE-READY04.json` 更新，业务/test/resource未改，当前总56,711 B；其 java10 局部 SHA 核对观察为 `MILITARY-BATTLE-JAVA10-SUBSET-OBSERVATION01.json`。

三位分组协调 owner（coalition、replenishment、projected_contact）均已回报向指定5/4/6位转发休假STOP，本人及其当前工具无后台写者。其他已返回最终说明的 owner 同样确认停写/不自启执行。停止状态不构成实现完成或测试通过。

特殊未完成边界：combatroles 需要真实 14-scene C++ wholewire，不能手造叶替代；sharedwire token hoist 对 true/1/1.0 的旧 Python 相等漏洞必须单列类型修复，不能声称任意 malformed 输入完全 parity。warexitterms 原 production disabled/旧 build AV 门禁保留。dejureexitterms 仅迁普通 unadmitted baseline，H2743 文件/编译 fixture/来源 pair verifier 未迁，须明确拒绝该 stock evidence 分支，不能发绿色占位 token。

## 本人未完成的 D 草稿

`J/prewarprior-draft/` 只含两个文件，总 24,494 B：

| 文件 | bytes | SHA-256 |
|---|---:|---|
| PrewarPrior.java | 14,013 | 28dc56d382360ec49470a42ef5e18ba25228a799fd57e19213f16d84c0eb8658 |
| PrewarPriorCodec.java | 10,481 | f1b41eb1784e51fe2b36755988fefddd8f24d9d3ede4c7b8526c83cb5dca0818 |

这是停工前已写 WIP，**未入 Z、未编译、无 JUnit、无 capture、无实际消费者 Java 接管，不是 SOURCE_READY**。没有为交接继续实现。实现意图为完整 `simulation/prewar_battle_proxy.py` 纯闭包：256×120 固定 aggregate prior、精确 BigInteger Q 算术、uint32 avalanche/uint64 SplitMix、原 IEEE binary64 Wilson，始终 calibrated=false / admitted=false。SHA 输入原 Python `json.dumps` 默认 ensure_ascii=True，必须保留，不能用共享 ensure_ascii=False canonical 替代。

后续若获恢复授权，先审当前两稿，再补真实原 producer、完整 `test_prewar_battle_proxy.py` 和两个实际策略 consumer 回归；验证 Unicode/控制字符 source SHA、RNG wrap、整数边界、Wilson binary64、float/bool token、JSON roundtrip。不能把该 aggregate prior 变成宣战授权，也不能把尚未实现的 planner seam 写成已迁移。source/fixture 合计上限仍 160 KiB；不要在本次休假停工期间补写或执行。

## 恢复时的先后顺序

1. 先取得新的恢复指令，核机器 ID、Root/storage/M7 已停止状态、真实可用空间与通用存储政策。原 release02 截止20:00Z不是无限授权；Root 的6GiB annex允许 Maven2GiB+四个独立D-only capture树并行，只在仍有效的真实准入内使用。休假期间不自动续期。
2. 先读 `java10` 原始 compiled snapshot 和各类报告，按有限现有请求采用实际原件或修确切捕获故障；不要重做已成功的原 capture、不覆盖旧失败证据。
3. 所有 owner 完成有限源码/资源采用后，由域 lead 给明确 whole-domain freeze。M7 使用新的来源 snapshot 真执行完整命令；Root 顺序消费退出码、超时和 Job0，不能以工具 ACK 代替实际结果。
4. 只修真实剩余 RED，不新增新包。最后统一更新 producer→全部消费者/序列化/roundtrip 的实际范围；Java 局部 PASS 不能授实机、Quarkus 路由切换或宣战结果。

军事迁移没有执行 Steam/Game/RPC、Game 动作、clock 提交、ledger/canonical/pending writer、Git 提交或推送。没有新增游戏日、保存、30年完成或秒/日性能信用。Root 的既有真实实机恢复现场另见总交接，不得重放 UNKNOWN 操作。
