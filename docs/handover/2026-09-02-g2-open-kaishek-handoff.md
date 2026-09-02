# G2 与 open_kaishek 交接（2026-09-02）

本文件是本次休假前的可复核交接基线。结论只使用已经存在的静态/paused
artifact；没有重跑 CK3，也没有扩大公共 ABI、MCP wire 或写操作。

## 仓库与 CI 基线

| 仓库 | 主线状态 | 最近提交 | 最近 CI |
| --- | --- | --- | --- |
| `ck3_eternal_recurrence` | `master` 已推送且工作树 clean | `7f31580`（can-be-acclaimed 记录） | Official Runner CI `33592554247` **SUCCESS** |
| `open_kaishek` | `main == origin/main`，clean | `759199b`（can-be-acclaimed schema fixture） | core-ci `33592356916`、`33592340523` **SUCCESS** |

本次交接前的 429 规则已在父仓 `AGENTS.md` 与
[`docs/branch-management.md`](../branch-management.md) 落盘（`340fd0b`）：子进程遇
429 先复用原线程/工作树继续同一 bounded 包，保留已有证据；不得从头重复无变化的
验证。临时分支应尽早合回主线。

## G2（GEN-034）

### 已闭合的事实

- 冻结 CK3 `1.19.0.6`，EXE SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`。
- `580f54f` 固化了 `CAddTruce` 两处 call-site 到 evaluator RVA `0x3373000` 的只读
  合同：script value `[effect+0x108]`、evaluation context `[context+0x28]`，返回
  signed `int32`；verifier 一次通过 `exact_build=1 evaluator=1 call_sites=2 read_only=1`。
  合同 SHA-256 为
  `55E5203647D2D0D0F017E990CBB736F42E306EFEE1269D7918DF39735A812799`。
- 最新 semantic-ready paused 报告：
  `Z:\ck3_mod_rewrite_process_assets\zg361\g2-fresh-semantic-ready-20260902T100431236\report.json`，
  SHA-256
  `4A7C66D34C851698572F4BBA2970ECAA00C005C2DC338ABCD75A7FD304F0B991`。
  该帧 WarID `50331699`、CharacterID `29829`，四域只读 terms（gold、prestige、
  prisoner-release、favor-hook）可观察且同帧双查询一致。
- 同次运行的 open_kaishek 预验：
  `...g2-fresh-semantic-ready-20260902T100431236\open-kaishek-preflight-mod-20260902.json`，
  SHA-256
  `5F7F67C439D8721E56C735E2DFA49E07A32630DD7019EB221C1C1215DD68AC90`。这是离线
  parser/profile 证据，不是 CK3 live 证据。

### 仍未闭合（GEN-034 不得升级）

当前 truce 行仍为 `evaluated_days_observable=false`、`evaluated_days=null`、
`expiry_date_raw=null`；因此 `truce_ready=false`、`decision_ready=false`，整体仍是
`static/query-ready + paused/live=false`（已有只读 primitive 不等于完整战役闭环）。
尚未取得：真实 evaluator input/result、expiry/期限持久化、war-bound/campaign
dominance、continue-vs-surrender policy、typed action、white-peace/投降写入及
postcondition。不要猜 offset、不要添加 public duration 字段、不要重复相同 checkpoint
timeout。

下一最小入口：绑定冻结 checkpoint/driver 后先运行当前 open_kaishek 离线预验；仅在
semantic-ready action literal 与角色/日期/WarID 快照同时存在时，做一次现有只读 paused
terms probe，保留两份 payload 及 SHA。若失败，只能使用已合入的 test-only
`RaiktorSurrenderTruceFailureV1` seam 做离线分类，不能把失败原因写入 public JSON/MCP
或 readiness。

## open_kaishek 当前能力

- `is_acclaimed`：`TRIGGER/CHARACTER/BOOLEAN`、0 参数、deterministic/read-only、
  `certified=false`；预验 artifact
  `Z:\ck3_mod_rewrite_process_assets\zg361\kaishek-is-acclaimed-20260902.json`，
  SHA-256 `D48913E0F4A831B0220EE2A818393CB3AA42B88D8B976097CF9652DEF30FFC73`；JAR
  SHA-256 `D1341CD872D07E8081A4E53040655C420FB4A8EEDD24DC5DE616761CDFF068A2`。
- `can_be_acclaimed`：同为 `TRIGGER/CHARACTER/BOOLEAN`、0 参数、
  `certified=false`；预验 artifact
  `Z:\ck3_mod_rewrite_process_assets\zg361\kaishek-can-be-acclaimed-20260902.json`，
  SHA-256 `503BA9C9F7D49E4154BC6B0FD29E763A59FD1AAC1BA3AED24767C29DC4ABE409`；JAR
  SHA-256 `421F49C93B21DBE5D96BFD81FFBFE422EB098B2170ECC498A415D4125490F2CB`。
- 两个切片都只覆盖 profile、validator、fixture、CLI 和 OfflinePreflight；parser/
  validator 为单文件 `163 bytes / 0 diagnostics`，IR/runtime 明确 `SKIPPED`，
  `ck3_started=false`、无 save/network。它们不提升 phase2/G2 readiness。
- `has_accolade_parameter` 仅完成静态审计，暂不实现：证据指向 scalar STRING，但
  native 要求 scope kind `0x24`（ACCOLADE），而当前 `ScopeType` 尚无 ACCOLADE。
  已知 literal/evaluator/helper：`0x434F9A8`、`0x2819DC0`、`0x251CB60`；注册区
  `0x52C7C0..0x52C853`，vtable `0x4350A20`。若后续施工，必须先同时扩展 profile/runtime
  scope enum，再登记 `TRIGGER/ACCOLADE/STRING`；不得把它误注册为 CHARACTER/THIS，
  也不得宣称 runtime-certified。

## 下一位执行者清单

1. 先 `git fetch` 并确认两仓主线仍为上述提交；所有 CK3 验收先跑 open_kaishek
   preflight，一次必要验证后提交并 push。
2. G2 只等待新的 exact-build paused evaluator input/result 证据；无证据时维护
   `GEN-034 unresolved`，不重放同形 timeout。
3. 继续 open_kaishek 的窄 schema slice，但保持 `certified=false` 与少分支；涉及
   ACCOLADE 前先解决 scope enum 合同。
4. 报告中保留上述 artifact 路径和 SHA；不要把离线预验、fixture 或 ACK 写成
   `fixture-live`/`production-live loop`。

