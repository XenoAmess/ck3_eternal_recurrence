# 实测工作流程（CK3 mod 调试）

## 启动与日志

```powershell
Start-Process "...\binaries\ck3.exe" -ArgumentList "-debug_mode"
```

日志目录 `Documents\Paradox Interactive\Crusader Kings III\logs\`：

- `error.log` — 解析错误（加载期）+ 运行时脚本错误（带调用栈和文件行号，**最有价值**）。累积式，按时间戳过滤
- `debug.log` — `debug_log` effect 的输出（jomini_effect_impl.cpp:450 前缀，带文件行号）
- `gui_warnings.log` — GUI 警告
- 解析错误在到主菜单前就会全部写入，启动游戏到主菜单即可完成静态验证

## 断点标记法（链路定位）

在每个环节插 `debug_log = "XAR: <步骤名>"`（项目约定 XAR: 前缀），然后：

```powershell
(Select-String -Path "...\logs\debug.log" -Pattern "XAR:").Line
```

链条断在哪一目了然。生成器生成的文件也可以带标记（本项目导入 scripted_gui 每条都带 k 值标记）。

## 运行时行为验证

- 全局存储落盘：直接读 `tutorial.txt` 数 `xar_hs_ge_*` 条目
- 控制台：`die`（死亡链）、`event xar.0001`（手动触发事件）、`effect xxx`（跑 effect）
- 修改后必须重启游戏（无热重载）；`-load` 启动参数实测无效（1.19.0.6）

## GUI 调试

- debug 模式工具栏：`Gui.Debug`、GUI Editor、Script Profiler
- 可视化调试面板：临时注册一个可见窗口，用 `text = "[Tutorial.GetStepText]"` 之类实时显示数据表达式的值（本项目用它发现 Tutorial 上下文在外部窗口为空）
- GUI 表达式解析错误：`error.log` 的 `pdx_data_factory.cpp` / `pdx_gui_factory.cpp` 条目（含文件行号）

## 自动化测试 harness（可选）

GUI state + `ExecuteConsoleCommand` 可以在进游戏后自动执行控制台命令（打标记、设变量、触发事件），实现免手动测试。注意：窗口必须注册；`ExecuteConsoleCommand` 在 state 的 on_start 里可用性未完全验证（本项目后来改用真实链路测试）。

## 排障心法

1. **先分清"没加载/没注册"与"加载了但没触发"**——CK3 大量失败是静默的
2. 报错要看完整调用栈（"while building tooltip/description" 这类后缀说明评估时机）
3. 怀疑优先级：目录名 > BOM > 注册 > scope 类型 > 求值时机（并发/延迟）> 逻辑
4. 对照原版/成熟 mod（POD）的同类写法是最快的验证手段
