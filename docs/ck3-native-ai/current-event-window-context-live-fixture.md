# current-event-window-context-v1：paused generic live 验收夹具

## 当前证据状态

- **[live-confirmed harness RED；not capability evidence]** Attempt1 在事件物化前因 CK3 PhysFS 路径超长退出；
  它只证明 runner 路径故障。
- **[live-confirmed capability RED]** Attempt2 已通过短路径 gate 并真实物化目标事件，但旧冻结 DLL 把
  `CEventOption+0x478 timeout_option` 错当成 cancel 来源，使 authored native index `3` 的
  `is_cancel_option=yes` 发布为 `cancel=false`。因此 Attempt2 当时不得标为 live-ready，fixture 预期也没有降成 false
  来掩盖故障。
- **[live-confirmed harness RED；capability fields passed]** Attempt3 的 seed 与 cold 都精确读到 native index `3`
  `cancel=true`、三个空 typed indicator 子集及 truthful readiness；失败只来自 runner 错把 process/playset-local
  calculated ID/runtime ordinal 当作跨进程稳定 identity。该 RED 不得改写，但它已给出修正验收合同的直接实证。
- **[live-confirmed fixture-scoped GREEN]** Attempt4 复用同一 `cea30a0...` production source 与 fresh DLL/injector，
  在 seed/checkpoint/fresh-cold 两个独立 CK3 进程中通过全部 gate。它闭合 current-window query 的完整 instance、canonical
  key、进程局部数值、物化 presentation/cancel 与**空 typed-indicator surface**；没有闭合 stock event、非空 indicator kind、
  lifecycle、scope、完整 effect preview 或 semantic choice。
- [static-confirmed] runner：
  [`run_current_event_window_context_live_acceptance.py`](../../ck3_autonomous_player/native_bridge/research/run_current_event_window_context_live_acceptance.py)。
- [static-confirmed] focused unit：
  [`test_current_event_window_context_live_acceptance.py`](../../ck3_autonomous_player/tests/unit/test_current_event_window_context_live_acceptance.py)。
- 验收口径必须写成 **fixture-definition/localization playset + production native bridge**。它不是 stock event，cold
  playset 也不是 production-only。

宗教边界不由本夹具扩张。本夹具是 generic、非宗教 character event，不读取 faith/doctrine/tenet/fervor、改宗或改革。
项目所有者只放行了两项与其他 OODA 域绑定的最小例外：战争闭环不得不使用的 holy-war 观测/动作，以及婚姻合法性或
接受度不得不使用的最小 faith 原生调用；这两项均与本夹具无关，也不得扩成通用宗教研究。

## Attempt1/Attempt2 已用冻结输入（历史；不得复用为下一 candidate）

| 项 | 冻结值 |
|---|---|
| CK3 | `1.19.0.6` |
| `ck3.exe` SHA-256 | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |
| consumer/source commit | `aab1daf0a8fd93ec43f29a9f5e9e8a9a6a224335` |
| fresh DLL | `.build-event-definition-identity-v1-msvc/xar_ck3_bridge.dll` |
| DLL SHA-256 | `A6CB88C8F02866A8F5052FE74BCA098A961459079FC1FC9B4F0DC017F915D1C4` |
| injector SHA-256 | `8C972446BF234C15FE5FEB5FC11F0900FE41E3E970242A9F6795E477D26B3FCB` |
| immutable profile | `C:\Users\xenoa\AppData\Local\Temp\xar-war-entry-known-good-profile-control\profile` |
| immutable save | `save games\xar_checkpoint_pre_white_peace_53175816.ck3` |
| immutable save SHA-256 | `5BA2136911EAD0CAF1F7D2F3DE02EAFBD8039861C46F01F35F698B3B5CFFFC5F` |
| fixture event key | `xar_event_window_live_fixture.1` |
| event definition SHA-256 | `CE5416E0BB2D508F5A3445B73EAEEA7D1383727FC465D18486467B4CD58D972E` |
| definition + 9 loc files manifest SHA-256 | `D2B6AC3D39D6362BA905299912BBF91EACF2C90A58DA00D0423E10F237BF3C7A` |

## Attempt3/Attempt4 冻结 binary 输入

| 项 | 冻结值 |
|---|---|
| consumer/source commit | `cea30a067b1e112596d70532b98fa068b2102ebf` |
| fresh MSVC build | `.build-event-window-cea30a0-msvc2` |
| DLL size / SHA-256 | `3,892,224` / `52398435F8AA5177D6D507BFAA38CD2578EB988F0629F1C5E13360CC91FB3BB0` |
| injector size / SHA-256 | `823,808` / `1618840EC108F688B3EBECC6D7F8963038BA64C8D4A3E10DDE2E29E3F443B4DF` |
| fresh native CTest | `37/37` passed |

该 build 从已推送、tracked-clean 的 `cea30a0...` 配置到全新 MSVC/Ninja 目录；不复用 Attempt1/2 DLL。Attempt4 只修正
runner 的跨进程证据合同，不改 production source 或 binary，因此继续要求上述 commit 与两个 hash 精确一致。

## Attempt1 immutable RED：PhysFS 路径超过 250 字符

2026-08-26 的 Attempt1 artifact 固定保留在
`C:\Users\xenoa\AppData\Local\Temp\xar-current-event-window-context-aab1daf-live-attempt1.json`，SHA-256 为
`3B376184260F52CA813009A8D18ACFA83A595FDD7E86CD46E2190A21B7B269D4`。默认 disposable root 是
`C:\Users\xenoa\AppData\Local\Temp\xar-current-event-window-context-80b050946ba74bbc8239ef0faf2a1f56`，长度为 99。
CK3 `error.log` 对 fixture 的 german、korean、french、polish 四个 localization 路径逐条报告
`path is over 250 characters long and will likely cause a crash on open`，进程随后以 code 1 退出；generation marker、
事件窗口和任何 typed query 均未发生。

该 artifact 的 `seed_stage.cleanup.ok=false`，最终 `disposable_cleanup.attempted=false/removed=false/ok=false`，原因是
`managed cleanup unproven for: seed-trigger-query-save-event`；不能把当前 root 仍存在改写成已清理。与此同时
`no_ck3_processes_after=true`（NoCK3），所以 RED 没有遗留 CK3 进程，但这不补足 root cleanup 证明。

最小修复只把默认 `_ROOT_PREFIX` 缩短为 `xew-`，并在创建 root/stage 或启动 CK3 前，按实际 root 枚举 seed/cold
两阶段 descriptor 与 10 个 fixture definition/localization 文件的 Windows 路径，要求最长路径严格小于实证的 PhysFS
上限 250。当前机器的默认 TEMP + 32 位 nonce 下最长 cold `simp_chinese` 路径为 243；如果调用者给出更长的
`--state-dir`，preflight 直接 RED 并要求改用显式短路径。冻结 source commit、DLL、injector 与 fixture bytes 均未改变。

runner 要求 `XAR_EVENT_WINDOW_ISOLATED_SOURCE_ROOT` 指向上述 commit 的独立 source tree。运行依赖由该树加载；runner
文件和最终 artifact 位于工作树外侧也可以。这样不会让验收悄悄消费共享 dirty worktree。生产 singleton verifier
保持原样；fixture 两阶段只复用既有 supervised fixture launch seam，并且只有在 stage-specific playset 的逐字节证明
先通过后才允许进入该 seam。

## Attempt2 immutable RED：cancel ABI 标签错误

2026-08-26 的 Attempt2 artifact 固定在
`C:\Users\xenoa\AppData\Local\Temp\xar-current-event-window-context-aab1daf-live-attempt2.json`，SHA-256 为
`E029135A8B23AA49850F04364864401CD088B60C9F1EFC5E7F9340B2D68F00F1`。路径 preflight 通过，实际最长生成路径
为 243；事件窗口真实物化为 instance ID `17`、canonical key `xar_event_window_live_fixture.1`、calculated ID
`4390001`、runtime ordinal `6831`，materialized authored native indices 精确为 `[0,1,3]`。shown/enabled/name/
reason/fallback 与 rendered/native mapping 全部符合夹具，唯一失败是 native index `3` 的 authored
`is_cancel_option=yes` 被旧 DLL 发布为 `cancel=false`，所以 `_context_proof.materialized_option_shape=false`。
本次没有选择 option；seed managed cleanup、disposable root cleanup 与 `no_ck3_processes_after` 均为 true。

纯静态根因闭合如下：derived parser logical extent `0x25378D0..0x2537D4A` 的三个 token branch 把
`timeout_option/show_unlock_reason/is_cancel_option` 分别写到 `CEventOption+0x478/+0x479/+0x47A`。
`SetupOptions` 在 `0x16CCAF7/0x16CCC64` 测试的是 `+0x478 timeout_option`，因此
`CEventWindowData+0x2C` 是 timeout authored index；真正 cancel 必须经 materialized item 的 authored native index
定位 `EventData` option pointer array，再读 `CEventOption+0x47A`。`+0x47A` 在 name-character custom widget
controller `0x182C3F0` 也有直接 consumer；parser assignment 自身没有 widget gate。

补充 retained-state diagnostic2 使用同一 frozen DLL，再现相同 mismatch，且完整日志证明事件已加载、没有
unknown/`is_cancel_option` parser error；artifact size `61905`，SHA-256
`A0C7CB19D049A44642BF0EBAF2A91BE46A90B67205ED4D96FB69A490899F0360`。它因 retain-state 故意为 RED，只作
辅助证据；主证据仍是 Attempt2 与 exact parser/disassembly。diagnostic1 使用错误 Python、没有启动 CK3，不能作为
能力证据（size `24065`，SHA-256 `27A195A508FB4FAB4225797F3C4D69FC2937D1803EF66427683BF543AF2D892B`）。
两个 diagnostic root、Attempt1 旧 root 后续均经 marker 验证并由 runner `_cleanup_root` 删除；该后续清理不改写
Attempt1 artifact 当时的 `root cleanup unproven` 事实。

## Attempt3 immutable RED：把 process-local 数值误当跨进程 identity

2026-08-26 的 Attempt3 artifact 固定在
`C:\Users\xenoa\AppData\Local\Temp\xar-current-event-window-context-cea30a0-live-attempt3.json`，size `130667`，
SHA-256 `2EF4BF85FB95CDD3D969C36BF79761AA33807C6159373CB27247D5248985D561`。seed PID `73636` 与 cold PID
`12820` 均为 green，完整 event instance ID `17`、date `53175816`、canonical key、逐字节 fixture、三项 option 与全部
readiness 一致；native index `3` 在两侧都真实发布 `cancel=true`，每项 indicator rows 均为空且 coverage 精确。

唯一失败为 cross-stage 的 `same_calculated_event_id=false` 与 `same_runtime_stats_ordinal=false`：seed 因额外加载
seed-only mod bridge，读到 `calculated_event_id=4360001`、`runtime_stats_ordinal=6773`；cold 只加载 production+fixture，
两次相邻 query 都稳定读到 `3940001/5881`。这在相同 save、完整 instance/key 与 byte-identical fixture 下直接证明
`EventData+0x08/+0x0C` 是 loaded definition table 的 process/playset-local 数值，不是 cross-process identity。修正合同必须：

- 跨进程继续要求完整 active instance、date、canonical key、save/checkpoint 与 fixture bytes 一致；
- `+0x08/+0x0C` 在每个进程内仍须为 signed int32，并由同帧/同进程双查询约束不漂移；
- 不要求 seed 与 cold 数值相等，也不要求它们必须不同。

Attempt3 没有选择 option；两个 managed process、nonce root 均清理成功，artifact 的
`no_ck3_processes_after=true`、`disposable_cleanup.ok=true`。它不能升级整体 readiness，但不能被描述成 cancel/indicator
再次失败。

## Attempt4 fixture-scoped GREEN：current window query 冷恢复闭合

2026-08-27 的 immutable artifact 位于
`C:\Users\xenoa\AppData\Local\Temp\xar-current-event-window-context-cea30a0-live-attempt4.json`，size `130779`，
SHA-256 `690EB5EA188B0903281E5F5DFDA343DA795117EE0FB1C83C3FCDC7F572170B7B`，总耗时 `145.062s`，自身分类为
`fixture-scoped-live-confirmed`。全部顶层 readiness gate 与 cross-stage check 均为 true：

- seed PID `22976`、cold PID `43140`；二者不同且均由 managed session 回收；
- date `53175816`、完整 event instance ID `17` 与 canonical key `xar_event_window_live_fixture.1` 跨 checkpoint 一致；
- seed 的 calculated ID/runtime ordinal 为 `3930001/5847`，cold 为 `3940001/5881`；四值均为 signed int32，cold
  相邻两次 query 内完全稳定。这是进程局部 registration metadata 的预期表现，不是 identity 漂移；
- 三条物化 row 的 rendered/native index 为 `(0,0) (1,1) (2,3)`；shown 均为 true，enabled 为
  `true/false/true`，第二条有非空原生 unavailable reason，第三条精确为 `cancel=true`，三条均非 fallback；
- 三条 `effect_indicators` 均为 available，coverage 精确为
  `played-character-event-icon-indicators-1.19.0.6-v1`，`complete_effect_set=false` 且 `rows=[]`；这只闭合空 surface，
  不证明 trait/stress/death/scheme 的非空 row 已实机命中；
- seed transcript 仅为 query/save；cold 仅为 query/query，cold context SHA-256 为
  `6975511D543E3B11953E376AC0CBF256325C3E907123D7F40D42A04BC5FB880A`，两帧除 query sequence 外严格相等；
- checkpoint、cold `autosave.ck3` 与 `last_save.ck3` 均为 `66,594,168` bytes，SHA-256
  `2098104E89BA64845BC49B0E4544C4E933EE3AF5DF5CF1D35CD1EBE9F7A01B45`；immutable source save 的 size/SHA/mtime
  前后不变；
- 没有调用任何 `select-event-option-*` 或 `auto-turn`；seed/cold cleanup、nonce-root removal 与
  `no_ck3_processes_after=true` 全部通过。

因此可以把 **fixture-definition/localization playset + production native bridge** 的 current-window read-only query 标为
`fixture-live`。`readiness.event_definition_identity_ready`、`option_presentation_ready`、`effect_indicators_ready` 在该范围内真实为
true；`effect_preview_ready=false`、`semantic_decision_ready=false`、`root_scope=null` 与 `saved_scopes=null` 仍是必须保留的
未闭合边界。它不是 stock/production-only event 证据，也不是完整事件 OODA。

## 确定性事件物化

immutable checkpoint 本身没有可供本合同消费的 current event。seed clone 因而加载三项：production autoplayer、
已有的 seed-only `mod_bridge`、以及本 runner 临时生成的 event definition/localization fixture。没有新增 OCR、鼠标、
前台窗口控制或新的 GUI transport；`mod_bridge` 仍只复用已验收的 paused `run/xar_mcp_inbox.txt` 轮询入口。

seed inbox 在 local human CharacterID `29829` scope 下执行一次带 global guard 的：

```text
trigger_event = { id = xar_event_window_live_fixture.1 }
```

runner 等待 diagnostic marker、正的完整 active-event instance ID 以及 paused/map-ready/date/player 全部稳定，然后立即把
inbox 恢复为 no-op。它先做一次 typed query，证明真正的 `CEventWindowData` 已物化，再调用 production
`save-checkpoint`。它不调用任何 `select-event-option-N`。

夹具 authored option 故意冻结为下表。九种 localization 目录都使用相同的 ASCII acceptance 文本；这是 disposable
验收占位，不是发布翻译。

| authored native index | 定义 | 预期窗口结果 |
|---:|---|---|
| `0` | 普通有效项 | rendered `0`，shown/enabled，非 cancel、非 fallback，name 精确相等，reason 为空 |
| `1` | `is_ai = yes`，并 `show_as_unavailable = always yes` | rendered `1`，shown 但 disabled，name 精确相等，reason 必须非空 |
| `2` | `trigger = always no`，不要求展示 | 不进入物化 vector |
| `3` | 普通有效项，`is_cancel_option = yes` | rendered `2`，shown/enabled/cancel，证明 rendered/native index 不可互换 |
| `4` | `trigger = always no`，`fallback = yes` | 因已有 regular item，不进入 fallback scan，也不进入物化 vector |

因此预期 native index vector 必须恰好为 `[0, 1, 3]`。每个已物化 row 的 `shown` 都必须为 true；三个 row 的
`fallback` 都必须为 false；这同时验证了当前 regular 路径不会把 authored fallback 冒充已展示项。若未来需要观察
`fallback=true`，应使用另一独立 fallback-only fixture，不能放宽本合同。

## seed → cold 两阶段

```mermaid
sequenceDiagram
    participant I as immutable save
    participant S as seed PID
    participant C as cold PID
    participant B as production native bridge

    I->>S: clone bytes into disposable profile
    Note over S: production + mod_bridge + exact fixture
    S->>S: guarded trigger_event while paused
    S->>B: typed query; no option selection
    S->>S: save active-event checkpoint
    S-->>C: copy checkpoint bytes
    Note over C: production + byte-identical fixture; no mod_bridge/inbox
    C->>B: query current-event context @ revision R
    C->>B: adjacent query @ the same revision R
    C->>C: managed shutdown and disposable cleanup
```

cold clone 必须继续加载相同 definition/localization bytes，否则 save 中的 event definition 无法被诚实解释；但它必须
没有 `mod_bridge` tree、outer descriptor 和 run inbox。两个进程 PID 必须为不同正整数，checkpoint、cold
`autosave.ck3` 与 `last_save.ck3` 必须逐字节相等。immutable source 的 SHA、size、mtime 在前后必须完全相同。

## cold paused 双查询的精确断言

同一个 public revision、native revision、snapshot ID、date、player 与完整 event instance ID 上连续调用两次
`query-current-event-window-context-v1`。允许变化的只有顶层 `query_sequence`，且第二个值必须严格等于第一个加一；
去掉该字段后完整 service result 必须相等，两个 `current_event_window_context` frame 还要直接逐项相等。

每帧必须同时满足：

1. `status=available`、`window_match_count=1`，full instance ID 与 snapshot/binding/envelope 全部一致；
2. `event_definition_key=xar_event_window_live_fixture.1`；
3. `calculated_event_id` 与 `runtime_stats_ordinal` 在 seed/cold 各自都必须是 signed int32；两次 cold query 必须各自
   不漂移，但 seed 与 cold 可因 playset/load order 不同而取不同值。不推断其正负值业务语义，也不把任一数值当
   canonical identity；
4. rendered/native indices 恰为 `(0,0) (1,1) (2,3)`，并按上表逐项验证 shown、enabled、resolved name、
   unavailable reason、cancel 和 fallback；
5. native indices `2` 与 `4` 不在物化 vector；本夹具没有 gameplay effect，每项 `effect_indicators` 必须精确为
   `status=available`、coverage `played-character-event-icon-indicators-1.19.0.6-v1`、
   `complete_effect_set=false`、`rows=[]`；这验证的是空 indicator 子集，不是完整 effect 集为空；
6. 每项 `effect_preview` 必须继续是
   `unavailable/indicator_subset_has_no_completeness_signal`，`resource_deltas` 与 `relationship_deltas` 也必须各自
   `status=unavailable`；`root_scope=null`、`saved_scopes=null`；readiness 必须精确为
   identity/presentation/effect-indicators true，effect preview/semantic decision false，且 service 顶层
   `current_event_effect_indicators_ready=true`；
7. cold command transcript 必须恰好为 query/query。seed native transcript 只允许 query/save；两阶段均禁止
   `select-event-option-*` 与 `auto-turn`。

任一 key、int32、pointer-derived identity、instance ID、revision、option row、reason、readiness 或 fixture byte 漂移都使
artifact RED。runner 不因 unavailable 而选择 fallback，也不提交任何游戏选项。

## 静态测试结果与已执行命令

[static-confirmed] focused unit 覆盖 exact fixture bytes、seed/cold projection、现有 fixture session seam、双查询
frame equality、full-ID/revision drift、key/两 int32/option/readiness/effect/scopes malformed、跨 PID/checkpoint 绑定以及
preflight 不得 launch：

```powershell
py -m unittest ck3_autonomous_player.tests.unit.test_current_event_window_context_live_acceptance -v
```

本轮 runner 合同修正后的 focused suite 为 `17/17`，shared event-window Python suite 为 `17/17`，fresh native CTest 为
`37/37`，`py_compile` 与两个 ABI verifier 均通过；收口检查 CK3 进程数为 0。Attempt2 已执行且是上述
immutable capability RED；旧
`aab1daf...` source tree、DLL SHA 与 injector 只能复核历史 artifact，绝不能再次作为 live candidate。

Attempt4 使用同一 detached clean production source/binary 与独立 pipe/output；不传 `--state-dir`，继续用默认
`%TEMP%\xew-<32-hex>` root 复验 path gate：

```powershell
$env:XAR_EVENT_WINDOW_ISOLATED_SOURCE_ROOT = 'C:\Users\xenoa\AppData\Local\Temp\xar-event-window-cea30a0-source'
& 'tools\.venv\Scripts\python.exe' 'ck3_autonomous_player\native_bridge\research\run_current_event_window_context_live_acceptance.py' `
  --game-dir 'Crusader Kings III' `
  --bridge-pipe '\\.\pipe\xar-event-window-context-cea30a0-attempt4' `
  --bridge-dll 'ck3_autonomous_player\native_bridge\.build-event-window-cea30a0-msvc2\xar_ck3_bridge.dll' `
  --expected-bridge-dll-sha256 '52398435F8AA5177D6D507BFAA38CD2578EB988F0629F1C5E13360CC91FB3BB0' `
  --bridge-injector 'ck3_autonomous_player\native_bridge\.build-event-window-cea30a0-msvc2\xar_ck3_bridge_injector.exe' `
  --output 'C:\Users\xenoa\AppData\Local\Temp\xar-current-event-window-context-cea30a0-live-attempt4.json'
```

上述命令已经成功执行，output 现为 immutable Attempt4 证据，不得覆盖或复用同名 pipe。重跑演示必须使用新的 pipe/output 名；
runner 仍会先验证 commit、EXE/save/fixture/DLL/injector、source cleanliness 与最长路径，任一漂移都在启动 CK3 前 RED。

Attempt4 已满足 artifact `ok=true`、全部 harness check、truthful readiness、managed process cleanup 与 nonce-root removal，故本专题
更新为 `[live-confirmed fixture-scoped]`。stable root/saved scopes、非空 indicator kinds、完整 structured effect preview、
event-window lifecycle 与 semantic event decision 仍然没有完成。
