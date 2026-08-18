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

runner 共用同一套现场备份恢复、静态校验、工坊同步和 OCR 大厅导航。`selftest`、`persistence-restart`、`death-edges` 加载开发树；四个生产 smoke 会先生成 production-only release 投影，再将该投影 `/MIR` 到工坊缓存后启动 CK3。

```powershell
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py"
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario on-first-life
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario on-recorded
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario on-high-budget
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario off
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario persistence-restart
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario death-edges
```

场景基线与边界：

- `selftest`：默认场景，保持原有完整死亡/计分/UI 全链；只有此场景读取 `--import-record 0|100`。
- `on-first-life`：固定 `xar_on` + 纪录 0，真实接受契约，OCR 验证 `xar.0010` 的「未燃之世」及「前世余烬」「余烬位阶」，再进入祝福窗口即结束，不触发死亡。
- `on-recorded`：固定 `xar_on` + 纪录 100，真实接受契约，验证生产商店（优先补充 100 点 OCR 证据；标题与 `shop event fired` 同时证明非首世分流），不购买商品，直接开始此生并进入祝福。
- `on-high-budget`：固定 `xar_on` + 纪录 1200，在默认成长 + 100% 下 OCR 确认 1200 预算，翻到第三页真实购买 1133 分宗教改革，断言余额 67、一次性选项消失，再进入祝福。
- `off`：固定 `xar_off` + 纪录 0，进局后观察 30 秒；契约标题或本次新增的任意 `XAR:` 启用日志均判 RED。
- `persistence-restart`：一次外层备份内启动两个 CK3 进程。A 从纪录 0 跑完整 selftest 并真实写入非零 lesson，进程树完全退出后固定 handoff SHA-256；B 不调用纪录预置函数，以新日志 offset 断言 importer 精确命中 A 的位阶及 request/ready/consumed 全链。该场景禁止非零 `--import-record`。
- `death-edges`：固定 selftest + 导入位 1，真实杀死带 `xa_enabled` 的 AI Roger，断言生产计分被 `is_ai=no` 阻断；再逐日使当前继承人失去继承资格，直到 `player_heir` 不存在后真实杀死玩家，验证同步 fallback 的严格调用顺序与原生 Game Over。
- 每次运行都写 `report.json` 与 JUnit `report.xml`；JSON 包含 run ID、UTC、版本、Git SHA、release-tree SHA-256、CK3/平台/Python 环境、场景、结果、artifact 清单、各阶段秒数和错误原因。即使中途失败，也会先恢复现场再写 RED 报告。`tutorial.txt`/`presets.txt` 备份位于独立临时目录，恢复后删除，不进入 artifacts。

冷启动通常约 2 分钟，`RESULT: GREEN/RED` + 退出码。判定依据：

1. `tools/validate_static.py` 通过：五套生成器逐文件 parity、全部运行文件 UTF-8 BOM、9 语言 loc 引用与首世/账簿格式 token parity、自动发现的全部 XAR event/decision AI 闸门、挑战继承/成长基线、契约 hook/PB/图鉴/里程碑、生产/selftest 共用入口、12 个购买 effect、无继承人 fallback、奖池过滤/权重/稳定 ID、descriptor 与发布资源；其中 `tools/validate_loc.py` 负责动态 wrapper、custom-loc 和 modifier 名。
2. debug.log 的 54 个具名 `XAR: TEST PASS`、`XAR: TEST sweep complete`、零 `FAIL` 及 `DONE` 标记全部出现（自测 effect：`common/scripted_effects/xar_selftest_effects.txt`，
   由游戏规则第三档 `xar_selftest` 触发，检查器 xar.0007 嵌套在结算事件 xar.1001 里跑）
3. OCR 真实接受契约、购买外交、结束商店，再依次真实点击重抽、拒绝、祝福、封印、第二次祝福和最终咒痕；验证动态文本无 raw/fallback，并断言 token 消耗、拒绝基线、封印免除效果及封印后的正常咒痕。
4. 从原生右栏进入决议面板，真实执行【琉焰账簿】并关闭，断言快照生成和五个临时 global 清理；随后真实执行【选择本世契约】并选择【征服者】，断言生产 effect 写入契约。
5. 通过 acceptance-only GUI 直接调用 `DefaultOnCharacterClick(GetPlayer.GetID)` 打开玩家原生人物页，以 DDS 模板定位【琉焰之视】，hover 后 OCR 确认“当前分量”实时渲染。
6. 结算确认后必须从原生 HUD OCR 到「正在观察」，证明观察者切换真实完成。
7. **error.log 中任何包含 `xar` 的日志都视为失败**，不再白名单过滤。

截图证据和 JSON 摘要在控制台报告里的 artifacts 目录。

### 覆盖边界（什么算验过、什么不算）

**验过的**：
- 奖池全部 200 条目的**运行期执行**：自测在死前跑 `xar_test_sweep_effect`（生成器产出，
  每条 code 内联按序施加），带 `xar` 上下文的报错会被 error.log 扫描抓红（drain 修正漏定义就是这样抓到的）
- 引擎解析 + PostValidate 静态校验全部生成文件
- **当前校验范围内的静态 loc 全覆盖**：event/custom-loc/GUI/trait/rule/modifier 引用、奖池目标键与五个 wrapper 精确表达式，均检查 9 语言。
- 生产契约接受、商店外交购买与结束、祝福三选一、诅咒二选一的简中实际像素渲染和点击。
- 商店样例的扣款 `200→175`、整数价格 `25→30`、纯脚本小数涨价 `11→14`、外交增长，以及余分换金币。
- 契约事件与纯脚本 selftest 都调用 `xar_enable_player_pact_effect`、`xar_initialize_run_state_effect`；外交生产 option 与 `25→30`/扣款脚本样例都调用 `xar_buy_diplomacy_shop_item_effect`。静态校验禁止两处重新内联对应实现。
- 12 个可重复购买商品和宗教改革/三种高价批量商品各自调用具名生产 effect；166600 点自测完整购买 1133+10000+50000+100000 后必须余 5467，借命补至 25 层。商店结束调用 `xar_finish_shop_effect` 完成余分兑换、清零及垂青会初始化。
- 原生 trait track 的 100 XP/10 级、每对 +1 XP、满级状态及 hover 当前分数的实际像素渲染；hover 公式还与死亡结算值作脚本断言。
- 生产里程碑 effect 在 10 XP 发放 1 次重抽、20 XP 发放 1 枚封印；selftest UI 真实消耗二者，并验证拒绝未发祝福、封印未施加首个咒痕、下一次正常接受施加了咒痕。
- 传说祝福只抽到稀有/传说诅咒、拒绝每次 -1% 最终分、request/ready/consumed 零值导入、同阈值不破纪录、跨阈值破纪录、cap 量化、死亡结算、纪录写入和教程落盘。
- 0/25/50/100% 继承的生产 effect；1200、5000、50000、166600 四档均实机脚本断言无额外预算封顶，1200 生产 UI 场景覆盖 1133 分宗教改革。AI 兄弟 scope 还会实际调用契约进度和导入消费 effect，确认 `is_ai = no` 在运行期阻断。
- 奖池 200 个 effect body 的运行期语法/引用 smoke test
- 静态验证首世 0 纪录分流和 selftest 200 点优先分支，并逐阈值校验账簿 candidate/next/gap 生成关系、cap 状态、七个展示字段及禁止写纪录/资源的边界；纯脚本自测直接调用生产 `xar_prepare_ledger_effect`，断言非负分数、投影关系和历史纪录不变后清理临时 global，不打开账簿 UI。
- 原生决议面板实际点击【琉焰账簿】和【选择本世契约】：账簿 UI 验证只读快照及关闭清理，契约 UI 验证确认页、`xar.2000` 和【征服者】生产选项。
- 账簿生产 UI 用三个连续事件分别捕获即时分数、投影阈值、复制显示快照；2026-08-18 实机证明只用一个或两个事件会让同一 `immediate` 的读后写依赖产生 `none`，三阶段链为 0 `xar` errors。
- `persistence-restart` 两进程实测：A 写入非零余烬 lesson 后完全退出，B 在 `process_b_preseeded=false` 且 `tutorial.txt` handoff SHA-256 不变的前提下导入同一位阶；JSON 记录两 PID 生命周期对应的耗时、位阶和 hash。
- 真实 AI 死亡负例：目标明确带 `xa_enabled`，引擎 `on_death` observer 确认死亡，但 `XAR: computing score on death` 在 AI 区间内未出现且分数 sentinel 未变。无继承人链验证 `player_heir` 确实为空、计分/写位、fallback、`xar.1001.immediate` 和同步返回；原生 Game Over OCR 到「退出到菜单」且无「继续扮演」。

**没验的**：
- 正常 `xar_on` 首世、已有 100 位阶和 `xar_off` 三条独立 smoke 已实机 GREEN，均为 `xar error.log = 0`。
- 200 项 dispatcher 的 ID→effect 语义映射；sweep 内联执行 effect body，只是运行期 smoke test
- 正常玩法的 1095 日重开分支；selftest UI 已真实点击拒绝、封印和重抽，但为缩短验收将重开压缩为立即触发。
- 计分各系数与边界的系统矩阵、后代去重边界；当前断言正分、拒绝倍率、preview/结算一致与写入
- PB 图鉴及里程碑事件仍没有实际像素点击覆盖；其生产 effects、lesson 落盘和事件引用已有脚本/静态覆盖。
- 无 `player_heir` 时计分、写位和 `xar.1001.immediate` 已实机证明同步完成，但 1.19 原生 `confirmation` 层 Game Over **确认完全遮住** `events` 层结算窗；截图只看到「游戏结束」，因此“玩家看到完整结算”仍未满足，不能记为 UI 通过。
- 数值与数据表的一致性（生成器自检 id/权重/语种，但 50 写成 500 这类数据错误测不出来）

### 关键事实（2026-08-17 实证，血泪）

- **游戏加载的是 Steam 工坊缓存，不是仓库 dev 目录**：dev .mod 带 `remote_file_id` 后启动器
  把它和工坊订阅合并，播放集里生效的是 `mod/ugc_3784706360.mod`
  （内容在 `Z:\SteamLibrary\steamapps\workshop\content\1158310\3784706360`）。
  **改完代码在游戏里看不到，先怀疑这个**。runner 每次跑前 robocopy /MIR 仓库 → 工坊缓存
  （用户已批准，不恢复；工坊更新时 Steam 会重下复原）。
- **大厅规则选择持久化在 `player\game_rules\presets.txt` 的 `LastAppliedRules` 块**，新开局重放它；
  改规则文件的 `default` 不影响已有档案。runner 会先移除该块内全部 `xar_on/xar_off/xar_selftest`，再写入场景目标值并验证同时只剩一个（事后恢复）。
- **pyautogui 合成键盘事件进不了 CK3**（esc/space/+ 实测全部无效），鼠标点击有效。
  解暂停只能点底栏日期旁的 ▶（坐标 (2315,1410)@2560x1440）。
- 每次点击前必须 `win32gui.SetForegroundWindow` 抢回前台（桌面有安卓模拟器抢焦点）。
- 安全软件通知也可能置顶遮住大厅“开始”按钮；runner 等待该按钮时会 OCR 识别并点击通知的“忽略”，只关闭当次提示，不改软件设置。
- 截图读坐标要用 PIL 裁真实 PNG（2560x1440）实测——聊天里显示的图有缩放，目测坐标必歪。
- 暂停链：开局默认暂停 → 死亡弹继承窗（强制暂停，须点「继续扮演」(1455,1130)）→
  结算事件窗硬暂停（「因轮回终结事件暂停」）。runner 用 debug.log 里 AI 日志行自带的
  局内日期（`1066.9.16:` 格式）跟踪时间是否流动，12s 不涨就补点 ▶（像素法有动画噪声，弃用）。
- 大厅路径坐标（2560x1440）：新游戏 (600,560) → 1066 罗贝尔卡 (1600,1230)（有儿子必有继承人）
  → 开始 (2257,1245)。结算确认选项 (1130,1041)（点了进观察者模式，桥有效）。
- 用户真实纪录靠 tutorial.txt 备份/恢复保护；默认 selftest 与 `on-first-life/off` 会剥掉 `xar_hs_ge_*` 行（纪录 0），`on-recorded` 固定预置 100；`--import-record 100` 仅改变 selftest。
- 独立 restore watchdog 等 runner 退出后，只终止 runner 启动的 CK3 PID，再用临时文件 + `os.replace` 原子恢复并做 SHA-256 校验；避免强杀 runner 后游戏继续覆盖用户现场。
- `ToggleGameViewData('character', GetPlayer.GetID)` 可能保留地图当前选中角色；要确定打开玩家本人，直接用原版 `button_me` 同款动作 `DefaultOnCharacterClick(GetPlayer.GetID)`（2026-08-18 实测）。
- trait 含原生 `track` 时，UI 会自动读取 `gfx/interface/icons/trait_level_tracks/<trait_key>.dds`；缺文件会在真正 hover 时写 VFS error，主 trait 的 `icon =` 不会替代它（2026-08-18 实测）。
- 原生决议右栏按钮是 `F8` 对应的羽笔图标；合成键盘无效时可按屏幕比例 `(0.987, 0.367)` hover，先 OCR 验证“决议”tooltip 再点击。低处条目必须在滚动框内下滚到中段后用 `deliberate_click`，否则底缘 hit-test 会关闭面板但不选中。决议触发的事件关闭后，决议面板会自动恢复，不要重复点右栏按钮（2026-08-18 实测）。

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
