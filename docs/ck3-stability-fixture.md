# 跨 mod 的长期稳定性夹具

`tools/ck3_stability_fixture/` 将长期角色游玩中反复出现的事件选项、战争结果窗口和普通存档续接整理成可配置工具。
它供原有 operator 使用：不会启动、接管或连接 CK3，不创建第二个 SDK、driver、session 或 pipe，也不领取或续租屏幕。
产品源码、角色策略、窗口模板、截图、存档和具体测试结果仍在各 mod 的独立项目与外置 attempt 中。

本实现源于外部 mod 百年测试的实际阻点：native event query 超时后，原监督进程仍持有游戏；结果窗口会阻塞自然时间推进。
默认仍按 [operator MCP 合同](operator-mcp.md) 的 MCP-first 顺序执行。只有当前调用路线已有实际失败证据、原 consumer 已停止、
原 operator 继续监督同一 PID 时，才使用本夹具的桌面辅助。不得为了使用它另外启动、附着或重新创建 native consumer。

## 入口和职责

在仓库 `tools` 目录使用已经验证依赖的解释器运行；隔离 worktree 没有相对 `.venv` 时，显式指定并记录主 worktree 的解释器。
依赖为 Pillow；Windows 桌面辅助另需 psutil、pyautogui、pywin32。无需宣传工具链或 OCR。

```text
<verified-python> -B -m ck3_stability_fixture --help
<verified-python> -B -m ck3_stability_fixture route --profile <external-profile.json> --image <closed-original.png> --output <new-route.json>
<verified-python> -B -m ck3_stability_fixture assist --profile <external-profile.json>
<verified-python> -B -m ck3_stability_fixture assist --profile <external-profile.json> --execute --max-actions 1 --timeout 60
<verified-python> -B -m ck3_stability_fixture verify-chain --manifest <closed-chain.json> --output <new-chain-report.json>
```

`route` 只读已经保存的原图。`assist` 默认只采集和分析；只有显式 `--execute` 才发送按键。默认最多一项，配置已审阅的上限与
命令上限共同约束有限循环，最多 30 项、600 秒。`verify-chain` 只检查已关闭 attempt 的文本 ZIP 存档，不处理正在写入的存档。
CLI 返回 0 表示声明的分析/辅助过程结束；不表示某 mod 通过验收。

| 窗口 | 处理和实证边界 |
| --- | --- |
| 普通事件 | 在已审阅布局内，以实际按钮边框确认连续的 1–5 个物理选项；只对明亮的物理首项发送 `Shift+1`。灰首项不跳到后项。亮字不是 native enabled 查询。 |
| 战争结果 | 核对窗内固定 shell 和唯一关闭按钮的四边。按钮可在配置范围内随正文长度上下移动；仅发送 `Escape`，不选择投降、议和或战争策略。 |
| 地图等待 | 仅当配置的已审阅 map regions 匹配时等待和采集，零输入。map-like 不是日期、暂停、玩家或存活真值。 |
| 未知、歧义、死亡、继承 | 无后续输入，返回 `NEEDS_OPERATOR` 并保留原图；死亡和继承由原 operator 审阅、正常处理及证明存档角色链。显式 `STOP` 模板优先于普通 shell。 |

输入前保存两帧，标题、静态正文、首项/关闭项的亮字或纸面暗字连通分量 mask 用于容差比较，完全不识别语言和字符。
已见普通事件的连续物理按钮边框既有金色也有中性灰，首项亮字判断继续独立执行；正文图示不能凭一段亮字被误当作第六按钮。
普通事件的标题亮字mask可以精确为零，仍要求正文和首项充分可见；两端空mask只作精确相等，正文动画不能释放相同首项动作。
普通事件以标题、首项、布局保守防重，正文动画不能释放旧动作。战争结果必须把静态战争正文纳入身份，避免相同“胜利”标题和
关闭按钮阻止另一个真实结果，同时不能把同一结果重绘当新结果。窗口边框或身份不稳定即停止。

输入后的两帧可能分别是地图与紧接着的新事件，也可能跨两个已知事件。这时只记录 `UNCONFIRMED_PENDING_NEXT_STABLE_ROUTE`，
有限循环的下一次输入必须重新通过独立稳定前置、guard 和跨 attempt 防重；不要求后置两帧硬凑成相同窗口。任一后置未知或歧义仍停止。
只有 `UI_TRANSITION_ROUTING_ONLY`、`UI_DISAPPEARED_ROUTING_ONLY` 或待确认路由这样的图像结论。按键 ACK、窗口消失、日期截图和日志中没有某项错误，
都不产生百年 credit，也不自动写 GREEN。后置出现未知窗口会立即交还原 operator。

## 外置配置

配置是当次产品和机器的输入，不能提交含第三方素材或私有存档的配置到本公共仓库。以下字段由当次现场提供：

```json
{
  "owner": {
    "run_id": "<canonical machine--mod--R number>",
    "repo": "<original owner's clean checkout>",
    "head": "<frozen commit>",
    "pid": 123,
    "process_create_time": 1234567890.0,
    "executable": {"path": "<actual ck3.exe>", "sha256": "<exact EXE hash>"},
    "control": {"path": "<original control/ck3.json>", "sha256": "<hash>"},
    "screen_task": "<existing sole screen owner>",
    "bus_dir": "<installed task bus directory>",
    "bus_cli": {"path": "<reviewed installed CLI>", "sha256": "<hash>"}
  },
  "fallback": {
    "reason": "<actual current MCP failure and why the existing route cannot proceed>",
    "evidence": {"path": "<closed failure receipt>", "sha256": "<hash>"},
    "consumer_handoff": {"path": "<actual original consumer stop receipt>", "sha256": "<hash>"}
  },
  "steam_offline_review": {"path": "<fresh directly reviewed offline receipt>", "sha256": "<hash>", "reviewed_offline": true},
  "evidence_directory": "<new external product/run assistance directory>",
  "normal_save_due_utc": "<original operator's normal Save/Exit deadline with timezone>",
  "reviewed_max_actions": 1,
  "allow_readonly_map_wait": false,
  "routing": {"frame_size": ["<actual raw width>", "<actual raw height>"], "variants": []}
}
```

`consumer_handoff` 必须是原操作者对实际已停止 consumer 的记录，包含 `consumer_stopped=true`、相同 `run_id` 与 `pid`。
工具不生成这份确认，不能用 native query 的失败 ACK 推断线程已停止。Steam receipt 也必须来自当次已直接审阅的新鲜离线画面，
不能由工具依据文件时间、旧图或 client flag 自行制造确认。可选 `git_executable` 用于明确本机 Git 路径。

`routing.variants` 是外置、已经审阅的布局；字段如下：

| 字段 | 合同 |
| --- | --- |
| `id`, `kind`, `reviewed_as` | 稳定布局标识和相同的已审阅种类；种类为 `STANDARD_EVENT`、`WAR_OUTCOME`、`MAP_WAIT`、`STOP`。 |
| `patterns` | 至少两个窗内固定区域，每项含绝对 `path`、文件 `sha256`、原图 `rect=[left,top,right,bottom]` 和可选 `max_delta`（默认 3）。不得包括会动画的地图、人物、窗外阴影。 |
| `identity_rois` | 事件/结果窗口含 `title` 和 `body` 两项，每项含原图 `rect`；纸面暗字正文设 `dark=true`。action mask 由实际首项或关闭按钮产生。 |
| `option_slots` | 普通事件的五个物理槽，从上到下；每项含 `top`、`bottom`、`line_x=[left,right]` 与 `glyph_rect`。first row 必须从实际连续边框确认。 |
| `excluded_slots` | 普通事件受支持五槽之前的已审阅排除区，以成对物理边框检测第六项或更早灰按钮；正文图示的孤立亮字不算按钮，布局歧义继续停止。 |
| `unique_close_button_reviewed` | 战争结果唯一关闭项已经实际审阅，必须为 true。固定位置可给 `action_rect`。 |
| `button_geometry` | 战争结果动态按钮：`search_rect`、实际像素的 `width_range`/`height_range`、`action_inset=[left,top,right,bottom]`。`strips` 的四项为外置 PNG `path`/`sha256`、相对按钮左上角的 `relative_rect` 和可选 `max_delta`。全部四边必须匹配。 |

每个配置 rectangle 必须属于原图的实际宽高；没有自动分辨率推断、历史倍率或截图缩放。PNG crop 的实际尺寸必须等于所声明 rectangle。
生产配置应覆盖本次已见死亡/继承的 STOP 变体，地图模板要含足以排除中心弹窗的区域；无法穷尽的新布局继续交给原操作者。
`tools/test_ck3_stability_fixture.py` 的程序化合成配置提供完整、无游戏素材的数据结构示例，不能当成真实 CK3 布局直接执行。

Windows backend 在每次采集、每次按键阶段核对唯一、新鲜（小于 600 秒）的原 SCREEN lease，exact HEAD 和干净 checkout，
原 control hash、唯一 PID/EXE/创建时间、前台窗口和当前桌面尺寸。它不更新 keeper 序号。按键前请求并读回目标控件 `LANGID=0x0409`，
核对焦点/PID/menu；完整的 32/64 位 `INPUT` union ABI 保含鼠标成员。120 ms 持键供 CK3 实际轮询，部分输入只释放已插入的 keydown，
不补第二次 keydown。无需鼠标输入；原操作者的鼠标兜底仍使用 [统一坐标换算](desktop-coordinate-mapping.md)。

每次 attempt 永久保存 exact profile input、副本、原始 before/after PNG、guard receipt、路由、输入前 intent、按键返回与失败。
动作先 fsync 到跨 attempt 的 ledger，再发送按键；同一不确定动作不自动重发。operator lock 关闭时移入 attempt，失败 lock/attempt 不删除。
升级辅助版本或改用新 evidence directory 时，配置 `inherited_ledgers=[{path,sha256}]`，指向按精确字节保全的旧同格式 ledger；
加载旧动作身份后才允许下一项，不能通过更换工具目录清空不确定输入历史。
正常 Save/Exit deadline 到达只停止辅助，不替代存档和退出；原 operator 必须在自己的 supervisor 超时前正常保存、退出和释放 lease。

## 百年角色与普通存档链

每段真实自然游玩由原 operator 产生普通存档并正常退出，原 keeper 停止后以实际 CAS 释放；冷载时唯一父档必须是上一段的精确字节。
不能以 debug 改日期、observer、强行换角色、旧 mod 的年数或 prelaunch 失败抵扣百年。

`verify-chain` 输入格式：

```json
{
  "schema": "ck3.stability-save-chain.v1",
  "closed_only": true,
  "start_date": "1066.9.15",
  "target_years": 100,
  "game_version": "<exact tested version>",
  "epochs": [{
    "run_id": "<canonical run id>",
    "load": {"path": "<closed parent.ck3>", "sha256": "<hash>"},
    "end": {"path": "<normal saved endpoint.ck3>", "sha256": "<hash>"},
    "retirement": {"path": "<normalized actual retirement.json>", "sha256": "<hash>"},
    "natural_progress_evidence": [{"path": "<actual preserved gameplay evidence>", "sha256": "<hash>"}],
    "natural_succession_evidence": [{"path": "<needed when saved actor changes>", "sha256": "<hash>"}]
  }]
}
```

normalized retirement 仅是各项目对真实原始收据的适配，必须引用并保存原始证据，不能改变它们：
`schema=ck3.stability-normal-retirement.v1`、`run_id`、实际 `pid`、`exit_code=0`、`save_sha256`，以及真实
`normal_save_then_exit`、`process_inventory_empty`、`keeper_stopped`、`screen_released` 四项 true 和 `evidence=[{path,sha256}]`。

扫描器复用现有 `xar_autoplayer.ck3_save_artifacts` 全 ZIP CRC 校验，检查唯一 UTF-8 `gamestate`、metadata 日期/版本、单一
played/current actor 和 player 1，逐段比对日期及父档 SHA。改朝/继承造成 actor 改变时必须另给自然继承证据。
它不解析二进制/raw saves，不推断人物生死或继承关系。结论只有 `CLOSED_CHAIN_TARGET_REACHED` / `CLOSED_CHAIN_INCOMPLETE`，
`stability_result=NOT_GRADED`；引用证据的内容、日志中的致命错误与真实自然玩法仍需原 operator 审阅。

## 验证与来源

必要合成测试在仓库根目录执行：

```text
<verified-python> -B tools/test_ck3_stability_fixture.py
```

无游戏、无桌面输入的测试覆盖 1–5 物理选项、灰首项、额外槽、STOP 优先、未知尺寸/窗口、模板损坏、war body 防重与变高按钮、
ACK 后 unchanged/uncertain action、锁、期限、实际 backend custody 检查、Win32 ABI 和闭合存档日期/父档/角色约束。
后续最小回归另覆盖中性灰边、正文图示、标题亮字缺席、混合后置与下一独立前置、未知后置和精确继承旧 ledger。
它们属于夹具回归，不能替代实机百年或其他 mod 验收。具体首次验证和真实能力边界见
[2026-10-03 富化记录](ck3-native-ai/stability-fixture-enrichment-2026-10-03.md)。
