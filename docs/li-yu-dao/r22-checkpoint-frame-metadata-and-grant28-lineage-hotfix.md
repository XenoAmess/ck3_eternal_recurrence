# R22 checkpoint frame metadata 与 grant28 lineage 实际恢复

2026-10-07，本机 R0022 从原 R10 `0240-detach-second-post-save` 冷载，加载 source HEAD `776818162eaac6925e01ea9e25ec23547dc2d615`、CK3 `1.20.0.4` / Steam build `25734779` / EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。ROOT 在同一游戏、Client/native session 与 lease 上完成两处外置 Python 修复，没有重新启动、重发 SAVE 或改写原 SDK/native 证据。当前基线获得完整 G2 与 headless G3、87 项 typed protection 匹配；`actual_pass=null`、`formal_mandate_credit=null`、`strict_formal_reader_executed=false`。本结果不授正式签署、新宗教 Title、C3、I4 或全产品通过信用。

本次 canonical 工作在 ROOT 确认正常 UI 闭场、owned helpers 原 HANDLE/exec 关闭及 CAS 释放后，才于独立源码树接入以下两叶。native/DLL 来源仍按实际加载 HEAD 记录，Python 热修覆盖层独立标识；不会把热修追记为本场曾加载的新 native HEAD。

## 两个原始 RED 与最小修复

1. 第一次 materializer 在建目标目录、读取存档正文之前返回 `QualificationError: checkpoint business field changed played_character`。真实 SAVE 的 `snapshot_before.played_character.event_trait_membership.snapshot_revision=1`，after 为 `2`，分别对应各自 native frame；日期、actor、traits 等业务字段不变。[原执行结果](C:/workspace/ck3_lyd_runtime_20261004/r22-root-baseline-materialize-original-exec-20261007-001/RESULT.actual.json) 为 exit1，1547B / SHA `46f58d41eb13cc1db621e86967e720f9624fa82b2cc675afedacedf1773dc7a8`。
2. CP002 修复 transition 后，materializer 实际 exit0。随后唯一一次旧 author 尝试在 line303、存档正文读取前被 `sdk_artifact_lineage.py` 仅接受 23/24 工具的限制拒绝，实际资格元数据为28工具。[原 author 执行结果](C:/workspace/ck3_lyd_runtime_20261004/r22-root-baseline-hot-author-original-exec-20261007-002/RESULT.actual.json) 为 exit1，1390B / SHA `069b9fc582add42d14f9c4622cec229ae4099630ebb6c5a13a249b937538da1a`。该执行使用旧 `author_output=baseline-author-001`，其 partial 输出保留；不能把执行编号002改称不存在的成功 baseline002。

`reader/checkpoint_transition_v2.py` 仅在私有比较副本中处理 available 的 trait-membership 行：闭合九字段/schema 校验后，严格要求 `snapshot_revision` 为 int 且等于该行所属的 before/after native revision，并校验日期及 played-character ID；随后只将副本的这一 revision 字段归一化以比较业务内容。原始快照及输出 proof 保持原字节/字段。traits、status、schema、game version、EXE、日期、actor 和其余 played-character 内容仍参与比较，其他全部业务字段及已有诊断 whitelist 不变。缺失或错误 revision 不等于0；unavailable 行不会获得 available 行的归一化许可。

`reader/sdk_artifact_lineage.py` 保留 readonly23、challenger24，新增精确 grant28 名称集合：原 readonly23 + challenger graph + 已实现的 Query/Prepare/Select/Send grant-title-picker 四工具。不是任意28行放行；重复、缺失、替代或未知工具名仍拒绝。metadata descriptor SHA、冻结 G2/G3 完整 Tool schema 校验及 author 原有 actual metadata/native qualification 验证不变。没有改变 reader 的12项 DTO AST、两 build helpers、codec、存档 AST/保护合同或生产业务文件。

| Canonical 叶 | 原 SHA-256 | 修复 SHA-256 |
| --- | --- | --- |
| `checkpoint_transition_v2.py` | `1114a145b2c600c070d2e5326233d6c50bdd7c5e84acded3dc1e2fc44eef5fa3` | `19e59023eb94b6b0f39e265de64e51a4dc5c6cdbad0f1f342f75f57bf26b3ee7` |
| `sdk_artifact_lineage.py` | `b7bcbfc371d7a3f6601f1231aae0e25b96e8d456c71f17d6ddab29d026f7bb37` | `760cfb373d0161b012b804610c3a02dc7e1652550df6e5d13c453094220bddf7` |

## 同场恢复的实际结果与边界

CP003 materializer 沿用原 capture/SAVE/G2/G3 实际引用，只将 INPUT 的 `author_output` 投影为全新 `baseline-author-003`，创建全新 `baseline-author-input-003`；原 INPUT、CP001/002、失败 partial 和全部旧执行回执保留。[CP003 精确源清单](C:/workspace/ck3_lyd_runtime_20261004/r22-checkpoint-author-sourceonly-20261007-003/INDEX.json) 为35379B / SHA `2c177589e3aa0e58d16c7721e20a75009742555c1e1f8cb749a83a98e2d182b8`。

ROOT 随后执行一次成功正文扫描，`save_body_reads=1`，没有第二次扫描或 fixture reset：

| 实际原件 | bytes | SHA-256 |
| --- | ---: | --- |
| [ROOT author 原执行结果](C:/workspace/ck3_lyd_runtime_20261004/r22-root-baseline-hot-author-original-exec-20261007-003/RESULT.actual.json)，exit0 | 1389 | `1f6cebba599cc37eefa5f430d8c9d906198ee41425012c650e227402f3f90adb` |
| [baseline-author-003 RESULT](C:/workspace/ck3_lyd_runtime_20261004/live-attempt-022/baseline-author-003/RESULT.json)，`ACTUAL_COMPACT_NATIVE_SAVED_OBSERVATIONS_JOINED` | 1056102 | `2efe01c4522ab1cec883a2a84e77a06ca454ed17922b711c6f1c8026dde01b8b` |
| [原0240 CONTROL](C:/workspace/ck3_lyd_runtime_20261004/live-attempt-022/ORIGINAL0240-CONTROL.actual.json)，ROOT 验证全部87项 typed protection 匹配 | 1250 | `9755f52a1456c92921ab8f5d156418b8517aa1bf5c1647e2a26f78bfabd0d3bc` |

CONTROL 分别绑定 INPUT、RESULT、STATE、TYPED-PROTECTION 与 QUALIFIED-NATIVE 的实际 SHA；STATE 与 native-qualified 文件不能互换为同一哈希。91MB 原存档继续在外置 runtime，未收入 Git。原 materializer/author RED 不被此次基线恢复覆盖。正常 UI 闭场与原 helpers/CAS operational 清理另由当次闭场归档记录；本专题不授游戏原 HANDLE、typed normal-exit 或 autosave 绿色信用。

## Canonical 定向回归

新增 `tests/test_checkpoint_observation_metadata.py` 与小型 JSON fixture；fixture只保留真实 R22 actor/frame 和新增五个 Tool 的 JSON 投影，运行仍使用已有 inert checkpoint/provenance，不访问 SDK、进程、CK3 或存档正文。测试覆盖 before/after 分属 revision、NULL/bool/wrong-frame 拒绝、真实 traits/actor/stress/date/schema 变化拒绝、原快照不改写，以及精确23/24/28集合、未知/缺失/重复名、G2 schema 与 SHA 拒绝。

2026-10-07 独立树基于实际 `origin/master=77c11406a3630f5d9fa168dc3f51179af5b802e7`，新增8项与原8项相关回归共16项一次执行通过。[完整原执行输出](C:/workspace/ck3_lyd_runtime_20261004/r22-checkpoint-canonical-integration-20261007-001/FOCUSED.original-exec.json)。未重跑实际正文/native fixtures/旧全量测试。首次独立 checkout 的历史超长路径失败原件保留，后继短路径 sparse checkout 在编辑前已确认 exact HEAD/clean；主树不被该准备修改。发布严格沿 fetch→rebase→定向复测→普通 push，无 merge/force。下一实际构建与冷载继续绑定届时完整新 source/export/native/metadata，而非沿用旧 DLL 或外推本次基线结果。
