# 《礼与道》第一轮实现与静态验收报告

日期：2026-10-04（Asia/Shanghai）。版本：开发版 0.1.0。结论：**正式源码 L0 GREEN，实机 NOT_RUN，产品验收尚未完成。**

## 本轮交付

新增独立 `mod_li_yu_dao/`，使用 `lyd` 命名空间，不覆盖原版儒家信仰、经学或道学。玩家主动入门后，可在孔门、孟氏、荀氏、郑氏、王氏、经疏、朱子、陆氏八个样板之间择师，并触发对应的修习事件。实际启用 15 个信条，36 礼仪／36 信条的完整设计仍保留在数据目录中。

24 个修习选项已接入支付能力、金币、虔诚、威望、压力与学识经验效果；每次完成后共用 180 天修习冷却，换学统冷却 365 天。取消选项不收费、不启动冷却。入口、事件与实际效果都检查玩家条件。没有新增 NPC 自主触发链；原生共享 faith／rite 的被动行为不因此变成玩家专用。

本轮共 18 个发布载荷文件、182 个中英文文案键、10 个事件。构建器仅投影正式运行文件，生成确定性 ZIP 和逐文件 SHA-256 manifest。夹具、研究与验收工具被排除。专用 GitHub Actions 运行生成字节、静态校验、工具测试及可复现构建，不启动 CK3。

宗主、争统、正式批准／分合、多派授权、军会与圣物尚未落地。两信仰／两礼仪的分合探针独立保存在 [native_cycle](../../mod_li_yu_dao/fixtures/native_cycle/README.md)，当前只证明结构检查通过，不是正式功能或游戏内通过。

## 验收输入与结果

永久原始回执：[report.json](acceptance/2026-10-04-iteration-1-l0/report.json)、[static-report.json](acceptance/2026-10-04-iteration-1-l0/static-report.json)、[evidence-index.json](acceptance/2026-10-04-iteration-1-l0/evidence-index.json)。原件另保留于 `C:/workspace/ck3_li_yu_dao_acceptance/20261004-readonly-iteration1-final/`；更早 attempt 保持原样。

解释器 Python 3.13.15。本机游戏确认 **1.20.0.3 Crozier**，EXE SHA-256 为 `94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`。安装身份确认不构成游戏加载验证。

| 已执行检查 | 结果 | 证明范围 |
| --- | --- | --- |
| 内容与运行时生成器 `--check` | GREEN，rc 0 | 当前生成文件与输入精确一致 |
| 正式源码 `validate_static.py` | GREEN，rc 0 | Clausewitz 结构、引用、三核心、玩家入口调用链、中英键与插值 |
| 构建器工具测试 | 3 tests OK，rc 0 | 可复现、夹具排除、错误条件拒绝 |
| 验收 runner 工具测试 | 6 tests OK，rc 0 | 版本、证据分层、环境／源码状态区分 |
| 正式源码双构建 `--check` | GREEN，rc 0 | 18 文件 manifest／ZIP 可复现 |
| 前后源码输入哈希 | 一致 | 编排没有修改受测源码 |
| 仓库 `validate_python_only.py` | GREEN，rc 0 | 未引入被禁止的 shell 调用 |

各命令的 stdout、stderr、时间和退出码已分别保全。结构解析不是 CK3 原生 scope 类型检查；工具测试不是游戏语义测试。

## 实机与剩余工作

本次只读编排观察到 CK3 进程数为 0；没有当前会话的 MCP `tools/list` 和产品原生读回证据，因此编排返回 **ENVIRONMENT_RED，rc 2，live NOT_RUN**。这是环境准备状态，不是已执行的 CK3 capability RED。仓库已有 1.20.0.3 provider 和本机桥接产物，正在复用它们建立本轮独立 profile；不能以旧 1.19 doctor 代替当前版本验收。

Open Kaishek 的当前 LYD 1.20 profile／语义夹具未声明，本步记录 `NOT_APPLICABLE`，没有虚构离线运行通过。真实 CK3 验收须另取得当前 Steam 离线画面、屏幕独占、独立 userdir、运行编号及当前 provider 后置状态。

下一门槛：简中普通战役 Robert 29829 的实际加载与修习效果；原生探针三轮合流／分立及人物、县、领袖绑定。五年自然冷却、继承和存读档必须另测；探针中的显式清除测试冷却不能作为五年到期证据。批准及争统功能仅在上述原生接口得到验证后进入下一轮正式源码。

2026-10-04 后续记录：[R0001](2026-10-04-R0001-loading-red.md) 已实际启动并出现原生加载 RED。本报告的 L0 结果保持原有证明范围；不得将其解释为当前产品已通过 CK3 加载。修复与下一次冷载使用新证据。
