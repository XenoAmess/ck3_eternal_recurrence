# R4 实际冷载错误修复候选

本包只在外置目录施工。R4 原输入、失败日志和更早 98 项证据保持原样；修复后的游戏冷载与正式授权流程均为 **NOT_RUN**。102 项通过只证明离线模型、实际模板布尔树及生成结构。

根代理只需合入 `candidate/mod_li_yu_dao/tools/` 下报告列出的四个变更文件：两个模板、`school_consent_model.py`、`test_school_consent.py`。生成器本体未变；根统一生成 runtime。完整 I3 已负责共享 factory/hooks，正式 `build_outputs(..., include_shared=False)`，不要重复加载本包历史共享模板。新 runtime 没有新增原生调用或修改授权、nonce、选举、玩家同意、费用及冷却门禁。

## 两项修复

`lyd_c2_same_main_doctrines_trigger = { TARGET = <Faith scope> }` 在来源 Faith root 调用。它检查双方实际 main_rite 存在，用全局 `any_doctrine` 枚举寻找双方 `main_rite.rite_has_doctrine = prev` 的任一差异，存在差异便拒绝。这是 **LYD 主流有效 Doctrine 集合双向相等的保守门禁**，不是不存在的原生 `has_same_core_doctrines` 接口，也不宣称精确等同引擎内部迁移规则。双方学派不同三核心 Tenet 保留，由实际跨 Faith 分歧 `<100` 管；未把 Tenet 名称送入 Doctrine 比较。

类型源分开：原版 `doctrine_types/_doctrine_types.info:1–5` 定义 Doctrine 类型，`tenet_types/_tenet_types.info:1–5` 定义 Tenet 类型。LYD 36 项定义只在 `tenet_types`；保存的目录键集合和原件 SHA 可独立复核。原版 `pam_interactions.txt:18270–18276` 已使用 `any_doctrine` 加 `rite_has_doctrine = prev` 比较不同礼仪。此为静态原版用法依据；新冷载仍须验证全局枚举在新增 36 Tenet 输入下的实际类型和结果，不能用静态类型文档替代实机。

分歧查询的 trigger 先将真实 `var:lyd_c2_target_main` 保存为临时 Rite scope，再使用固定 `"divergence(scope:lyd_c2_native_target_main)" < 100`。正式 commit 在首个退休／迁移操作之前再显式保存同一捕获 Rite 为事件 scope，后置也只查该固定 scope。quoted 参数中已没有 `$ACTOR$` 或 `.var:` 路径。原版 `00_religious_triggers.txt:2529` 提供固定已保存 scope 的数值函数用法；`passive_rite_learning_triggers.txt:5–16` 提供 trigger 内临时 scope 绑定。

保守门禁会拒绝双方主流 Doctrine 任意差异，包括领袖教义不同。这不是静默更改教义来促成合流；该类情况应保持拒绝并展示原因。原生迁移 setter 的实际行为、最终 head/main/rite 图后置及后续自动分离仍要 R5 验证。

## 证据与验证边界

- `candidate-report.json`：四文件前后 SHA、102 项结果与 NOT_RUN 状态。
- `evidence/diffs/`：逐文件文本差异。
- `evidence/tests.stderr.bin`：实际 102 项测试原输出。
- `evidence/render-report.json`：14 个 C2 runtime 的精确 SHA；未生成 I3 共享文件。
- `evidence/native-interface-source-boundary.json`：本轮 Program Files (x86) 源根、1.20.0.3、七份原版所读文件 SHA、定义目录 SHA 和类型边界。
- `evidence/native-source/`：有行号的精确内容摘录及本轮 LYD Tenet 原件。
- `evidence/r4-failed-error.log`、`evidence/r4-failed-debug.log`：退出后复制的 R4 失败日志；不把失败 attempt 改写成功。

旧研究中 `has_same_core_doctrines` 的可执行性被 R4 实际 Unknown trigger 否定。需要在新报告追加勘误、降权旧 API 推断；保留旧报告和提交原样。本次修复不声称零 error.log GREEN。

R5 最小验证：冷载确认旧 Unknown 与 quoted divergence 参数编译错误消失；进真实 campaign，读回 fixture 的双方主流 Doctrine 兼容值与实际跨 Faith pair divergence；同教义、不同 Tenet 的完整授权可继续至真实 setter，并读回图与资源后置；双向任一 Doctrine 差异须拒绝，无地玩家未同意与旧 nonce 回调仍不得实施。原生跨 Faith 分歧、所有生命周期和完整三轮正式玩法不由本包离线测试授予 credit。
