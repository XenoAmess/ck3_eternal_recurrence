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
| 永恒轮回 | 特质目录、Rite、原生继承窗投影已迁移；L0 GREEN | R0003：廷臣五阶段实际通过；额外目录、保存、死亡与导入继续 |
| 白绮独立版 | 独立新版快照、Rite、文案与 LF 字节合同已合成；L0 GREEN | 待隔离验证 |
| 肃清曼荼罗 | L0、可复现构建、parser GREEN；核心实机后更新兼容声明至 1.20.0.2 | R0001：9 个严格核心断言通过，日志无错误；fixture 核心覆盖 |
| XenoAmess 体验优化 | 三类总督任命及改信/释放/赎金迁移；L0 GREEN、26 文件构建 | 待隔离验证 |
| 重整河山 | 新版原生臣服、政府预算与毁头衔后果已迁移；30 项测试和 L0 GREEN | 待隔离验证 |
| 驱策朝贡国 | L0、构建、parser GREEN；外置核心后果夹具已准备 | 待隔离验证 |
| 天朝经商贪腐维护版 | 从新原版保留政府机制，只加经商能力；L0 GREEN | 待隔离验证 |
| 自动升级建筑维护版 | 45 项门禁按新版 potential/rite/DLC 迁移；L0 GREEN | 待隔离验证 |
| 牛来 | L0、构建、parser GREEN；生产拒绝/招募 UI 夹具已准备 | 待隔离验证 |
| 天朝特色361制 | 新原版依赖审计无删除；8 组静态 GREEN，既有内容审计一组 RED | 待隔离验证 |

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
其窗口、交付、Rite、死亡、保存及跨进程导入仍在执行。另八个场景及 TED/AUB/XCCC/361/Ox 的独立输入均已准备，
文件与 parser 证据仅记录准备资格，不填实机 PASS。十个玩家产品以表格为验收清单；`tools/fixtures` 属于验收夹具，
`ck3_autonomous_player/mod_bridge` 为开发桥接工具，另列其文件与测试检查，不能冒充独立产品功能通过。

[CI 审计](ck3-1.20.0.2-github-ci-audit-2026-10-01.md)确认旧 workflow success 隐藏了命令失败。
[退出传播修复](ck3-ci-command-failure-propagation-2026-10-01.md)已推主线；新 run 36823839237 如实显示
TED 离线依赖失败，后续[导入与安装路径修复](ck3-ci-runner-import-closure-2026-10-01.md)在独立环境 5 项测试通过。
361 的 52 failures 和 1 error 的输入与升级前逐字节相同，未以刷新审阅批准消除旧 RED；本轮实际引擎问题独立归因。
