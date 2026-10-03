# 本机 CK3 升级与全产品兼容验收

2026-10-03 用户已要求接续；当前本机已经是 **1.20.0.3 / build25652598 / EXE94b55397…de02a6**。新版接续状态以[接续记录](ck3-upgrade-resume-2026-10-03.md)为准；下文 .2 历史实机与交接仍保持原样。九个公开 prepare 入口的版本锁已修复，11 个真实调用正确绑定 .3 并保持 NOT_RUN；这不增加产品实机通过数。

2026-10-01，用户授权更新本项目 master、本机 CK3，并逐个检查、测试和修复项目中的 mod。本页滚动记录这台机器的实际结果；其他机器的 native、profile 或实机结果保持各自身份。

## 已完成的环境更新

- 仓库使用 `fetch`、`rebase origin/master` 和普通 fast-forward push 同步；并发远端更新均线性接入，未创建合并提交。
- Steam 更新完成：CK3 从 1.19.0.6 / build 23530548 升至 **1.20.0.2 Crozier / build 25588574**；当前 EXE SHA-256 为 `ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d`。
- 游戏实际安装在 `C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III`。仓库内被忽略的参考链接指向该安装。旧 EXE、manifest、特质、继承 GUI 和 3591 个原版文本文件已保全至外置 `baseline/`。
- 更新后 Steam 已恢复离线；启动前直接检查每次新鲜离线截图。在线期间发现其他机器正在使用账号，未启动游戏或接管其会话。
- 使用本仓库 `tools/.venv/Scripts/python.exe`（Python 3.14.7），分别安装常规、静态和独立宣传工具链依赖。本轮不制作宣传视频。

## 产品工作包

| 产品 | 源码/静态检查状态 | 新版实机状态 |
| --- | --- | --- |
| 永恒轮回 | 特质目录、Rite、原生继承窗投影已迁移；L0 GREEN | R0003：廷臣五阶段及三项新增目录价格实际通过，已保存；后续七 cell 0/7，用户要求收尾后不再续跑 |
| 白绮独立版 | 独立新版快照、Rite、文案与 LF 字节合同已合成；L0 GREEN | 待隔离验证 |
| 肃清曼荼罗 | L0、可复现构建、parser GREEN；核心实机后更新兼容声明至 1.20.0.2 | R0001：9 个严格核心断言通过，日志无错误；fixture 核心覆盖 |
| XenoAmess 体验优化 | 三类总督任命及改信/释放/赎金迁移；全额付款的余额上限及接收者上下文已修复；兼容声明 1.20.0.2，L0 GREEN、27 文件构建 | R0003 天朝与交互、R0004 弱/强牵制付款、R0005 行政17标记/6次开关/2候选面板通过；复杂防御与其余边界未覆盖 |
| 重整河山 | 新版原生臣服、政府预算与毁头衔后果已迁移；30 项测试和 L0 GREEN | 待隔离验证 |
| 驱策朝贡国 | L0、构建、parser GREEN；夹具 target 冲突已修复，兼容声明 1.20.0.2，13 原断言/16 生产文件不变 | R0005 原核心、实际投降、同实例保存/载入部分通过；85 条错误和3项部分 UI/GAP，严格仍 RED，已正常清理 |
| 天朝经商贪腐维护版 | 从新原版保留政府机制，只加经商能力；兼容声明 1.20.0.2，22 文件构建 | R0001：11 条原核心标记、真实决议、退出第四档及三年冷却通过；两条夹具诊断/getter 缺口保留 |
| 自动升级建筑维护版 | 45 项门禁按新版 potential/rite/DLC 迁移；兼容声明 1.20.0.2，L0 GREEN | R0001：39 条原标记与真实死亡继承通过；93 条未归因日志使严格汇总仍为 RED |
| 牛来 | L0、构建、parser GREEN；生产拒绝/招募 UI 夹具已准备 | 待隔离验证 |
| 天朝特色361制 | 新原版依赖审计无删除；8 组静态 GREEN；并发上游文案接入后修复四处按钮长度，32/33 项通过，审阅字节绑定仍 RED | R0002 在规则核对阶段停止，未 Apply/Start，核心 NOT_RUN；按用户要求正常结束并保全证据 |

以上是开发兼容工作，不是 Steam Workshop 发布。静态、parser 或版本声明不代替功能实机通过。七语正式翻译和公开发布流程未进入本轮。

## 本机实机记录

原版基线完整 ID：`4-8e1c2f1861--vanilla--R0001`。已成功进入原版大厅、新建 1066 罗贝尔开局、读取暂停 HUD 并保存；`error.log` 和 `gui_warnings.log` 均为空。保存文件 10,935,391 bytes，SHA-256 `a122e52d4339129d692cd1266fe57795d7c509c0274a739b9b8165bf940cdfeb`，副本在 `baseline/vanilla-save/`。该进程已关闭，仅证明新版原版基线，不证明任何 mod 功能。

本机当前可用工具、EXE 与 native 输入按每次启动记录；不把其他机器的已构建 DLL 当作本机准入。没有适配本机新版本的可用 typed 能力时，官方 UI/引擎夹具路径记录实际覆盖及缺口，禁止以旧 RVA 替换哈希冒充新版原生迁移。

外置根目录：`C:/workspace/ck3-upgrade-20261001/`。`new-build/identity.json` 绑定本次游戏；`audits/`、各产品目录绑定原版差异与 L0；`live/<完整ID>/` 保留 raw PNG、坐标换算回执、独立 userdir、生产 staging、游戏日志和启动身份。所有失败 attempt 与过程素材保留。

源码工作包按必要验证后逐包提交推送。报告后续追加实际功能结果、修复和最终主线身份，不把待验项目填成 GREEN。

## 15:15 串行实机与 CI 增量

本机已从冻结 `d19e794041eae408666702a1039bde41639cbf6f` 另行构建精确 1.20 native 候选，
DLL SHA `c02b8d83d5ddef813a69d3cf9745d51e889ba3961342fe70cad2dce2761c87ab`，
injector SHA `523d22dc3bcedf3be5fd399275049d451b430296a30cb1acd077aafccdf3628e`。
foundation 检查 17 signatures、7 vtables、34 instruction checks；四项 C++ 测试、10 项 harness 测试通过。
SDK smoke 仅为模拟 server 检查；实际 TED R0001 的 native snapshot 另证明当前 EXE/build 匹配、暂停地图可读。
以上证据不推广成所有 advertised query/action 已通过。外置 `native/candidate-manifest.json` SHA
`cb95015460879d4bfc667fcc9024d67b54450baf014777e2f8f83c6ec747d66a` 保持冻结。

TED R0001 在实际地图之后因计划中非必需的 campaign query 失败结束，保留 HARNESS_RED；后续使用仅检查暂停地图的计划。
TED R0002 和主 mod R0001 在进入地图前触发控制会话等待超时，未形成产品功能结论。
主 mod R0002 查出夹具缺失 tooltip，修复准备器的三项文本后冻结新夹具，旧 attempt 均保留。
后续会话延长等待时限，并由唯一桌面验收负责者连续操作；每次仍须新鲜 Steam 离线证明、独立 profile 和完整 run ID。

主 mod R0003 已在大厅真实核对禁用轮回、继承 100%、成长计分和 standalone 测试规则；空保存预设菜单不影响该实证。
其后五项廷臣 UI 交付断言实际通过，冷载入、Rite 分支交付、死亡及跨进程导入仍在执行。另八个场景及 TED/AUB/XCCC/361/Ox 的独立输入均已准备，
文件与 parser 证据仅记录准备资格，不填实机 PASS。十个玩家产品以表格为验收清单；`tools/fixtures` 属于验收夹具，
`ck3_autonomous_player/mod_bridge` 为开发桥接工具，另列其文件与测试检查，不能冒充独立产品功能通过。

[CI 审计](ck3-1.20.0.2-github-ci-audit-2026-10-01.md)确认旧 workflow success 隐藏了命令失败。
[退出传播修复](ck3-ci-command-failure-propagation-2026-10-01.md)已推主线；新 run 36823839237 如实显示
TED 离线依赖失败，后续[导入与安装路径修复](ck3-ci-runner-import-closure-2026-10-01.md)在独立环境 5 项测试通过。
361 的 52 failures 和 1 error 的输入与升级前逐字节相同，未以刷新审阅批准消除旧 RED；本轮实际引擎问题独立归因。

## 18:10 实机与修复增量

主 mod `4-8e1c2f1861--eternal-recurrence--R0003` 实际完成：取消零副作用、119 分禁用购买、120 分一次交付/扣款、348 分自定义取消保留，以及重开后 348 分一次交付/扣款。同一 GUI 中实际选择 Aluk 的 Rite 并完成交付；额外特质 `erudite`、`lifestyle_scholar`、`herald` 的可见增价分别为 50、15、100。非默认 Rite 真言宗的配置预览已取得，但该分支的交付尚未执行。

保存是实际引擎文件 68,450,662 bytes，SHA-256 `52e8d94ef42e6d3f61c83e9cef92da8a5898347e51947fa76577ee637cf4341e`。原进程已关闭，独立冷载入 profile 已准备，保存不等于重载通过。外置 `audits/courtier-main-ui-R0003-closeout/report.json` 绑定 14 张原始 UI 图、全部断言、日志、保存和正常清理证明；debug SHA `d4599fbc2f1f65f1df9100981db4a94841980586eff9176a4e5a12137e37c5cc`。

该会话 `error.log` 有五种变量未使用诊断、各两次：两种 curse rarity 是此前明确记录的静态例外，三种 settlement 变量来自升级前逐字节相同的 `xar_effects.txt`。它们有 native 消费者源码，但真实死亡消费仍待本轮测试；没有扩大忽略规则或制造脚本读取来抹除日志。归因报告 `audits/main-ui-unused-variable-attribution-01/report.json` SHA `03dac72d098e8b9aef7dd197fc479725e279b7d4ed5701576e560f7873bb92a9`。

体验优化 R0001 的付款准备断言失败促成生产修复：1.20 的 `golden_obligation_value` 新增 `max = gold`，原有 `gold >= golden_obligation_value` 因此不能拒绝付不起全额的角色。新生成 script value 保留原版赎金基数及强牵制 1.5 倍，只移除报价的余额上限；实际交易仍走原版交互。生成、静态、8 项构建测试和 27 文件双构建均通过，实机 R0002 使用新冻结输入继续验证。证据位于 `audits/xqol-live-payment-fix-001/`，此前失败未覆盖。

上述历史 361 RED 后，接入远端 `dbb84a92d` 文案更新。新的聚焦 33 项检查发现四个简中按钮超过 14 字上限；修改生成器并重新生成后长度为 14、13、12、14，付款数字、工具提示和机制不变。机器 ledger 无失败、1034 文件双构建可复现，32 项通过；剩余一项是旧人工审阅 manifest 不再绑定当前四句文案。人工审阅文件保持原字节，不把机器更新写成人工批准。最新证据 `zhongguo/upstream-copy-refresh-attempt-02/`，旧 52+1 只属于此前输入。

## 19:00 付款上下文与严格总督结果

体验优化 R0002 的目标检查失败保持未定原因；诊断记录能证明初始化目标已不在预期作用域，但不能反推其精确消失过程。新的夹具选取真实任命法、非 landless、年龄/健康符合条件的现任者，保存头衔和人物身份，并跨实际日界刷新后检查。R0003 已实际通过 `enabled_highest_non_player_heir_selected`、退位转移、死亡转移及关闭后的原版继承/guard 恢复断言。

R0003 后续 `payment_full_only` 失败仍保留。其原观察器覆盖了当时的预期金额，不能恢复精确失败条件；独立受控交易的八项严格条件及跨日复读均通过，没有把该失败归为每日收入。另一探针实际证明同一历史廷臣在钱包 100 时，无接收者上下文报价 15，绑定 `recipient=this` 后原版报价 50。生产全额筛选因此补上正确接收者上下文，仍调用原版交互。新夹具同时修正预期的 actor/recipient 上下文、原版舍入分支，并在原观察器改写字段前保存金额、次数、三个目标的钱包及八项条件。

此工作包已生成/静态/可复现构建/production parser 通过；终版夹具新增诊断后的独立 parser 为 6/6、零错误。证据在 `audits/xqol-payment-context-fixture-001/checks.json` 与 `audits/xqol-payment-context-fixture-002/final-report.json`；终版准备器 SHA `609b1815dc673faf32653089abd573e3500e6cffcccb3103a436e8f3572d2b5f`。修正后的生产字节仍待新付款会话实际验证，R0003 不标整体 PASS。完整范围见[付款上下文修正](xqol-native-payment-context-2026-10-01.md)。

361 最新 1034 文件 production/profile02 已冻结，相对旧 staging 仅两份简中文案变化，830 份 TXT/GUI 与夹具保持原字节；不重复旧 parser，也不把新 profile 的文件准备写成实机通过。五个独立产品的连续启动与功能收集器，以及主/白绮冷载入、双顺序和死亡 driver，均以外置新 attempt 保留准备证据，等待串行取得实际桌面。

## R0003 交互 UI 收口

体验优化 R0003 已于 19:42 正常结束受管会话，`cleanup_proven`、`tree_gone` 为 true，job 及 CK3 inventory 均为零。实际 UI 与后续业务检查取得 `conversion_threshold_50_filtered`、`ransom_full_only`、`ransom_any_one_gold`、`release_priority_matrix`、`release_conversion_rite_matched` 五项 PASS；角色搜索器及完整角色面板实际读回 ZQA 两名样本、禅宗/罗马礼与意见正负。原 `payment_full_only` FAIL 保留，native report 的 GREEN 仅表示受管会话成功结束，不表示产品全矩阵通过。

外置 `audits/xqol-R0003-ui-closeout-02/report.json` SHA `62b160a22ab231350b6d1ca409323ce6acd6996227f4ddf9ddb1a3ea0b5fbd4d` 冻结日志、三个实际 UI 原图、四个观察器结果、profile 输入与清理证明。最终 `error.log` 为 50,209 bytes，136 条记录中 57 条明确来自 tooltip 构建；其中包括验收探针的无人物/未设置 pending 作用域诊断。未将所有记录归为原版或声称零错误。前一 closeout 准备 attempt 因两个截图文件名不匹配停止，也已保留。

冻结 R0003 的改信文件与当前 production 逐字节相同；付款/俘虏文件各顶层 effect 中，只有 `xqol_bulk_demand_payment_full_effect` 随接收者修复变化，其余赎金及释放 effect 均保持原字节。已通过的交互结果仅按这些未变输入延续；付款使用新的 `xqol-payment-context-profile-04` 独立验证弱牵制及强牵制边界，不重复未变的总督与交互矩阵。

本机已再接入 `42d74678d` 的最新 master。相对此前主线，十个玩家产品、开发 bridge、准备器、构建器和静态检查输入均无变化，外置冻结的 d19 native 候选保持独立身份。

## 付款修复通过与产品收口口径

体验优化 R0004 于 19:58:58 完成三项弱牵制付款断言和两项强牵制边界断言。强牵制目标钱包 74 时，未截断报价为 75、原版截断报价为 74，足额筛选正确拒绝；钱包 76 时重新报价 75，原版实付 75。弱牵制交易的八项金额、计数、钱包与牵制检查亦全部通过。独立 `payment-only` 范围说明保留原完整合同，未重跑未变的 R0003 功能。

该场随后误调用未初始化 draft 的改信 dispatcher，产生 303 条真实 runtime error（202 条 callee scope、101 条 caller comparison），并非 tooltip。最终 385 条错误另含 3 条夹具 BOM、21 条夹具变量和 58 条原版 court scene 来源记录；不由来源路径推定全部根因。付款结果在额外调用前保存，改信不从该场取得 PASS。原 closeout 及更正附录均保留，后续准备器已删除额外分支，但其 parser 通过不算新实机证明。

证据 `audits/xqol-R0004-payment-closeout-01/report.json` SHA `057b530005c7a9b77fb2ca35934e6956761ad9365499d70e75bc5b1685213b06`；更正附录 SHA `71fc04cf9b889aa4c99e4e09568ad616c1f1f288e7a47a9ac4abeb1bf6f95ce6`。场景已正常清理、CK3 零进程。详见[产品范围](xqol-ck3-1.20-compatibility-2026-10-01.md)与[付款实机证据](xqol-native-payment-context-2026-10-01.md)。

按产品主要迁移范围的实机工作包计，当时为 **2/10**：肃清曼荼罗核心范围，以及体验优化的天朝/行政核心、付款修复与代表交互已完成；这不是每条功能边界或正式发布验收。体验优化的复杂免费防御战争后果、其余任命家族/slider/宗教负门禁仍未覆盖，见[产品专题](xqol-ck3-1.20-compatibility-2026-10-01.md)。自动建筑 R0001 已完成全部 39 条原标记和真实死亡继承，兼容声明、必要静态与构建检查已交付；93 条未归因日志保留，不能计为完整兼容收口。其详细来源边界见[自动建筑专题](ck3-1.20.0.2-auto-upgrade-buildings-compatibility-2026-10-01.md)。驱策朝贡国 R0004 已定位原版遗留 Dynasty_house target 与夹具选择 guard 冲突，朝贡关系及 actor 正常；源夹具改用独占选择作用域，原13断言与16生产文件不变，parser通过，profile05待实机复验。天朝经商贪腐维护版 R0001 已启动，后台继续必要准备。采用前台单产品连续验收、后台源诊断和准备并行的方式，每个必要工作包验证后立即交付，不重复未变输入的检查。

## 经商贪腐 R0001 收口增量

当前主要迁移工作包为 **3/10**：肃清曼荼罗、体验优化的已列核心范围，以及天朝经商贪腐的政府迁移/第四档/代表决议范围。这不是十个产品全部功能或正式发布进度。经商贪腐原11标记各一次、无FAIL，真实生产决议与退出第四档、1066-09-18至1069-09-18冷却通过；21运行时文件与实际测试投影字节一致，仅descriptor改兼容版本，必要静态/双构建通过。两条夹具初始化变量诊断明确归因，严格零错误门仍保留RED，第二事件typed getter也保留缺口。

外置 `audits/xccc-R0001-closeout-01/report.json` SHA `8afc3f5b9100affcdf3f4b40d216f1eefc7a965f12a18605c6233eac025dd387`；严格收集器SHA `cc948c462bc3f9f9e01235c6bc7c75a009033449689558e263a247a0669230c2`。详情见[经商贪腐专题](ck3-1.20.0.2-celestial-commerce-corruption-compatibility-2026-10-01.md)。驱策朝贡国使用修正后的独占选择作用域在R0005继续实机；先前失败与启动前时效拒绝均永久保留。

## 2026-10-02 用户要求收尾：最终状态

用户要求停止开启新工作，温和完成在手事项并写交接。此后只收妥既有报告、结束当前会话与恢复环境；原全产品计划不再自动续跑，此前 ETA 取消。详细待办、证据身份与可恢复入口见[交接文档](ck3-upgrade-handoff-2026-10-02.md)。

最终主要迁移工作包口径维持 **3/10（30%）**，不是全功能或发布完成。TED R0005 原13核心标记全通过，真实投降并在同一实例实际保存/载入；玩家/日期/无战争已读回，关系/停战等仍缺独立 UI 核验。最终85条错误及三项部分 UI/GAP保留，严格汇总 RED，正常清理证据完整。[TED 专题](ck3-1.20.0.2-tributary-expansion-directives-compatibility-2026-10-01.md)已追加最终报告。

361 R0002 未取得三组规则真实选中项，启动驱动在 Apply/Start 前停止，功能核心 NOT_RUN。用户收尾指令后仅对绑定的实际窗口发送正常关闭，退出码0、受管树/job/watchdog清理完成；native RED记录的是 readiness 前结束，不能把它当作机制测试结论。全部规则原图和失败回执保留。

交接时 CK3及本轮控制进程为空，桌面恢复 **1024×768 / 60 Hz**，原始新截图直接确认 Steam 仍离线；资源释放。外置 `wrapup-20261002-01/closeout-report.json` SHA `2d363fab9df05168196483a9f4c8945ab60f67e12c2004f2381ad83826c8d856` 绑定清理和恢复证据。未启动新的验收、未改生产机制、未上传 Workshop。
