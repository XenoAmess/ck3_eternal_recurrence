# Epsilon-Q 历史实验归档（2026-10-03）

这份索引将先前保留在本机、尚未被 Git 跟踪的 17 组 Epsilon-Q 家徽拟合实验纳入主线。共 465 个文件、57,612,127 字节：251 张 PNG、167 份家徽代码文本和 47 份 JSON。它们记录了早期 smoke、候选预算对比、消融实验及 holdout 测量，可用于复核算法取舍和失败原因。

既有文件逐字节保留，大小及 SHA-256 见 [manifest.json](manifest.json)。根目录 `.gitattributes` 为这 17 个实验目录保留原始字节，包括 167 份文本的 CRLF；后续归档不得重写这些历史结果。

## 结果边界

43 份 `report.json` 包括 42 份浏览器拟合报告及一份早期 holdout 报告，另有四份 `quality-summary.json`。47 份 JSON 的原始顶层状态分布为：

| 原始状态 | 份数 | 含义 |
| --- | ---: | --- |
| `browser-passed-native-mcp-pending` | 42 | 报告记录浏览器完成；原生 CK3 验收待完成。 |
| `browser-passed-quality-target-missed-native-pending` | 2 | 浏览器完成，质量目标未达，原生验收待完成。 |
| `measured-quality-target-met` | 1 | 早期 v11 holdout 的测量结果，适用范围见原报告。 |
| `red` | 2 | 原实验汇总失败，按失败证据保留。 |

本轮检查通过的范围是文件完整性、PNG 解码、UTF-8 文本和 JSON 语法。实验中的质量失败、各行回归和原生待验状态仍以原报告为准。当前正式结论及 CK3 原生失败证据见 [Epsilon-Q 研究报告](../../ck3-coat-of-arms-editor-epsilon-q-report.md)，正式工件为 [v14 / 1024](../epsilon-q-v14-budget1024/README.md)、[v13 / 128](../epsilon-q-v13-budget128/README.md) 和 [v14 holdout](../epsilon-q-v14-holdout/README.md)。

## 实验索引

| 目录 | 文件 | 字节 | report.json |
| --- | ---: | ---: | ---: |
| [epsilon-q-smoke-128-focused-r2](../epsilon-q-smoke-128-focused-r2/) | 11 | 1,003,394 | 1 |
| [epsilon-q-smoke-128-focused](../epsilon-q-smoke-128-focused/) | 11 | 1,002,080 | 1 |
| [epsilon-q-smoke-128](../epsilon-q-smoke-128/) | 9 | 877,932 | 1 |
| [epsilon-q-v10-budget128](../epsilon-q-v10-budget128/) | 33 | 3,235,248 | 3 |
| [epsilon-q-v11-budget128](../epsilon-q-v11-budget128/) | 78 | 7,295,062 | 7 |
| [epsilon-q-v11-holdout](../epsilon-q-v11-holdout/) | 1 | 160,170 | 1 |
| [epsilon-q-v11-joint1024-ablation](../epsilon-q-v11-joint1024-ablation/) | 22 | 2,231,172 | 2 |
| [epsilon-q-v11-joint2048-ablation](../epsilon-q-v11-joint2048-ablation/) | 11 | 1,109,276 | 1 |
| [epsilon-q-v11-joint2048-archive-ablation](../epsilon-q-v11-joint2048-archive-ablation/) | 23 | 2,219,884 | 2 |
| [epsilon-q-v11-smoke-picture05-complete](../epsilon-q-v11-smoke-picture05-complete/) | 11 | 1,075,757 | 1 |
| [epsilon-q-v12-budget128](../epsilon-q-v12-budget128/) | 78 | 7,338,535 | 7 |
| [epsilon-q-v12-directj256-ablation](../epsilon-q-v12-directj256-ablation/) | 11 | 1,122,849 | 1 |
| [epsilon-q-v12-directj512-ablation](../epsilon-q-v12-directj512-ablation/) | 22 | 2,262,723 | 2 |
| [epsilon-q-v12-high256-ablation](../epsilon-q-v12-high256-ablation/) | 22 | 2,255,530 | 2 |
| [epsilon-q-v12-medium512-ablation](../epsilon-q-v12-medium512-ablation/) | 22 | 2,256,946 | 2 |
| [epsilon-q-v13-budget1024](../epsilon-q-v13-budget1024/) | 78 | 17,130,218 | 7 |
| [epsilon-q-v14-smoke-1024](../epsilon-q-v14-smoke-1024/) | 22 | 5,035,351 | 2 |

各实验的 PNG、候选代码及报告保持原目录关系。仓库根目录的零字节 `detours.installed` 是本机安装标记，仍保留在本机并按精确路径忽略。
