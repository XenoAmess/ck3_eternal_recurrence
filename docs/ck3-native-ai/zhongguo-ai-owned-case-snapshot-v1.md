# 天朝 361 AI-owned B1 案卷原生快照 v1

## 当前边界

- 状态：`static-ready / fixture-ready / live-unverified`
- 能力：`game.command.query-zhongguo-ai-owned-case-snapshot-v1`
- 固定 step：`query-zhongguo-ai-owned-case-snapshot-v1`
- 固定案种：`zhongguo.b1.performance`
- 固定 route：`authorized_ai_background`
- CK3 实机 artifact：无；不得写成 `production-live`
- OCR：不参与查询、资格判定、路由或 GREEN 真值

这个 provider 补齐的是“案卷 owner 不是玩家，而是 AI 天朝制公爵及以上领主”这一条只读观测路径。它与已有玩家-owner
`query-zhongguo-case-snapshot-v1` 互补，不会把两种 owner 混成同一授权路径：请求 owner 等于 paused played character 时，在读取任何
B1 变量之前返回 `owner_is_played_character`；授权 AI owner 则返回同一 B1 案卷 identity、stage、policy、operation、receipt 和 readiness，
并额外给出 manager 资格与 AI 后台 route。

它不切换玩家，不操纵 AI，不执行事件、decision、interaction 或任意变量写入。当前 v1 也不声称覆盖玩家案卷 provider 的 deadline
投影；它只覆盖下文固定的 17 项 B1 状态与 roster-lock receipt。

权威实现与合同文件为：

- typed ABI：`native_bridge/include/xar_bridge/zhongguo_ai_owned_case_snapshot_v1.hpp`
- reader / serializer：`native_bridge/src/zhongguo_ai_owned_case_snapshot_v1.cpp` 与
  `native_bridge/src/zhongguo_ai_owned_case_snapshot_v1_serializer.cpp`
- application-main mailbox：`native_bridge/include/xar_bridge/zhongguo_ai_owned_case_snapshot_v1_mailbox.hpp` 与
  `native_bridge/src/zhongguo_ai_owned_case_snapshot_v1_mailbox.cpp`
- JSON Schema：`schemas/zhongguo-ai-owned-case-snapshot-v1.schema.json`
- ABI / source fixture：`native_bridge/research/zhongguo_ai_owned_case_snapshot_v1_abi.json` 与
  `native_bridge/research/fixtures/zhongguo_ai_owned_case_snapshot_v1_source_contract.json`

## 请求与固定读取面

公开请求只允许：

```text
request_nonce
expected_revision
owner_character_id
subject_character_id
```

`case_kind`、变量名、scope alias、资格布尔值和任何动作参数都不是公开输入。caller 提交的 owner/subject 只是本次固定查询的 identity
filter；资格必须由 application-main 上的 exact-build 原生观测得出，不能由 caller 声明。

subject scope 只双读以下 17 个编译期固定变量：

| 组 | 固定变量 |
|---|---|
| B1 identity/stage | `zg361_b1_case_owner`、`zg361_b1_case_subject`、`zg361_b1_cycle_serial`、`zg361_b1_case_serial`、`zg361_b1_case_state`、`zg361_b1_case_active`、`zg361_b1_case_revision`、`zg361_b1_case_timeline_serial`、`zg361_b1_case_feedback_revision` |
| operation/policy | `zg361_b1_case_last_operation`、`zg361_b1_case_last_choice` |
| roster-lock receipt | `zg361_b1_roster_lock_receipt_owner`、`zg361_b1_roster_lock_receipt_subject`、`zg361_b1_roster_lock_receipt_cycle`、`zg361_b1_roster_lock_receipt_case`、`zg361_b1_roster_lock_receipt_state`、`zg361_b1_roster_lock_receipt_choice` |

数值变量仍按 CK3 character-variable kind `1` / Q100000 解码；角色 target 必须为 kind `4`，并经 generation-aware character store
重新解析后才发布 CharacterID。provider 不暴露 arbitrary variable reader。

## AI manager 资格

在任何 17-row 读取之前，reader 必须从真实原生对象证明：

1. owner 与请求 owner 相同，仍存活；
2. compiled `is_ai` 语义为真；存活/In-office 是独立门槛，不能拿“死亡角色也会被 is_ai evaluator 归类为 AI”绕过；
3. effective government stable key 精确等于 `celestial_government`；
4. owner 有真实 primary landed title，tier 为 `3..6`，即 `duchy / kingdom / empire / hegemony`；
5. subject 的 immediate liege 经 generation-aware character resolver 解析后就是该 owner。

失败分别返回 `owner_not_alive`、`owner_not_ai`、`owner_not_celestial`、`owner_not_landed_duke_plus` 或
`subject_not_direct_subject`，而且不会继续读取 B1 变量。owner/subject 解析、title/government/liege 调用或 stable-key 读取失败统一是
`owner_eligibility_unavailable`，不能降级为 caller assertion。

成功时 `owner_eligibility` 发布 owner、AI、primary title、tier、government 与 immediate-liege 事实，`authorized=true`；这组事实本身也会在
同一查询内读取两遍并要求逐字段相等。

## Stage、route 与 receipt

`stage` 是对真实 `zg361_b1_case_state` 和 `zg361_b1_case_active` 的封闭投影：

| state | key | active |
|---:|---|---|
| 1 | `targets_open` | true |
| 2 | `midcycle_open` | true |
| 3 | `evidence_open` | true |
| 4 | `facts_frozen` | true |
| 5 | `shadow_open` | true |
| 6 | `quota_ready` | true |
| 7 | `calibration_open` | true |
| 8 | `published` | false |

不满足该矩阵时响应仍可为 `status=available`，但 `stage.key` 为 typed `stage_inconsistent`、`stage_ready=false`、总 `ready=false`；不能把畸形
产品状态伪装为顶层查询失败，也不能把 `available` 等同于业务 ready。

当前操作 allowlist 只有真实 `operation_id=39 + choice=1`，投影为 `mechanism_039 / roster_lock`。receipt 必须与同一
owner/subject/cycle/case 严格 join 且 choice 为 1，才是 `recorded`。`operation_id=0` 是合法 typed negative：旧 receipt 即使仍残留也会被清掉，
返回 `not_recorded / receipt_not_recorded`，并且 `receipt_ready=true`。未知操作或不一致 receipt 不会被补零。

`route.kind=authorized_ai_background`、`visible_event_allowed=false` 不是从某个 mod route 变量直接读取的事实，而是以下已验证事实的
**语义投影**：owner 为授权 AI manager、subject 为其直属受评者，而可见交互仍只允许玩家路径。它只能用于区分 AI 后台处理路径，不能被引用为
“CK3 已持久化 route 字段”或“provider 已执行 AI 动作”的证据。

## Exact-build ABI

该实现只绑定以下构建：

- 游戏版本：CK3 `1.19.0.6`
- `ck3.exe` SHA-256：`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`

冻结的只读锚点与布局为：

| 语义 | RVA / offset |
|---|---|
| character variable context | `0x3329A40` |
| character storage / fallback slot | `0x570C130` / `0x570C138` |
| landed-title storage / fallback slot | `0x570C410` / `0x570C3F8` |
| government fallback slot | `0x570CB50` |
| primary-title resolver | `0x25F3350` |
| immediate-liege resolver | `0x2613480` |
| effective-government resolver | `0x26165B0` |
| is-human-player leaf | `0x28BCEB0` |
| character identity / death marker | `+0x18` / `+0x1C8` |
| landed-title identity / template | `+0x10` / `+0x160` |
| title-template tier | `+0x5C` |
| government stable key (`std::string`) | `+0x18` |

`0x2613480` 和 `0x26165B0` 在本合同中分别只表示 immediate liege 与 effective government。它们不能从其他旧命名字段推断或复用；升级游戏
版本时必须重新冻结 EXE hash、调用签名、对象布局和 generation resolution，不能只改版本字符串。

所有引擎调用都只在 paused application-main mailbox 执行并包裹 SEH。原子性顺序为：

```text
frame before
  -> eligibility observation #1
  -> 17 allowlisted rows #1
  -> eligibility observation #2
  -> 17 allowlisted rows #2
  -> frame after
```

两帧、两组资格事实和两组 raw rows 必须完全相同，否则返回 `state_changed`。查询结束后不保留 CK3 engine pointer。

## Readiness 与实机晋级门

聚合 `ready` 只在以下六个 component gate 全部为真时为真：

```text
owner_eligibility_ready
case_identity_ready
stage_ready
route_ready
receipt_ready
same_frame_ready
```

`ready` 是这六项的合取结果。`status=available` 只说明固定读取得到可解释响应，不代表所有业务 gate 都通过。

当前 native reader、serializer、schema 与离线 fixture 只能证明 `static-ready / fixture-ready`。没有 exact-build paused MCP artifact 以前，
不得宣称 `production-live`，也不得让 runner 用 OCR、坐标或测试决议绕过。首轮 MCP-first 实机批次至少要保存：

1. 真实 AI 天朝制 duchy owner + 直属 subject 的完整可用响应；
2. kingdom/empire/hegemony 中至少一个更高 tier 的正例；
3. player owner、human owner、非天朝政府、county、非直属 subject 五类读取前拒绝；
4. state `1..8` 的 stage/active 映射，以及至少一个 `stage_inconsistent` typed negative；
5. `roster_lock` recorded 与 zero-operation `not_recorded` 两种 receipt；
6. 同一 request 的 frame/eligibility/raw-row drift 负例，证明不会混帧；
7. source/binding 中的 nonce、public/native revision、date、paused player、owner、subject、connection generation 与 exact DLL identity 全部一致。

所有实机响应、RED attempt 和 fixture 输出都应保留原始 JSON；截图只可在 MCP 真值闭合后作为展示物料补做。

## Fresh MSVC 构建路径教训

在当前较深的 integration worktree 内，把 fresh Ninja build 目录继续放在
`native_bridge/.build-ai-owned-case-integrated-*` 下，会让部分既有长 target 的
`/Fd` 路径越过 MSVC 可用边界，表现为与本 provider 无关的
`fatal error C1083: 无法打开编译器生成的文件: “”: Invalid argument`。失败目录应原样保留作诊断，
不能把这类 harness RED 记成 capability RED。相同源码改用短绝对 fresh root
（本轮为 `Z:\xar-ai20-20260831-02`）后，完整 DLL 构建和 focused CTest 均通过。
后续同类原生 provider 应优先给 `build_fresh.ps1 -BuildDir` 传入短绝对路径，同时仍保留脚本的
source fingerprint 与 `ck3_11906.hpp` Ninja dependency gate。
