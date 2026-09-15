# G2 M4 Council R691 harness RED handover

## 结论与当前边界

R691 已在执行入口失败并终止，轮次处置为 `aborted_prelaunch_consumed_no_retry`，下一次实际启动轮次必须是 **R692**。R691 的失败发生在 Python harness 进程内：Windows Error Reporting 将故障模块记录为 `pythoncom313.dll`，异常码为 `c0000005`，fault offset 为 `0xC52E`。launch command 已进入 bootstrap，但 CK3 进程没有启动，也没有 bridge publication、raw private probe、council capability 结果、UI/玩法输入、日期推进或存档写入；事后受管进程数为零。

因此本次结论严格分类为 **harness RED**。Steward candidate private observer/council capability 是 `not_run / not_observed`，不是 capability RED，不能据此断言 native observer 成功或失败。该 RED 保持开放，直到新的 R692 候选完成一次暂停态、只读、先 raw publication 后 semantic validation 的真实 CK3 验收。

## 冻结证据

| 证据 | SHA-256 / 身份 | 结论 |
| --- | --- | --- |
| R690 live report | `E2D562A9BC88BFEA1752AAE55473B1148824B019917138FB3BF1B34D55C82F50` | 既有 `take_internal_semantic_snapshot` harness mismatch RED；CK3 曾启动，cleanup GREEN，存档不变 |
| COUNCIL13 candidate prelaunch source-identity RED report | `F7834A075BEEE0D5CA95F5565B9CDB1F24123F79308E2C179FE2E7B4C4890234` | 旧候选依赖错误的外部 runtime source；未分配轮次、未启动 CK3 |
| 上述 prelaunch artifact manifest | `BA7A4F5F607D36837C6AD28A87249BD34AC2D87BD8C2C307E32C20CFFE3DBCC7` | 固定 prelaunch report 的内容身份 |
| R691 candidate manifest | `645CDCFA8A9B03E87C14E5D0C8967BA9783BD2AB08A75EA9C3A305C45B13FD02` | self-contained runtime 候选；预检 GREEN |
| R691 sealed prep manifest | `D585577C8A6AFF83537257DB4A26FF05EA2BD6EB479E4ACD46D8B847355C790C` | 596 个 sealed 文件；候选输入冻结 |
| R691 harness RED report | `5E6CB7FD3C632EF17877E0165E0B8012345AF77B10B303D0E988416633D6D62F` | `failure_layer=harness`、`capability_probe_status=not_invoked`、CK3 未启动、R691 已消费且不可重试 |
| R691 copied WER | `78FBF1762EA54990639F25C38D7D7A444A806A3D7B9BB1DE571E7D84039CEAE4` | `python.exe / pythoncom313.dll / c0000005 / offset C52E` 原始故障证据 |
| R691 artifact manifest | `67CBFD8EAF69177E7615F9B10682B56DF7F4F09E04D8FF6E5FC44CCE0CE5EA57` | 固定 report、WER、preflight、ownership、postcrash inventory 与 watchdog/runner crash marker 共 7 个文件 |
| 冻结 source/target save | `9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63` | R691 前后内容身份不变 |

最终交接以表内 repo-external live-evidence artifact 及其 SHA-256 为准，而不是依赖固定机器上的 WER 绝对路径。证据目录可迁移到任一获授权环境；哈希、candidate manifest 和 sealed manifest 是身份锚点。

## Git 集成账本

本轮 self-contained runtime 工作已通过 rebase 线性进入远端 `master`，没有 merge commit。原工作提交到最终 master 提交的映射为：

| 原工作提交 | 最终 master 提交 |
| --- | --- |
| `b311d31db954f461a89cc464c6271913b66dd3a8` | `2a1d4f0da89a0e2398c07cb7e39009c56883e7e9` |
| `e5c6b4db63bf5d407c8bb04746f1e9d620b9599a` | `9f8411aa025da27873d7d01317f676cad8cdd62b` |
| `d3d9e817a2668150e7775617bde1f79d02f4ec1e` | `b1f7139cb07ee9488b2afb1e3c2021fd514a7d5b` |
| `942d6a34aa1842805e0600a4515b41d86b4e64c7`（export/fix） | `f742b80fa308d9d9e6bfcb9cbc644344ea20feb4` |

`f742b80fa308d9d9e6bfcb9cbc644344ea20feb4` 是本 handover 的代码基线。R691 使用的 runtime source commit 为 `dd36d1b7e8e3a79260a888efaeadd4b922df5f7f`；候选对外 public schema、MCP、planner 和 shared bridge surface 均未变化。

## R692 恢复条件

1. 保留 R691 RED，不复用 R691，不对同一失败入口作无输入变化重试。
2. 修复或替换触发 `pythoncom313.dll / c0000005` 的 harness 进程路径，并生成一个身份不同、重新 sealed 的 R692 候选。
3. 启动前重新确认所有受管环境中 CK3 inventory 为空，冻结 candidate、runtime source、DLL、游戏 EXE、启动参数与 source/target save，并取得 CK3 独占所有权。
4. R692 只执行一个暂停态、只读 steward-candidate private heartbeat；先保存 raw publication，再做 semantic validation。若仍在 harness 层失败，继续保留 harness RED；只有 capability 真正运行并产生结果后，才允许判断 capability GREEN/RED。
5. 验收后记录 R692 轮次所有权、进程创建身份、报告与 manifest SHA-256、cleanup、最终进程 inventory 和存档前后哈希。

当前 open_kaishek 无适配工作：本次没有公共接口或版本组合变化。MCP 通用资产也没有新增或变更；council private probe 仍是未发布的研究/静态能力。该局部 RED 只阻塞 council live observation，不阻塞其他互不依赖的 G2、原版树、MCP 资产或静态实现工作。
