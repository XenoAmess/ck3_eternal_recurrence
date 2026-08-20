# CK3 Mod 知识库索引

本目录沉淀琉焰卿的永恒轮回开发过程中验证过的机制与教训。除文内明确标注“源码证据”“待实测”或“未查明”的项目外，结论均经过 1.19.0.6 日志或游戏内验证。

## 机制篇

- [cross-save-persistence.md](cross-save-persistence.md) — **跨存档全局存储的完整方案**（本项目核心）。通道排查结论、教程位机制、读写架构、分层阈值编码、限制与扩展
- [gui-system.md](gui-system.md) — GUI 系统：scripted_widgets 注册、动画 state（trigger_when/on_start）求值规则、数据上下文作用域、scripted_gui 执行链
- [on_actions-events.md](on_actions-events.md) — on_action 覆盖/合并行为、开局钩子选择、effect 与事件的并发陷阱、延迟事件的 root 失效
- [variables-scriptvalues.md](variables-scriptvalues.md) — 变量体系：global_var 的读写上下文差异、save_scope_value_as 显示链路、script value 数学
- [testing-workflow.md](testing-workflow.md) — 实测流程：debug_mode 启动、日志断点标记法、tutorial.txt 验证、GUI 可视化调试面板
- [acceptance-runner-latency.md](acceptance-runner-latency.md) — 场景测试 runner 暂停弹窗延迟：按场景量化瓶颈、证据边界、两级恢复与验收建议
- [courtier-creator.md](courtier-creator.md) — 付费自定义廷臣 v2：七页生成目录、数值步进、动态来处、玩家隔离状态与原子扣金（CK3 1.19.0.6 实机 GREEN）
- [autonomous-player-agent.md](autonomous-player-agent.md) — 排队中的长期工程：不作弊的 CK3 高分自主玩家、视觉驱动、经验记忆、大模型复盘与持续多局优化
- [workshop-publishing.md](workshop-publishing.md) — **创意工坊发布**（启动器上传器）：物料清单、picture 路径解析、预览图 1MB 限制、remote_file_id 内外层之别、更新流程

## 玩家篇

- [scoring-rules.md](scoring-rules.md) — **完整算分规则**（逐条分列，README 只放链接；实现本体在 `common/scripted_effects/xar_effects.txt`）

## 语法篇

- [grammar/](grammar/README.md) — CK3 Paradox 脚本语法梳理与踩坑合集
