# CK3 兼容任务接续：2026-10-03

用户于 2026-10-03 要求接手[前任交接](ck3-upgrade-handoff-2026-10-02.md)并继续兼容任务。本文保存接续增量；原 1.20.0.2 实机、失败 attempt、原片和 profile 保留原样。

## 当前安装与实际阻点

20:46（Asia/Shanghai）实际读取本机 Steam 安装：CK3 **1.20.0.3 / Crozier / build 25652598**，EXE 101,039,736 bytes，SHA-256 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。安装仍位于 `C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III`，仓库参考链接指向同一目录。launcher-settings、Steam appmanifest 与 EXE 身份一致；旧交接的 AE1B/1.20.0.2 不能用于这次启动。

接续起点 `dafba6bea02ba43388e47a20779c3c6f9c352e5d` 已包含[中央 .3 迁移](ck3-1.20.0.3-migration.md)与[原生 ABI 复用依据](ck3-native-ai/crozier-1.20.0.3-native-migration.md)。复用这些源码及证据，不重复逆向，也不把另一机器的实机结果视为本机产品通过。本机进程盘点为 CK3 0；任务总线没有活跃屏幕 owner。尚未启动游戏或操作 Steam；`inspect` 的默认 D 盘 bus 路径在本机不存在，返回 `task_bus_error=CalledProcessError`，不能据该字段缺失判断资源空闲。实际 C 盘 bus 的 `poll --ack` 和 `list` 已单独核验。

原九个公开 prepare 入口共享的 `fixture_engine_prepare` 只接受 .2 EXE；其中四个入口还把 .2 的版本/build 常数直接写入收据。这是新版实际准备阻点。共享 helper 现在按已核对的 .2/.3 **完整 EXE SHA**选择身份；公共收据与廷臣 fixture descriptor 使用实际身份。未知 EXE 仍在输出写入前拒绝；原版身份匹配不证明脚本、native 或产品实机通过。

## 准备入口验证

项目解释器为 `C:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe`，Python 3.14.7。实际依赖 probe：MCP 2.2.0、psutil 7.2.2、Pillow 12.3.0、pyautogui 0.9.54、capstone 5.0.9、jsonschema 4.26.0、attrs 26.1.0。

`tools/test_fixture_engine_prepare.py` 的 3 项聚焦测试通过，覆盖两版身份保留、未知 EXE 在创建输出前拒绝、公共收据保持 `NOT_RUN`。正式 CI 加入该测试，纯 Python，不需要 CK3。

真实安装上的 11 个公开调用全部成功：MRM、Ox、TED、AUB、XCCC、361、XQOL 天朝/行政、RMTM、主 mod/白绮 UI。每个输出为全新外置目录，收据均绑定上述 .3 SHA/build，状态仍为 `NOT_RUN`。主/白绮同时走正式 production builder；其他产品只准备独立夹具。所有输入快照、stdout/stderr 与输出保存在 `C:/workspace/ck3-upgrade-20261003/preparation/public-entry-points-01/`；[完整报告](C:/workspace/ck3-upgrade-20261003/preparation/public-entry-points-01/report.json) SHA-256 `9f841b2be5440ca5ee41c859fd94681ae3652fca64f1380bed086e385c7050a5`，结果 **PASS_PREPARATION_ONLY**。

此包仅修改 Python 身份/收据路由；`open_kaishek` 对该层没有可覆盖的 CK3 语义，记录 `not-applicable`。未变脚本的历史 parser 证据不重跑，也不改名为 .3 实机。

## 并行范围与下一步

准备器工作包已提交并普通推送至 master `00af1b285`。随后采用[TED 初始化 guard 修复与通用日志知识](ck3-1.20-aub-ted-log-continuation-2026-10-03.md)：替代引擎入口继承原决议的一次初始化 trigger，13项聚焦合同与1项changed-event parser通过。当前源码候选已应用，实机归零仍 NOT_RUN；原85/93条日志不改写。

根执行者负责本机桌面、版本准备、汇总和主线交付；三个独立线程分别处理 AUB/TED 已有日志、主/白绮七 cell 接续、361 规则页实际停止。候选都写外置目录，避免污染未来 clean source freeze。

旧廷臣 continuous driver 固定 d19e794/.2 helper，导航使用 RapidOCR。它不能因收到继续指令而直接视为 .3 正式 MCP 路径。需要采用实际 .3 frozen source/binary 并确认可用的原生 UI 能力；规则、死亡、冷载入及教程 bytes 的业务结果继续独立读回。七 cell 的 .3 实机目前 **0/7**。

旧 AUB93/TED85 错误及 strict RED 保留；361 原规则停止仍是启动驱动未完成，功能 **NOT_RUN**。主要工作包历史 **3/10** 只描述前任 .2 已列范围，不能换算成本次 .3 产品通过率。没有 Workshop 上传、发布 tag、七语发布审计或人工 approval。

21:28 本机续跑增量见 [`.3` 原生启动 R0002](ck3-upgrade-native-startup-2026-10-03.md)。已建立真实 MCP/native 会话，但首个可用 route=`bookmarks` 被驱动拒绝，NewGame/Start 均未调用；AUB 仍未到地图。受管 containment 完成、CK3 为零、屏幕 CAS 已释放。现修复实际前端 tree/条件广告阻点，再使用新 run；准备、加载观察和清理完成都不提升产品通过口径。

此前准备器提交 `00af1b285` 的[官方 CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37124590688)及 TED guard 提交 `6440948e7` 的[官方 CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/37124685230)均实际完成 success；官方 CI 不提供实机通过。本次记录包的 Python-only validator 通过，未重跑已复用的 parser/L0。

后续前端接线修复已普通推送 `6e11ba8dd`；[规则窗口真实读取接口](ck3-native-ai/frontend-game-rules-1.20.0.3-2026-10-03.md)已完成有限离线验证与组合DLL，待新独立诊断run读取实际值。[RMTM/Ox新冷profile](ck3-1.20-rmtm-ox-native-preparation-2026-10-03.md)也已完成文件准备，仍runtime NOT_RUN。当前native缺口是规则选择/Apply/应用后读回、通用决议/产品GUI模型与必要持久化动作；旧ingame UI的工具schema不能替代 `.3` ABI/能力验证。

R0003已实际续跑，但首个Bookmarks route是加载瞬态：随后树为 `_root_`/截断/不可见，下一路由不可用，原生规则打开命令未派发。新增[route/tree一致等待修复与证据](ck3-upgrade-native-startup-2026-10-03.md#r0003瞬态路由不能证明可操作窗口)，单一聚焦回归PASS，真实规则值仍 NOT_RUN。当次清理是现有 job containment；没有正常退出，不能用来证明教程落盘。CK3=0、keeper停止与CAS释放均已读回；新验证继续用新run及新userdir。
