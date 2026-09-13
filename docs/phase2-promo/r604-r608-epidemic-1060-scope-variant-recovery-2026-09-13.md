# R604–R608 `epidemic_events.1060` 作用域变体恢复（2026-09-13）

## 验收边界

- T0 P1 保持 `9/9 GREEN`；本轮没有重跑或改写 P1。
- T0 P2 保持 `0/8`。R605–R608 只完成前四个连续 clean spans，失败 take 不拆分计数。
- 最终宣传片硬锁继续生效；本轮只采集 P2 源录像，没有制作、更新、发布或预热最终成片。
- R608 的真实原版事件合同漂移被保留为 RED。修复仅接纳 exact-build 定义允许且 R608 实见的一个作用域变体。

## 连续 take 与进程处置

artifact 根：

`Z:\ck3_mod_rewrite\_runtime\p2-capture-r604-plus-e68cf74-20260913`

| 当前/旧轮次 | PID | 用途与处置 |
|---|---:|---|
| R604 | `190744` | frontend warmup；frontend 后终止 |
| R605 | `31052` | gameplay spans 1–2；clean end 后终止 |
| R606 | `34276` | manager governance span 3；clean end 后终止 |
| R607 | `78304` | promotion compensation span 4；clean end 后终止 |
| R608 | `129788` | HC/Workforce source；遇到原版事件合同 RED 后终止 |

连续 FFmpeg PID `72124` 已在 cleanup 停止。最终 CK3、FFmpeg 与 injector 清单均为空，protected storage 未变化。

| 文件 | SHA-256 |
|---|---|
| `capture-plan.json` | `7A85568362ADBB5A32A4D1B09DE4FB84AB94CCB97DB0694EF9B99647D54C15CD` |
| `capture/report.json` | `8AF53648F558E7B4B9C491D1EA57DCDD3146E55A1FED25523BE4EE935085E862` |
| HC native event wait gate | `092451C4F9B2006982922F0D953790197FBC98A8938C6B2D0822E67BF8C8D82F` |
| `capture-timeline.json` | `14CB77D388FA4AB348E78AB6E1B74E22ED062834653F1EE2C50158E9827D3175` |
| raw MKV | `BD0AE9EBCBAC7AAA2D17365DACACA42503D0F4FECF495632AA3111F24FAA60B6` |

原始 MKV 为 `326,805,944` bytes。时间线包含前四段的八个 clean marks；HC、Projects、Incidents、Endgame 四段未完成，所以 `clean_capture_complete=false`。

## 实机顺序与 RED

R608 在 RED 前完成的 reviewed 路径为：

1. 原版 `ep3_story_cycle_admin_eunuch.8030` authored 4/native 3 GREEN；
2. Central `zg361p2c.2` authored 1/native 0 GREEN；
3. 产品 `zg361.40` authored 1/native 0 GREEN；
4. 原版 `epidemic_events.1060` 因新增 `faith_to_blame` 作用域而 fail-closed。

失败 frame 为 instance `624`、date `53368992`、root/player `32904`、snapshot revision `124`。保存作用域精确为：

- `epidemic: epidemic`（raw type `50`）；
- `epidemic_scope: epidemic`（raw type `50`）；
- `story_scope: story`（raw type `17`）；
- `faith_to_blame: faith`（raw type `13`）。

画面只渲染 native 1/2；authored option count 仍为 3。旧合同只接纳前三个作用域，因此同时在 `saved_scope_count` 与 `saved_scope_names_exact` 保留 RED，没有点击选项。

## exact-build 原版审查

冻结版本为 CK3 `1.19.0.6`，EXE SHA-256 为 `2D00FF3101EF70B566F2FCBA292F09263199C80E9DC8F139B82D7D96F83DB86`。

- 定义：`events/dlc/ce1/epidemic_events.txt` lines `1722-1995`，SHA-256 `FEF2972BD4F778818CD3A414C337D036F5132C1598FEBAB0E2623E0252DB7A1E`。
- 直接调用池：`common/on_action/ce1_on_actions.txt` 的 `epidemic_ongoing_events`，SHA-256 `96B42FA1A542836171A2A608B7155A8A80D30B0D8F8D9742EBE8AFF231B85E16`。该池 `chance_of_no_event=95`，`.1060` 权重为 `100`。
- immediate 先创建 plague-witch-hunt story；随机归罪于动物、人物特质或宗教少数群体。只有宗教少数群体分支调用 `select_scapegoat_faith_effect` 并导出 `faith_to_blame`，所以 R608 的四作用域形态是原版合法分支。
- native 0 只在极高虔诚时可见；native 1 接受持续十年的 rampant witch trials；native 2 令审判减缓十年且不派生新事件。原有 authored 3/native 2 安全选择对四作用域变体仍成立。

宗教域仍按项目约束暂缓。这里仅把 `faith_to_blame` 当作不透明的 typed identity，用于关闭当前真实事件合同；没有扩展通用 faith/doctrine/tenet 策略。

## 最小通用资产补丁

提交 `19828ebf312abe8c0504f34c1288e57eaf03d455` 完成以下工作：

- 保留原有三作用域 base contract；
- 新增一个必须精确包含 `faith_to_blame: faith` 的四作用域 `scope_variants` 项；
- 保持 authored 3/native 2、rendered native tuple `(1, 2)` 和其他门禁不变；
- 将 exact-build 来源、调用链、选项语义和 R608 artifact 写入共享 vanilla-event query 资产；
- 对错误的 `faith_to_blame: character` 继续 RED。

聚焦验证：合同测试普通/optimized 各 `1/1` GREEN；embedded-A 通用事件资产测试 `13/13` GREEN；公共 `query_vanilla_event_knowledge_v1` 可序列化并返回 R608 证据及 authored 3/native 2；`py_compile` 与 `git diff --check` GREEN。

本包没有修改 mod、DLL、游戏文件、启动参数、加载顺序、MCP schema/version 或公共接口。它更新了已有 MCP 通用事件知识的数据内容，不触发 open_kaishek 兼容层代码变化。

## 下一步

下一次 CK3 启动为新轮次 R609 warmup。只运行一轮新的连续八段 P2 source capture；若出现新 RED，仍按真实事件 SOP 做一次最小审查与聚焦修复，不扩大为全注册表审计或单 bug 永久长跑。
