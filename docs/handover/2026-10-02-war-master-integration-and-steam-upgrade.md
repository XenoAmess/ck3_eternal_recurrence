# 2026-10-02 Steam CK3 升级与战争研究 / 第二期视频主线整合

执行任务：`ck3-steam-upgrade-war-e2-integrate-20261002`。用户明确要求升级本机 Steam 管理的 CK3，并整合全部有价值的研究、视频及关联成果；这是 2026-09-30 `ie` 隔离指令所要求的明确合回授权。原交接见 [2026-10-02-war-episode02-video-research.md](2026-10-02-war-episode02-video-research.md)。

## 本机升级结果

Steam 公共默认分支已由 **1.19.0.6 (Scribe), build 23530548** 更新为 **1.20.0.3 (Crozier), build 25652598**。实际安装目录为 `C:/SteamLibrary/steamapps/common/Crusader Kings III`；更新后 manifest `StateFlags=4`，无 beta opt-in，launcher 版本与主线 exact-build 身份一致。

- 更新后 `ck3.exe`：101,039,736 bytes，SHA-256 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。
- [安装身份回读](evidence/2026-10-02-war-master-integration/identity.json)记录 UTC `2026-10-02T05:31:56.098243+00:00`。
- 更新完成立即关闭下载并恢复 Steam 离线。随后正常重启客户端，取消临时本地 CEF 调试开关；保留 `-cef-disable-gpu` 以恢复本机冻结的桌面像素。
- [最终离线原图](evidence/2026-10-02-war-master-integration/steam-offline-final.png)显示“离线模式”和当日 13:34 时钟；[尺寸 / SHA 回执](evidence/2026-10-02-war-master-integration/steam-offline-final.json)绑定 1024×768 原图，执行者直接审阅。
- 本次没有启动 CK3，也没有执行 Workshop 或视频外部发布。

升级后的 `00_traits.txt` SHA-256 为 `93ad0316b733aa474d34841bd92fb3fc9336c111e9f06e7910178e74482185aa`，与主线 1.20.0.2 的 306 项 trait 快照逐字节相同；保留原快照版本来源标签，记录这次 1.20.0.3 等价回读，未为相同输入重生产品文件。

14:07 左右补采桌面时，画面时钟停在 13:44，该次截图作为 stale RED 保留，没有当成新鲜实机授权。只读回读唯一已保存账号的 `WantsOfflineMode=1`，且临时 CEF 8080 调试端口已关闭、CK3 进程为零；这些仅补充升级完成状态，不能替代后续游戏启动所需的新鲜离线原图。

旧 EXE、原 manifest、全部桌面恢复 attempt、下载 / 重启日志及失败尝试保留在 `C:/Users/1/ck3-upgrade-integration-20261002-a01/`。曾按本机恢复合同尝试 ToDesk 服务恢复，显式重启返回权限拒绝；后来正常重启 Steam 恢复了新鲜画面。桌面独占 claim 已按 CAS 回收；其 `expired-own-claim-released` 收据中的 `unresolved_red` 是过期 claim 的保守业务标记，不覆盖上述安装身份和离线原图结果。

## 整合范围与字节保全

从主线基线 `67184ba9dda67ff53af7d83fb691b7ee7b178552` 开始，独立 detached worktree 负责原生代码和视频 / 文档。整合使用线性 rebase，普通 fast-forward push；不产生 merge commit，不 force-push。

| 来源 | 冻结 tip | 进入主线的内容 |
| --- | --- | --- |
| `codex/war-series-brown-gold-20261001` | `04bf1fe17de2a351288b70d9292316535d69d7de` | a04–a09 视频制作源码、配置、文案、素材索引、审核与交付记录、全部失败证据及最新交接 |
| `codex/war-e2-mechanism-closure-20261001` | `c4e87182397e19ccb4112617bde13168d96eb50d` | R0148/R0149 研究结论、原生 UI / observer / trace、identifier append 及其依赖修补 |
| `ie` | `ff1b17dc294fb416667f849636d07dadf47f2567` | H3937 inventory / single query / queued wake、H2743 stock predicate 及消费链 |
| `codex/war-e2-identifier-append-capture-20261002` | `431461d6841604ebd19e65670661ca2a732dbff8` | 已包含于研究 tip 的捕获工作；避免重复重放 |
| 十个关联 Episode02 / H2743 / H3937 / R0266 来源 | [完整来源表](2026-10-02-war-source-provenance.json) | 补入原主线与三个主 tip 都缺失的 398 个文件，覆盖历史脚本、测试、夹具、证据和知识文档 |

[视频 Git blob 回执](evidence/2026-10-02-war-master-integration/video-source-preservation.json)核对最新视频来源的 9,995 个改动路径，零字节差异。成片、raw、TTS、失败 attempt、配置快照和历史签核没有重渲染或改写。

[关联文件导入回执](2026-10-02-war-related-source-preservation.json)逐文件绑定原 tip、Git blob 和 SHA-256。补入后还组合了历史 `a3fdd31ca...` 中更晚的 Decimal PTS 定位补丁与配套测试，解决旧 preview sampler 缺少 `seek_text` 导致索引工具无法导入的实际错误；[组合回执](2026-10-02-war-pts-source-composition.json)记录这两份文件的新权威来源。早期字节仍可从原标签和导入提交读取。

13 个 `archive/war-handover-20261002/*` 标签保全相关来源的 **605 个原始提交**，包含被新主线实现替代的历史共享文件变体；它们不充当活跃开发分支。直接关联来源的改动路径联合数为 10,608，不意味着所有旧共享文件版本都适合覆盖当前实现。完整范围判断见 [只读分析](evidence/2026-10-02-war-master-integration/recommendation.md)。

## 实现与验证边界

保留主线 CK3 1.20.0.2 / 1.20.0.3 adapter、dispatcher、runtime、任务总线 CAS 和受管 session 行为，按函数组合原生冲突。旧 UI、de-jure 和战斗研究仍受 1.19.0.6 exact EXE / RVAs / GUI 身份约束；相关 opt-in 功能继续默认关闭。不能把原生编译、Python 测试或旧 1.19 实机证据称为新增 1.20 production-live 能力。

视频 / 索引定向测试：29 个 Episode02 合同测试、3 个 frozen PTS 测试、8 个 sampler 测试通过。最初缺失 `seek_text` 的 RED 及修复后两组 PASS 收据均保留于 [本次证据目录](evidence/2026-10-02-war-master-integration/index.json)。原生最终候选 `d88f25140bcacb23f9a36ecfed92c89eb9c001f5` 基于并发更新后的主线 `d4f377d97b7a4f97ac85151610adbc4d4df818f8`；20 个独立 Native 用例有效 PASS 覆盖，Python 145 tests + 201 subtests 与最新版 session/runtime 75 tests + 28 subtests PASS。先前 native a02/a03/a04 RED 全部保留，后续只复测受修复影响的项目。Mailbox source-contract 与 feast fixture 接线修复没有改变生产 DLL bytes。完整结果见 [原生报告](evidence/2026-10-02-war-master-integration/native-source-final-report.md) 和 [SHA 回执](evidence/2026-10-02-war-master-integration/native-source-final-receipt.json)。

Python-only 检查首次将十份冻结构建环境日志里的默认 Windows PATH 目录误判为 shell 调用。检查器现在仅在三类构建环境 metadata 中忽略该目录名称，实际 engine executable、脚本扩展名和其他调用继续拒绝；没有改写这些历史 bytes。交接中的禁令说明改为引用根目录 AGENTS，避免普通文档触发相同字面扫描。

最终 master SHA、普通 push 和该 SHA 的官方 Actions 终态收据保存在外置执行目录；来源分支只在对应 master 官方 CI GREEN 后退役，冻结 checkout、构建与过程资产继续原地保留。

## 保持真实的未完成项

- R0148/R0149 的 nonzero screen / nonempty growth 等未闭合项沿用原研究边界，没有用本次版本升级补写 GREEN。
- a09 完整 1× 观看 / 听审和人工签核仍待人工完成。既有 OneDrive InSync 记录没有新增远端字节回读，本次没有重新上传或宣称视频最终签核。
- 新升级安装已核验；本次整合没有新增 CK3 1.20 实机 attempt。后续原生能力验收须使用新版本身份及新鲜 Steam 离线画面，不能复用 1.19 的地址与配对验收结果。

## 首次官方 CI 的依赖修复

首个整合提交 `b441b91465f4c70c1b8a9deebb994bc787c1e060` 已普通推送；[官方 run 36975221321](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/36975221321) 在 ZhongGuo capture 离线合同测试导入 `bridge.mcp_server` 时实际返回 `ModuleNotFoundError: pydantic`。原生 UI 的严格整数输入使用该包，而官方静态依赖遗漏；本机主 venv 已装 2.13.5，导致先前定向检查没有暴露这项环境差异。补入 `tools/requirements-static.txt` 和 `ck3_autonomous_player/pyproject.toml` 的精确依赖，未安装或调用 CK3，也未放宽类型校验。

[原始 CI RED](evidence/2026-10-02-war-master-integration/ci-failed-log-065219352034.json) 与[受影响完整 capture 离线回归 PASS](evidence/2026-10-02-war-master-integration/zhongguo-capture-ci-regression-065425429869.json) 均按原字节入库。本机 regression 使用明确的主 venv，实际 RC=0；其中测试故意生成的 RED 路径属于拒绝错误输入的断言，不是新实机 attempt。13 个来源归档标签已普通上传并逐项匿名 Git refs 回读核对；来源分支仍须等待修复后 master 的准确 SHA 官方 CI GREEN 再退役。
