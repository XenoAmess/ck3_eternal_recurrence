# G2 same-frame white-peace comparison（2026-09-07）

状态：**static-ready / no launch / no live promotion**。

## Research-first 输入

本包施工前重读了 G2 roadmap、`GEN-034` blocker、
[战争终止原生树](war-termination.md)、
[玩家战争退出策略](player-war-exit-policy.md) 与
[Raiktor 三方退出策略](raiktor-three-way-exit-policy.md)。冻结结论不变：白和、投降是两个独立原生结果；“按钮可用”与 acceptance raw 不能替代实际条款；没有 owner-approved utility model 时，条款差异不能变成 outcome preference。

现有 `raiktor-white-peace-comparison-provider-v1` 已能合取 white-peace observation、campaign、owner profile 与 utility evaluation 的 SHA/frame，但 source-specific lifecycle 的 durable pre-mutation checkpoint 尚没有一个独立 consumer，直接证明 source、white-peace 与 surrender 六域属于同一 paused source frame。尤其 six-domain v1 不携带 `snapshot_id`，不能脱离 source/white observation 自证 snapshot 身份。

## 静态 provider/comparator

`raiktor_same_frame_white_peace_comparator.py` 新增纯函数
`provide_raiktor_same_frame_white_peace_comparison`。它只接受三项显式输入：

1. `xar.ck3.g2_source_specific_pre_mutation_checkpoint.v1` durable source checkpoint；
2. `raiktor-white-peace-terms-observation-v1`；
3. `ck3-1.19.0.6-native-raiktor-surrender-six-domain-v1` aggregate。

source checkpoint 是 snapshot 锚。provider 必须同时证明：

- source 与 white-peace 的 `snapshot_id`、public revision、native revision、full-generation WarID 相等；
- source 与 surrender 的 public revision、native revision、WarID 相等；
- white-peace observation 的 `evaluated_surrender_terms_sha256` 等于实际 normalized surrender aggregate SHA；因此 surrender 的 `snapshot_id` 只能经由“同一 white frame + exact surrender hash”传递绑定，不能猜测或默认；
- date、PID、玩家/primary attacker 与完整 coarse Raiktor frame 也一致；
- source checkpoint 的 canonical binding SHA、全部 frame checks、white completeness 与 surrender action-terms readiness 为真。

完整静态输入只产生
`raiktor-same-frame-white-peace-comparison-v1`：它冻结 claims、gold、prestige、truce、PoW、favor 与 hostage observation boundary 的逐字段差异。它明确记录 `utility_compared=false / preferred_outcome=null`，所以不是既有三方 policy 所需的 owner-utility comparison certificate，也不替代 campaign 或 owner profile。

## Hash-bound no-launch comparator

离线文件入口为
`prepare_g2_same_frame_white_peace_comparison.py`。三项输入都必须给出 exact bytes SHA-256，输出路径必须尚不存在：

```powershell
& "Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe" `
  "ck3_autonomous_player\native_bridge\research\prepare_g2_same_frame_white_peace_comparison.py" `
  --source-checkpoint <source-checkpoint.json> `
  --source-checkpoint-sha256 <SOURCE_SHA256> `
  --white-peace-observation <white-peace-observation.json> `
  --white-peace-observation-sha256 <WHITE_SHA256> `
  --surrender-terms <surrender-six-domain.json> `
  --surrender-terms-sha256 <SURRENDER_SHA256> `
  --output <new-comparison.json>
```

runner 不枚举、不启动、不附加、不查询或终止 CK3，也不发送 mutation。无论输入自身是否声称 live，顶层恒为
`production_live=false`、`production_recommendation_ready=false`、`action_ready=false`、`action_literal=null`、`automatic_surrender_ready=false`、`gen034_closed=false`。

## Fixture 与验收边界

静态 source contract fixture 为
`raiktor_same_frame_white_peace_comparison_v1_contract.json`，显式标记
`synthetic_fixture_only=true / do_not_ship_as_live_evidence=true`。focused tests 覆盖：

- 完整同帧三路合取得到条款差异；
- `snapshot_id`、revision、native revision、WarID 任一漂移均 fail closed；
- stale surrender SHA 与 incomplete white observation 保持 typed RED；
- source binding SHA 漂移直接拒绝；
- hash-bound file runner 与 output overwrite guard；
- fixture 和所有 action/live/GEN-034 边界。

## 剩余 live gate

本包没有新增 production observation。下一次排他 CK3 生命周期仍须在 WarID `50331699` 的 durable pre-mutation source checkpoint 上，取得同一 paused frame 的完整 white-peace observation 与完整 surrender aggregate，再由本 comparator 复算。即使这一步 GREEN，owner-approved white-peace utility、campaign certificate、owner budget、三方推荐、typed submit 与 action-boundary postcondition 仍是独立门；`GEN-034` 继续 unresolved。
