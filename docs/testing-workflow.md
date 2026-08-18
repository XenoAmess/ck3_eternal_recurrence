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

runner 共用同一套现场备份恢复、静态校验、工坊同步和 OCR 大厅导航。`selftest`、`persistence-restart`、`death-edges`、`bargain-reopen`、`progression-ui`、`scoring-matrix` 加载开发树；四个生产 smoke 会先生成 production-only release 投影，再将该投影 `/MIR` 到工坊缓存后启动 CK3。

```powershell
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py"
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario on-first-life
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario on-recorded
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario on-high-budget
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario off
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario persistence-restart
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario death-edges
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario bargain-reopen
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario progression-ui
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\tools\run_acceptance.py" --scenario scoring-matrix
```

场景基线与边界：

- `selftest`：默认场景，保持原有完整死亡/计分/UI 全链；只有此场景读取 `--import-record 0|100`。
- `on-first-life`：固定 `xar_on` + 纪录 0，真实接受契约，OCR 验证 `xar.0010` 的「未燃之世」及「前世余烬」「余烬位阶」，再进入祝福窗口即结束，不触发死亡。
- `on-recorded`：固定 `xar_on` + 纪录 100，真实接受契约，验证生产商店（优先补充 100 点 OCR 证据；标题与 `shop event fired` 同时证明非首世分流），不购买商品，直接开始此生并进入祝福。
- `on-high-budget`：固定 `xar_on` + 纪录 2000，在默认成长 + 100% 下 OCR 确认 2000 预算，翻到第四页真实购买 250 分恐怖值和 500 分正统性服务，返回第三页购买 1133 分宗教改革，断言余额 117、一次性选项消失，再进入祝福。
- `off`：固定 `xar_off` + 纪录 0，进局后观察 30 秒；契约标题或本次新增的任意 `XAR:` 启用日志均判 RED。
- `persistence-restart`：一次外层备份内启动两个 CK3 进程。A 从纪录 0 跑完整 selftest 并真实写入非零 lesson，进程树完全退出后固定 handoff SHA-256；B 不调用纪录预置函数，以新日志 offset 断言 importer 精确命中 A 的位阶及 request/ready/consumed 全链。该场景禁止非零 `--import-record`。
- `death-edges`：固定 selftest + 导入位 1，真实杀死带 `xa_enabled` 的 AI Roger，断言生产计分被 `is_ai=no` 阻断；再逐日使当前继承人失去继承资格，直到 `player_heir` 不存在后真实杀死玩家，验证前向提交链、原生继承窗内的八值结算、无“继续扮演”、退出确认和返回主菜单。随机原生事件会由 recovery 点击底部选项后继续日 tick。
- `bargain-reopen`：固定 selftest + 导入位 2，但不进入主 selftest。独立 bootstrap 调用生产契约/运行初始化，随后真实点击三轮 `xar.0004` 祝福与 `xar.0005` 咒痕；安全 wire id 只由 acceptance instrumentation 固定，祝福/诅咒仍走生产 dispatcher。每轮成交后保留生产 option 的 `xar.0006 days = 1095`，另设仅观察状态的 day-1094 probe；脚本保存成交时的 `current_date` 并在两条路径相减，断言累计对数 1/2/3、session 在祝福后为 1 且 `xar.0006` 重置为 0、XP `0→1→2→3`、拒绝数 0、1094 日不重开、1095 日精确重开及第三对后的完整新窗口。runner 用鼠标选择速度 5，并以底栏渲染日期 OCR 判断游戏是否仍在推进；debug marker 只负责机制断言，合成键盘不参与。
- `progression-ui`：固定 selftest + 导入位 3，通过玩家限定 acceptance 编排依次调用生产贤王契约进度 effect，真实点击 3/6/10 三个生产里程碑事件；随后调用两次生产成交 effect 达到【琉焰之视】10 XP 并点击其生产里程碑事件。runner 要求 `tutorial.txt` 精确稳定为该契约的 PB 3/6/10 与完成四个 lesson，再从原生决议打开账簿，同帧 OCR 确认当前 `0/10`、历史 `PB 10`、贤王图鉴、`R 1` 与 `S 0`。该场景不伪造 PB、图鉴或里程碑状态，acceptance 只负责安全地产生生产入口所需的玩家行为。
- `scoring-matrix`：固定 selftest + 导入位 4，先保存历史角色的生产计分与只读 preview 基线，再创建受控谱系：同一后代经兄妹两条路径可达、另一支穿过已故第一代延伸到第五代，并额外创建第六代排除项。跨事件边界后要求新增宗族/家族计数恰为 7、头衔桶不变、临时去重 flag 全清、preview 增量为 1.4 且与生产总分误差不超过 0.01。随后 200 个 wire ID 逐一调用生产 apply dispatcher；每个实际命中的分支自行写 marker，下一事件再断言 100 次祝福计数、代表修正、最终稀有度和 100 XP 已提交。
- 每次运行都写 `report.json` 与 JUnit `report.xml`；JSON 包含 run ID、UTC、版本、Git SHA、release-tree SHA-256、CK3/平台/Python 环境、场景、结果、artifact 清单、各阶段秒数和错误原因。即使中途失败，也会先恢复现场再写 RED 报告。`tutorial.txt`、`presets.txt` 与 `save games/autosave*.ck3` 备份位于独立临时目录，恢复后删除，不进入 artifacts；手动命名存档不移动。

普通场景冷启动通常约 2 分钟；`bargain-reopen` 还要在速度 5 下实走 9 个游戏年，预计整场约 16-22 分钟，随机原生事件多时更长。所有场景都输出 `RESULT: GREEN/RED` + 退出码。判定依据：

1. `tools/validate_static.py` 通过：六套生成器逐文件 parity、全部运行文件 UTF-8 BOM、9 语言 loc 引用与首世/账簿格式 token parity、自动发现的全部 XAR event/decision AI 闸门、挑战继承/成长基线、契约 hook/PB/图鉴/里程碑、生产/selftest 共用入口、21 个购买 effect、无继承人 fallback/原生继承窗投影、奖池过滤/权重/稳定 ID、descriptor 与发布资源；其中 `tools/validate_loc.py` 负责动态 wrapper、custom-loc 和 modifier 名。
2. debug.log 的 57 个具名 `XAR: TEST PASS`、`XAR: TEST sweep complete`、零 `FAIL` 及 `DONE` 标记全部出现（自测 effect：`common/scripted_effects/xar_selftest_effects.txt`，
   由游戏规则第三档 `xar_selftest` 触发，检查器 xar.0007 嵌套在结算事件 xar.1001 里跑）
3. OCR 真实接受契约、购买外交、结束商店，再依次真实点击重抽、拒绝、祝福、封印、第二次祝福和最终咒痕；验证动态文本无 raw/fallback，并断言 token 消耗、拒绝基线、封印免除效果及封印后的正常咒痕。
4. 从原生右栏进入决议面板，真实执行【琉焰账簿】并关闭，断言快照生成和五个临时 global 清理；随后真实执行【选择本世契约】并选择【征服者】，断言生产 effect 写入契约。
5. 通过 acceptance-only GUI 直接调用 `DefaultOnCharacterClick(GetPlayer.GetID)` 打开玩家原生人物页，以 DDS 模板定位【琉焰之视】，hover 后 OCR 确认“当前分量”实时渲染。
6. 结算确认后必须从原生 HUD OCR 到「正在观察」，证明观察者切换真实完成。
7. **error.log 中任何包含 `xar` 的日志都视为失败**，不再白名单过滤。

截图证据和 JSON 摘要在控制台报告里的 artifacts 目录。

### GitHub 官方 CI 与本机 L1-L3

`.github/workflows/static-ci.yml` 只使用 GitHub 官方 `windows-latest`。每次 push/PR 都安装最小静态依赖并执行 Python 编译、`validate_static.py`、计分 reference vectors 和 `build_release.py --check`；手动触发或 `v*` tag 时额外构建并上传 ZIP/manifest，tag 构建仍要求 clean worktree、HEAD 上存在 `v<version>` tag。

官方 runner 没有 CK3、Steam 授权、工坊缓存、用户目录或可靠交互桌面，因此禁止调用 `run_acceptance.py`，也不能把云端 L0 表述成引擎或 UI 已验。官方 CI 能证明生成器 parity、BOM/loc、玩家/AI 闸门、release allowlist、acceptance 剥离和构建可复现；不能证明 Paradox 运行时语义、跨存档落盘、鼠标/OCR 或游戏日期推进。

真实游戏层在本机串行执行并保存 artifacts：

- L1：`off`，production release 投影冷启动、引擎解析及禁用规则负例。
- L2：`selftest`、`persistence-restart`、`death-edges`、`bargain-reopen`、`progression-ui`、`scoring-matrix`，覆盖 57 项机制断言、200 effect body 与 200 dispatcher runtime sweep、两进程持久化、AI/无继承人死亡边界、三轮生产交易的 1094/1095 日边界、PB/图鉴/里程碑生产链，以及受控后代去重/深度/死亡中间节点计分。
- L3：`on-first-life`、`on-recorded`、`on-high-budget`，覆盖 production-only 首世、已有纪录和第四页高预算真实 OCR/点击。L2 的交易 UI、决议、trait hover 和无继承人窗口也计入整体 L3 证据，不重复启动。

本机报告必须记录 JSON/JUnit、截图、runtime hash 和本次增量 `debug/error/gui_warnings`；发布 QA 引用具体 run ID，不把未运行的远端 CK3 状态写成 GREEN。GitHub tag artifact 只提供经过 L0 验证的候选 ZIP/manifest，不自动创建 GitHub Release 或上传 Steam。

### 覆盖边界（什么算验过、什么不算）

**验过的**：
- 奖池全部 200 条目的**运行期执行**：自测在死前跑 `xar_test_sweep_effect`（生成器产出，
  每条 code 内联按序施加），带 `xar` 上下文的报错会被 error.log 扫描抓红（drain 修正漏定义就是这样抓到的）
- 引擎解析 + PostValidate 静态校验全部生成文件
- **当前校验范围内的静态 loc 全覆盖**：event/custom-loc/GUI/trait/rule/modifier 引用、奖池目标键与五个 wrapper 精确表达式，均检查 9 语言。
- 生产契约接受、商店外交购买与结束、祝福三选一、诅咒二选一的简中实际像素渲染和点击。
- 商店样例的扣款 `200→175`、整数价格 `25→30`、纯脚本小数涨价 `11→14`、外交增长，以及余分换金币。
- 契约事件与纯脚本 selftest 都调用 `xar_enable_player_pact_effect`、`xar_initialize_run_state_effect`；外交生产 option 与 `25→30`/扣款脚本样例都调用 `xar_buy_diplomacy_shop_item_effect`。静态校验禁止两处重新内联对应实现。
- 14 个可重复购买商品和宗教改革/三种高价批量商品/三种冠冕服务各自调用具名生产 effect；166600 点自测先购买原四种固定商品并断言余 5467，再购买重抽、封印和三种冠冕服务并断言余 3217、代币涨价和所有权。商店结束调用 `xar_finish_shop_effect` 完成余分兑换、清零及垂青会初始化。
- 原生 trait track 的 100 XP/10 级、每对 +1 XP、满级状态及 hover 当前分数的实际像素渲染；hover 公式还与死亡结算值作脚本断言。
- 生产里程碑 effect 在 10/20 XP 发放早期单枚代币，30-100 XP 逐步升级为重抽/封印组合，并同步增加原生属性；selftest 精确断言 30 XP 奖励和 40-100 XP 累计奖励。UI 真实消耗重抽与封印，并验证拒绝未发祝福、封印未施加首个咒痕、下一次正常接受施加了咒痕。
- 传说祝福只抽到稀有/传说诅咒、拒绝每次 -1% 最终分、request/ready/consumed 零值导入、同阈值不破纪录、跨阈值破纪录、cap 量化、死亡结算、纪录写入和教程落盘。
- 0/25/50/100% 继承的生产 effect；1200、5000、50000、166600 四档均实机脚本断言无额外预算封顶，2000 production-only UI 场景覆盖第四页冠冕服务和 1133 分宗教改革。AI 兄弟 scope 还会实际调用契约进度和导入消费 effect，确认 `is_ai = no` 在运行期阻断。
- 奖池 200 个 effect body 的运行期语法/引用 smoke test
- 静态验证首世 0 纪录分流和 selftest 200 点优先分支，并逐阈值校验账簿 candidate/next/gap 生成关系、cap 状态、七个展示字段及禁止写纪录/资源的边界；纯脚本自测直接调用生产 `xar_prepare_ledger_effect`，断言非负分数、投影关系和历史纪录不变后清理临时 global，不打开账簿 UI。
- 原生决议面板实际点击【琉焰账簿】和【选择本世契约】：账簿 UI 验证只读快照及关闭清理，契约 UI 验证确认页、`xar.2000` 和【征服者】生产选项。
- 账簿生产 UI 用三个连续事件分别捕获即时分数、投影阈值、复制显示快照；2026-08-18 实机证明只用一个或两个事件会让同一 `immediate` 的读后写依赖产生 `none`，三阶段链为 0 `xar` errors。
- `persistence-restart` 两进程实测：A 写入非零余烬 lesson 后完全退出，B 在 `process_b_preseeded=false` 且 `tutorial.txt` handoff SHA-256 不变的前提下导入同一位阶；JSON 记录两 PID 生命周期对应的耗时、位阶和 hash。
- 真实 AI 死亡负例：目标明确带 `xa_enabled`，引擎 `on_death` observer 确认死亡，但 `XAR: computing score on death` 在 AI 区间内未出现且分数 sentinel 未变。无继承人链验证 `player_heir` 确实为空、计分/写位与快照按前向事件边界提交；OCR/像素覆盖八项数值、无「继续扮演」、原生退出确认及主菜单。最新 GREEN：`xar_accept_fmq_wxxc`，0 `xar` errors。
- 独立 `bargain-reopen` 开发树场景覆盖生产一场一对语义：三轮真实 options/dispatchers、累计对数 1/2/3、session `1→0`、XP `0→1→2→3`、拒绝数 0。每轮 acceptance-only day-1094 probe 与生产 `xar.0006 days = 1095` 都用 `current_date - 成交日` 分别精确断言 1094/1095，三个生产 reset marker 必须有序且第三次确实打开下一场。2026-08-19 首次完整 GREEN：`xar_accept_ue4ye_un`，九游戏年、三次生产 reset、0 `xar` errors。
- 独立 `progression-ui` 开发树场景覆盖生产贤王 3/6/10 和【琉焰之视】10 XP 事件的正文、选项与真实点击；四个 tutorial lesson 必须精确落盘，原生账簿必须同帧显示当前 `0/10`、`PB 10`、贤王已完成、`R 1`、`S 0`。2026-08-19 首次完整 GREEN：`xar_accept_gqppgi_f`，图鉴 mask 16，0 `xar` errors。
- 独立 `scoring-matrix` 开发树场景实测 1–5 代计入、第六代排除、同一后代双路径只计一次、穿过已故中间节点后继续计分、清理不对 dead scope 执行 flag effect，并比较 preview/生产误差。全部 200 个稳定 wire ID 还会逐一穿过生产 dispatcher，结合冻结语义契约证明 ID→effect/filter/weight 映射。2026-08-19 GREEN：`xar_accept_h0lgmvyf`，200/200 marker，0 `xar` errors。

**没验的**：
- 数值是否符合最初产品意图仍需人工平衡审阅；冻结契约能阻止未审阅的 `50→500` 或 ID 重排，但不能证明首次冻结前的设计值天然正确。

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
- 速度 5 也必须走鼠标：原生 `timeline_widget` 最右侧 `speed_5` hitbox 中心约 `(2536,1418)@2560x1440`。2026-08-19 对照截图与原生 `hud.gui` 实测：该按钮只执行 `SetGameSpeed`，不会解除手动暂停；但关闭运行中弹出的原生事件会自动恢复时间，此时再点 ▶ 反而会暂停。`bargain-reopen` 现 deliberate-click 速度 5 后先观察底栏日期 2 秒，仅在尚未前进时 deliberate-click OCR 识别出的日期按钮，最终要求日期在 10 秒内前进才视为成功。
- 每次 OCR/点击前必须抢回并反证 CK3 前台。2026-08-19 实测裸 `SetForegroundWindow` 会因 Windows 前台锁静默失败，runner 随后把 OpenCode 整窗识别成事件选项；现通过 `AttachThreadInput` + Alt 前台许可重试，并要求 `GetForegroundWindow()` 精确等于 CK3 句柄，否则立即 RED，不再截取或点击其他应用。
- 主菜单【新游戏】也必须 deliberate-click 并以罗贝尔书签实际出现作反证；2026-08-19 实测 OCR 找到按钮后的一次瞬时点击可被 CK3 丢弃，runner 若直接进入 30 秒书签等待只会在原主菜单超时。
- 安全软件通知也可能置顶遮住大厅“开始”按钮；runner 等待该按钮时会 OCR 识别并点击通知的“忽略”，只关闭当次提示，不改软件设置。
- 截图读坐标要用 PIL 裁真实 PNG（2560x1440）实测——聊天里显示的图有缩放，目测坐标必歪。
- 长测日期 12 秒不推进时禁止盲点固定坐标。runner 每次用单调递增序号保存 `stall_<场景>_<序号>.png`、候选框标注图和完整 OCR JSON：在画面下部先找左侧内容栏中的真实选项；没有左侧候选时才兼容右侧全宽布局，并在候选栏中优先同一 x 轴纵向堆叠的最下行。点击后必须观察到日期继续推进；连续三次仍卡住立即 RED，并由执行者读取这些截图/OCR 分析，不能继续空点到总超时。2026-08-18 实测定位：全宽事件【摆脱尘世】的选项约在 `(0.68,0.79)`，旧恢复点 `(0.38,0.72)` 落在正文空白处。2026-08-19 【诺曼人的西西里】实测三个真实选项纵向对齐在 `x≈930`，人物名位于 `x≈1377/1841`，按右侧优先会误开人物面板；【埃玛成年】仅有一个左侧选项 `x≈930`，人物名/关系则纵向对齐在 `x≈1505`，不能只按列密度判断。同期实测 `debug.log` 在无事件时可长期没有日期行，不能用它单独判断冻结；长测改读底栏 `公元 Y年M月D日` 的实际像素。
- 暂停链：开局默认暂停 → 死亡弹继承窗（强制暂停，须点「继续扮演」(1455,1130)）→
  结算事件窗硬暂停（「因轮回终结事件暂停」）。runner 用 debug.log 里 AI 日志行自带的
  局内日期（`1066.9.16:` 格式）跟踪时间是否流动，12s 不涨就补点 ▶（像素法有动画噪声，弃用）。
- 大厅路径坐标（2560x1440）：新游戏 (600,560) → 1066 罗贝尔卡 (1600,1230)（有儿子必有继承人）
  → 开始 (2257,1245)。结算确认选项 (1130,1041)（点了进观察者模式，桥有效）。
- 用户真实纪录靠 tutorial.txt 备份/恢复保护；默认 selftest 与 `on-first-life/off` 会剥掉 `xar_hs_ge_*` 行（纪录 0），`on-recorded` 固定预置 100；`--import-record 100` 仅改变 selftest。
- 独立 restore watchdog 等 runner 退出后，只终止 runner 启动的 CK3 PID，再用临时文件 + `os.replace` 原子恢复并做 SHA-256 校验；避免强杀 runner 后游戏继续覆盖用户现场。2026-08-19 实测发现 dev selftest autosave 会让下一次 release 投影扫描已剥离的 `xar_selftest` 规则键并误报；现启动前先完整复制并校验全部 `autosave*.ck3`，写 ready 标记后才移走，结束时删除测试 autosave 并恢复原件。
- `--artifacts-dir` 只创建调用方给定的新目录；CI 上传只包含从本次日志 offset 起的新内容，严禁用 `%TEMP%\xar_accept*` 通配上传，因为 `xar_accept_backup_*` 可能含玩家现场。
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
