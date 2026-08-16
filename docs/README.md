# CK3 Mod 知识库索引

本目录沉淀琉焰卿的永恒轮回开发过程中验证过的机制与教训。所有结论均经过 1.19.0.6 实测（日志/游戏内验证），非推测。

## 机制篇

- [cross-save-persistence.md](cross-save-persistence.md) — **跨存档全局存储的完整方案**（本项目核心）。通道排查结论、教程位机制、读写架构、分层阈值编码、限制与扩展
- [gui-system.md](gui-system.md) — GUI 系统：scripted_widgets 注册、动画 state（trigger_when/on_start）求值规则、数据上下文作用域、scripted_gui 执行链
- [on_actions-events.md](on_actions-events.md) — on_action 覆盖/合并行为、开局钩子选择、effect 与事件的并发陷阱、延迟事件的 root 失效
- [variables-scriptvalues.md](variables-scriptvalues.md) — 变量体系：global_var 的读写上下文差异、save_scope_value_as 显示链路、script value 数学
- [testing-workflow.md](testing-workflow.md) — 实测流程：debug_mode 启动、日志断点标记法、tutorial.txt 验证、GUI 可视化调试面板

## 语法篇

- [grammar/](grammar/README.md) — CK3 Paradox 脚本语法梳理与踩坑合集
