# current-event-window-context-v1：paused generic live 验收夹具

## 当前证据状态

- **[live-confirmed harness RED；not capability evidence]** Attempt1 在事件物化前因 CK3 PhysFS 路径超长退出；
  它只证明 runner 路径故障。
- **[live-confirmed capability RED]** Attempt2 已通过短路径 gate 并真实物化目标事件，但旧冻结 DLL 把
  `CEventOption+0x478 timeout_option` 错当成 cancel 来源，使 authored native index `3` 的
  `is_cancel_option=yes` 发布为 `cancel=false`。因此 `current_event_window_context_live_ready` 仍不得标为 `true`，
  fixture 预期也不得降成 false 来掩盖故障。
- **[static-confirmed；not-live-evidence]** exact parser/token/consumer 已把 cancel 更正到 authored
  `CEventOption+0x47A`；combined cancel + indicator source、runner 与 focused unit 静态更新后，仍须由主代理冻结新
  commit/DLL 再进行全新 live candidate。本轮文档与 runner 修订没有启动或 attach CK3。
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
3. `calculated_event_id` 与 `runtime_stats_ordinal` 各自是 signed int32，并且 seed/cold/两次 cold query 均不漂移；
   不推断其正负值业务语义，也不把 ordinal 当 canonical identity；
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

## 静态测试结果与待批准命令

[static-confirmed] focused unit 覆盖 exact fixture bytes、seed/cold projection、现有 fixture session seam、双查询
frame equality、full-ID/revision drift、key/两 int32/option/readiness/effect/scopes malformed、跨 PID/checkpoint 绑定以及
preflight 不得 launch：

```powershell
py -m unittest ck3_autonomous_player.tests.unit.test_current_event_window_context_live_acceptance -v
```

本轮 combined cancel/indicator 合同更新的 focused suite 为 `13/13`，shared event-window Python suite 为
`17/17`，`py_compile` 与两个 ABI verifier 均通过；收口检查 CK3/Python 进程数均为 0。Attempt2 已执行且是上述
immutable capability RED；旧
`aab1daf...` source tree、DLL SHA 与 injector 只能复核历史 artifact，绝不能再次作为 live candidate。

下一次 live 命令暂不冻结在文档中。主代理必须先审阅并提交 combined cancel + indicator source，fresh MSVC build，
再把新的完整 source commit、DLL SHA-256、injector SHA-256 同步写入 runner 常量、focused unit 与本页；之后另用新的
pipe/output 名运行唯一 candidate。未获得主代理明确批准前不得启动 CK3。新 candidate 仍使用默认
`%TEMP%\xew-<32-hex>` root 来复验 path gate，且 artifact 必须明确引用新的 commit/DLL，不能覆盖 Attempt2。

只有 artifact 自身 `ok=true`、全部 harness check 为 true、readiness 精确保持
identity/presentation/indicator true 与 preview/semantic false、managed process cleanup 与 nonce-root removal 都为 true 后，
才能把本专题从 [not-live-evidence] 更新为 `[live-confirmed fixture-scoped]`。即使该次通过，stable root/saved scopes、
完整 structured effect preview 与 semantic event decision 仍然没有完成。
