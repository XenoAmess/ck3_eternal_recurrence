# current-event nonempty effect indicators：paused live 夹具

## 当前状态

- **[live-confirmed fixture-scoped]** 2026-08-27 Attempt1 已用 bounded、generic、非宗教 runner 完成真实 CK3
  seed → checkpoint → fresh-cold paused 验收：
  [`run_current_event_nonempty_effect_indicators_live_acceptance.py`](../../ck3_autonomous_player/native_bridge/research/run_current_event_nonempty_effect_indicators_live_acceptance.py)。
- [static-confirmed] runner 复用 Attempt4 已验收的 managed seed → checkpoint → fresh-cold 会话、production native
  bridge、不可变源存档、逐字节 checkpoint transfer、双查询、进程回收与 nonce root cleanup；它不复制或放宽这些门。
- [static-confirmed] focused tests：
  [`test_current_event_nonempty_effect_indicators_live_acceptance.py`](../../ck3_autonomous_player/tests/unit/test_current_event_nonempty_effect_indicators_live_acceptance.py)。
- [live-confirmed fixture-scoped] production reader 在两个不同 CK3 PID 中实读空 control、`trait/add brave` 与
  `stress/increase affected=false` → `death/played_character`，fresh-cold 重新物化后结构一致；完整 artifact、PID、checkpoint
  与 cleanup 证据见下文。这个等级不外推到 stock event、视觉图标、其它同 kind 分支或完整 effect preview。

本夹具的 production query 只读取通用事件按钮已经物化的 `OptionEffectItem` vector；seed setup 会在 disposable clone 内
写 single-use guard、触发夹具事件并保存 checkpoint，因此不能笼统称整条 harness 为“无写入只读”。它不读取
faith/doctrine/tenet/fervor、改宗、宗教改革、holy order 或任何宗教专用事件树。战争圣战与婚姻必要 faith 判定的两项
窄例外均与本夹具无关。

## 为什么需要独立非空夹具

Attempt4 已证明三个真实物化 option 都能发布：

```json
{
  "status": "available",
  "coverage": "played-character-event-icon-indicators-1.19.0.6-v1",
  "complete_effect_set": false,
  "rows": []
}
```

这只闭合了空 vector 的 transport、coverage 与 readiness，不能证明四种已静态闭合的 native kind 在真实 CK3
materializer 中能够被 production reader 解码。本夹具只推进这个缺口：用同一 current-window query 命中 trait、stress 与
death 三条特定 row，同时保留一个 `rows=[]` 对照。它不选择选项，也不借机验证 effect execution 或 selection lifecycle；
更不外推为 trait remove、stress decrease/affected=true/critical transition 或整个 kind family 的 live 覆盖。

## 冻结夹具矩阵

事件 canonical key 为 `xar_event_indicator_live_fixture.1`。definition UTF-8 BOM bytes SHA-256 为
`4E532E372932276A26B549B0B3A8A67C3943EC5762B7773940E03BA3E04329C3`；definition 加九语言 ASCII
acceptance localization 的 canonical manifest SHA-256 为
`8110439FBCBCD3DB8FE0AED0B2B040339940E344485B92BC8A626AF0B7C317DE`。这些 localization 只是 disposable fixture
占位，不是发布翻译。

| authored native index | 定义 | 必须物化的结果 |
|---:|---|---|
| `0` | enabled、无 gameplay effect | rendered `0`；`effect_indicators.rows=[]`，作为空 row control |
| `1` | enabled；`add_trait_force_tooltip = brave` | rendered `1`；恰好一条 `trait/add`，identity `available`、key `brave`、native ID 为 `0..2^31-1` |
| `2` | `trigger = { always = no }` | hidden，不进入物化 vector |
| `3` | enabled/cancel；先 `add_stress = minor_stress_gain`，再对 root 描述 `death_accident` death | rendered `2`；恰好两条 row，顺序为 `stress/increase` 后 `death/played_character` |
| `4` | invalid fallback | 因 regular item 已存在而不进入物化 vector |

stress row 必须保留 `magnitude={status=unavailable}`、`affected_by_trait=false`；`critical` 可按冻结角色当前 stress
边界为 true 或 false，但必须是 bool。death row 必须精确为：

```json
{
  "kind": "death",
  "subject": "played_character",
  "direction": "not_applicable"
}
```

不允许把 death materializer 的机械 `gain=1` 发布为收益。stress 与 death 都是在 visitor traversal 返回后追加，故本夹具
按已冻结的 materializer 顺序要求 stress 在 death 之前；它仍不代表 authored effect 的完整执行顺序。

## 两阶段不选项观测序列

```mermaid
sequenceDiagram
    participant I as immutable save
    participant S as seed PID
    participant C as fresh-cold PID
    participant B as production native bridge

    I->>S: clone + production + mod_bridge + exact indicator fixture
    S->>S: guarded trigger_event while paused
    S->>B: query current-event context
    S->>S: save active-event checkpoint; select nothing
    S-->>C: byte-identical checkpoint + fixture
    Note over C: production + fixture; no mod_bridge/inbox
    C->>B: query @ revision R
    C->>B: adjacent query @ same revision R
    C->>C: managed shutdown + nonce-root cleanup
```

seed native transcript 只能是 `query-current-event-window-context-v1`、`save-checkpoint`；cold transcript 只能是连续两次
query。seed 此前由 disposable `mod_bridge` 执行 guard + `trigger_event` setup；两阶段都禁止 `select-event-option-*` 与
`auto-turn`。因此 definition 中的 trait/stress/death 只参与 engine-owned GUI-description row 物化，从未执行；玩家 trait、
stress 与生死状态不是本轮后置条件，也不得被夹具改变。本 runner 不截取或比对 GUI 图标像素，故即使 GREEN 也只能证明
GUI backing rows 与 typed query，不能声称视觉图标已经人工/截图核验。

## GREEN 合同

一次候选只有同时满足下列项目才可标为 `fixture-scoped-live-confirmed`：

1. frozen CK3 `1.19.0.6` EXE SHA、reviewed DLL/injector SHA、production dependency commit 与 immutable save
   全部等于 Attempt4 合同；任一漂移都在启动前 RED；
2. seed/cold 为不同正 PID，均 paused/map-ready，完整 event instance ID、date、canonical key 与 checkpoint bytes 一致；
3. cold 同 revision 双查询除 `query_sequence +1` 外严格相等；seed/cold 的 process-local calculated ID/runtime ordinal
   都必须为 signed int32，且 cold 两次 query 内不得漂移；seed 只有一次 query，不额外声称其进程内时间稳定，也不要求
   seed/cold 数值跨进程相等；
4. rendered/native 映射恰为 `(0,0) (1,1) (2,3)`，native `2/4` 不出现；
5. native `0` 空对照、native `1` 的 `trait/add brave`、native `3` 的 `stress/increase affected=false`→death rows
   逐字段满足上表，seed/cold 重新物化后的 options 结构完全相等；
6. 每个 materialized option 的 indicator surface 都保持
   `coverage=played-character-event-icon-indicators-1.19.0.6-v1` 与 `complete_effect_set=false`；
7. `effect_preview=unavailable/indicator_subset_has_no_completeness_signal`，resource/relationship delta 均 unavailable，
   `root_scope=null`、`saved_scopes=null`；
8. `effect_indicators_ready=true`，但 `effect_preview_ready=false`、`semantic_decision_ready=false`；非空 row 不能冒充
   完整 preview 或高智商事件选择 readiness；
9. 没有选项提交、没有时间推进，immutable source 不变，seed/cold managed cleanup、nonce root removal 与
   `no_ck3_processes_after=true` 全部通过。

失败时必须区分 parser/materializer/capability RED 与 harness/cleanup RED，保留 artifact，不得通过降低 row 预期或把 payload
改成 unknown 来制造 GREEN。

## 静态验收

2026-08-27 已执行、未启动 CK3：

```powershell
& 'tools\.venv\Scripts\python.exe' -m unittest `
  ck3_autonomous_player.tests.unit.test_current_event_window_context_live_acceptance `
  ck3_autonomous_player.tests.unit.test_current_event_nonempty_effect_indicators_live_acceptance `
  ck3_autonomous_player.tests.unit.test_event_window_context_v1_bridge -v
```

结果为 `49/49` GREEN。focused 新增 suite 为 `15/15`；覆盖 exact fixture bytes、scoped profile 恢复、短路径、cold
playset 无 mod_bridge、空对照、三种 typed row、错误 identity/row order/completeness 拒绝、semantic readiness false、跨 PID
绑定与禁止 option selection 的 transcript 边界。

## Attempt1 immutable GREEN

2026-08-27 08:58:38–09:01:14（Asia/Shanghai）执行以下命令；它已经成功结束，原 output 与 pipe 名不得覆盖或复用：

```powershell
$env:XAR_EVENT_WINDOW_ISOLATED_SOURCE_ROOT = 'C:\Users\xenoa\AppData\Local\Temp\xar-event-window-cea30a0-source'
& 'tools\.venv\Scripts\python.exe' `
  'ck3_autonomous_player\native_bridge\research\run_current_event_nonempty_effect_indicators_live_acceptance.py' `
  --game-dir 'Crusader Kings III' `
  --bridge-pipe '\\.\pipe\xar-event-nonempty-indicators-attempt1' `
  --bridge-dll 'ck3_autonomous_player\native_bridge\.build-event-window-cea30a0-msvc2\xar_ck3_bridge.dll' `
  --expected-bridge-dll-sha256 '52398435F8AA5177D6D507BFAA38CD2578EB988F0629F1C5E13360CC91FB3BB0' `
  --bridge-injector 'ck3_autonomous_player\native_bridge\.build-event-window-cea30a0-msvc2\xar_ck3_bridge_injector.exe' `
  --output 'C:\Users\xenoa\AppData\Local\Temp\xar-current-event-nonempty-indicators-attempt1.json'
```

冻结结果：

- artifact：`C:\Users\xenoa\AppData\Local\Temp\xar-current-event-nonempty-indicators-attempt1.json`，`136947` bytes，
  SHA-256 `1DE73B16CBD90FE05112D60A7F09274E95FE1BAC8D18D79C2AF8A8A2BC8249C3`，`ok=true`，
  `evidence_classification=fixture-scoped-live-confirmed`，elapsed `155.762s`；独立只读审计再次核对 artifact 与 runner stdout 一致。
- exact build：CK3 `1.19.0.6` EXE SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；DLL
  `52398435F8AA5177D6D507BFAA38CD2578EB988F0629F1C5E13360CC91FB3BB0`；injector
  `1618840EC108F688B3EBECC6D7F8963038BA64C8D4A3E10DDE2E29E3F443B4DF`；adapter
  `ck3-1.19.0.6-msvc-x64`；isolated production dependency commit
  `cea30a067b1e112596d70532b98fa068b2102ebf`。
- seed/cold：PID `23632/35364`，两边均 paused/map-ready；date `53175816`、完整 event instance `17` 与 canonical key
  `xar_event_indicator_live_fixture.1` 一致。process-local calculated ID/runtime ordinal 分别为
  `4350001/6763` 与 `4360001/6773`；两边只要求 signed int32，cold 相邻双查询内不漂移，不要求跨进程相等。
- 真实 options：rendered/native `(0,0) (1,1) (2,3)`；native `2` hidden、native `4` fallback 未物化。native `0`
  为 `rows=[]`；native `1` 恰为 `trait/add`、trait `available`、native ID `64`、key `brave`；native `3` 先发布
  `stress/increase`、`magnitude=unavailable`、`affected_by_trait=false`、`critical=false`，再发布
  `death/played_character/not_applicable`。seed/cold first/cold second 三份 option 结构一致，cold 相邻查询仅 sequence `1 → 2`。
- readiness 保持诚实：每项 coverage 都是 `played-character-event-icon-indicators-1.19.0.6-v1`，
  `complete_effect_set=false`；`root_scope/saved_scopes=null`；`effect_preview_ready=false`、
  `semantic_decision_ready=false`。stress magnitude 仍 unavailable。
- 三份 checkpoint 均为 `66594169` bytes、SHA-256
  `9E846D2B6ADFA3417D99B3544AA48D189BD2D53ED211AE1A5C8384397C7D5B88`。immutable source save 在运行前后均为
  `66594755` bytes、SHA-256 `5BA2136911EAD0CAF1F7D2F3DE02EAFBD8039861C46F01F35F698B3B5CFFFC5F`，mtime 也未变。
- seed command ledger 只有 query/save，cold 只有 query/query；没有 `select-event-option-*` 或 `auto-turn`。两个 managed
  process、driver 与 tree 均回收，nonce root 已删除，`no_ck3_processes_after=true`；独立审计时再次确认无 CK3 进程。
- 本次 wrapper 为 `17299` bytes、SHA-256
  `05563518839C6D715AB93E936E73E252A2724EAC92D31418F9E7C695D9DC7638`；复用的 base runner 为 `88233` bytes、SHA-256
  `99C9C7673C51B0B144365D255F7164D221D5B8CA4CBE3B94A5F970886C31D13C`。artifact 本身冻结 production dependency 与
  fixture manifest；wrapper/test 的仓库身份由本里程碑提交绑定。

## Attempt1 后仍未完成的能力

本次只把本矩阵的 **fixture `trait/add brave`、`stress/increase affected=false`（本帧 `critical=false` 只证明 bool
transport）与 death row** 升级为 live。trait remove、stress decrease/affected=true/critical transition、scheme row、视觉 GUI
图标、stock event、option selection lifecycle、实际 effect postcondition、stable root/saved scopes、stress magnitude、
resource/relationship delta、其它角色/战争/头衔效果、完整性信号、完整 structured preview 与 semantic event decision
仍然未完成。下一观测入口继续是另一 engine-owned structured visitor/tooltip model，而不是扩义 `OptionEffectItem`。
