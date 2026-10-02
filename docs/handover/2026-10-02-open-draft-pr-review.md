# 2026-10-02 全部 open draft PR 逐项处理

冻结审阅基线：`db4c94d17a3ae8c3241543c511c8ef253d8afd1b`。GitHub 全部开放 PR 共 **45** 个，全部为 `XenoAmess` 提交的 draft；本次先逐项比对 exact head、原始 diff 与当前主线，而不是按标题或年代批量丢弃。补入、验证、GitHub 关闭与来源保全均已完成，最终回读见文末。

**处理分类：21 个补入遗漏，16 个已在主线，8 个被后续实现替代。** 仓库要求线性 rebase/提交；补入内容之后关闭旧 PR，GitHub `closed` 不冒充 `merged`。每个原始 head 都有 `archive/draft-review-20261002/pr-<number>-<sha9>` 归档标签，远端 exact SHA 已复核；源码、旧 worktree、历史录像、失败 attempt 和其他过程资产不随分支引用清理而删除。

## 逐项决定

| PR | 处理 | 理由 | 原始 head |
| --- | --- | --- | --- |
| [#448](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/448) | 补入遗漏后关闭 | 补齐停战查询接线、决策元数据和六段历史 follow-up；保留当前紧急退出政策。 | `24c51a37d` |
| [#449](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/449) | 补入遗漏后关闭 | 补入现金研究历史与独立响应快照；旧全局 observer、旧 CLI 和无 producer 的现金原型归档。 | `3bc267e0d` |
| [#451](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/451) | 补入遗漏后关闭 | 补齐 current battle knight 只读端口和遗漏回归测试；保留后续 runtime。 | `d921dd3a0` |
| [#500](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/500) | 补入遗漏后关闭 | 补入 R0321/H3911 请求、失败证据与历史续篇。 | `784e2bb33` |
| [#502](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/502) | 补入遗漏后关闭 | 恢复多防守方不能按单防守方处理的两个实际守卫与入口回归。 | `6374697d0` |
| [#503](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/503) | 补入遗漏后关闭 | 补入三份来源边界审计及原响应的追加记录。 | `346da8d15` |
| [#507](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/507) | 补入遗漏后关闭 | 补入首跳只读查询顺序与同日重试抑制；未恢复缺真实现金 producer 的移动候选。 | `f7e78a1a9` |
| [#512](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/512) | 补入遗漏后关闭 | 补入 hard conversion 只读诊断，纠正研究结果的可用性标签。 | `3af6fdd2f` |
| [#514](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/514) | 补入遗漏后关闭 | 补入默认关闭的 private compact MCP snapshot、历史 readiness 工具与证据。 | `e70f0a802` |
| [#565](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/565) | 后续替代，关闭 | 旧 H3928 runner/test 已保留；旧固定 CLI 被当前 H3937 配置入口替代。 | `2d68e899e` |
| [#595](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/595) | 已在主线，关闭 | 候选查询与测试已保留，当前配置 runner 已包含后续修复。 | `3219e2669` |
| [#612](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/612) | 补入遗漏后关闭 | 补齐省份 siege native 查询及精确 H3937 范围内的 planner hold。 | `f96dc0054` |
| [#653](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/653) | 补入遗漏后关闭 | 补入 a04 readiness RED 响应与独立核对。 | `0ebe9a62e` |
| [#669](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/669) | 补入遗漏后关闭 | 补入窗口审阅规划、来源报告与精确 PTS/截图输入支持。 | `7b8ac1fb9` |
| [#673](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/673) | 补入遗漏后关闭 | 补入角色读取原始研究与三组测试；旧 dormant worker 原型归档。 | `2ad213f56` |
| [#679](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/679) | 补入遗漏后关闭 | 补入 a11 readiness RED 响应，保留失败截图事实。 | `63fb1023c` |
| [#684](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/684) | 已在主线，关闭 | ColdLoadObserver、测试和文档已逐字保留。 | `ae6c5eed8` |
| [#685](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/685) | 补入遗漏后关闭 | 补齐 siege capability 映射及 watchdog 早期 import 失败诊断；不倒退当前 CAS/custody。 | `e7c0727b7` |
| [#696](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/696) | 补入遗漏后关闭 | 补入 a12 查询拒绝 RED 的修订响应。 | `bf861e123` |
| [#714](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/714) | 补入遗漏后关闭 | 补入 a13 启动前 watchdog RED 响应。 | `226ea4979` |
| [#719](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/719) | 后续替代，关闭 | 当前成片文案已包含后续正确计数说明，旧候选文案归档。 | `7648739b7` |
| [#721](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/721) | 已在主线，关闭 | 交接与周报增量已在主线，早期日报状态被当天后续记录替代。 | `f83f72b72` |
| [#723](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/723) | 后续替代，关闭 | pair 校验已由后续 #749 runner 和 #743 测试完整保留。 | `98d0871eb` |
| [#724](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/724) | 后续替代，关闭 | 旧进程树终止原型被 #730 Job containment 与当前 runtime 替代。 | `a852f4bf6` |
| [#728](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/728) | 后续替代，关闭 | static seal 与模式隔离已由后续 #749 完整保留。 | `d4004005e` |
| [#730](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/730) | 已在主线，关闭 | Job helper 已逐字保留，当前 runtime 还包含后续结果/CAS 修复。 | `965a5d5ef` |
| [#731](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/731) | 补入遗漏后关闭 | 恢复历史 combined runner 的即时退役入口和相配套的归档测试夹具。 | `b13925c22` |
| [#732](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/732) | 已在主线，关闭 | CAS protocol、九项测试和文档已逐字保留。 | `848b89008` |
| [#733](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/733) | 后续替代，关闭 | 不恢复会让当前恢复入口全部停止的旧门槛；原始候选完整归档。 | `04b7b5460` |
| [#735](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/735) | 已在主线，关闭 | static seal 与测试已逐字保留，仍不制造 live 权限。 | `5cec58c6c` |
| [#736](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/736) | 已在主线，关闭 | worker proof 合同与测试已逐字保留。 | `e90d04c57` |
| [#737](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/737) | 后续替代，关闭 | 当前 frontend-first、GUI disk 校验与后续修复已替代旧版本。 | `080178785` |
| [#739](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/739) | 补入遗漏后关闭 | 补入第二 recorder 静态设计；明确当前每 capture 仍只允许一次 raw attempt。 | `146b2ff12` |
| [#740](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/740) | 补入遗漏后关闭 | 补齐 d26→d27 控制路径及回归；保留当前 d11 seal/pair。 | `5168746fb` |
| [#742](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/742) | 补入遗漏后关闭 | 补齐 day32 终端 typed frame 验证与负例。 | `499047b70` |
| [#743](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/743) | 后续替代，关闭 | 旧 lease helper 的停止条件已在 #749 后续版本中保留。 | `a9943b4fe` |
| [#745](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/745) | 已在主线，关闭 | 前端任务引导与相关测试已保留，后续改动继续保留。 | `e348c0fda` |
| [#746](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/746) | 已在主线，关闭 | 清理回读模块已逐字保留。 | `2abf954ad` |
| [#747](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/747) | 已在主线，关闭 | 多成员 Job fixture 与测试已逐字保留。 | `9e2076c97` |
| [#749](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/749) | 已在主线，关闭 | 最终旧 runner、cleanup 测试和文档已逐字保留。 | `f05de7a41` |
| [#750](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/750) | 已在主线，关闭 | 显式 HWND/UI Automation 操作及测试已保留，保留后续修复。 | `5a1025282` |
| [#752](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/752) | 已在主线，关闭 | GUI scale readback helper 与测试已保留，生产调用链保留后续版本。 | `62e39f933` |
| [#756](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/756) | 已在主线，关闭 | watchdog custody helper/test 已逐字保留，当前 runtime 已接入。 | `38b28769b` |
| [#761](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/761) | 已在主线，关闭 | selector scoped-monitor 源码与两组测试已逐字保留。 | `96acba4f1` |
| [#770](https://github.com/XenoAmess/ck3_eternal_recurrence/pull/770) | 已在主线，关闭 | 受管 H2743 entry、pair verifier 与测试已保留；后续 stock provenance 继续保留。 | `78d75e018` |

## 版本、证据和未激活原型

本次原生读取补丁只恢复 CK3 **1.19.0.6** 的历史只读端口及其离线 fixtures。当前 **1.20.0.3** adapter、stock/mailbox 和后续 runtime 保留，119 研究选项不自动开启；旧 DLL、EXE、源码 seal 与 run/config pins 不刷新。本次没有启动 CK3，没有新 live 结果，没有重编成片或人工签核。

R0321 首跳仅恢复只读查询顺序，缺少真实现金 producer 的旧移动候选保持未激活。H3937 planner hold 与未认证 inventory 的限制收窄到历史 exact H3937 范围；H2743 恢复 readiness/handoff 元数据，不覆盖当前 route emergency exit。旧全局现金 observer、旧固定 CLI、dormant worker/supervisor 和会停止当前桌面恢复路径的候选均保留归档，而不重新接入。

补回的历史 JSON 中 RED、未审阅截图、未完成查询及 UNKNOWN 保持原事实。第二 recorder 文档补有当前“一次 raw attempt/capture”的说明，静态设计不冒充已实现。

## 验证与后续状态

机器可读逐项 head、比较计数、理由和归档映射见 [review JSON](2026-10-02-open-draft-pr-review.json)。实际移植路径/函数、解释器、测试 stdout/stderr、native OFF/ON 构建、CI 与关闭回读永久保存在外置目录 `D:/ck3-pr-review-20261002-a01/`；最终本节追加已完成检查和关闭事实。

## 补入工作包与离线检查

角色 transport/collector/准备合同及 readiness 共 78 项测试通过；Python 只读 bridge facades 普通与 `-O` 各 74 项测试及 155 项子测试通过；planner 定向普通与 `-O` 各 80 项及 39 项子测试、当前 planner 回归 38 项、正式退出消费者 27 项及 45 项子测试通过；历史入口退役/watchdog 诊断普通与 `-O` 各 55 项通过；视频证据工具普通与 `-O` 各 49 项通过。初次环境/旧夹具不匹配的 RED 原件保留，新 attempt 的实际 source path 与解释器明确记录。仓库 Python-only 检查 GREEN；原生最终结果与 exact master CI 在后续追加。

原生 C++、Python facades、planner/research、视频证据、历史知识五个独立文件所有权工作包按项目 AGENTS 并行；协调者汇入文档与证据。open_kaishek 对本次 C++ 编译、Python 文件/MCP 传输、Windows 控制夹具和媒体证据工具不适用：它们不执行 CK3 脚本语义，未启动游戏。

原生最终检查：新的外置 OFF 与 H2743-ON 两组配置均编译 full bridge 和受影响 targets，CTest 每组 7/7，通过合计 14 项；共享 GameAdapter layout 在120 runtime与119可选读口间保持一致，119 reader、knight mailbox 缺失 fixture stub 和 query capability 接线一并补齐。完整 source mapping 与初次 fixture/linkage RED 保存在 `reviews/native-implementation.json`，新 DLL 仅用于编译验证，未刷新或冒充旧 live seal。

## 最终 GitHub 回读与来源保全

已按编号逐项关闭全部 **45** 个旧 draft，每次 PATCH 后独立回读 `state=closed`、原 head 不变和 `merged=false`；开放 PR 与 draft 均为 **0**。21 个遗漏成果通过线性提交 [`763ae3cd8`](https://github.com/XenoAmess/ck3_eternal_recurrence/commit/763ae3cd839055ccf0654bbd2a21ca5e09c23d39) 进入 master；其 [exact SHA 官方 CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/36989710144) 为 completed/success。未制造 merge commit、强推或额外 PR 评论。

随后退役关联 **45 local + 45 remote source refs**，37 个附属原始 worktree 在 unchanged exact HEAD detach，写入冻结 sidecar，目录和全部 ignored/process assets 保留；tracking refs 亦回读不存在。所有 45 original PR head 与额外 local565 的 archive tag 保留，其余七个 differing local head 的 ancestry/patch-equivalence 及已有 archive containment 已记录。已对已知 workspace/process/temp Git metadata 做跨 common-dir 来源引用审计；本次仅退役这45个来源，不触碰其他活跃任务引用。

逐项关闭 JSON、最后开放列表、common-dir 审计、pre/post worktree ledger 与删除回执位于 `D:/ck3-pr-review-20261002-a01/`。此文及 JSON 是永久跟踪记录；最终报告另作普通 master commit/push，其 CI 回执继续外置保留。历史 RED、119-only readiness 和人工视频签核状态不因关闭 PR 而改变。
