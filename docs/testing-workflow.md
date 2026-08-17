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

## 全自动验收 runner（tools/run_acceptance.py）

一键跑完全流程：备份现场 → **静态 loc 校验** → 同步代码 → 启动游戏过大厅 → 自测规则档驱动全链断言 → 日志判定 → 恢复现场。

```powershell
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py"
```

冷启动通常约 2 分钟，`RESULT: GREEN/RED` + 退出码。判定依据：

1. `tools/validate_loc.py` 静态校验通过（事件选项 wrapper、custom-loc 目标键、全部 88 个 modifier 名在 9 语言 yml 中齐全；resolver 同名静态键视为遮蔽错误）
2. debug.log 的 14 个具名 `XAR: TEST PASS`、`XAR: TEST sweep complete`、零 `FAIL` 及 `DONE` 标记全部出现（自测 effect：`common/scripted_effects/xar_selftest_effects.txt`，
   由游戏规则第三档 `xar_selftest` 触发，检查器 xar.0007 嵌套在结算事件 xar.1001 里跑）
3. 真实打开祝福/诅咒事件，OCR 等到对应标题后验证 ID 0/50/99 三个选项均为不同动态文本、无 raw/fallback，再点击并等待脚本 acceptance marker
4. **error.log 中任何包含 `xar` 的日志都视为失败**，不再白名单过滤

截图证据在报告里的 artifacts 目录。

### 覆盖边界（什么算验过、什么不算）

**验过的**：
- 奖池全部 200 条目的**运行期执行**：自测在死前跑 `xar_test_sweep_effect`（生成器产出，
  每条 code 内联按序施加），带 `xar` 上下文的报错会被 error.log 扫描抓红（drain 修正漏定义就是这样抓到的）
- 引擎解析 + PostValidate 静态校验全部生成文件
- **当前校验范围内的静态 loc 全覆盖**：事件选项名、奖池 custom-loc 目标键、全部 modifier 名在 9 语言 yml 中的存在性，以及六个奖池 wrapper 的精确表达式
- 祝福/诅咒 ID 0/50/99 的简中实际像素渲染与事件选项点击
- 自测链中的契约核心 effect、一个商店价格/扣款样例、抽取、发放、零值导入、死亡结算、纪录写入和教程落盘
- 奖池 200 个 effect body 的运行期语法/引用 smoke test

**没验的**：
- 正常 `xar_on` 路径的契约和商店 UI；当前契约/商店断言是 effect 模拟，不证明事件选项与 scripted GUI 无漂移
- 非零纪录导入及 `xa_shop_pending → xa_local_points`；当前只验导入 0
- 200 项 dispatcher 的 ID→effect 语义映射；sweep 内联执行 effect body，只是运行期 smoke test
- 祝福/诅咒会的 `<3` 返回、拒绝、1095 日重开分支
- 计分各系数与边界的精确总分；当前只断言正分和写入
- AI 双闸门的负例、结算后观察者状态；当前仅静态依赖闸门并保留确认后截图
- 事件标题/描述、GUI `Localize()`、规则和特质的全量 loc 引用扫描；当前 validator 尚未覆盖
- 数值与数据表的一致性（生成器自检 id/权重/语种，但 50 写成 500 这类数据错误测不出来）

### 关键事实（2026-08-17 实证，血泪）

- **游戏加载的是 Steam 工坊缓存，不是仓库 dev 目录**：dev .mod 带 `remote_file_id` 后启动器
  把它和工坊订阅合并，播放集里生效的是 `mod/ugc_3784706360.mod`
  （内容在 `Z:\SteamLibrary\steamapps\workshop\content\1158310\3784706360`）。
  **改完代码在游戏里看不到，先怀疑这个**。runner 每次跑前 robocopy /MIR 仓库 → 工坊缓存
  （用户已批准，不恢复；工坊更新时 Steam 会重下复原）。
- **大厅规则选择持久化在 `player\game_rules\presets.txt` 的 `LastAppliedRules` 块**，新开局重放它；
  改规则文件的 `default` 不影响已有档案。runner 把它里面的 `xar_on` 换成 `xar_selftest`（事后恢复）。
- **pyautogui 合成键盘事件进不了 CK3**（esc/space/+ 实测全部无效），鼠标点击有效。
  解暂停只能点底栏日期旁的 ▶（坐标 (2315,1410)@2560x1440）。
- 每次点击前必须 `win32gui.SetForegroundWindow` 抢回前台（桌面有安卓模拟器抢焦点）。
- 截图读坐标要用 PIL 裁真实 PNG（2560x1440）实测——聊天里显示的图有缩放，目测坐标必歪。
- 暂停链：开局默认暂停 → 死亡弹继承窗（强制暂停，须点「继续扮演」(1455,1130)）→
  结算事件窗硬暂停（「因轮回终结事件暂停」）。runner 用 debug.log 里 AI 日志行自带的
  局内日期（`1066.9.16:` 格式）跟踪时间是否流动，12s 不涨就补点 ▶（像素法有动画噪声，弃用）。
- 大厅路径坐标（2560x1440）：新游戏 (600,560) → 1066 罗贝尔卡 (1600,1230)（有儿子必有继承人）
  → 开始 (2257,1245)。结算确认选项 (1130,1041)（点了进观察者模式，桥有效）。
- 用户真实纪录靠 tutorial.txt 备份/恢复保护；测试基线 = 剥掉 `xar_hs_ge_*` 行（纪录 0）。
- 独立 restore watchdog 等 runner 退出后，只终止 runner 启动的 CK3 PID，再用临时文件 + `os.replace` 原子恢复并做 SHA-256 校验；避免强杀 runner 后游戏继续覆盖用户现场。

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

## 自动化测试 harness（GUI 桥方案，已被 runner 取代）

GUI state + `ExecuteConsoleCommand` 可以在进游戏后自动执行控制台命令（打标记、设变量、触发事件）。注意：窗口必须注册；`ExecuteConsoleCommand` 在 state 的 on_start 里可用性未完全验证（本项目后来改用真实链路测试，最终定型为上文的全自动验收 runner）。

## 排障心法

1. **先分清"没加载/没注册"与"加载了但没触发"**——CK3 大量失败是静默的
2. 报错要看完整调用栈（"while building tooltip/description" 这类后缀说明评估时机）
3. 怀疑优先级：目录名 > BOM > 注册 > scope 类型 > 求值时机（并发/延迟）> 逻辑
4. 对照原版/成熟 mod（POD）的同类写法是最快的验证手段
