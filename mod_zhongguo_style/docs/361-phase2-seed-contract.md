# 361 二期 MCP-only 存档种子合同

状态（2026-09-01）：仓库中的固定种子合同是
`blocked_seed_generation_required`，不是 ready，也不是 production-live 证据。它可以作为
旧存档来源账本，但不得启动二期正式批量验收。权威机器合同是仓库根的
`tools/zg361_phase2_seed_contract.json`。

## 已纠正的旧存档身份

旧合同把事件保存作用域里的上司误当成事件 root：

- 来源运行：
  `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-worktrees\v0.4-main_process_assets\zg361\runs\zga_20260830_191131_7e82d061`
- `report.json` 的 `witnessed_result_identity` 中，事件 `zg361.4` 的
  `root_scope.typed_identity.character_id` 是 **29037**；这才是当时实际扮演的历史角色
  `han_6875`。
- 同一窗口的 `saved_scopes[name=zga_reviewing_superior]` 是 **32904**；它是上司
  `han_8052`，不是玩家。
- `cell/10_phase2_witnessed_result_identity_01_prequery_pause_gate.json` 也绑定玩家
  CharacterID 29037；`cell/10_phase2_result_accept_speed_one_gate.json` 的
  `starting_character_id` 同样是 29037。
- 原版 `Crusader Kings III/game/history/titles/e_china.txt` 的 1066 段把
  `k_hedong` holder 绑定为 `han_6875`。

因此旧合同现声明 `date_raw=53147016 / CharacterID=29037 / han_6875`。旧 autosave
不是 typed `save-checkpoint` ACK 的产物，日期仍只是待验证的来源假设。

## 为什么旧存档不能继续冒充 ready

该存档早于现有 B1、B2、Incident、Workforce 产品状态。当前 runner 又需要五个真实
selector：B2、Incident、Workforce 三个 received-self owner，以及 AI-owned B1 case
的 owner/direct-subject。旧 MCP 没有枚举这些关系的通用查询，旧 artifact 也没有捕获
这些五项。故机器合同的 `domain_query_matrix` 目前精确保留五个 `null`；blocked 合同
允许 `null`，ready 合同必须五项都是正 int32 CharacterID，且 owner 不能是玩家、
AI owner 不能等于 subject。禁止填假 ID 只为让 loader 通过。

旧 save、报告与索引仍保留如下来源信息：

- save：52,902,730 bytes，SHA-256
  `98687d21fe816a4a42d1d6bef85cea9d8a0ed9e74d53cdeadf653b0d3a57ecb3`；
- product tree：`ddac4703...`，fixture tree：`e2c092a4...`；两者只作 provenance；
- 当前代码加载后仍必须用 mount inventory、loaded-feature manifest 和 paused MCP
  snapshot 验证当前 runtime，不能用 OCR 猜测。

## 最小 MCP-first bootstrap

专用外部 fixture 位于
`tools/fixtures/zg361_phase2_seed_bootstrap/`。它与普通
`tools/fixtures/zg361_acceptance/` 分离，只有 seed-generation acceptance 可以挂载，
发布构建和宣传运行时永远不能加载。它没有 decision、GUI、角色/头衔/关系创建命令，
也不直接写任何 `zg361_*` 产品变量、receipt 或 Workforce history。
seed-generation profile 应把此树单独复制到既有外层 mod ID
`zga_acceptance_fixture.mod` 的目标目录；不得与普通 acceptance fixture 同时合并，且
candidate runtime 中记录的是本专用树的实际 SHA-256。

流程如下：

1. 从旧存档继续，fixture 只接受真实历史玩家 `han_6875` 与其现存直属 AI 天朝上司。
2. 在 manager-root 隐藏事件中调用 shipped B1、Incident X、Workforce public entry；
   若旧存档确有真实已交付 3.25 result，则在 player-root 隐藏事件中调用 shipped B2
   adapters。缺少前置事实时 shipped effect 自行 no-op，fixture 不补造输出。
3. 打开唯一可见事件 `zga_phase2_seed.1`。该事件保存：
   `zga_phase2_b2_owner`、`zga_phase2_incident_owner`、
   `zga_phase2_workforce_owner`、`zga_phase2_ai_owned_owner`、
   `zga_phase2_ai_owned_subject`。
4. MCP 调 `query-current-event-window-context-v1`，严格读取 root 与五个 typed character
   scopes，并保存同帧 paused/map-ready 玩家 snapshot；不使用 OCR。
5. MCP 选择唯一的 `select-event-option-1`，要求 postcondition ACK，然后调
   `save-checkpoint`。
6. `tools/zg361_phase2_seed_bootstrap.py` 验证事件定义、scope 唯一性、真实正整数 ID、
   paused snapshot、close ACK、checkpoint path/size/SHA/date/player，并保留原始四份
   JSON、report、index
   与 candidate contract。helper 永远先输出 blocked candidate；selector 捕获不能替代
   四个产品 provider 的状态证明。

已有 native session runner 可直接调用 helper 的 `capture_mcp_evidence(service,
artifacts)`：它只使用现有 `snapshot`、`query_current_event_window_context_v1`、
`select_event_option`、`save_checkpoint` 四个 MCP 方法，严格保持“同帧查询 → 唯一选项
关闭 ACK → paused checkpoint”的顺序；它不负责启动 CK3、lobby 或视觉导航。

完成一次 MCP 捕获后的物化命令为：

```powershell
& "tools\.venv\Scripts\python.exe" "tools\zg361_phase2_seed_bootstrap.py" `
  --event-context "<run>\event-context.json" `
  --paused-snapshot "<run>\paused-snapshot.json" `
  --event-close "<run>\event-close.json" `
  --checkpoint-response "<run>\save-checkpoint.json" `
  --profile "<isolated-profile>" `
  --output-dir "<new-empty-run-dir>" `
  --source-git-commit "<40-hex-commit>" `
  --product-tree-sha256 "<64-hex-product-tree>" `
  --fixture-tree-sha256 "<64-hex-seed-fixture-tree>"
```

fixture/loader/helper 的静态验收：

```powershell
py tools/test_zg361_phase2_seed_fixture.py
py -O tools/test_zg361_phase2_seed_fixture.py
py tools/test_zg361_phase2_loader_stage.py
py -O tools/test_zg361_phase2_loader_stage.py
py tools/test_zg361_phase2_seed_bootstrap.py
py -O tools/test_zg361_phase2_seed_bootstrap.py
py tools/test_run_zhongguo_promo_capture.py
```

这里的普通模式承载 fixture/bootstrap 脚本中的语义断言；对应的 `python -O` 命令只作
导入与运行时兼容性 smoke，不把断言移除后的结果当成额外业务证明。seed preflight
会对 loader、bootstrap、fixture 三个脚本分别执行普通与 `-O` 两种模式，再允许进入
投影检查；任一模式失败都保留静态 RED。

## attempt 07：不是“再等一会”，而是 loader parser RED

冻结运行
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-seed-attempts\phase2_seed_20260901_042407_head_48fbe07_attempt07`
在 bridge transport 已连接后等待了 `900s`，但 `8,916` 次 typed observation 全部为
`semantic_snapshot_temporarily_unavailable`。CK3 `debug.log` 在 `04:26:53` 停止，最后阶段仍是 database/script
初始化；没有出现健康基线已有的 `Setting idler 'Frontend'`、`Setting idler 'Load Save'` 或
`Setting idler 'In Game'`。因此这不是 event selector、MCP 查询或普通超时问题，`-continuelastsave` 也尚未获得执行到
frontend 的机会。

同一现场的只读重放由 `tools/zg361_phase2_loader_stage.py` 归并出 `30` 个去重后的已实证 fatal：

- `16` 个可由同一行 `events/zg361_*` 路径归属的非法生成事件注册（原始日志另有 `17` 条数字 ID `>=10000` 报错；
  最后一条 `52750` 本身不带 source path，因此 early-fatal allowlist 不单独采信；物理文件中每个 ID 只定义一次）；
- `6` 个 manager-governance `value/add/multiply` 被当成 trigger 的 parser 错误；
- `5` 个 career-HC `TICKET_SUBJECT` 未声明参数错误；
- `3` 个 Workforce `revoke_court_position` 缺少 effect block 的错误。

重放 artifact 是
`artifacts/attempt07-loader-stage-replay.jsonl`，SHA-256
`7687E389A75F0800B52AA64693C5375ED17FC926813CCF49A7042F28EEAAFCAE`。它同时记录 `9` 个 theme warning，
但 theme-only 不会触发 `loader_parse_red`。seed 的唯一可见事件 `zga_phase2_seed.1` 已显式增加
`theme = stewardship`，静态 fixture test 会阻止回归。

冻结证据的关键哈希为：`runner-report.json`
`319A3A3419DB77D1349F12CA8450281597612F15E23856268E1ED17E678D2ECE`、cleanup
`C656193A80A7A7E5AAA8CB77EC5C0EC7B18BA3DC1258EBF5FE055413E214011F`、原始 event wait JSONL
`2452104F92E75406ABAB3524AF6955D5292F3B15E8F583F959A5C9B01D838DE9`、`debug.log`
`50F1D64E14684AE13AE7497C2061601BB781281062762684BCC4EAFDF05C3112`、`error.log`
`C59845A20BA424211DF3187D497256B559B667329BEB8023AAB1FB9B3F4D030A`。重放文件是追加型证据，已有文件不得重复运行再追加。

双挂载也已排除：`debug.log` 对 product 与专用 seed fixture 各只有一次 `Mounted Data`，两棵树都是普通目录；上述超限 ID
在生成文件中各只有一个顶层定义。CK3 对非法 ID 随后报告同路径 “Duplicated event ID” 是非法注册恢复噪声，不是 VFS
把 product 挂了两次。bridge hello/build/PID/heartbeat 正常，而 main-thread mailbox 一直 `installed=false`；在应用从未越过
database init 时，这只能说明 native hook 尚未到达可安装阶段，不能反向归罪 provider。

后续 seed runner 必须先调用 `wait_for_phase2_seed_loader_stage(log_dir, progress_jsonl, ...)`。它只读 CK3 的 append-only
`debug.log/error.log`，自身也只追加 JSONL；不会读取 runner 正在 atomic-replace 的 partial report。日志若在 database init
静止且存在上述 allowlist 中的 mod parser/compiler error，默认 quiet `45s` 后以 typed `loader_parse_red` 结束并保存去重错误，
不再空等 `900s`。只有进入 `Load Save` / `In Game` 或 native semantic readiness 后，才可启动
`zga_phase2_seed.1` event waiter。仅到 Frontend 而未开始 Load Save 时应另报 `save_resume_red`；theme-only 只继续等待，不能冒充
fatal。

loader gate 还轮询受管 `native_session` supervisor 的只读 terminal probe。supervisor 在 session report/error
写入后才置 `session_done`；若 CK3 提前以非零码退出，gate 立即追加 `native_session_process_exit`（保留完整
`session_report`、`exit_reason`、`process_exit_code` 与当时日志 hash）并结束本轮，不把已知进程崩溃拖成
`loader_stage_timeout`。无论该 typed RED 或其它 loader RED，runner 仍进入同一受管 cleanup，并单独保存
`09_phase2_native_session_cleanup.json`；这条早停只改善诊断时延，不把 RED 提升为 live readiness。

后续 exact-build 私有只读证据已证明两条已观察 callback 均正常返回、vector exhausted，且 sequence 2
外层 owner 最终从 `0x88B648` 返回到 `0x3B9CFD2`。因此新 runner 不再把“已有 callback 完成记录但仍未出现
Load Save/In Game/native readiness”归因为 `database_callback_stall`。冻结的完整两节点序列报告
`loader_terminal_missing_after_database_completion_publish`，其它不完整序列才报告一般性的
`loader_terminal_missing_after_database_callbacks`；旧 reason 只以 `deprecated_reason_code` 保留给历史消费者。
这只是修正故障归属，不放宽 `event_wait_authorized`，也不提升 seed/paused/live readiness。
该诊断回链静态合同 `phase2-outer-completion-edge-v1` 及 publish RVA `0x3B9CFD7`；runner 本身不新增内存读取或
production detour。

下一次 CK3 只允许单局验证这一个假设：在所有已实证 parser/compiler/theme 项静态清零后，新 HEAD 是否从
`04:26:53` 对应阶段继续到 `Load Save/In Game` 与 native semantic snapshot。单局顺序固定为：冻结 projection/SHA →
确认 product/fixture 各挂载一次 → append-only loader gate → exact event query → 五 selector 与 paused checkpoint 捕获 →
受管 cleanup。若 loader gate 再次 RED，保留新日志后停止，不增加超时、不启动第二局；只有该门 GREEN 才继续 seed 业务验收。

## 可复用 seed capture runner（static-ready，尚未运行 attempt 08）

attempt 07 的 `run_seed_capture.py` 是冻结现场中的一次性脚本，路径、HEAD、DLL、injector 与 pipe 全部硬编码，且 bridge
transport 连接后直接进入 `900s` event wait。它只属于失败现场，**不得重跑或改写**。仓库内的新入口是
`tools/run_zg361_phase2_seed_capture.py`；它以显式参数建立新 attempt，不读取或覆盖 attempt 07：

```powershell
py tools/run_zg361_phase2_seed_capture.py `
  --clean-source "<attempt>\source" `
  --attempt-dir "<attempt>" `
  --artifacts-dir "<attempt>\artifacts" `
  --source-zip "<attempt>\head-source.zip" `
  --git-sha "<40-hex-frozen-HEAD>" `
  --game-dir "<CK3-install>" `
  --bridge-dll "<frozen-bridge>\xar_ck3_bridge.dll" `
  --injector "<frozen-bridge>\xar_ck3_bridge_injector.exe" `
  --pipe '\\.\pipe\xar_ck3_bridge_zg361_<unique-id>' `
  --seed-contract "<attempt>\source\tools\zg361_phase2_seed_contract.json"
```

调用者必须创建一个全新的 attempt；`native-state` 必须不存在、artifact 目录必须为空。runner 拒绝重用非空 artifact，因而
不会覆盖先前 RED。所有 CK3/Python 项目模块都从 `--clean-source` 导入，并验证模块 origin；导入前设置
`PYTHONDONTWRITEBYTECODE=1` 与 `sys.dont_write_bytecode=True`，避免 attempt 07 已实证的 `__pycache__/*.pyc` 污染冻结源码。
preflight 也会拒绝 clean source 中任何既存 `__pycache__`、`.pyc` 或 `.pyo`。
preflight 同时保存：声明 git SHA、source ZIP blob SHA、ZIP logical-tree SHA、解压源码 tree SHA、ZIP/源码逐文件等价结果、旧 save、
CK3 EXE、game rules、bridge DLL 与 injector 的 before hash；CK3 版本和 EXE SHA 还必须等于仓库冻结的 `1.19.0.6` exact-build
合同。bootstrap 声明的 product/fixture tree hash 还必须等于 runner 对实际挂载投影独立计算的 hash，candidate 只采用后者；所有
timeout 必须为有限正数，seed contract 的 `absolute_save` 必须真的是绝对路径。退出时再核对源码树与全部外部依赖 after hash。

实机前可先对同一组冻结输入执行 no-launch 门：在上述参数后追加 `--preflight-only`。该入口只做 config、clean
source/ZIP 逐文件等价、旧 save/CK3/rules/bridge/injector 哈希、exact-build 版本、静态 preflight 与 product/fixture
投影检查；不会启动 `ck3.exe`、native session、driver、HKL watchdog，也不会进入 loader/event waiter。它在
`artifacts/preflight.json` 写入 machine-readable 结果：`result/status/ok=GREEN/preflight-ready/true` 且
`ck3_launch_attempted=false` 时退出码为 `0`；这里的 `status=preflight-ready` 只表示冻结输入与投影门通过，报告固定
`readiness_scope=frozen_inputs_and_projection_only`、`seed_ready=false`，并原样记录当前
`seed_contract_status`（通常仍为 `blocked_seed_generation_required`），不能解读为 seed 或 live capability 已就绪。
任何 blocker 都保留 RED artifact（`status=preflight-blocked/ok=false`）并退出码为 `2`。
每次实机 capture 仍必须使用新的空 attempt/artifact 目录，不能把 preflight 目录直接复用为 attempt 08。
这里的静态门是 seed 专用离线检查（`_run_seed_static_preflight`）；不会调用面向完整 acceptance fixture 的通用
`run_zhongguo_acceptance.preflight`，避免把 seed-only fixture 错判为缺少完整宣传验收夹具。

成功路径的硬顺序为：

1. 把 clean product 与专用 seed fixture 投影到隔离 profile，`enabled_mods` 必须严格等于 product/fixture 各一个；
2. 启动受管 `native_session -continuelastsave`，仅通过 MCP transport 取得 PID/generation；
3. 启动 US-English HKL watchdog。它是唯一的非 MCP 平台操作；以 MCP 返回的 CK3 PID 枚举该进程窗口，直接向其 UI thread
   发送 `WM_INPUTLANGCHANGEREQUEST(04090409)`，不抢前台焦点，也不发送按键、文字、鼠标或游戏命令。至少一份 HKL
   attestation 必须 GREEN；
4. **先**运行 `wait_for_phase2_seed_loader_stage`。database init 出现已实证 parser/compiler allowlist 且日志静止 `45s` 时，
   `01_phase2_loader_stage_progress.jsonl` 原样落 `loader_parse_red` 与去重错误，后续 mount/native/event 均不得执行；
5. loader GREEN 后验证 debug inventory 中 product 与 fixture 各 `Enabled/Mounted` 一次，再运行 native readiness 与完整项目
   `error.log` quiet scan；
6. 最后才进入一个总 monotonic deadline 的 exact `zga_phase2_seed.1` waiter；默认 `300s`，不会按 snapshot unavailable、调速、
   pause/resume 等子状态重置计时；
7. MCP 捕获五 selector、关闭事件、保存 checkpoint、逐项查询四域 provider 并物化 candidate；
8. 无论 GREEN/RED 都停止 supervisor、证明进程 cleanup、关闭 driver、复制并哈希 CK3 logs、复核 mounted runtime/source/external
   dependency unchanged，最后写 `runner-report.json`。

业务操作严格 MCP-only；没有 OCR、屏幕坐标、测试决议或视觉兜底。失败路径追加
`runner-failures.jsonl`，loader 与 event wait 分别使用自己的 append-only JSONL；最终报告只在 cleanup 后落盘。若 source ZIP 与解压
tree 不等价、mount 不是一加一、HKL 从未 GREEN、cleanup/driver close/immutability 任一缺失，则不得得到 GREEN。

离线验收（不启动 CK3）：

```powershell
py tools/test_run_zg361_phase2_seed_capture.py
py -O tools/test_run_zg361_phase2_seed_capture.py
```

fake tests 覆盖显式 CLI 校验、no-launch GREEN/RED 与 launch boundary、ZIP/tree exact hashes、单挂载及顺序、45 秒 parser fail-fast 原样证据、单一 event deadline、
GREEN cleanup/driver/log/immutability、parser RED 后仍 cleanup，以及拒绝重跑时不覆写原失败 artifact。截至本段记录时仅为
`static-ready / fake-tested / not-live`；不构成 attempt 08，也不授权在 parser/theme 静态项清零前启动 CK3。

## 仍不能由 seed fixture 消除的两项产品阻塞

### Incident mixed matrix

2026-09-01 已完成 `static-ready / fixture-tested` 修复：shared `zg361_ip_probe_*` 只作为内部 detector/cache，
X/Y/Z public open 在选择 terminal arm 前分别冻结 10 字段 `zg361_ip_{profile}_probe_*` receipt；native provider
的每份固定 50-key allowlist 已改读相应 profile receipt。同一 paused frame 的 X=N/A、Y/Z=incident 离线 fixture
已经 GREEN，runner 要求的 `{na, incident}` 因而不再是静态不可达合同。

这不等于当前 seed 已 ready：旧 save 没有这些新增 profile receipt；bootstrap 仍只能调用 shipped public entry，
不得直接补写。必须在真实 CK3 中让中央 stage/public entry 生成至少一份 exact N/A 与一份 positive terminal，
再用 MCP 同帧查询三 profile 并保存 raw response。没有 paused artifact 前仍是 `not-live`。

### Workforce 三周期 charter

Workforce ready 必须完整跑三个严格递增真实 review cycle；每周期消费 shipped B1/B2
生成的 #357/#358/#359 receipt，通过 #360 history gate，第三周期才由产品生成 #361
charter。不存在诚实的一键 effect。fixture 只能调用 public entry；直接写 receipt ID、
rolling history 或 charter 输出都属于制造产品证据，禁止。

只有 Incident 合同变为可达、Workforce 三周期真实跑完，且 B1/B2/Incident/Workforce
四个 provider 在新 checkpoint 上独立 GREEN 后，才可把 candidate 改为 `ready` 并进入
一次二期批量实机。宣传视频仍只加载真实产品 runtime，不得出现或挂载这个 fixture。
