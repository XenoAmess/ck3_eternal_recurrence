# 本机 CK3 升级与全产品兼容验收

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
| 永恒轮回 | 特质目录、Rite、原生继承窗投影已迁移；L0 GREEN | R0003：廷臣五阶段及三项新增目录价格实际通过，已保存；冷载入、Rite 分支交付、死亡与导入继续 |
| 白绮独立版 | 独立新版快照、Rite、文案与 LF 字节合同已合成；L0 GREEN | 待隔离验证 |
| 肃清曼荼罗 | L0、可复现构建、parser GREEN；核心实机后更新兼容声明至 1.20.0.2 | R0001：9 个严格核心断言通过，日志无错误；fixture 核心覆盖 |
| XenoAmess 体验优化 | 三类总督任命及改信/释放/赎金迁移；全额付款的余额上限及接收者上下文已修复；L0 GREEN、27 文件构建 | R0003：总督/退位/死亡/关闭严格断言通过；付款原 FAIL 保留，改信实际 UI 和修复后独立付款继续 |
| 重整河山 | 新版原生臣服、政府预算与毁头衔后果已迁移；30 项测试和 L0 GREEN | 待隔离验证 |
| 驱策朝贡国 | L0、构建、parser GREEN；外置核心后果夹具已准备 | 待隔离验证 |
| 天朝经商贪腐维护版 | 从新原版保留政府机制，只加经商能力；L0 GREEN | 待隔离验证 |
| 自动升级建筑维护版 | 45 项门禁按新版 potential/rite/DLC 迁移；L0 GREEN | 待隔离验证 |
| 牛来 | L0、构建、parser GREEN；生产拒绝/招募 UI 夹具已准备 | 待隔离验证 |
| 天朝特色361制 | 新原版依赖审计无删除；8 组静态 GREEN；并发上游文案接入后修复四处按钮长度，32/33 项通过，审阅字节绑定仍 RED | 待隔离验证 |

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
