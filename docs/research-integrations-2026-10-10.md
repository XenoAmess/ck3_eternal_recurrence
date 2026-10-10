# 2026-10-10 旧研究分支的主线整合

本页收录 dynastic movements、heresiarch mechanics 与 living saints 三条共享历史分支中，主线原先缺失且仍可复用的研究。版本、SHA、调查方法及未完成的实机边界以各专题为准；本次仅整合已有文档，没有新增游戏行为或验收事实。

| 专题 | 用途与边界 |
|---|---|
| [宝物历史文案](artifact-history-modding.md) | 1.19.0.6 静态资料：原生历史条目字段、本地化模板与自定义 GUI 的边界。 |
| [侧室子女宣称继承](ck3-1.20.0.3-concubine-claim-inheritance.md) | 1.20.0.3：强宣称转为子女弱宣称的通用资格，区分侧室子女与未合法化私生子。 |
| [群雄割据的朋党清理链](ck3-1.20.0.3-dynastic-cycle-movement-persistence.md) | 1.20.0.3：成员标记、参与组资格、阶段参数与 GUI 各自的职责。 |
| [保留朋党的修改方案](ck3-1.20.0.3-dynastic-cycle-movement-mod-changes.md) | 理论方案；没有实施，也不能恢复已经被清空的旧成员。 |
| [生前封圣与光环](ck3-1.20.0.3-living-saints-and-halo.md) | 1.20.0.3：正常获取路线、herald/saint 区别及肖像条件。 |
| [枢机投票刷新](ck3-native-ai/cardinal-election-refresh-1.20.0.3.md) | 1.20.0.3：调度周期、候选重建、既存 ballot、定向重算；[静态证据](ck3-native-ai/evidence/cardinal-election-refresh-1.20.0.3.json)。 |
| [食人样本机制](research/shiren-1.19.0.6-static-analysis.md) | 第三方 1.19.0.6 样本的属性、特质、遗骨、成长与收藏循环；不恢复旧整包覆写。 |
| [单次处决诊断](research/shiren-1.19.0.6-single-execution-analysis.md) | 历史故障推断与入口拆分方案；精确远端胜出的文件仍未查明。 |
| [宣战迁移](ck3-native-ai/ck3-1.20-declarations-migration.md) | 补回主线战争外交专题已引用的 .2 原生枚举、interaction context 与 command 生命周期。 |
| [事件与待答互动迁移](ck3-native-ai/ck3-1.20-event-interaction-migration.md) | 补回 .2 原生窗口布局、命令和历史 fixture 证据边界。 |
| [军事命令迁移](ck3-native-ai/ck3-1.20-military-command-migration.md) | 补回 .2 raise/move/split/merge/disband 调用链及 F17/F18 历史结果，不提升为 .4 验收。 |
| [更新前冻结](ck3-pre-update-baseline-and-cleanup-2026-09-30.md)、[根目录清理](z-drive-root-cleanup-2026-09-30.md)、[旧 runtime 清理](z-drive-runtime-cleanup-2026-09-30.md) | 压缩保留历史统计、存档身份及manifest→object查找映射；不恢复旧shell、永久保留或当前可读性声明。 |

可复用的 [升级差异采集器](../tools/capture_ck3_update_diff.py) 恢复七目录/八后缀的逐文件 SHA added/removed/changed 清单，并仅复制新增或变化数据及重读校验；其 [安装身份辅助模块](../tools/freeze_ck3_migration_metadata.py) 只保留 `digest/identify/save_json`，不恢复旧会话、源码树和1.19 capability冻结入口。未来运行前仍须执行统一存储策略的任务开始及重型写入前检查；本次未运行采集器。

相同来源的 [异端创始人](ck3-1.20.0.3-heresiarch-mechanics.md)、[礼仪分裂与复合](ck3-1.20.0.3-rites-split-and-reunion.md) 已在主线，无需重复恢复。旧拜占庭征服者静态检查由 [1.0.1 实机加载调查](byzantium-867-conqueror-v1.0.1-live-review.md) 继续承接。

旧分支的 1.20.0.2 原生实现已由主线保留并扩展为多个 exact-build adapter；没有用旧版本替换现有生产入口。Kaishek 已正式拆到独立仓库，原父仓源码不重新 vendoring；入口见 [项目总览](project-system-overview.md#111-open_kaishek开发者可见的独立开源脚本工具链)。日报及能力状态继续以自动玩家统一进度入口为准，本页不恢复旧报告中已经改变的授权或完成状态。
